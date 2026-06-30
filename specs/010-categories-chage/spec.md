# Feature Specification: Unified Entity Tree (010-categories-chage)

**Feature Branch**: `010-categories-chage`

**Created**: 2026-06-30

**Status**: Draft

**Input**: Zjednotiť categories a elements do jednej stromovej štruktúry; analyzovať scale pre top-level uzly a separáciu user-defined kategórií pre multi-user.

---

## Kontext

Aplikácia momentálne rozlišuje medzi dvoma typmi konfiguračných objektov:

- **Category** — štítok so závislosťami (napr. `sleep`, `lifestyle`) bez priamej sledovateľnosti
- **Element** — konkrétna sledovaná aktivita (napr. `Kvalitný spánok`) s `impact`, `weight`, `active`

Tento dualismus je zbytočný. Každý uzol stromu môže byť buď rodič (má potomkov) alebo list (je priamo sledovateľný) — alebo oboje (top-level uzol s podkategóriami, ktorý sa dá sám tiež trackovat). Rozlíšenie závisí iba od toho, či má `parent` alebo nie, a či má `active: true`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Existujúce sledovanie funguje bez zmeny po refaktore (Priority: P1)

Ako vývojár a používateľ chcem, aby sa po zlúčení štruktúry nič viditeľné v UI nezmenilo — všetky existujúce entity sa trackujú rovnako ako doteraz.

**Why this priority**: Základná podmienka refaktoru — nesmie spôsobiť regresiu v existujúcom trackovaní.

**Independent Test**: Nainštalovať app po zmene, otvoriť Tracker, vyplniť existujúce entity (spánok, stres, fyzická aktivita...), uložiť. Denný index musí byť vypočítaný rovnako ako pred zmenou.

**Acceptance Scenarios**:

1. **Given** existujúca DB s dátami, **When** app sa aktualizuje na novú verziu, **Then** všetky doterajšie záznamy sú čitateľné a zobrazované správne.
2. **Given** nový inštalácia, **When** YAML config je načítaný, **Then** Tracker zobrazí rovnaké entity ako pred refaktorom — v rovnakom poradí a s rovnakými váhami.
3. **Given** vyplnený deň, **When** sa vypočíta index, **Then** výsledok je numericky zhodný s výpočtom pred refaktorom (tolerancia ±0.01).

---

### User Story 2 — Top-level kategóriu možno priamo trackovať (Priority: P2)

Ako používateľ chcem mať možnosť označiť celú kategóriu (napr. „Fyzická aktivita") bez nutnosti vyplňovať jej podkategórie. Ak zároveň vyplním podkategórie, index tejto kategórie sa prepočíta ako vážený priemer podkategórií.

**Why this priority**: Rozširuje sledovateľnosť bez nutnosti meniť UI — pridáva hodnotu pre používateľov s jednoduchším životným štýlom, kde podkategórie nemajú zmysel.

**Independent Test**: V YAML nastaviť top-level kategóriu `physical_activity` s `active: true`, `impact: 1`. Otvoriť Tracker — `physical_activity` sa objaví ako switchovateľná entita. Zapnúť switch. Denný index musí zahŕňať príspevok tejto kategórie podľa jej váhy.

**Acceptance Scenarios**:

1. **Given** top-level kategória má `active: true` a `impact` definovaný, **When** Tracker sa otvorí, **Then** kategória je viditeľná ako samostatná položka s on/off switchom.
2. **Given** top-level kategória je zapnutá A aspoň jedna jej podkategória je tiež zapnutá, **When** sa počíta index, **Then** hodnota top-level kategórie je vážený priemer hodnôt jej zapnutých podkategórií (nie súčet).
3. **Given** top-level kategória je zapnutá A žiadna podkategória nie je zapnutá, **When** sa počíta index, **Then** top-level kategória prispieva s `valueEffective = 1.0` (binárne zapnuté) × svoju váhu.
4. **Given** top-level kategória má `active: false`, **When** Tracker sa otvorí, **Then** kategória v Trackeri viditeľná nie je (rovnaké správanie ako doteraz pre nearchivované entity).

---

### User Story 3 — `overall_feeling` je súčasťou jednotnej štruktúry (Priority: P2)

Ako vývojár chcem, aby `overall_feeling` nebolo špeciálny prípad v kóde, ale regulárny koreňový uzol (parent: null) v jednotnej stromovej štruktúre.

**Why this priority**: Odstraňuje hardkódované špeciálne správanie a zjednodušuje výpočtovú logiku.

**Independent Test**: Odstrániť zo zdrojového kódu všetky hardkódované kontroly `if (key == "overall_feeling")` — nahradiť generickými pravidlami (napr. `if (el.scale != null && el.parent == null)`). Tracker musí stále zobrazovať `Celkový pocit` ako povinný slider 1–5.

**Acceptance Scenarios**:

1. **Given** `overall_feeling` je definovaný v unified config s `parent: null`, `scale: [1,2,3,4,5]`, `active: true`, **When** Tracker sa načíta, **Then** `Celkový pocit` sa zobrazí ako povinný slider na prvej pozícii.
2. **Given** unified štruktúra, **When** sa vytvára zoznam trackovaných entít, **Then** logika nevyžaduje špeciálny prípad pre `overall_feeling` — vyplýva z atribútov uzla.

---

### User Story 4 — User-defined kategórie v škálovateľnej dátovej štruktúre (Priority: P3)

Ako vývojár chcem, aby user-defined kategórie (pridané cez EntityManagement) boli uložené tak, že pri prechode na multi-user nepovedia existujúce preddefinované systémové kategórie.

**Why this priority**: Rozhodnutie o separácii tabuliek je lacné urobiť teraz, drahé neskôr (migrácia všetkých dát pri multi-user roll-out).

**Independent Test**: Pridať user-defined entitu cez EntityManagement. Entita sa objaví v Trackeri. V DB (overiteľné cez SQLite browser) je uložená v inej tabuľke ako systémové entity.

**Acceptance Scenarios**:

1. **Given** používateľ pridá novú entitu cez EntityManagement, **When** sa uloží, **Then** je v `user_element` tabuľke (nie v systémovej konfigurácii).
2. **Given** systémové entity sú v YAML config (immutable), **When** sa načíta zoznam entít, **Then** Tracker merguje systémové + user-defined do jedného zobrazenia.
3. **Given** budúci multi-user server, **When** sa budú synchronizovať dáta, **Then** systémové entity sú zdieľané (per-config), user-defined sú per-user (oddeliteľné bez migrácie).

---

### Edge Cases

- Čo sa stane, ak top-level kategória aj jej podkategória sú obe zapnuté? → Index kategórie sa nahradí váženým priemerom podkategórií (podkategórie majú prioritu).
- Čo ak má uzol `parent` sám seba alebo cyklickú referenciu? → Config loader MUST validovať a zamietnuť cyklické referencie.
- Čo ak `overall_feeling` chýba v config? → App MUST zobraziť chybový stav a znemožniť uloženie dňa.
- Čo ak je top-level uzol zapnutý A jeho podkategórie majú celkovú váhu 0? → Použiť fallback na binárnu hodnotu uzla samého.
- Čo ak používateľ pridá user-defined entitu s rovnakým kľúčom ako systémová? → User-defined entita sa odmietne (duplikátny kľúč je chyba).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Systém MUST načítať YAML config ako jednu stromovú štruktúru bez rozlíšenia na `categories` a `elements` sekcie — každý uzol má `key`, `weight`, `impact?`, `parent?`, `description?`, `active`, `scale?`.
- **FR-002**: Uzol bez `parent` je koreňový (top-level); uzol s `parent` je potomok. Hĺbka stromu nie je obmedzená konfiguráciou (prakticky max 2–3 úrovne).
- **FR-003**: Uzol s `active: true` MUSÍ byť zobrazený v Trackeri ako sledovateľná položka bez ohľadu na to, či má potomkov.
- **FR-004**: Systém MUST vypočítať `valueEffective` top-level uzla ako vážený priemer `valueEffective` jeho aktívnych potomkov, ak sú aspoň 2 potomkovia zapnutí. Ak je zapnutý iba rodičovský uzol, použije sa jeho binárna hodnota (1.0).
- **FR-005**: `overall_feeling` MUST ostať koreňovým uzlom (`parent: null`) so `scale: [1,2,3,4,5]` a nesmie byť vynechateľný pri ukladaní dňa.
- **FR-006**: Config loader MUST validovať: (a) neexistenciu cyklických referencií, (b) prítomnosť `overall_feeling`, (c) nezápornú váhu každého uzla.
- **FR-007**: User-defined entity MUST byť uložené v oddelenej DB tabuľke (`user_element`) s FK pripravením na budúci `user_id` stĺpec — oddelené od systémovej konfigurácie.
- **FR-008**: Kotlin dátový model (`ElementConfig` a súvisiace triedy) MUST reflektovať zjednotenú stromovú štruktúru — trieda `Category` sa zlučuje s `Element` do jednej triedy (napr. `EntityNode`).
- **FR-009**: Všetky miesta v kóde, ktoré rozlišujú medzi `Category` a `Element` (napr. `elementConfig.categories`, `elementConfig.elements`), MUST byť nahradené prístupom cez jednotnú stromovú štruktúru.
- **FR-010**: DB schéma MUST byť aktualizovaná s migráciou (Room migration) — žiadne dáta existujúcich používateľov nesmú byť stratené.

### Analýza: Scale na top-level uzloch

**Otázka**: Majú mať top-level kategórie (napr. `physical_activity`, `sleep`) parameter `scale`?

**Odporúčanie: NIE pre fázu 1.**

Dôvody:
1. **Kognitívna záťaž**: Pridanie slidera 1–5 ku každej top-level kategórii zdvojnásobuje počet vstupov bez jasnej pridanej hodnoty — top-level kategórie sú prirodzene binárne („robil/nerobil celú oblasť").
2. **Konflikt s potomkami**: Ak kategória `physical_activity` má scale a zároveň jej potomok tiež má scale, nie je jasné, ako ich skombinovať — priorita potomkov vs. priama hodnota rodiča by bola ambivalentná.
3. **Výpočtová čistota**: Bez scale pre top-level uzly platí jednoduchá logika: ak sú potomkovia zapnutí, použije sa ich vážený priemer; ak je zapnutý len rodič, je to `1.0`.

**Budúce rozhodnutie**: Scale na top-level pridať iba ak sa ukáže, že existujú kategórie bez podkategórií, ktoré prirodzene potrebujú gradáciu (napr. nová kategória `wellbeing` bez podkategórií).

### Analýza: User-defined kategórie — rovnaká vs. separátna tabuľka

**Otázka**: Musia byť user-defined kategórie v rovnakej DB tabuľke ako systémové?

**Odporúčanie: SEPARÁTNA tabuľka `user_element` (existujúca prax — zachovať).**

| Kritérium | Rovnaká tabuľka | Separátna tabuľka (`user_element`) |
|-----------|----------------|-------------------------------------|
| Jednoduchosť kódu | Vyššia | Mierne nižšia (merge pri načítaní) |
| Multi-user readiness | Nízka — `user_id` FK v systémovej tabuľke | Vysoká — `user_element` dostane `user_id`, systémová ostane shared |
| Migrácia pri multi-user | Drahá (split tabuľky) | Lacná (pridať stĺpec `user_id`) |
| Bezpečnosť | Riziko: user zmení systémové entity | Nula: systémové entity sú read-only |
| Výkon pri 10k+ user entities | Degradácia systémovej tabuľky | Izolovaná — systémová ostane malá a cacheable |

**Záver**: Separátna tabuľka `user_element` (aktuálne existuje ako `UserElementEntity`) je správna voľba. Stačí pridať `userId: String? = null` stĺpec ako nullable placeholder — pri multi-user sa naplní.

### Key Entities

- **EntityNode**: Zjednotený uzol stromu — nahrádza `Category` + `Element`. Atribúty: `key`, `weight`, `impact?`, `parent?`, `description?`, `active`, `scale?`, `clickable?`.
- **EntityConfig**: Nová verzia `ElementConfig` — obsahuje `Map<String, EntityNode>` namiesto separátnych `categories` a `elements`.
- **UserElementEntity**: Existujúca DB entita pre user-defined entity — rozšírená o nullable `userId` pre budúci multi-user.
- **WeightEntity**: Zostáva nezmenená — odkazuje na `element_key` (zachovaná spätná kompatibilita).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Po aktualizácii žiadna existujúca dátová strata — 100% existujúcich záznamov je čitateľných a správne zobrazených.
- **SC-002**: Vypočítaný denný index sa numericky zhoduje s predchádzajúcim výpočtom pre rovnaké vstupné dáta (tolerancia ±0.01 percentuálneho bodu).
- **SC-003**: Tracker zobrazuje rovnaký počet sledovateľných entít ako pred refaktorom — pri totožnej konfigurácii.
- **SC-004**: Top-level kategória s `active: true` sa objaví v Trackeri a jej príspevok k indexu je správne vypočítaný (overiteľné ručným výpočtom).
- **SC-005**: Čas načítania konfigurácie neprekračuje 200ms na referenčnom zariadení (Android min SDK 26).
- **SC-006**: User-defined entita pridaná cez EntityManagement je v Trackeri viditeľná do 2 sekúnd bez reštartu aplikácie.

---

## Assumptions

- Existujúce YAML súbory (`entities.yaml` alebo ekvivalent) sú dostupné v assets a budú manuálne aktualizované počas implementácie.
- Hĺbka stromu bude v praxi max 2 úrovne (root → leaf) — hlbšie stromy nie sú predpokladané.
- Top-level kategórie bez `impact` definovaného sú defaultne netrackovateľné (`active: false`) — nezobrazujú sa v Trackeri.
- `scale` na top-level uzloch sa NEPRIDÁVA v tejto fáze (viď analýza vyššie).
- `userId` v `user_element` tabuľke sa pridáva ako nullable stĺpec — v single-user ostáva `null`.
- Room migrácia z aktuálnej verzie DB je povinná — žiadne deštrukívne zmeny schémy.
- Výpočtová logika indexu (§II Constitution) zostáva funkčne ekvivalentná — zmeny sú iba v tom, ako sa zisťuje zoznam aktívnych entít a ich váhy.
