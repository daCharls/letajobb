# Onboarding — instruktioner till AI:n för första körningen

Det här dokumentet är skrivet TILL DIG, AI-assistenten (Claude Code, Cowork eller
motsvarande), inte till slutanvändaren. Om du läser det här har du sannolikt
öppnats i en färsk klon av det här repot, och din uppgift är att intervjua
användaren och skräddarsy jobbsöket åt hen — innan något annat körs.

## Vad det här projektet är, i korthet

Hittajobb = en HTML-pipeline (`pipeline.html`) + två skannrar (`career-ops/`
för internationella portaler, `af-mcp/scan.py` för svenska Platsbanken) +
utvärderingsrapporter. Allt styrs av konfigfiler som är gitignorerade
eftersom de innehåller personuppgifter. En färsk klon saknar dem helt.
`CLAUDE.md` i repo-roten har de fullständiga driftreglerna (särskilt
"Pipeline.html redigeringsregler" — läs den innan du rör `pipeline.html`
med Edit-verktyget, för det ska du **aldrig** göra).

## Detektering — kolla tyst vid varje sessionsstart

Kolla om dessa filer finns, utan att fråga användaren om det än:

- `career-ops/config/profile.yml`
- `career-ops/cv.md`
- `career-ops/portals.yml`
- `career-ops/modes/_profile.md`
- `pipeline.html`
- `career-ops/data/pipeline.md`

**Saknas någon av dem → du är i onboarding-läge.** Gör inget annat (ingen
utvärdering, ingen scan, inget CV) förrän grunderna är på plats. Om ALLA
redan finns: onboardingen är redan gjord, hoppa direkt till vanligt arbete.

## Regler under onboardingen

- Ställ **3–5 frågor åt gången**, inte alla nio block i en enda vägg av text.
- Sammanfatta vad du tänker skriva innan du skriver det, så användaren kan
  rätta dig.
- **Rör aldrig `pipeline.html` med Edit/Write.** Allt skrivande till den
  filen går via `af-mcp/pipeline_lib.py` (se `CLAUDE.md`). I onboardingen
  räcker det att köra `python af-mcp/init.py`, som bygger en tom
  `pipeline.html` ur `pipeline.example.html` på ett säkert sätt.
- **Skriv aldrig sekretess-/NDA-uppgifter till en spårad fil.** De hör hemma
  i `CLAUDE.local.md` (gitignorerad), aldrig i `CLAUDE.md`, `README.md`,
  `career-ops/modes/_profile.md` eller andra committade filer.
- Använd å ä ö, aldrig ASCII-ersättningar.
- Om användaren redan har en skrivstilsanalys eller ett CV att klistra in —
  använd det, gissa inget.

## De nio frågeblocken

Ställ dem ungefär i den här ordningen. Varje block landar i en specifik fil
— skriv dit direkt när du har svaret, fråga inte allt först och skriv sist.

### 1. Identitet & kontakt
Namn, mejl, telefon, ort, LinkedIn, ev. portfolio.
→ `career-ops/config/profile.yml` → `candidate:`

### 2. Nuläge
Nuvarande roll/bransch, hur länge, anställd/arbetslös/uppsägningstid. CV:
klistra in text, ladda upp en PDF, eller berätta muntligt så skriver du CV:t.
→ `career-ops/cv.md` (hela CV:t), `narrative.exit_story` i profile.yml

### 3. Målroller
3–10 jobbtitlar du vill ha träffar på. Titlar du ALDRIG vill se. Brett
jobbsök eller selektiv jakt på drömroller?
→ `career-ops/portals.yml` → `title_filter.positive/negative` +
  `platsbanken.searches` (se `career-ops/templates/portals.svenska.example.yml`
  för formatet — kopiera den till `portals.yml` om den inte redan finns)
→ `career-ops/config/profile.yml` → `target_roles`

### 4. Geografi & arbetsform
Ort, pendlingsradie, remote/hybrid/på plats, flyttvillig?
→ `career-ops/portals.yml` → `platsbanken.municipality` (kommunkod — slå upp
  med `af-mcp/server.py`:s `sok_taxonomy`-verktyg) + `platsbanken.default_city`
→ `career-ops/modes/_profile.md` → Location Policy

### 5. Hårda gränser
Lägsta lön, skiftarbete, resor, visstidsanställning, bemanningsföretag,
offentlig sektor, språkkrav, körkort, säkerhetsprövning — vad är uteslutet
oavsett hur bra annonsen ser ut?
→ `career-ops/config/profile.yml` → `compensation`
→ `career-ops/modes/_profile.md` → Deal-breakers

### 6. Vad du har
Kärnkompetenser, 2–3 största prestationer (gärna med siffror), kända gap du
vill att systemet är ärligt om.
→ `career-ops/modes/_profile.md` → Adaptive Framing
→ `career-ops/interview-prep/story-bank.md` (STAR-historier, om användaren
  har konkreta exempel)

### 7. Sekretess & integritet (VIKTIGT — gitignorerad fil)
Finns NDA eller andra bindande sekretessregler kring nuvarande/tidigare
uppdragsgivare? Får nuvarande arbetsgivare namnges i ansökningar? Får
personnummer/adress stå i CV:t?
→ `CLAUDE.local.md` (skapas av `af-mcp/init.py`, redan gitignorerad —
  **skriv ALDRIG det här svaret någon annanstans**)

### 8. Ton & skrivstil
Be om ett skrivprov om användaren har ett (gammalt ansökningsbrev, ett
LinkedIn-inlägg — vad som helst med deras egen röst). Formell eller
informell ton? Uttryck de aldrig vill se i sina texter? Vilket språk ska
ansökningar skrivas på?
→ `career-ops/modes/_profile.md` (fritt textavsnitt om ton)
→ Se `CLAUDE.md` → "Din skrivstil" och "AI-marker scan" för de regler som
  redan gäller (aldrig em-dash, aldrig "spännande"/"brinner för" osv.)

### 9. Drift
Vill de ha återkommande scanning (t.ex. var 3:e dag)? Om ja, föreslå
`/schedule` eller `/loop` (om skillen finns tillgänglig i den här miljön) —
annars påminn om att köra `python af-mcp/scan.py` manuellt då och då.

## Efter intervjun

1. Kör `python af-mcp/init.py` (skapar `pipeline.html`,
   `career-ops/data/*.md/.tsv`, kopierar example-filer om de saknas — rör
   aldrig en fil som redan finns).
2. Fyll i de skapade filerna (`profile.yml`, `portals.yml`, `_profile.md`)
   med svaren från intervjun — nu är de inte längre tomma mallar.
3. Kör `python af-mcp/init.py --check` (ska rapportera att allt finns) och
   `python af-mcp/verify.py` (en helt tom pipeline är inget fel — den
   rapporterar "pipeline.html är tom", inte ett ❌; exit-koden ska vara 0).
4. Kör `python af-mcp/scan.py --dry-run --days 14` och visa användaren hur
   många träffar titelfiltret gav. Om det är 0 eller absurt högt (typ alla
   annonser i Sverige) — titelfiltret är troligen fel, gå tillbaka till
   block 3.
5. Be användaren öppna `pipeline.html` i webbläsaren och bekräfta att det
   ser rimligt ut (tomt just nu, det är okej — första skarpa scan fyller den).
6. Berätta att `career-ops/modes/` till stor del är på **spanska**
   (arvet efter upstream-projektet santifer/career-ops) — `/career-ops`
   fungerar ändå eftersom AI:n läser och förstår spanska instruktioner, men
   om användaren vill ha modes på svenska/engelska är det ett separat,
   större jobb (inte del av den här onboardingen).

## Felsökning

| Symptom | Orsak | Åtgärd |
|---|---|---|
| `/career-ops` finns inte | Skillen är ny i det här repot (`career-ops/.claude/skills/career-ops/SKILL.md`) — kontrollera att den faktiskt klonades med | `git status` — om filen saknas helt, något gick fel vid klon/checkout |
| `scan.py` kraschar med `FileNotFoundError` | `pipeline.html` eller `career-ops/data/pipeline.md` saknas | `python af-mcp/init.py` |
| `scan.py`/`verify.py` kraschar på `UnicodeEncodeError` i Windows-terminalen | Gammal version utan UTF-8-fix | Ska vara fixat i alla af-mcp-skript nu — om det ändå händer, kör `chcp 65001` i terminalen först |
| `scan.py` säger "portals.yml saknas" och avbryter | Väntat beteende — filen är gitignorerad och innehåller din sökprofil | `python af-mcp/init.py` skapar den från `career-ops/templates/portals.svenska.example.yml` |
| `scan.py` avslutar med "Alla N sökningar misslyckades" (exit-kod 2) | JobTech API:t svarar inte eller nätet blockerar `jobsearch.api.jobtechdev.se` | Kolla nätverket/proxyn och kör igen. Inga filer har ändrats |
| Titelfiltret ger 0 träffar | `portals.yml` kopierades från fel mall (t.ex. `templates/portals.example.yml`, som är AI/ML på engelska) eller `title_filter.positive` är för smalt | Använd `career-ops/templates/portals.svenska.example.yml`, bredda listan |
| `/career-ops`-lägena pratar spanska | Upstream-arv, se ovan | Inget att fixa akut — fungerar ändå, översättning är ett eget projekt |

## Referens: var saker bor

| Vad | Fil |
|---|---|
| Kandidatprofil (namn, mål, lön) | `career-ops/config/profile.yml` |
| CV, källa till sanning | `career-ops/cv.md` |
| Titelfilter + sökfrågor | `career-ops/portals.yml` |
| Personlig framing, deal-breakers, förhandling | `career-ops/modes/_profile.md` |
| Sekretess/NDA (ALDRIG spårad) | `CLAUDE.local.md` |
| Din jobbpipeline | `pipeline.html` |
| Utvärderingsrapporter | `reports/*.html` + `career-ops/reports/*.md` |
| Driftregler (pipeline.html, scan, kortformat) | `CLAUDE.md` |
