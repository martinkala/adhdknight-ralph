# Feature Specification: Visual Update 03

**Feature Branch**: `011-visual-update-03`

**Created**: 2026-06-30

**Status**: Draft

**Short name**: `visual-update-03`

## User Scenarios & Testing

### User Story 1 — Oprava: Home zobrazuje data aktuálneho dňa (Priority: P1)

Ako používateľ chcem, aby Home obrazovka vždy zobrazovala dáta aktuálneho dňa. Ak dňešný deň ešte nie je vyplnený, chcem vidieť vizuálny placeholder — nie dáta z predchádzajúceho dňa.

**Why this priority**: Kritická chyba v dátovej integrite — používateľ vidí zavádzajúce informácie (dáta z iného dňa). Oprava je nevyhnutná pred ďalšími vizuálnymi zmenami.

**Independent Test**: Vyplniť deň, počkať do ďalšieho dňa (alebo zmeniť systémový dátum) → otvoriť Home → musí sa zobraziť placeholder (sivé bary), nie dáta z predchádzajúceho dňa. Nadpis musí ukazovať aktuálny dátum.

**Acceptance Scenarios**:

1. **Given** som otvoril Home a dnešný deň ešte nie je vyplnený, **When** sa obrazovka zobrazí, **Then** bar chart zobrazuje placeholder: 3 sivé bary rôznej veľkosti naľavo aj napravo, bez popiskov, v svetlosivej farbe.
2. **Given** som otvoril Home a dnešný deň je vyplnený, **When** sa obrazovka zobrazí, **Then** bar chart zobrazuje skutočné dáta aktuálneho dňa.
3. **Given** Home obrazovka je otvorená, **When** sa zmení dátum (nový deň), **Then** pri ďalšom zobrazení Home sa automaticky skontroluje aktuálny dátum a zobrazí placeholder (ak nový deň nie je vyplnený).
4. **Given** placeholder je zobrazený, **When** si ho používateľ prezrie, **Then** nie sú viditeľné žiadne hodnoty indexov ani entít z predchádzajúceho dňa.

---

### User Story 2 — Auto-ukladanie pri prepnutí aktivity (Priority: P1)

Ako používateľ chcem, aby sa každá zmena v trackeri (prepnutie switcha, pohyb slidera) automaticky uložila, aby som nestratil dáta pri prekliknutí na inú obrazovku. Tlačidlo "Uložiť deň" nie je potrebné.

**Why this priority**: Súčasné tlačidlo "Uložiť deň" spôsobuje stratu dát pri navigácii bez uloženia. Auto-ukladanie robí aplikáciu odolnejšou a priamočiarou.

**Independent Test**: Otvoriť tracker → prepnúť switch entity na ON → bez kliknutia "Uložiť" navigovať na Home → vrátiť sa na tracker pre rovnaký deň → switch musí zostať ON.

**Acceptance Scenarios**:

1. **Given** som v trackeri a prepnem switch entity, **When** sa switch zmení, **Then** zmena sa okamžite uloží bez nutnosti kliknúť tlačidlo.
2. **Given** som v trackeri a posuniem slider, **When** slider zmení hodnotu, **Then** nová hodnota sa uloží (s krátkym debounce aby sa neznásobili DB zápisy).
3. **Given** som v trackeri, **When** zobrazím obrazovku, **Then** tlačidlo "Uložiť deň" nie je viditeľné.
4. **Given** navigujem preč z trackera bez manuálneho uloženia, **When** sa vrátim na tracker pre rovnaký deň, **Then** všetky vyplnené hodnoty sú zachované.

---

### User Story 3 — Vylepšený dual bar chart: kategórie, váhy, skupovanie (Priority: P2)

Ako používateľ chcem, aby dual bar chart zoskupoval entity podľa kategórie, zobrazoval entity z rovnakej kategórie vedľa seba (pozitívne napravo, negatívne naľavo), a aby bol v každom bare viditeľný presný výpočet váhy.

**Why this priority**: Aktuálny graf neumožňuje porovnanie entít v rámci tej istej kategórie. Zobrazenie váh dáva používateľovi priamu spätnú väzbu o vplyve každej aktivity.

**Independent Test**: Vyplniť deň vrátane aspoň 1 pozitívnej aj 1 negatívnej entity z rovnakej kategórie (napr. Strava: Proteiny + Alkohol) → otvoriť Home alebo Detail → skontrolovať, že sú zobrazené naproti sebe, a že vo vnútri baru je číselná hodnota váhy.

**Acceptance Scenarios**:

1. **Given** mám vyplnenú pozitívnu aj negatívnu entitu z rovnakej kategórie, **When** zobrazím dual bar chart, **Then** obe entity sú zobrazené na rovnakom riadku — negatívna naľavo, pozitívna napravo.
2. **Given** kategória má iba jednu stranu (len negatívne alebo len pozitívne), **When** sa zobrazí riadok, **Then** druhá strana zostáva prázdna (biela/prázdna plocha).
3. **Given** bar chart je zobrazený, **When** pozriem na ľubovoľný bar, **Then** vo vnútri baru vidím presnú číselnú hodnotu váhy pre daný deň.
4. **Given** mám viacero entít v jednej kategórii (napr. Strava: Alkohol, Kofeín, Proteiny), **When** sa zobrazia v grafe, **Then** všetky entity z kategórie Strava sú skupeny vedľa seba — žiadna iná entita nie je medzi nimi.

---

### User Story 4 — Koláčový graf na obrazovke Denný detail (Priority: P2)

Ako používateľ chcem vidieť koláčový graf na obrazovke Denného detailu, ktorý zobrazuje relatívne zastúpenie všetkých vyplnených aktivít za daný deň.

**Why this priority**: Koláčový graf poskytuje rýchly prehľad o kompozícii dňa — ktoré aktivity dominovali.

**Independent Test**: Vyplniť aspoň 3 entity → otvoriť Denný detail (VectorScreen) → koláčový graf musí byť viditeľný a zobrazovať všetky vyplnené entity s rôznymi farebnými výsečami.

**Acceptance Scenarios**:

1. **Given** som na obrazovke Denný detail a mám vyplnené aspoň 2 entity, **When** sa obrazovka zobrazí, **Then** koláčový graf je viditeľný s farebnými výsečami pre každú vyplnenú entitu.
2. **Given** koláčový graf je zobrazený, **When** si ho prezerám, **Then** každá výseč je farebne odlíšená a označená menom entity alebo skratkou.
3. **Given** žiadne entity nie sú vyplnené, **When** sa zobrazí Denný detail, **Then** koláčový graf nie je zobrazený alebo zobrazuje prázdny stav.

---

### User Story 5 — Navigácia swipom medzi dňami na Home (Priority: P2)

Ako používateľ chcem na Home obrazovke swipovať doľava/doprava medzi dňami, aby som mohol rýchlo prechádzať históriou bez potreby otvárať iné obrazovky.

**Why this priority**: Rýchla navigácia v histórii je kľúčová pre sledovanie trendov priamo z hlavnej obrazovky.

**Independent Test**: Swipnúť doľava na Home → musí sa zobraziť predchádzajúci deň (ak existuje). Swipnúť doprava → musí sa zobraziť nasledujúci deň. Swipe na neexistujúci deň nemá žiadny efekt.

**Acceptance Scenarios**:

1. **Given** som na Home a existuje predchádzajúci vyplnený deň, **When** swipnem doľava, **Then** zobrazí sa graf a dáta predchádzajúceho dňa; nadpis sa zmení na "Historické dáta – [dátum]".
2. **Given** som na Home a zobrazujem historický deň, **When** swipnem doprava, **Then** zobrazí sa nasledujúci deň (alebo dnešný ak je najbližší).
3. **Given** zobrazenú deň je najstarší dostupný, **When** swipnem doľava, **Then** swipe sa nevykoná (žiadna akcia).
4. **Given** zobrazujem dnešný deň, **When** swipnem doprava, **Then** swipe sa nevykoná (neexistuje budúci deň).
5. **Given** zobrazujem historický deň, **When** vidím nadpis, **Then** nadpis hovorí "Historické dáta – [dátum]" namiesto "Dnešný prehľad".

---

### User Story 6 — Info obrazovka s váhami entít (Priority: P3)

Ako používateľ chcem mať v menu prístup k informačnej obrazovke, kde vidím aktuálne váhy a popisy každej entity, aby som rozumel, čo ovplyvňuje môj index.

**Why this priority**: Transparentnosť algoritmu zvyšuje dôveru a záujem o vyplňovanie.

**Independent Test**: Otvoriť menu → kliknúť "Info" → zobraziť zoznam entít s ich váhami a popismi.

**Acceptance Scenarios**:

1. **Given** som v aplikácii, **When** otvorím menu, **Then** vidím novú položku označenú "Info" (s ikonou "i").
2. **Given** som na Info obrazovke, **When** sa zobrazí zoznam, **Then** každá entita je zobrazená s názvom, aktuálnou váhou a krátkym popisom.
3. **Given** som na Info obrazovke, **When** sa zobrazia váhy, **Then** váhy zodpovedajú aktuálnym hodnotám (personalizovaným ak existujú, inak default).

---

### User Story 7 — Ikona domu v menu namiesto "H" (Priority: P3)

Ako používateľ chcem vidieť v dolnom menu ikonu domu namiesto písmena "H", aby bola navigácia intuitívnejšia a konzistentná s bežnými mobilnými aplikáciami.

**Why this priority**: Štandardná ikona domu je všeobecne zrozumiteľná. Písmeno "H" je menej intuitívne.

**Independent Test**: Otvoriť aplikáciu → dolné menu → namiesto "H" musí byť ikona domu.

**Acceptance Scenarios**:

1. **Given** som v aplikácii, **When** zobrazím dolné navigačné menu, **Then** Home položka má ikonu domu (nie text "H").

---

### User Story 8 — Vyšetrovanie: User-defined entity v trackeri (Priority: P3)

Ako správca aplikácie chcem potvrdiť, či entity pridané používateľom cez správu entít sa zobrazujú v trackeri. Ak nie, je to chyba na opravu.

**Why this priority**: Bez možnosti zadávať vlastné entity v trackeri je funkcia správy entít neúplná.

**Independent Test**: Pridať novú entitu v EntityManagementScreen → otvoriť tracker → nová entita musí byť viditeľná a prepínateľná.

**Acceptance Scenarios**:

1. **Given** som pridal novú entitu cez správu entít, **When** otvorím tracker, **Then** nová entita je viditeľná v zozname s on/off switchom.
2. **Given** nová entita je v trackeri, **When** ju prepnem a uložím, **Then** jej hodnota je zahrnutá do denného indexu.

---

### Edge Cases

- Čo ak dnešný deň ešte neexistuje v DB pri auto-ukladaní? → Automaticky vytvoriť záznam pre aktuálny deň.
- Čo ak slider produkuje príliš veľa DB zápisov pri posúvaní? → Implementovať debounce (napr. 500ms) aby sa save spustil až po skončení pohybu.
- Čo ak dual bar chart má kategóriu s 3 negatívnymi a 0 pozitívnymi entitami? → Všetky 3 negatívne entity sú zobrazené na ľavej strane v rámci kategórie; pravá strana prázdna.
- Čo ak na Info obrazovke sú personalizované váhy? → Zobraziť personalizovanú váhu (ak existuje), s vizuálnym odlíšením od default váhy.
- Čo ak swipe detekcia koliduje so scrollovaním? → Horizontálny swipe má prednosť pred vertikálnym scrollom; vertikálne scrollovanie je stále funkčné.
- Čo ak koláčový graf má príliš veľa entít (napr. 12)? → Zobraziť iba top 5–6, zvyšok zlúčiť do "Ostatné".

## Requirements

### Functional Requirements

- **FR-001**: Home obrazovka MUSÍ pri každom zobrazení skontrolovať aktuálny dátum a zobraziť dáta iba ak dnes existuje vyplnený záznam.
- **FR-002**: Ak dnes neexistuje vyplnený záznam, Home MUSÍ zobraziť placeholder: 3 sivé bary naľavo a 3 sivé bary napravo, rôznych veľkostí, bez popiskov, v svetlosivej farbe.
- **FR-003**: Tracker MUSÍ automaticky uložiť zmeny pri každom prepnutí switcha entity.
- **FR-004**: Tracker MUSÍ uložiť zmenu slidera po krátkej pauze (debounce) bez nutnosti kliknúť tlačidlo.
- **FR-005**: Tlačidlo "Uložiť deň" MUSÍ byť odstránené z trackera (horné aj dolné).
- **FR-006**: Dual bar chart MUSÍ zoskupovať entity podľa kategórie — všetky entity tej istej kategórie sú zobrazené za sebou.
- **FR-007**: V dual bar charte, entity z rovnakej kategórie s opačným impaktom MUSIA byť zobrazené naproti sebe (negatívna naľavo, pozitívna napravo na rovnakom riadku).
- **FR-008**: Každý bar v dual bar charte MUSÍ zobrazovať číselnú hodnotu efektívnej váhy vo vnútri baru.
- **FR-009**: VectorScreen (Denný detail) MUSÍ zobrazovať koláčový graf so všetkými vyplnenými aktivitami.
- **FR-010**: Home obrazovka MUSÍ podporovať horizontálny swipe doľava (predchádzajúci deň) a doprava (nasledujúci deň).
- **FR-011**: Swipe na neexistujúci deň (žiadny záznam pred/po) MUSÍ byť ignorovaný.
- **FR-012**: Keď Home zobrazuje historický deň, nadpis MUSÍ byť "Historické dáta – [dátum]".
- **FR-013**: Menu MUSÍ obsahovať novú položku "Info" s ikonou "i".
- **FR-014**: Info obrazovka MUSÍ zobraziť zoznam všetkých entít s ich aktuálnou váhou a popisom.
- **FR-015**: Dolné menu MUSÍ zobraziť ikonu domu pre Home položku namiesto textu "H".
- **FR-016**: Entity pridané používateľom cez správu entít MUSIA byť viditeľné a použiteľné v trackeri.

### Key Entities

- **DenníZáznam (DayRecord)**: Vyplnený deň v DB. Existencia záznamu pre aktuálny dátum určuje, či Home zobrazuje dáta alebo placeholder.
- **KategóriaEntity**: Skupina entít; rozhoduje o zoskupení v dual bar charte (nové zobrazenie — entity z rovnakej kategórie na rovnakých riadkoch).
- **VáhaEntity**: Aktuálna efektívna váha entity (personalizovaná alebo default); zobrazuje sa vo vnútri baru.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Home zobrazuje placeholder (nie predchádzajúce dáta) v 100 % prípadov, keď dnešný deň nie je vyplnený.
- **SC-002**: 0 % strát dát pri navigácii preč z trackera bez manuálneho uloženia — všetky prepnuté entity zostávajú zachované.
- **SC-003**: Dual bar chart správne skupuje entity podľa kategórie — žiadna entita nesusedí s entitou z inej kategórie ak existuje voľné miesto v jej vlastnej kategórii.
- **SC-004**: Každý bar v dual bar charte zobrazuje číselnú hodnotu váhy viditeľnú bez priblíženia.
- **SC-005**: Koláčový graf na VectorScreen je zobrazený pre každý deň s aspoň 1 vyplnenou entitou.
- **SC-006**: Swipe doľava aj doprava funguje správne — zobrazuje predchádzajúci/nasledujúci deň; swipe na neexistujúci deň nemá žiadny efekt.
- **SC-007**: Info obrazovka je dostupná z menu a zobrazuje váhy všetkých entít.
- **SC-008**: Entity pridané používateľom cez správu entít sú viditeľné v trackeri.

## Assumptions

- Auto-ukladanie (FR-003, FR-004) nevytvára duplicitné záznamy — ak záznam pre daný deň existuje, aktualizuje sa; inak sa vytvorí nový.
- Debounce pre slider je ~500ms — dostatočne rýchly pre plynulý UX, dostatočne pomalý pre redukciu DB zápisov.
- Koláčový graf (FR-009) zobrazuje relatívne váhy vyplnených entít — rozmer výseče zodpovedá hodnote `value_effective` každej entity.
- Swipe navigácia (FR-010) prechádza iba cez dni s existujúcimi záznamami v DB — nebude navigovať na prázdne dni bez záznamu (výnimka: dnešný deň, kde placeholder je platný stav).
- Ciel 3 (user entities v trackeri) sa predpokladá ako bug: entity pridané cez správu entít by mali byť v trackeri viditeľné. Ak sa potvrdí, že je to zámer, bude USC8 uzavretá ako "won't fix".
- Info obrazovka zobrazuje váhy z `WeightEntity` (personalizované ak existujú, default inak) — žiadna nová entita v DB nie je potrebná.
- Ikona domu (FR-015) použije Material Icons štandardnú ikonu `Icons.Default.Home` — žiadny externý zdroj ikon.
