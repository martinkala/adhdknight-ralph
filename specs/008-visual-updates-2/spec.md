# Feature Specification: Visual Updates 2

**Feature Branch**: `008-visual-updates-2`

**Created**: 2026-06-29

**Status**: Draft

**Input**: User description: 7 vizuálnych cieľov pre Android ADHD Tracker app

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Double Bar Chart pre Vektor (Priority: P1)

Používateľ vidí na hlavnej obrazovke a na detaile dňa dvojitý stĺpcový graf namiesto radar grafu. Ľavá strana zobrazuje červené záporné entity (impact = -1), pravá strana zelené pozitívne entity (impact = +1). Každý stĺpec má označenie s názvom entity a názvom jej rodičovskej kategórie.

**Why this priority**: Radar graf je ťažko čitateľný na mobilnom displeji. Dvojitý bar chart je prehľadnejší a priamo odráža polaritu entít (pozitívne vs. záporné).

**Independent Test**: Spusti app, otvor HomeScreen a VectorScreen — vidíš dva zoznamy stĺpcov rozdelené na pozitívne/záporné; každý stĺpec má label `[kategória] / [entita]`.

**Acceptance Scenarios**:

1. **Given** zaznamenaný deň s hodnotami, **When** otvorím HomeScreen, **Then** vidím double bar chart s červenými stĺpcami naľavo (záporné entity) a zelenými napravo (pozitívne entity)
2. **Given** double bar chart, **When** čítam label stĺpca, **Then** vidím `[parent kategória] / [názov entity]` (napr. `Životný štýl / Kofeín`)
3. **Given** VectorScreen pre konkrétny dátum, **When** otvorím detail dňa, **Then** rovnaký double bar chart nahradil radar graf
4. **Given** entita bez záznamu pre daný deň, **When** zobrazím chart, **Then** stĺpec má výšku 0 (nie je skrytý)

---

### User Story 2 — Trend: zoradenie od najnovšieho + farebné pozadie (Priority: P1)

Na Trend obrazovke sú dni zobrazené od najnovšieho záznamu po najstarší (zostupne). Každý riadok dňa má bledočervené alebo bledozelené pozadie podľa prevládajúceho impaktu entít zaznamenaných v ten deň.

**Why this priority**: Používatelia prirodzene čítajú od aktuálneho stavu do minulosti. Farebné kódovanie umožňuje rýchlo identifikovať dobré a zlé dni bez čítania čísel.

**Independent Test**: Otvoriť TrendScreen s viacerými záznami — najnovší deň je vždy na vrchu; dni s vysokým indexom majú zelenkastý odtieň, dni s nízkym červenkastý.

**Acceptance Scenarios**:

1. **Given** viaceré záznamy rôznych dní, **When** otvorím TrendScreen, **Then** záznamy sú zoradené od najnovšieho po najstarší
2. **Given** deň kde prevažujú pozitívne entity (index ≥ 50), **When** zobrazím riadok, **Then** pozadie je bledozelené
3. **Given** deň kde prevažujú záporné entity (index < 50), **When** zobrazím riadok, **Then** pozadie je bledočervené
4. **Given** rovnaké záznamy ako pred zmenou, **When** porovnám poradie, **Then** poradie je obrátené oproti pôvodnému (najnovší navrchu)

---

### User Story 3 — Tlačidlo „Uložiť deň" dole na Tracker obrazovke (Priority: P2)

Na Tracker obrazovke pribudne druhé tlačidlo „Uložiť deň" v spodnej časti stránky. Horné tlačidlo zostáva. Používateľ môže uložiť data aj keď je odscrollovaný nadol, bez nutnosti scrollovať späť nahor.

**Why this priority**: UX zlepšenie znižujúce trenie pri zadávaní — časté akcie by mali byť dostupné bez scrollovania.

**Independent Test**: Scrolluj na dno TrackerScreen — vidíš druhé tlačidlo „Uložiť deň"; jeho stlačenie uloží tie isté dáta ako horné tlačidlo.

**Acceptance Scenarios**:

1. **Given** TrackerScreen scrollovaný na spodok, **When** hľadám tlačidlo uloženia, **Then** vidím tlačidlo „Uložiť deň" v dolnej časti obrazovky
2. **Given** vyplnené hodnoty, **When** stlačím dolné tlačidlo, **Then** dáta sú uložené rovnako ako pri hornom tlačidle
3. **Given** horné aj dolné tlačidlo, **When** skontrolím horné, **Then** horné tlačidlo zostáva na svojom mieste bez zmeny

---

### User Story 4 — Farebné pozadie sekcií na Tracker obrazovke (Priority: P2)

Každá sekcia entity na Tracker obrazovke má bledozelené pozadie ak je impact = +1, alebo bledočervené pozadie ak je impact = -1. Farba pochádza z konfigurácie entity (EntityConfig), nie z hodnoty záznamu.

**Why this priority**: Vizuálne odlíšenie sekcií pomáha používateľovi rýchlo identifikovať pozitívne návyky vs. negatívne faktory.

**Independent Test**: Otvoriť TrackerScreen — sekcie pre sleep, physical_activity, mindfulness majú zelenkasté pozadie; sekcie pre stress_work, caffeine, alcohol majú červenkasté pozadie.

**Acceptance Scenarios**:

1. **Given** entita s impact = +1, **When** zobrazím jej sekciu na TrackerScreen, **Then** sekcia má bledozelené pozadie
2. **Given** entita s impact = -1, **When** zobrazím jej sekciu na TrackerScreen, **Then** sekcia má bledočervené pozadie
3. **Given** zmena impact entity v YAML konfigurácii, **When** reštartujem app, **Then** farba sekcie zodpovedá novej hodnote impact

---

### User Story 5 — Kompaktná hlavná obrazovka: metriky na jednej úrovni + premenovanie (Priority: P2)

Na HomeScreen sú „Denný ADHD index", „Spokojnosť" a „Vyplnené" zobrazené na rovnakej vizuálnej úrovni (vedľa seba alebo v kompaktnom rade). „Splnené" je premenované na „Vyplnené". Cieľom je ušetriť jeden riadok výšky oproti súčasnému stavu.

**Why this priority**: Kompaktnejší layout hlavnej obrazovky zobrazí viac relevantných informácií bez scrollovania.

**Independent Test**: Otvoriť HomeScreen — tri metriky sú viditeľné súčasne bez scrollovania; text „Splnené" sa zobrazuje ako „Vyplnené".

**Acceptance Scenarios**:

1. **Given** HomeScreen s platnými dátami, **When** otvorím aplikáciu, **Then** „Denný ADHD index", „Spokojnosť" a „Vyplnené" sú na rovnakej vizuálnej úrovni
2. **Given** HomeScreen, **When** hľadám text „Splnené", **Then** text sa namiesto toho zobrazuje ako „Vyplnené"
3. **Given** kompaktné zobrazenie, **When** porovnám výšku s pôvodným layoutom, **Then** zobrazenie zaberá o aspoň 1 riadok menej

---

### User Story 6 — Odstránenie „Tip dňa" z HomeScreen (Priority: P3)

Sekcia „Tip dňa" je odstránená z hlavnej obrazovky. HomeScreen je jednoduchší a bez rušivého obsahu.

**Why this priority**: Tip dňa neprispieva k sledovaniu ADHD metrík a zaberá cenné miesto.

**Independent Test**: Otvoriť HomeScreen — žiadna sekcia „Tip dňa" nie je viditeľná.

**Acceptance Scenarios**:

1. **Given** HomeScreen, **When** otvorím aplikáciu, **Then** sekcia „Tip dňa" nie je zobrazená
2. **Given** žiadny tip dňa, **When** skontrolím layout, **Then** ostatné sekcie zaplnia uvoľnené miesto

---

### User Story 7 — Premenovanie titulku VectorScreen (Priority: P3)

Titulok VectorScreen (detail dňa) sa mení z formátu `Radar [dátum]` na `Denný detail [dátum]`.

**Why this priority**: Názov „Radar" odkazuje na konkrétny typ grafu, ktorý sa mení. „Denný detail" je popisnejší a odráža obsah obrazovky.

**Independent Test**: Otvoriť VectorScreen pre ľubovoľný dátum — titulok zobrazuje `Denný detail YYYY-MM-DD`.

**Acceptance Scenarios**:

1. **Given** VectorScreen otvorený pre konkrétny dátum, **When** čítam titulok, **Then** titulok je `Denný detail [dátum]`
2. **Given** pôvodný titulok `Radar [dátum]`, **When** aplikujem zmenu, **Then** slovo „Radar" sa nikde v titulku nenachádza

---

### Edge Cases

- Čo sa stane keď nie sú žiadne záznamy pre double bar chart? → Graf sa zobrazí prázdny (výška 0 pre všetky stĺpce), nezostane pôvodný radar.
- Čo ak entita nemá parent kategóriu (root element ako `overall_feeling`)? → Label zobrazí iba názov entity bez lomky.
- Čo ak má deň na Trend obrazovke index presne 50? → Bledozelené pozadie (hraničná hodnota patrí do "dobré").
- Čo ak používateľ stlačí obidve tlačidlá rýchlo za sebou? → Druhé uloženie prepíše prvé (idempotentná operácia).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aplikácia MUST nahradiť radar graf dvojitým stĺpcovým grafom na HomeScreen aj VectorScreen; ľavé stĺpce sú červené (impact = -1), pravé zelené (impact = +1)
- **FR-002**: Každý stĺpec grafu MUST zobrazovať label vo formáte `[parent kategória] / [názov entity]`; root entity (parent = null) zobrazujú iba názov entity
- **FR-003**: TrendScreen MUST zobrazovať záznamy zoradené zostupne (od najnovšieho po najstarší)
- **FR-004**: Každý riadok dňa na TrendScreen MUST mať bledozelené pozadie ak index ≥ 50, bledočervené ak index < 50
- **FR-005**: TrackerScreen MUST obsahovať druhé tlačidlo „Uložiť deň" v dolnej časti obrazovky; obidve tlačidlá musia vykonávať identickú akciu
- **FR-006**: Každá entita sekcia na TrackerScreen MUST mať bledozelené pozadie pre impact = +1 a bledočervené pre impact = -1; farba MUSÍ pochádzať z EntityConfig
- **FR-007**: HomeScreen MUST zobrazovať „Denný ADHD index", „Spokojnosť" a „Vyplnené" na rovnakej vizuálnej úrovni; text „Splnené" MUST byť nahradený textom „Vyplnené"
- **FR-008**: Sekcia „Tip dňa" MUST byť odstránená z HomeScreen
- **FR-009**: Titulok VectorScreen MUST byť vo formáte `Denný detail [dátum]` namiesto `Radar [dátum]`

### Key Entities

- **BarEntry**: reprezentuje jeden stĺpec v double bar charte — kľúč entity, hodnota (0.0–1.0), farba (positive/negative), label (parent/name)
- **TrendRow**: riadok dňa na TrendScreen — dátum, indexValue, farba pozadia odvodeného z indexValue

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Používateľ identifikuje pozitívne vs. záporné entity na prvý pohľad bez čítania čísiel (vizuálne farebné rozlíšenie)
- **SC-002**: Všetkých 7 vizuálnych zmien je viditeľných bez úpravy Kotlin kódu okrem dotknutých obrazoviek
- **SC-003**: TrendScreen zobrazuje najnovší záznam na prvom mieste po otvorení obrazovky
- **SC-004**: TrackerScreen umožňuje uloženie dňa bez scrollovania nahor
- **SC-005**: HomeScreen zobrazuje 3 metriky v jednom vizuálnom riadku — ušetrí aspoň 40px výšky oproti pôvodnému stavu
- **SC-006**: Žiadna regresiu v existujúcej funkcionalite (indexovanie, notifikácie, export) po vizuálnych zmenách

---

## Assumptions

- Farby sú definované ako pastelové odtiene (alpha ~15–20%) kompatibilné s Material3 ColorScheme svetlej aj tmavej témy
- Double bar chart je implementovaný ako Compose Canvas alebo Row/Column layout (bez externej grafickej knižnice — zachováva §VII constitution)
- Výška stĺpcov je normalizovaná voči maximálnej hodnote v danom sete (nie absolútna)
- `overall_feeling` root element sa v double bar charte nezobrazuje (je to špeciálna metrika, nie bežná entita)
- Zmeny sú čisto UI/Compose vrstvy — žiadna zmena doménovej logiky, databázy ani Repository
- Existujúce testy (unit testy indexu, notifikácií) nesmú regresovať
