#!/usr/bin/env python3
"""Platsbanken-scanner — söker nya jobb och uppdaterar pipeline-filer.

Användning:
    python af-mcp/scan.py              # senaste 7 dagarna
    python af-mcp/scan.py --days 14    # senaste 14 dagarna
    python af-mcp/scan.py --dry-run    # visa resultat utan att skriva filer
    python af-mcp/scan.py --no-filter  # skippa titelfiltrering (debugging)

Exit-koder:
    0  OK (även när inga nya jobb hittades)
    1  saknad fil eller pipeline.html-skrivning vägrad av safe_write
    2  alla sökningar misslyckades (API/nät nere) - ingenting skrevs
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import re
import sys
from datetime import date
from html import escape
from pathlib import Path

import httpx
import yaml

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
JOBSEARCH_BASE = "https://jobsearch.api.jobtechdev.se"
TODAY = date.today().isoformat()

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
CAREER_OPS = ROOT / "career-ops"
SCAN_HISTORY = CAREER_OPS / "data" / "scan-history.tsv"
PIPELINE_MD = CAREER_OPS / "data" / "pipeline.md"
PIPELINE_HTML = ROOT / "pipeline.html"
PORTALS_YML = CAREER_OPS / "portals.yml"

INIT_HINT = "Kör: python af-mcp/init.py"

# Sökningarna (vilka termer, vilken ort, vilken kategori) läses numera från
# portals.yml -> platsbanken.searches, inte hårdkodade här. Se
# career-ops/templates/portals.svenska.example.yml för formatet.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_portals_config() -> dict:
    """Laddar portals.yml. Hårt fel om den saknas — ingen tyst nollfiltrering."""
    if not PORTALS_YML.exists():
        print(
            f"❌ {PORTALS_YML.relative_to(ROOT)} saknas — kan inte köra scan.py utan den "
            "(sökfrågor och titelfilter bor där).\n"
            f"   {INIT_HINT}",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(PORTALS_YML, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_platsbanken_config(config: dict) -> tuple[str, str, list[dict]]:
    """Läser platsbanken-blocket: (default_municipality, default_city, searches)."""
    pb = config.get("platsbanken")
    if not pb or not pb.get("searches"):
        print(
            f"❌ {PORTALS_YML.relative_to(ROOT)} saknar ett platsbanken:-block med searches.\n"
            "   Se career-ops/templates/portals.svenska.example.yml för formatet.",
            file=sys.stderr,
        )
        sys.exit(1)
    return pb.get("municipality", ""), pb.get("default_city", "Sverige"), pb["searches"]


def _tags_for_search(search: dict, default_city: str) -> tuple[str, str]:
    """Returnerar (data-tags sträng, kategori-label) utifrån en searches-post i portals.yml.

    'category' styr CSS-klassen (bara tech/komm finns som taggfärger i pipeline.html),
    valfri 'label' styr den synliga texten (t.ex. "Python" istället för generiska "Tech").
    """
    category = (search.get("category") or "tech").strip().lower()
    tag_class = "komm" if category == "komm" else "tech"
    cat_label = search.get("label") or {"tech": "Tech", "komm": "Kommunikation"}.get(
        category, category.capitalize()
    )
    tags = f"{tag_class} gbg new"

    if search.get("remote"):
        tags = tags.replace("gbg", "remote")
    return tags, cat_label


async def _fetch(path: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{JOBSEARCH_BASE}{path}",
            params=params,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        return r.json()


def _load_title_filters(config: dict) -> tuple[list[re.Pattern], list[re.Pattern]]:
    """Kompilerar positiva och negativa titelfilter ur portals.yml-configen till regex."""
    tf = config.get("title_filter", {})

    def _compile(terms: list[str]) -> list[re.Pattern]:
        patterns = []
        for term in terms:
            t = term.strip()
            # Word boundaries förhindrar att "PR" matchar "primärvården", "AI" matchar "mail" etc.
            patterns.append(re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE))
        return patterns

    return _compile(tf.get("positive", [])), _compile(tf.get("negative", []))


def _passes_title_filter(
    headline: str,
    positive: list[re.Pattern],
    negative: list[re.Pattern],
) -> bool:
    """True om headline matchar minst ett positivt mönster och inget negativt."""
    if not positive and not negative:
        return True
    if positive and not any(p.search(headline) for p in positive):
        return False
    if any(n.search(headline) for n in negative):
        return False
    return True


def _load_known_ids() -> set[str]:
    """Laddar alla Platsbanken-IDs som redan finns i scan-history och pipeline.html."""
    known: set[str] = set()

    if SCAN_HISTORY.exists():
        with open(SCAN_HISTORY, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                m = re.search(r"/annonser/(\d+)", row.get("url", ""))
                if m:
                    known.add(m.group(1))

    if PIPELINE_HTML.exists():
        for m in re.finditer(r"/platsbanken/annonser/(\d+)", PIPELINE_HTML.read_text(encoding="utf-8")):
            known.add(m.group(1))

    return known


async def _search(q: str, municipality: str, remote: bool | None, published_after: str, limit: int = 50) -> list[dict] | None:
    """Returnerar träfflistan, eller None om anropet misslyckades.

    None (inte []) så att main() kan skilja "inga träffar" från "API:t svarade
    inte" — annars ser ett trasigt API ut som en lyckad körning utan nya jobb.
    """
    params: dict = {
        "q": q,
        "limit": limit,
        "sort": "pubdate-desc",
        "published-after": published_after,
    }
    if municipality:
        params["municipality"] = municipality
    if remote:
        params["remote"] = "true"

    try:
        data = await _fetch("/search", params)
        return data.get("hits", [])
    except Exception as e:
        print(f"  ⚠️  Sökning '{q}' misslyckades: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# HTML-generering
# ---------------------------------------------------------------------------
def _html_entry(ad: dict, data_tags: str, cat_label: str, default_city: str) -> str:
    # Em-dash får ALDRIG slinka in i output (hård regel). En-dash är ok.
    # Allt som kommer från API:t eller portals.yml HTML-escapas: annonsrubriker
    # som "Sales & Marketing" eller "<Remote>" får inte bryta markupen eller
    # injicera HTML i pipeline.html.
    headline = escape((ad.get("headline") or "Utan rubrik").replace("—", "-"))
    employer = escape(((ad.get("employer") or {}).get("name") or "Okänd").replace("—", "-"))
    wp = ad.get("workplace_address", {}) or {}
    city = escape(wp.get("city", "") or wp.get("municipality", "") or "")
    cat_label = escape(str(cat_label))
    default_city = escape(str(default_city))
    ad_id = escape(str(ad.get("id", "")))
    url = f"https://arbetsformedlingen.se/platsbanken/annonser/{ad_id}"

    deadline = ad.get("application_deadline", "")
    if deadline and "T" in deadline:
        deadline = deadline.split("T")[0]

    deadline_html = ""
    if deadline:
        try:
            dl = date.fromisoformat(deadline)
            days_left = (dl - date.today()).days
            if days_left <= 14:
                deadline_html = (
                    f' <span style="color:#f87171;font-size:0.75rem;margin-left:0.5rem">'
                    f'⚠️ Deadline {deadline}</span>'
                )
        except ValueError:
            pass

    is_remote = "remote" in data_tags
    loc_tag = (
        '<span class="tag tag-remote">Remote</span>'
        if is_remote
        else f'<span class="tag tag-gbg">{default_city}</span>'
    )
    cat_class = "tag-komm" if "komm" in data_tags else "tag-tech"
    description = f"{employer} - {city}" if city else employer

    return (
        f'  <a href="{url}" target="_blank" class="job" data-tags="{data_tags}">\n'
        f'    <div class="job-info">\n'
        f'      <div class="job-title">{headline}{deadline_html}</div>\n'
        f'      <div class="job-company">{description}</div>\n'
        f'    </div>\n'
        f'    <div class="tags">\n'
        f'      <span class="tag tag-new">NY</span>\n'
        f'      <span class="tag {cat_class}">{cat_label}</span>\n'
        f'      {loc_tag}\n'
        f'    </div>\n'
        f'    <span class="arrow">→</span>\n'
        f'  </a>\n'
    )


def _pipeline_md_entry(ad: dict, default_city: str) -> str:
    headline = ad.get("headline", "Utan rubrik")
    employer = ad.get("employer", {}).get("name", "Okänd")
    wp = ad.get("workplace_address", {}) or {}
    city = wp.get("city", "") or wp.get("municipality", default_city)
    ad_id = ad.get("id", "")
    url = f"https://arbetsformedlingen.se/platsbanken/annonser/{ad_id}"
    return f"- [ ] {url} | {employer} | {headline} ({city})"


# ---------------------------------------------------------------------------
# Pipeline HTML update
# ---------------------------------------------------------------------------
# _update_pipeline_html och _update_senast_skannad togs bort 2026-07-09 efter
# pipeline-korruptionsincidenten. Nya jobb infogas nu direkt i Ovärderade-sektionen
# via pipeline_lib (backup + atomisk skrivning + verifiering + räknarsynk).
# Inga fler lösa <!-- NYA JOBB -->-sektioner.


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main(days: int, dry_run: bool, no_filter: bool) -> None:
    from datetime import timedelta
    since = date.today() - timedelta(days=days)
    published_after = f"{since.isoformat()}T00:00:00"

    print(f"🔍 Platsbanken-scan — {TODAY} (senaste {days} dagarna)")
    if dry_run:
        print("  [DRY RUN — skriver inga filer]")

    config = _load_portals_config()
    municipality_default, default_city, searches = _load_platsbanken_config(config)
    print(f"  {len(searches)} sökningar konfigurerade, default-ort: {default_city}")

    # Ladda titelfilter
    if no_filter:
        positive_filters: list[re.Pattern] = []
        negative_filters: list[re.Pattern] = []
        print("  [--no-filter: titelfiltrering avstängd]")
    else:
        positive_filters, negative_filters = _load_title_filters(config)
        if positive_filters:
            print(f"  Titelfilter: {len(positive_filters)} positiva, {len(negative_filters)} negativa termer")
    print()

    known_ids = _load_known_ids()
    print(f"  Kända Platsbanken-annonser: {len(known_ids)}\n")

    # Kör alla sökningar
    all_hits: dict[str, dict] = {}          # ad_id -> ad
    id_to_search: dict[str, dict] = {}      # ad_id -> searches-post (för taggning)

    failed: list[str] = []

    for search in searches:
        q = search["q"]
        municipality = search.get("municipality", municipality_default)
        remote = search.get("remote")
        label_loc = " (remote)" if remote else f" ({default_city})" if municipality else " (Sverige)"
        print(f"  🔎 '{q}'{label_loc}...")
        hits = await _search(q, municipality, remote, published_after)
        if hits is None:
            failed.append(q)
            print("    → MISSLYCKADES (se varning ovan)")
            continue
        new_here = 0
        filtered_out = 0
        for ad in hits:
            ad_id = str(ad.get("id", ""))
            if not ad_id or ad_id in known_ids or ad_id in all_hits:
                continue
            headline = ad.get("headline", "")
            if not _passes_title_filter(headline, positive_filters, negative_filters):
                filtered_out += 1
                continue
            all_hits[ad_id] = ad
            id_to_search[ad_id] = search
            new_here += 1
        filter_note = f", {filtered_out} filtrerade" if filtered_out else ""
        print(f"    → {len(hits)} träffar, {new_here} nya{filter_note}")

    # Alla sökningar misslyckades = API:t är nere, nätet blockerat e.d. Det får
    # ALDRIG se ut som "inga nya jobb" — särskilt inte i schemalagda körningar.
    if failed and len(failed) == len(searches):
        print(
            f"\n❌ Alla {len(searches)} sökningar misslyckades — ingen data hämtades, "
            "inga filer ändrade. Kolla nätverket/JobTech API:t och kör igen.",
            file=sys.stderr,
        )
        sys.exit(2)
    if failed:
        print(
            f"\n⚠️  {len(failed)} av {len(searches)} sökningar misslyckades: "
            + ", ".join(f"'{q}'" for q in failed)
            + ". Resultatet nedan är ofullständigt.",
            file=sys.stderr,
        )

    if not all_hits:
        print("\n✅ Inga nya jobb hittades.")
        return

    n = len(all_hits)
    print(f"\n🆕 {n} nya jobb:\n")

    for ad_id, ad in all_hits.items():
        headline = ad.get("headline", "")
        employer = (ad.get("employer") or {}).get("name", "")
        wp = ad.get("workplace_address", {}) or {}
        city = wp.get("city", "") or wp.get("municipality", "")
        deadline = ad.get("application_deadline", "")
        if deadline and "T" in deadline:
            deadline = deadline.split("T")[0]
        print(f"  • {headline}")
        print(f"    {employer} — {city}  |  Deadline: {deadline or '—'}")
        print(f"    https://arbetsformedlingen.se/platsbanken/annonser/{ad_id}")
        print()

    if dry_run:
        return

    # Skrivordning (VIKTIGT): pipeline.html först, scan-history.tsv sist.
    # scan-history.tsv är det som gör ett jobb "känt" för nästa scan. Skrivs den
    # först och pipeline.html sedan vägras av safe_write, försvinner jobben för
    # gott: de syns inte i pipelinen och hoppas över i alla framtida scans.
    # Därför kontrolleras alla filer innan något skrivs, och historiken skrivs
    # bara när pipeline.html (källan till sanning) redan är uppdaterad.
    for required in (PIPELINE_HTML, PIPELINE_MD, SCAN_HISTORY):
        if not required.exists():
            print(f"❌ {required.relative_to(ROOT)} saknas. {INIT_HINT}", file=sys.stderr)
            sys.exit(1)

    # --- 1. pipeline.html (backup + atomisk skrivning + verifiering) ---
    html_entries = "".join(
        _html_entry(ad, *_tags_for_search(id_to_search[ad_id], default_city), default_city)
        for ad_id, ad in all_hits.items()
    )
    from pipeline_lib import (backup_pipeline, count_jobs, insert_new_jobs,
                              safe_write, stamp_updated, sync_counters)

    html = PIPELINE_HTML.read_text(encoding="utf-8")
    old_total = count_jobs(html)["total"]
    bak = backup_pipeline(PIPELINE_HTML)
    print(f"🔒 Backup: {bak.name}")
    html = insert_new_jobs(html, html_entries)
    html = stamp_updated(html)
    html = sync_counters(html)
    try:
        safe_write(PIPELINE_HTML, html, expect_total=old_total + n)
    except RuntimeError as e:
        print(
            f"❌ {e}\n   Inga filer ändrade (pipeline.md och scan-history.tsv orörda), "
            "så jobben dyker upp igen nästa scan. Kör python af-mcp/verify.py.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"✅ pipeline.html — {n} nya jobb i Ovärderade-sektionen (totalt {old_total + n})")

    # --- 2. pipeline.md ---
    md_lines = [_pipeline_md_entry(ad, default_city) for ad in all_hits.values()]
    md = PIPELINE_MD.read_text(encoding="utf-8")
    marker = "## Pendientes\n"
    idx = md.find(marker)
    if idx != -1:
        pos = idx + len(marker)
        md = md[:pos] + "\n".join(md_lines) + "\n" + md[pos:]
    else:
        md += "\n" + "\n".join(md_lines) + "\n"
    PIPELINE_MD.write_text(md, encoding="utf-8")
    print(f"✅ pipeline.md — {n} jobb tillagda")

    # --- 3. scan-history.tsv (sist: markerar jobben som kända) ---
    with open(SCAN_HISTORY, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["url", "first_seen", "portal", "title", "company", "status"],
            delimiter="\t",
        )
        for ad_id, ad in all_hits.items():
            writer.writerow({
                "url": f"https://arbetsformedlingen.se/platsbanken/annonser/{ad_id}",
                "first_seen": TODAY,
                "portal": "Platsbanken",
                "title": ad.get("headline", ""),
                "company": (ad.get("employer") or {}).get("name", ""),
                "status": "added",
            })
    print(f"✅ scan-history.tsv — {n} rader tillagda")

    print(f"\n🎯 Kör karriärpipelinen: /career-ops pipeline  för att utvärdera jobben")


if __name__ == "__main__":
    # Sätt UTF-8 på stdout/stderr för att hantera svenska tecken i Windows-terminal
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Scanna Platsbanken för nya jobb")
    parser.add_argument("--days", type=int, default=7, help="Sök jobb publicerade de senaste N dagarna (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Visa resultat utan att skriva filer")
    parser.add_argument("--no-filter", action="store_true", help="Skippa titelfiltrering (debugging)")
    args = parser.parse_args()
    asyncio.run(main(args.days, args.dry_run, args.no_filter))
