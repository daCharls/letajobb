# Hittajobb — jobbsökningsprojekt

## FÖRSTA KÖRNINGEN (läs detta först)

Kolla tyst om dessa filer finns: `career-ops/config/profile.yml`,
`career-ops/cv.md`, `career-ops/portals.yml`, `career-ops/modes/_profile.md`,
`pipeline.html`, `career-ops/data/pipeline.md`. **Saknas någon av dem** —
det här är en ny installation. Gör inget annat förrän du har läst
`ONBOARDING.md` och intervjuat användaren enligt den. Rör aldrig
`pipeline.html` med Edit/Write innan `af-mcp/init.py` har körts (se
"Pipeline.html redigeringsregler" nedan).

Finns alla filer redan är onboardingen klar — fortsätt som vanligt.

## Syfte
AI-assisterad jobbsökning med career-ops som pipeline-motor. Det här repot startade som ett
personligt jobbsök men är städat till en återanvändbar mall — se README.md för hur du gör den din.

## Struktur
- `career-ops/` — Klonad från santifer/career-ops, anpassad för svensk arbetsmarknad
- `{Ditt_Namn}_CV_{variant}.pdf` — CV-varianter per roll/bolag (gitignored, dina egna filer)
- `career-ops/{ditt_namn}_kontext_claude_code.md` — din fullständiga kontextfil (gitignored, skapa själv vid behov)

## Kandidatprofil (snabbref)
Fyll i din egen profil här, t.ex.:
- **Ditt namn**, ort, ålder (valfritt)
- Nuvarande roll/bransch och hur länge
- Bakgrund som är relevant för sökningen (tidigare karriärer, utbildning)
- Kärnkompetenser
- Vad du söker BRETT eller SMALT — roller, geografi, remote/hybrid-preferens

Se `career-ops/config/profile.example.yml` för den maskinläsbara versionen av samma sak.

## Sekretessregler (KRITISKT)
Har du bindande sekretessregler kring nuvarande/tidigare uppdragsgivare (NDA, interna förhållanden
som aldrig får nämnas i ansökningar) — **lägg dem i en lokal `CLAUDE.local.md`** och se till att den
står i `.gitignore`. Läs den filen FÖRST innan CV, brev eller publika dokument skrivs. Poängen: den
typen av regler ska aldrig kunna hamna i detta publika repo, i commits eller i publika dokument.

## Career-ops
Kör `/career-ops` i career-ops-mappen för alla kommandon.
Alla personliga anpassningar: `career-ops/config/profile.yml` + `career-ops/modes/_profile.md`

## HTML-output (VIKTIGT)
- `pipeline.html` — jobbpipeline med filter, statusmarkeringar och rapportlänkar. Bra som din startsida i Chrome. Ligger i repo-roten, gitignored (persondata) — se `pipeline.example.html` för formatet.
- `reports/{NNN}-{företag}.html` (t.ex. `reports/001-exempelbolag.html`) — utvärderingsrapporter per jobb, i undermappen `reports/`
- Markdown-versioner sparas även i `career-ops/reports/` för career-ops-systemet
- **Efter varje utvärdering:** spara HTML-rapporten i `reports/`, uppdatera pipeline.html med status "UTVÄRDERAD" + länk `reports/NNN-slug.html`
- **Efter varje scan:** uppdatera pipeline.html med nya jobb
- **Använd ALLTID å ä ö** — aldrig ASCII-ersättningar i svenska texter
- Rapporternas HTML har mörkt tema, scorecard, STAR-historier, personligt brev, ATS-keywords
- Rapporter länkas tillbaka till pipeline.html via footer med `../pipeline.html` (ett steg upp från reports/)

## Pipeline.html design (VIKTIGT)
- **4 sektioner i ordning:** ✅ Ansökta, 📋 Att söka NU (sorterbar tabell), 📋 Utvärderade (kort), 🔍 Ovärderade, ❌ Ej aktuella
- **"Att söka NU"-tabell** efter ANSÖKTA-sektionen, listar alla utvärderade-icke-ansökta-icke-EJ-AKTUELLA jobb
- Tabellen är **sorterbar** - klick på kolumnrubrik (Score / Deadline / Lokation / Företag) togglar sortering
- Default-sortering: Score DESC
- Varje rad har **två knappar**: 🔗 Ansök (direktlänk till annonsen) + 📋 [nr] (länk till rapporten)
- Deadline-celler färgkodade: röd (`deadline-urgent`) ≤ 7 dagar, orange (`deadline-warn`) ≤ 21 dagar, grön (`deadline-ok`) > 21 dagar
- Stats i headern: jobb totalt / ansökta / utvärderade / nya / ej aktuella
- Filter-knappar: Alla / Ansökta / Utvärderade / Nya / {Din ort} / Remote / Komm / Tech / Ej aktuella

## Pipeline.html kortformat (OBLIGATORISKT)
Alla jobb-kort i pipeline.html MÅSTE följa samma struktur. Inga undantag.
CSS-klassen `tag-gbg` är ett fast namn i systemet (används av `pipeline_lib.py`,
`pipeline.example.html` osv.) — den betyder "ortstagg", inte specifikt
Göteborg. Byt bara ut den synliga texten mot din egen ort, inte klassnamnet.

**Ansökta kort** (`class="job applied"`):
```html
<a href="{url}" target="_blank" class="job applied" data-tags="{tags} applied">
  <div class="job-info">
    <div class="job-title">{titel}</div>
    <div class="job-company">{företag} - {meta}</div>
  </div>
  <div class="tags">
    <span class="tag tag-applied">ANSÖKT ✓</span>
    <span class="tag tag-tech">...</span>
    <span class="tag tag-gbg">{Din ort}</span>
  </div>
  <a href="reports/{nr}-{slug}.html" class="report-link" onclick="event.stopPropagation()">📋 Rapport</a>  <!-- om rapport finns -->
  <span class="arrow">→</span>
</a>
```

**Utvärderade kort** (`class="job done"`):
```html
<a href="{url}" target="_blank" class="job done" data-tags="{tags} utvärderad">
  <div class="job-info">
    <div class="job-title">{titel}</div>
    <div class="job-company">{företag} - Score: {x}/5</div>
  </div>
  <div class="tags">
    <span class="tag tag-done">UTVÄRDERAD</span>
    <span class="tag tag-tech">...</span>
    <span class="tag tag-gbg">{Din ort}</span>
  </div>
  <a href="reports/{nr}-{slug}.html" class="report-link" onclick="event.stopPropagation()">📋 Rapport</a>
  <span class="arrow">→</span>
</a>
```

**Ovärderade kort** (`class="job"`):
```html
<a href="{url}" target="_blank" class="job" data-tags="{tags}">
  <div class="job-info">
    <div class="job-title">{titel}</div>
    <div class="job-company">{företag} - {lokation}</div>
  </div>
  <div class="tags">
    <span class="tag tag-tech">...</span>
    <span class="tag tag-gbg">{Din ort}</span>
  </div>
  <span class="arrow">→</span>
</a>
```

**Ej aktuella kort** (`class="job ej"`):
```html
<a href="{url}" target="_blank" class="job ej" data-tags="{tags} ej">
  <div class="job-info">
    <div class="job-title">{titel}</div>
    <div class="job-company">{företag} - EJ AKTUELL: {orsak}</div>
  </div>
  <div class="tags">
    <span class="tag tag-ej">EJ AKTUELL</span>
    <span class="tag tag-tech">...</span>
  </div>
  <span class="arrow">→</span>
</a>
```

**data-tags konvention** - MÅSTE matcha filterknapparna:
- `applied` (inte "ansökt") - filterknappen söker `applied`
- `utvärderad` - filterknappen söker `utvärderad`
- `ej` - filterknappen söker `ej`
- `tech`, `komm`, `gbg`, `remote` - kategoritaggar

## Pipeline.html redigeringsregler (KRITISKT, uppdaterade efter incidenten 2026-07-09)
**All säkerhetslogik finns i `af-mcp/pipeline_lib.py`** - backup, atomisk skrivning, verifiering, räknarsynk. Använd den, uppfinn inte egna varianter.

1. **Edit-verktyget rör ALDRIG pipeline.html.** Inte för strukturändringar, inte för räknare, inte för en enstaka note. Alla ändringar går via Python-skript i bash som använder pipeline_lib (`backup_pipeline` + `safe_write`). Detta löser också Windows/Linux-synkproblemet: bara bash skriver till filen.
2. **Backup tas automatiskt** av `backup_pipeline()` (behåller de 5 senaste `pipeline.html.bak.YYYYMMDD_HHMMSS`). Egna skript MÅSTE anropa den före ändring.
3. **`safe_write()` är enda tillåtna skrivvägen** - skriver till tempfil, verifierar (slutar med `</html>`, alla sektionsmarkörer finns exakt en gång, inga dubblett-URL:er, förväntat jobbantal), byter atomiskt. Den kastar fel istället för att skriva trasigt.
4. **Verifiera efter varje ändring:** `python3 af-mcp/verify.py` - kontrollerar struktur och att räknarna matchar korten. `--sync` rättar osynkade räknare (med egen backup).
5. **Räknare handredigeras ALDRIG.** De beräknas från korten via `sync_counters()` / `verify.py --sync`. Definitioner: ansökta = `class="job applied"`, utvärderade = `class="job done"`, ovärderade/nya = `class="job"`, ej aktuella = `class="job ej"`. Totalt = summan. Synkas på alla ställen samtidigt (stats-header, filterknappar, sektionsrubriker, footer).
6. **Scan-sektioner (`<!-- NYA JOBB -->`) FÅR INTE FINNAS.** Sedan 2026-07-09 infogar scan.py nya jobb direkt i Ovärderade-sektionen. Om en `<!-- NYA JOBB` dyker upp i filen har något gått fel - stoppa och utred, radera inte.
7. **Sektionsmarkörerna `<!-- ANSÖKTA -->`, `<!-- ATT SÖKA NU -->`, `<!-- UTVÄRDERADE -->`, `<!-- OVÄRDERADE -->`, `<!-- EJ AKTUELLA -->` är strukturella ankare** som pipeline_lib navigerar efter. Får aldrig tas bort eller dubbleras.
8. **Obevakade körningar (schemalagda tasks) får ALDRIG improvisera fix-skript** mot pipeline.html. Vid fel: rapportera till användaren, rör ingenting. Det var ett improviserat fix-skript kl 05 som orsakade incidenten 2026-07-09 (se INCIDENT-filen för detaljer).

## Verifiera deadlines och status (VIKTIGT)
- Innan utvärdering eller "Att söka NU"-listning: **kolla att jobbet är öppet**
- Platsbanken-jobb (`arbetsformedlingen.se/platsbanken/annonser/{id}`): hämta via API `https://jobsearch.api.jobtechdev.se/ad/{id}` - returnerar deadline + apply URL
- Indeed-länkar (`to.indeed.com/...`): kan vara expired - öppna i Chrome och leta efter "jobbet har gått ut"
- Annars-länkar (Greenhouse, Ashby, Teamtailor, Workable): kan vara JS-renderade - använd företagets job-board API om sådan finns, annars Chrome MCP
- **Om jobb visat sig stängt:** markera som EJ AKTUELL i pipelinen med text "tjänsten har gått ut (verifierad YYYY-MM-DD)"
- **Om deadline okänd eller "verifiera":** lös detta innan jobbet hamnar i "Att söka NU"-tabellen
- Äldre Indeed-jobb (>7 dagar): verifiera proaktivt om de fortfarande är värda att rekommendera

## EJ AKTUELL-flow (VIKTIGT)
Jobb som är "EJ AKTUELL" SKA stanna i pipeline.html (med `class="job ej"` + `tag tag-ej`) eftersom:
- Scannern (`af-mcp/scan.py`) läser pipeline.html för kända IDs och hoppar över dem nästa scan
- Visuellt nedtonade (CSS `opacity: 0.4`) men sökbara via filter "Ej aktuella"
- Plus extra dubbel-spårning: lägg till rad i `career-ops/data/scan-history.tsv` med status `skipped-not-actual`

Vanliga EJ AKTUELL-orsaker att flagga tydligt i note-text:
- **Geografi-mismatch:** "tjänsten är i {annan ort} (inte {din ort})"
- **Mandatory-krav saknas:** "kräver 5+ års X" / "PhD i Y" / "PLC-programmering" / "10 års strategisk kommunikation"
- **3-skift / visstid / villkor:** "3-skift rullande schema + visstid - dåligt fit"
- **Tjänsten tillsatt:** "verifierad expired YYYY-MM-DD"

## Din skrivstil (OBLIGATORISKT före CV/brev)
Om du har en egen skrivstilsanalys (t.ex. genererad från tidigare texter) — peka på den här och
läs den innan CV eller personligt brev skrivs. Annars, sträva efter:
1. (Valfritt) Hämta din skrivstilsanalys från Google Drive eller lokal fil, läs dokumentet
2. Anpassa ton, ordval och meningsbyggnad efter analysen:
   - Kort och direkt, inte blommigt
   - Ärlighet om gap, inga bortförklaringar
   - Parentetisk humor och ironi där det passar
   - Varierad meningslängd, inte robotmässigt jämn
   - Inga corporatefloskler eller överdrifter
   - Dina egna favorituttryck OK att använda sparsamt — fyll på listan här när du hittar dina egna
3. Efter skrivning: läs igenom och fråga "skulle jag ha skrivit det här?" - om svaret är nej, skriv om

## AI-marker scan (OBLIGATORISKT före leverans)
Efter att CV och brev skapats, kör regex-scan PLUS manuell läsning för att fånga AI-trigger-formuleringar:

Regex-flaggor (i ordning):
```
em-dash:          — (em-dash ALDRIG. en-dash – är ok om den används sparsamt, flagga bara vid överanvändning)
"spännande":      \bspännande\b
"genuint intresse": \bgenuint intresse\b
"lösningsorienterad", "resultatdriven", "passionerad", "brinner för", "min passion"
"perfekt blandning", "naturlig fortsättning", "i en alltmer", "i en värld där"
"säkerställa att", "värt att notera", "världsledande"
"I'm thrilled", "passionate about", "leverage", "synergy", "spearhead"
```

Manuell trippelkoll (efter regex):
- Repetitiva meningsstartar
- Triadiska adjektivlistor ("kompetens, engagemang och driv")
- "Inte bara X utan också Y"-konstruktioner
- För perfekt struktur (varje stycke exakt 3 meningar)
- Kliché-formuleringar som inte säger något konkret ("matchar min utvecklingsriktning")
- Hyperlativer utan konkret backup

## Platsbanken-scanner
`af-mcp/scan.py` söker Platsbanken (Arbetsförmedlingens API) och uppdaterar pipeline-filerna.

```
python af-mcp/scan.py              # senaste 7 dagarna
python af-mcp/scan.py --days 14    # senaste 14 dagarna
python af-mcp/scan.py --dry-run    # visa resultat utan att skriva filer
python af-mcp/scan.py --no-filter  # skippa titelfiltrering (debugging)
```

Scannern filtrerar träffar mot titelfiltret i `career-ops/portals.yml` (`title_filter.positive`/`negative`).

### Sökfrågor
Sökfrågorna bor i `career-ops/portals.yml` under `platsbanken.searches` (en post per fråga
med `q`, `category`, valfritt `remote`, `municipality` och `label`), inte i scan.py. Utgå från
`career-ops/templates/portals.svenska.example.yml`. Bredda med fler frågor och fler negativa
brusfilter-termer (t.ex. PhD, Doktorand, Elektriker) när du ser vilket brus din sökning ger.

Uppdaterar: `pipeline.html`, `career-ops/data/pipeline.md`, `career-ops/data/scan-history.tsv`

### Säkerhetslager (nytt 2026-07-09)
- `af-mcp/pipeline_lib.py` - backup, atomisk skrivning (`safe_write`), verifiering, räknarsynk, `insert_new_jobs` (lägger nya kort i Ovärderade-sektionen)
- `af-mcp/verify.py` - fristående kontroll: `python3 af-mcp/verify.py` (läge: check) eller `--sync` (rättar räknare)
- `af-mcp/rebuild.py` - engångsmigrationen som flyttade in scan-sektionerna 2026-07-09; kan återanvändas som full ombyggnad om strukturen skadas igen
- scan.py tar backup, skriver atomiskt och verifierar. Vid fel: avbryter utan att skriva.
- **Skrivordning i scan.py:** `pipeline.html` först, sedan `pipeline.md`, sist `scan-history.tsv`. Historiken är det som gör ett jobb "känt" - skrivs den bara när pipeline.html redan är uppdaterad kan ett vägrat skrivförsök aldrig tappa jobb för gott.
- **Exit-koder:** 0 = OK (även "inga nya jobb"), 1 = saknad fil eller vägrad skrivning, 2 = alla sökningar misslyckades (API/nät nere). Schemalagda körningar ska rapportera allt utom 0 till användaren, inte tolka det som "inga nya jobb".

## CV per jobb (OBLIGATORISKT)
- **Skapa ALLTID ett dedikerat CV för varje jobb du söker**, även om det är 99% återanvändning av ett befintligt CV
- Spara som `{Ditt_Namn}_CV_{företag}.pdf` (eller .docx) via career-ops PDF-generering
- Justera minst: titel, profil-stycke, och 2-3 rader i kompetenser/erfarenhet så de speglar annonsens ord
- Detta gäller även snabba ansökningar - återanvänd aldrig ett tidigare CV rakt av
- Logga vilket CV som skickades i pipeline.html-noten (t.ex. "Ansökt 2026-04-22, CV: {företag}-variant")

## Generera CV och brev (workflow)
- Standardvägen: `/career-ops pdf` (kör `career-ops/generate-pdf.mjs`, Playwright HTML→PDF via `career-ops/templates/cv-template.html`), källa till sanning är `career-ops/cv.md` + `career-ops/config/profile.yml`
- Skapas i `career-ops/output/`: `{namn}-cv-{key}.html` + PDF
- Om du hellre bygger .docx-varianter för hand (äldre arbetssätt): skriv ett eget skript i `outputs/` som tar profilen + variant-specifik info och bygger .docx via python-docx, konvertera med `libreoffice --headless --convert-to pdf {fil}.docx --outdir .`. Namnge `{Ditt_Namn}_CV_{key}.docx`/`_Brev_{key}.docx` i repo-roten — matchar gitignore-mönstren `*_CV_*`/`*_Brev_*`
- **Båda format levereras** när du bygger .docx-varianten - .docx för redigering, .pdf för uppladdning
- Leverera filerna till användaren med den länk- eller filfunktion som miljön har (Claude Code, Cowork osv.)
- I miljöer där Edit-verktyget och bash ser olika sökvägar (t.ex. Windows-mapp + Linux-mount i Cowork): skriv skript och filer via bash i sin helhet hellre än att blanda verktygen

## Chrome-flöde för ansökningar
- Öppna annonsen i Chrome MCP, identifiera ansökningssättet:
  - **Mail (info@xxx.se):** skapa ett utkast via en ansluten mejlkoppling (t.ex. Gmail-connector) om sådan finns, annars ge användaren mottagare, ämne och brevtext att klistra in själv. Lägg aldrig brevtext eller kontaktuppgifter i URL-parametrar
  - **Webbformulär:** scrolla, identifiera fält via `find`, fyll i namn/mejl/telefon, klistra in brev i cover letter-textbox där sådan finns
  - **Portaler med eget konto (Zerolime/recman m.fl.):** lösenord-baserad inloggning kräver att du själv loggar in (säkerhetsregel)
- **File upload (CV/brev) blockeras av Chrome MCP säkerhetsregler** - du måste själv klicka 📎 paperclip eller 'upload'-knappen och välja PDF:erna
- Stanna ALLTID innan submit/send: tryck aldrig "skicka", användaren skickar själv
- Cookie-banners: välj alltid "Avvisa alla" / mest privacy-bevarande automatiskt

## Principer
- Ärlig, konkret ton, inget corporatespeak
- Anpassa CV-variant efter roll (career-ops PDF-generering + nya per-jobb-varianter)
- Anpassa efter ditt läge — akut bred sökning kontra selektiv jakt på drömroller kräver olika strategi
- Aldrig em-dash (—) i text. En-dash (–) är ok men sparsamt. Vanligt bindestreck (-) duger oftast
- **Inga rapporter för ohjälpliga jobb** - om mandatory-krav saknas, markera EJ AKTUELL direkt och gå vidare
