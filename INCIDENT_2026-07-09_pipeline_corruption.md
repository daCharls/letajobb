# Incident: pipeline.html korruption vid schemalagd scan
**Datum:** 2026-07-09
**Utlöst av:** Schemalagd `jobb-scan` task (automatisk, ingen användare närvarande)
**Påverkan:** ~99 jobb temporärt förlorade ur pipeline.html. Delvis återställda till 214 (av 217 pre-korruption). 6 ansökta kort fortfarande saknade.

## Tidslinje

1. `scan.py` kördes och hittade 3 nya jobb. Lade dem i en ny `<!-- NYA JOBB 2026-07-09 -->` sektion. Fil nu 217 jobb. **Inga problem här.**

2. Claude använde **Edit-verktyget** (Windows-sökväg) för att uppdatera räknare i headern (214→217, etc.). **Smärre problem:** Edit opererar på Windows-filsystemet.

3. Claude skapade `fix_scan.py` och körde det via **bash** (Linux-mount). Syftet: flytta 3 nya jobb-kort från den appendade scan-sektionen in i Ovärderade-sektionen.

4. **fix_scan.py hade en kritisk bugg:** Regex `content[:scan_section_match.start()].rstrip()` klippte bort ALLT från `<!-- NYA JOBB 2026-07-09 -->` till filens slut. Men filen hade **7 äldre scan-sektioner** (`2026-06-26`, `2026-06-25`, `2026-06-09`, `2026-06-08`, `2026-06-04`, `2026-05-26`, `2026-05-22`) som låg EFTER den nya sektionen. Alla ~99 jobb i dessa sektioner raderades.

5. Skriptet försökte sedan infoga de 3 nya korten i Ovärderade-sektionen och lägga till `</body></html>`, men ~99 jobb var redan borta.

6. Efterföljande recovery-försök (full_recovery.py) lyckades återställa 37 av de saknade Platsbanken-jobben från `scan-history.tsv`, men 6 ansökta kort (tillagda mellan 2026-06-26 och 2026-07-09) kunde inte återskapas p.g.a. filsystem-synk-problem.

## Grundorsaker

### 1. fix_scan.py förstod inte filens struktur
scan.py infogar nya scan-sektioner **före** äldre sektioner (rad 263-265 i scan.py):
```python
m = re.search(r"\n<!-- (NYA JOBB|HITTADE)", html)
if m:
    return html[: m.start()] + new_section + html[m.start() :]
```

fix_scan.py antog att scan-sektionen var appendad i slutet och att allt efter den kunde klippas bort:
```python
content = content[:scan_section_match.start()].rstrip() + '\n'
```

Detta raderade alla äldre scan-sektioner (med ~99 jobb).

### 2. Edit-verktyget vs bash-mount: olika filsystem-snapshots
Edit-verktyget skriver till Windows-sökvägen (projektmappen på Windows-sidan).
Bash-skript läser/skriver via Linux-mount (`/sessions/.../mnt/hittajobb/pipeline.html`).

Dessa kan vara ur synk. Det förklarar varför `pipeline.html.corrupted` (sparad av recovery-skriptet via bash) hade 15 applied istället för de 21 som Edit-versionen hade: bash-scriptet läste en äldre snapshot som inte hade Edit-ändringarna.

### 3. Ingen automatisk backup före destruktiva operationer
CLAUDE.md hade regler om att använda Python-skript (inte Edit) för strukturella ändringar, men **ingen regel om att ta backup först**. scan.py skapar inte heller backup.

### 4. Scan-sektionerna integrerades aldrig i huvudstrukturen
Jobb från scan.py hamnade i separata `<!-- NYA JOBB -->` sektioner istället för att integreras i Ovärderade/Ej aktuella-sektionerna. Detta skapade en bräcklig struktur där jobb kunde raderas genom att bara klippa bort scan-sektioner.

## Saknade data (ej återställda)

6 ansökta kort som lades till mellan 2026-06-26 och 2026-07-09 (företagsnamn borttagna/generaliserade
här, listan är bara till för att illustrera dataförlustens omfattning):

| Titel | Företag (exempel) | URL (trunkerad) |
|-------|---------|-----------------|
| Kommunikatör (vikariat) | Regionexempel | exempelregion.varbi.com/...xxxxx |
| 2nd line-tekniker | Rekryteringsbolag A | exempel.recman.page/job/xxxxxx |
| 2nd Line Technician | ? (Indeed) | se.indeed.com/...jk=xxxxxxxxxxxxxxxx |
| IT Technician, First Line | ? (Indeed) | se.indeed.com/...jk=xxxxxxxxxxxxxxxx |
| IT Support Technician | IT-bolag B | career.exempel.com/jobs/xxxxxxx |
| IT Supporttekniker 1st line | IT-bolag C | rekrytering.exempel.se/jobs/xxxxxxx |

Dessa sex jobb finns i "Att söka NU"-tabellen men saknar ansökta-kort i Ansökta-sektionen. Användaren hade pre-korruptionsversionen öppen i Chrome vid tillfället.

## Nuläge

- `pipeline.html` - delvis återställd (214 jobb, 15 applied, borde vara 21)
- `pipeline.html.bak` - backup från 2026-06-26 (177 jobb, intakt)
- `pipeline.html.corrupted` - den korrupterade versionen (sparad för forensik)

## Rekommenderade åtgärder

1. **Alltid ta backup innan pipeline.html ändras** (bör vara en hård regel i CLAUDE.md)
2. **scan.py bör skapa `.bak` automatiskt** före varje skrivning
3. **Integrera scan-resultat i huvudsektionerna** istället för separata `<!-- NYA JOBB -->` sektioner, eller dokumentera tydligt att dessa sektioner existerar och inte får raderas
4. **Testa att Edit-tool och bash-mount ser samma filversion** innan båda används på samma fil i samma session
5. **Aldrig trunkera pipeline.html baserat på regex-match** utan att först verifiera vad som klipps bort
6. **Återställ de 6 saknade ansökta korten** manuellt eller från användarens Chrome-cache
