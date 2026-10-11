#!/usr/bin/env python3
"""Delade säkerhetsfunktioner för pipeline.html.

Skapad efter incidenten 2026-07-09 (se INCIDENT_2026-07-09_pipeline_corruption.md).
Regler:
- Ta ALLTID backup före skrivning (backup_pipeline)
- Skriv ALDRIG direkt (safe_write: tempfil -> verifiering -> os.replace)
- Räknare beräknas från korten, aldrig för hand (sync_counters)
"""

from __future__ import annotations

import os
import re
from datetime import datetime, date
from pathlib import Path

CARD_RE = re.compile(
    r'<a href="[^"]+" target="_blank" class="job[^"]*".*?<span class="arrow">→</span>\s*</a>',
    re.DOTALL,
)
CLASS_RE = re.compile(r'target="_blank" class="(job[^"]*)"')
HREF_RE = re.compile(r'<a href="([^"]+)" target="_blank" class="job')

SECTION_MARKERS = ["<!-- ANSÖKTA -->", "<!-- ATT SÖKA NU -->", "<!-- UTVÄRDERADE -->",
                   "<!-- OVÄRDERADE -->", "<!-- EJ AKTUELLA -->"]

KEEP_BACKUPS = 5


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------
def backup_pipeline(path: Path) -> Path:
    """Kopierar pipeline.html till .bak.YYYYMMDD_HHMMSS och gallrar gamla."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.with_name(f"{path.name}.bak.{stamp}")
    # Två backuper inom samma sekund (t.ex. scan.py direkt följt av
    # verify.py --sync) får aldrig skriva över varandra: lägg till _2, _3 ...
    n = 2
    while bak.exists():
        bak = path.with_name(f"{path.name}.bak.{stamp}_{n}")
        n += 1
    bak.write_bytes(path.read_bytes())
    # Gallra: behåll de KEEP_BACKUPS senaste tidsstämplade backuperna.
    # OBS: i vissa miljöer (t.ex. skyddade mappar i Cowork) får filer inte
    # raderas efter skrivning - unlink() ger då PermissionError. Vi försöker
    # ändå, men ett misslyckat unlink får ALDRIG stoppa hela skrivningen.
    pattern = re.compile(re.escape(path.name) + r"\.bak\.(\d{8}_\d{6})(?:_(\d+))?$")
    def _order(p: Path) -> tuple[str, int]:
        m = pattern.match(p.name)
        return (m.group(1), int(m.group(2) or 1))

    baks = sorted((p for p in path.parent.iterdir() if pattern.match(p.name)), key=_order)
    for old in baks[:-KEEP_BACKUPS]:
        try:
            old.unlink()
        except OSError:
            pass
    return bak


# ---------------------------------------------------------------------------
# Räkning och verifiering
# ---------------------------------------------------------------------------
def count_jobs(html: str) -> dict[str, int]:
    classes = CLASS_RE.findall(html)
    counts = {
        "applied": classes.count("job applied"),
        "done": classes.count("job done"),
        "ej": classes.count("job ej"),
        "nya": classes.count("job"),
    }
    counts["total"] = sum(counts.values())
    return counts


def verify_pipeline(html: str, expect_total: int | None = None) -> list[str]:
    """Returnerar lista med fel. Tom lista = OK."""
    errors: list[str] = []
    if not html.rstrip().endswith("</html>"):
        errors.append("filen slutar inte med </html> (trunkerad?)")
    if "</body>" not in html:
        errors.append("</body> saknas")
    if "<footer>" not in html:
        errors.append("<footer> saknas")
    if "<script>" not in html:
        errors.append("<script>-blocket saknas")
    for marker in SECTION_MARKERS:
        n = html.count(marker)
        if n != 1:
            errors.append(f"sektionsmarkör {marker} förekommer {n} gånger (ska vara 1)")
    counts = count_jobs(html)
    if counts["total"] == 0:
        errors.append("0 jobbkort hittades")
    if expect_total is not None and counts["total"] != expect_total:
        errors.append(f"jobbantal {counts['total']} != förväntat {expect_total}")
    hrefs = HREF_RE.findall(html)
    dups = {h for h in hrefs if hrefs.count(h) > 1}
    if dups:
        errors.append(f"{len(dups)} dubblett-URL:er: {sorted(dups)[:3]}...")
    return errors


# ---------------------------------------------------------------------------
# Räknarsynk — räknarna BERÄKNAS, handredigeras aldrig
# ---------------------------------------------------------------------------
def sync_counters(html: str) -> str:
    c = count_jobs(html)

    # Stats i headern
    html = re.sub(r'<span class="num">\d+</span> jobb totalt',
                  f'<span class="num">{c["total"]}</span> jobb totalt', html)
    html = re.sub(r'(<span class="num"[^>]*>)\d+(</span> ansökta)',
                  rf'\g<1>{c["applied"]}\g<2>', html)
    html = re.sub(r'(<span class="num"[^>]*>)\d+(</span> utvärderade)',
                  rf'\g<1>{c["done"]}\g<2>', html)
    html = re.sub(r'(<span class="num"[^>]*>)\d+(</span> nya)',
                  rf'\g<1>{c["nya"]}\g<2>', html)
    html = re.sub(r'(<span class="num"[^>]*>)\d+(</span> ej aktuella)',
                  rf'\g<1>{c["ej"]}\g<2>', html)

    # Filterknappar
    html = re.sub(r"(filterJobs\('all'\)\">Alla) \(\d+\)", rf"\g<1> ({c['total']})", html)
    html = re.sub(r"(filterJobs\('applied'\)\">Ansökta) \(\d+\)", rf"\g<1> ({c['applied']})", html)
    html = re.sub(r"(filterJobs\('done'\)\">Utvärderade) \(\d+\)", rf"\g<1> ({c['done']})", html)
    html = re.sub(r"(filterJobs\('new'\)\">Nya) \(\d+\)", rf"\g<1> ({c['nya']})", html)
    html = re.sub(r"(filterJobs\('ej'\)\">Ej aktuella) \(\d+\)", rf"\g<1> ({c['ej']})", html)

    # Sektionsrubriker
    html = re.sub(r"(✅ Ansökta) \(\d+\)", rf"\g<1> ({c['applied']})", html)
    html = re.sub(r"(📋 Utvärderade) \(\d+\)", rf"\g<1> ({c['done']})", html)
    html = re.sub(r"(🔍 Ovärderade) \(\d+\)", rf"\g<1> ({c['nya']})", html)
    html = re.sub(r"(❌ Ej aktuella) \(\d+\)", rf"\g<1> ({c['ej']})", html)

    # Footer
    html = re.sub(
        r"\d+ ansökningar, \d+ utvärderade, \d+ ovärderade, \d+ ej aktuella\.",
        f"{c['applied']} ansökningar, {c['done']} utvärderade, "
        f"{c['nya']} ovärderade, {c['ej']} ej aktuella.",
        html,
    )
    return html


def stamp_updated(html: str) -> str:
    today = date.today().isoformat()
    html = re.sub(r"Senast uppdaterad \d{4}-\d{2}-\d{2}", f"Senast uppdaterad {today}", html)
    html = re.sub(r"(<footer>career-ops pipeline - Uppdaterad )\d{4}-\d{2}-\d{2}",
                  rf"\g<1>{today}", html)
    return html


# ---------------------------------------------------------------------------
# Säker skrivning
# ---------------------------------------------------------------------------
def safe_write(path: Path, html: str, expect_total: int | None = None) -> None:
    """Skriver via tempfil, verifierar, byter atomiskt. Kastar RuntimeError vid fel."""
    errors = verify_pipeline(html, expect_total)
    if errors:
        raise RuntimeError("Vägrar skriva pipeline.html:\n  - " + "\n  - ".join(errors))
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(html, encoding="utf-8")
    # Läs tillbaka och kontrollera att inget trunkerades på vägen
    readback = tmp.read_text(encoding="utf-8")
    if readback != html:
        tmp.unlink()
        raise RuntimeError("Tempfilen matchar inte innehållet i minnet — avbryter.")
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Infoga nya kort i Ovärderade-sektionen (ersätter gamla scan-sektioner)
# ---------------------------------------------------------------------------
def insert_new_jobs(html: str, new_entries_html: str) -> str:
    """Infogar nya jobbkort sist i Ovärderade-sektionens <ul>."""
    marker = "<!-- OVÄRDERADE -->"
    idx = html.find(marker)
    if idx == -1:
        raise RuntimeError("Hittar inte <!-- OVÄRDERADE --> — vägrar gissa var korten ska in.")
    ul_start = html.find('<ul class="job-list">', idx)
    ul_end = html.find("</ul>", ul_start)
    if ul_start == -1 or ul_end == -1:
        raise RuntimeError("Hittar inte Ovärderade-sektionens <ul> — avbryter.")
    return html[:ul_end] + new_entries_html + html[ul_end:]
