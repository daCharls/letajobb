# Hittajobb

AI-assisterad jobbsökning med pipeline-tänk. Byggt för att hålla koll på ett brett jobbsök utan att tappa bort sig i ett kaos av flikar och bokmärken.

## Vad det här är

En jobbsökningspipeline som skannar svenska och internationella jobbportaler, utvärderar roller mot din profil, och samlar allt i en filtrerad HTML-vy. Tänk CRM, fast för den som *söker* jobbet istället för den som säljer.

Bygger på [career-ops](https://github.com/santifer/career-ops) av [@santifer](https://github.com/santifer), som skapades för en helt annan jobbmarknad och rolltyp. Det här är en svensk fork, omskriven för svenska jobbportaler (Platsbanken, Indeed Sverige, Teamtailor m.fl.), svensk arbetsmarknad, och en bred profil som kan spänna från teknisk support till kommunikatörsroller. Pipeline-vyn, utvärderingssystemet och portalskonfigurationen är egna tillägg.

## Bakgrund

Det här var ursprungligen mitt eget, faktiska jobbsök — inte ett demoprojekt från början. Jag hittade jobb och behöver inte längre verktyget aktivt, men lämnar det kvar och städat som en fungerande mall åt andra som söker jobb och vill ha samma typ av AI-assisterad pipeline. All min egen ansökningsdata är borttagen från repot (se `.gitignore`) — det du ser här är antingen generisk mall-kod eller påhittad exempeldata.

## Hur det fungerar

**Skanning:** Söker igenom LinkedIn, Platsbanken, Indeed, Greenhouse, Ashby, Lever, Teamtailor och Workable efter roller som matchar. Portaler och sökfrågor konfigureras per användare i `career-ops/portals.yml` (kopiera från `career-ops/templates/portals.svenska.example.yml` — inte `templates/portals.example.yml`, som är upstreams engelska AI/ML-mall och inte matchar Platsbanken-skannern).

**Pipeline:** Alla hittade jobb hamnar i din egen `pipeline.html` — en dark-mode dashboard med filter för kategori, plats, status och urgency. Varje jobb taggas (tech/komm, ort/remote, ny/utvärderad/utgången) och kan klickas igenom till originalannonsen. Den här filen är gitignored eftersom den innehåller din faktiska sökdata — se `pipeline.example.html` för hur formatet ser ut i praktiken.

**Utvärdering:** Intressanta jobb utvärderas mot din kandidatprofil och får en rapport med scorecard, gap-analys, STAR-historier, personligt brev-utkast och ATS-keywords. Rapporterna genereras som HTML med mörkt tema och länkas direkt från pipeline-vyn. Även rapporter är gitignored (`reports/`) — de innehåller kontaktuppgifter och detaljer om din faktiska sökning.

**CV-generering:** Projektet bygger också ett skräddarsytt CV per jobb du söker, inte bara ett generellt CV du återanvänder. Utgångspunkten är `career-ops/cv.md` + din profil, och `/career-ops pdf` genererar HTML+PDF via Playwright (`career-ops/generate-pdf.mjs`) där titel, profiltext och några kompetensrader justeras efter annonsens ordval. Funkar även manuellt som .docx om du föredrar det.

## Struktur

```
letajobb/
├── pipeline.example.html          # Exempel på pipeline-formatet (committed)
├── pipeline.html                  # Din egen jobbpipeline (gitignored, genereras lokalt)
├── reports/                       # Utvärderingsrapporter (gitignored)
├── CLAUDE.md                      # AI-instruktioner för projektet — börja här
├── ONBOARDING.md                  # Intervjuprotokoll AI:n följer vid första körningen
├── LICENSE                        # MIT
├── .gitignore
├── af-mcp/                        # Platsbanken-scanner (MCP-server) + säkerhetslager för pipeline.html
│   ├── server.py                  # MCP-server mot JobTech API
│   ├── scan.py                    # Batch-scanner med titelfiltrering
│   ├── init.py                    # Bootstrap: skapar pipeline.html + datafiler för en ny installation
│   ├── pipeline_lib.py            # Backup, atomisk skrivning, verifiering, räknarsynk
│   ├── verify.py                  # Fristående strukturkontroll av pipeline.html
│   └── test_scan.py               # Regressionstester (inget nätverk, rör inte din pipeline)
└── career-ops/                    # Pipeline-motor (fork av santifer/career-ops)
    ├── .claude/skills/career-ops/ # /career-ops-skillen (committed sedan denna mall städades)
    ├── config/
    │   ├── profile.yml            # Din kandidatprofil (gitignored — persondata)
    │   └── profile.example.yml    # Exempelprofil, kopiera och fyll i
    ├── portals.yml                # Sökfrågor och bevakade företag (gitignored)
    ├── templates/
    │   └── portals.svenska.example.yml  # Svensk mall som matchar af-mcp/scan.py
    ├── data/                      # Ansökningsstatus, pipeline-inbox (gitignored)
    ├── reports/                   # Utvärderingsrapporter i markdown (gitignored)
    ├── interview-prep/            # STAR-historier och interviewprep (gitignored)
    ├── modes/                     # career-ops lägen och profil
    └── ...
```

## Kom igång

Förutsättningar: Python 3.10+, Node.js 18+, git.

1. Klona repot
2. `pip install -r af-mcp/requirements.txt`
3. `npm install --prefix career-ops && npx playwright install chromium`
4. `python af-mcp/init.py` — bygger en tom `pipeline.html` och de datafiler
   career-ops/af-mcp behöver (rör aldrig en fil som redan finns)
5. Öppna mappen i Claude Code eller Cowork och skriv t.ex. "starta jobbsöket"
   — AI:n läser `ONBOARDING.md`, intervjuar dig om målroller, geografi,
   sekretess och skrivstil, och fyller i din profil åt dig. I Claude Code
   kan du också köra `/starta-jobbsok` direkt.
6. Testa scannern: `python af-mcp/scan.py --dry-run --days 14`
7. Valfritt: `python af-mcp/test_scan.py` kör regressionstesterna för scannern

Cowork-not: samma flöde fungerar i Cowork som i Claude Code — AI:n läser
`CLAUDE.md`/`AGENTS.md` automatiskt och hittar `ONBOARDING.md` därifrån, det
finns ingen Cowork-specifik variant att installera.

## Vad som skiljer den här forken

Originalet (career-ops) är riktat mot en specifik internationell marknad. Den här varianten är anpassad för:

- **Svenska jobbportaler** — Platsbanken, Indeed Sverige, Teamtailor-baserade karriärsidor, Varbi (offentlig sektor)
- **Bred rollprofil** — kan söka parallellt inom flera olika yrkesspår, t.ex. IT-support, utveckling, kommunikation och hybridroller
- **HTML-pipeline** — egen dark-mode dashboard (`pipeline.html`) med filter, taggar och rapportlänkar som ersätter career-ops standardvy
- **Utvärderingsrapporter** — scorecard, gap-analys, STAR-historier och personligt brev-utkast, genererade som statisk HTML
- **Säkerhetslager** (`af-mcp/pipeline_lib.py`) — backup, atomisk skrivning och strukturverifiering av pipeline.html, byggt efter en incident där ett improviserat fix-skript raderade ~99 jobb (se `INCIDENT_2026-07-09_pipeline_corruption.md` för postmortemet och varför reglerna i CLAUDE.md ser ut som de gör)

## Teknik

Ingen fancy stack. HTML + vanilla JS för pipeline-vyn. career-ops körs med Node.js + Playwright för portalskanning. Rapporter genereras som statisk HTML. Hela grejjen är byggd för att orkestreras via Claude Code (eller annan AI-kodassistent) som körs mot `CLAUDE.md`.

## Licens

MIT, se `LICENSE`. career-ops (undermappen) har sin egen MIT-licens från originalförfattaren.

---

*Persondata (CV:n, personnummer, kontaktuppgifter, löneanspråk, din faktiska pipeline och dina rapporter) exkluderas via `.gitignore`. Se `CLAUDE.md` för hur säkerhetsreglerna kring `pipeline.html` fungerar.*
