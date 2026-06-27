# Feature Specification: Dual Vector Split (Positive/Negative ADHD Sub-Indices)

**Feature Branch**: `004-dual-vector-split`

**Created**: 2026-06-27

**Status**: Done

**Input**: User description: "rozdelit vypocet ADHD vektora na pozitivnu cast (sleep, physical_activity, nutrition_protein, mindfulness - chceme maximalizovat) a negativnu cast (stress_work, stress_personal, alcohol, caffeine - chceme minimalizovat). Trend screen zobrazuje oba vektory ako dual-bar chart (zelene a cervene stlpce per den). Home screen zobrazuje oba sub-indexy. Radar chart kreslí dva oddělene polygóny - zeleny pre pozitívne elementy, červený pre negatívne. DB migrácia v1 na v2."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pochopenie svojho stavu cez dva vektory na Home obrazovke (Priority: P1)

Používateľ otvorí aplikáciu a na hlavnej obrazovke vidí dve čísla: zelený pozitívny index (koľko sa stará o prospešné návyky) a červený negatívny index (koľko škodlivých vzorov má aktívnych). Bez ďalšieho klikania vie, na ktorú oblasť sa dnes zamerať.

**Why this priority**: Home obrazovka je vstupný bod každého dňa. Duálny pohľad okamžite komunikuje, čo zlepšovať — bez nutnosti ísť do detailných obrazoviek.

**Independent Test**: Vyplniť denný tracker, otvoriť Home obrazovku a overiť, že sú viditeľné obe hodnoty — zelený pozitívny index (0–100) a červený negatívny index (0–100) — bez scrollovania.

**Acceptance Scenarios**:

1. **Given** používateľ vyplnil denný tracker, **When** otvorí Home obrazovku, **Then** vidí zelený pozitívny index a červený negatívny index, každý s hodnotou 0–100.
2. **Given** oba indexy sú zobrazené, **When** používateľ sleduje čísla, **Then** je vizuálne jasné, že zelené číslo chce maximalizovať a červené minimalizovať (napr. pomocou farby, popisku alebo šípky).
3. **Given** žiadne dáta nie sú zadané, **When** používateľ otvorí Home obrazovku, **Then** oba indexy zobrazujú prázdny stav (nie chybovú hlášku) s výzvou na vyplnenie trackera.

---

### User Story 2 - Sledovanie trendu oboch vektorov v čase (Priority: P2)

Používateľ otvorí obrazovku Týždenný trend a vidí pre každý deň dva stĺpce — zelený (pozitívny vektor) a červený (negatívny vektor). Môže sledovať, ako sa oba vektory vyvíjajú a či sa mu darí zvyšovať zelený a znižovať červený.

**Why this priority**: Trend je kľúčový pre dlhodobú motiváciu. Vizuálne porovnanie dvoch vektorov v čase dáva oveľa bohatšiu informáciu ako jeden kombinovaný index.

**Independent Test**: Po 3+ dňoch vyplnených dát otvoriť Trend obrazovku a overiť, že každý deň má zelený stĺpec (pozitívny index) a červený stĺpec (negatívny index) s proporcionálnymi výškami.

**Acceptance Scenarios**:

1. **Given** existujú záznamy za posledné 7 dní, **When** používateľ otvorí Trend obrazovku, **Then** zobrazí sa dual-bar chart so zeleným a červeným stĺpcom pre každý deň.
2. **Given** deň s vysokými pozitívnymi hodnotami (napr. dostatok spánku, cvičenie), **When** je zobrazený v grafe, **Then** zelený stĺpec je výrazne vyšší ako červený.
3. **Given** deň s vysokou záťažou (stres, alkohol), **When** je zobrazený v grafe, **Then** červený stĺpec je výrazne vyšší ako v normálny deň.
4. **Given** chýbajúce dáta pre niektoré dni, **When** je graf zobrazený, **Then** tieto dni sú reprezentované prázdnymi stĺpcami alebo jasným vizuálnym indikátorom chýbajúcich dát.

---

### User Story 3 - Vizuálne rozdelenie radar chartu na dva polygóny (Priority: P3)

Používateľ otvorí obrazovku Advanced vektor a vidí radar chart s dvoma oddelenými polygónmi — zeleným (pozitívne elementy) a červeným (negatívne elementy). Má okamžitý vizuálny prehľad o silných stránkach (zelená plocha) vs. problematických oblastiach (červená plocha).

**Why this priority**: Vizuálne oddelenie v radare posilňuje duálnu metaforu. Je to vizuálne vylepšenie nad feature 003 (farebnými osami), nie blocker.

**Independent Test**: Otvoriť Advanced vektor obrazovku a overiť, že radar chart zobrazuje dva oddelené farebné polygóny — jeden pre 4 pozitívne osi (svetlozelený), jeden pre 4 negatívne osi (svetločervený).

**Acceptance Scenarios**:

1. **Given** používateľ má vyplnený denný tracker, **When** otvorí Advanced vektor, **Then** radar chart zobrazuje zelený polygón spájajúci hodnotové body pozitívnych elementov a červený polygón spájajúci hodnotové body negatívnych elementov.
2. **Given** oba polygóny sú zobrazené, **When** sú oba vizuálne čitateľné, **Then** zelený polygón je väčší pri dobre zvládnutom dni, červený polygón je menší pri dobre zvládnutom dni.
3. **Given** chýbajúce hodnoty pre niektoré elementy, **When** je radar zobrazený, **Then** chýbajúce body sú nastavené na nulu a polygón je stále vykreslený konzistentne.

---

### Edge Cases

- Čo ak má používateľ vyplnené len niektoré elementy jednej skupiny? Sub-index sa vypočíta z dostupných elementov, výsledok sa zobrazí s upozornením "neúplné dáta".
- Čo ak sú všetky negatívne elementy nula (žiadny stres, žiadny alkohol)? Negatívny index = 0, zelený stĺpec dominuje — toto je ideálny stav, aplikácia ho môže vizuálne oceniť.
- Čo ak sú všetky pozitívne elementy nula? Pozitívny index = 0, červený stĺpec dominuje — aplikácia zobrazí varovanie alebo CTA na zlepšenie.
- Čo ak existujúce záznamy nemajú uložené sub-indexy (dáta pred migráciou)? Tieto dni sa zobrazia v grafe bez hodnôt sub-indexov (prázdne stĺpce) — historické dáta sa neprepisujú.
- Čo ak kombinovaný ADHD index prestane existovať? Predpokladáme, že zostáva — sub-indexy sú doplnok, nie náhrada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Systém MUST vypočítať pozitívny sub-index (0–100) ako vážený priemer elementov `sleep`, `physical_activity`, `nutrition_protein`, `mindfulness` s ich aktuálnymi váhami.
- **FR-002**: Systém MUST vypočítať negatívny sub-index (0–100) ako vážený priemer elementov `stress_work`, `stress_personal`, `alcohol`, `caffeine` s ich aktuálnymi váhami (vyššia hodnota = horšie správanie).
- **FR-003**: Oba sub-indexy MUST byť vypočítané a uložené vždy, keď sa ukladá alebo prepočítava denný tracker.
- **FR-004**: Home obrazovka MUST zobrazovať pozitívny sub-index (zelený) a negatívny sub-index (červený) súčasne, viditeľne bez scrollovania.
- **FR-005**: Home obrazovka MUST vizuálne komunikovať smer každého indexu — pozitívny = chceme vyšší, negatívny = chceme nižší.
- **FR-006**: Trend obrazovka MUST zobrazovať dual-bar chart s jedným zeleným stĺpcom (pozitívny sub-index) a jedným červeným stĺpcom (negatívny sub-index) pre každý deň za posledných 7 dní.
- **FR-007**: Radar chart (Advanced vektor) MUST kresliť dva oddelené polygóny — zelený pre osi pozitívnych elementov, červený pre osi negatívnych elementov.
- **FR-008**: Historické záznamy pred zavedením sub-indexov (dni bez uložených sub-indexov) MUST byť zobrazené bez sub-indexových hodnôt (prázdny stav per deň), nie chybová hláška.
- **FR-009**: Kombinovaný ADHD index (existujúci) MUST zostať funkčný a zobrazený — sub-indexy sú doplnok.
- **FR-010**: Výpočet oboch sub-indexov MUST rešpektovať aktuálne adaptované váhy elementov (nie len default váhy).
- **FR-011**: Dátová schéma MUST byť rozšírená migráciou tak, aby každý denný záznam mohol uchovávať oba sub-indexy.

### Key Entities

- **Pozitívny sub-index**: Skóre 0–100 odvodené z pozitívnych elementov; vyššia hodnota = lepšie. Uložený per deň.
- **Negatívny sub-index**: Skóre 0–100 odvodené z negatívnych elementov; vyššia hodnota = horšie. Uložený per deň.
- **Denný záznam (rozšírený)**: Existujúci denný výpočtový záznam rozšírený o oba sub-indexy.
- **Duálny trend rad**: Séria dvojíc (pozitívny, negatívny) per deň pre vizualizáciu trendu.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Používateľ dokáže na Home obrazovke do 5 sekúnd určiť, ktorý vektor je dnes vyšší — bez čítania popiskov.
- **SC-002**: Oba sub-indexy sú vypočítané a zobrazené do 1 sekundy od otvorenia Home obrazovky pri bežnom dennom logu.
- **SC-003**: Trend chart zobrazuje správne hodnoty pre 100 % dní s dostupnými dátami — bez vizuálnych odchýlok alebo chýbajúcich stĺpcov tam, kde dáta existujú.
- **SC-004**: Historické dáta (dni pred migráciou) neohrozia funkčnosť aplikácie — žiadny crash, žiadna chybová hláška.
- **SC-005**: Používateľ rozumie duálnej metafore (maximalizovať zelené, minimalizovať červené) bez potreby návodu — overiteľné prvým otvorením po aktualizácii.
- **SC-006**: Radar chart s dvoma polygónmi je vizuálne prehľadný — oba polygóny sú rozlíšiteľné aj pri nízkych hodnotách.

## Assumptions

- Kombinovaný ADHD index zostáva ako primárna metrika — sub-indexy sú doplnkové zobrazenie, nie náhrada.
- Váhy pozitívnych a negatívnych elementov sa naďalej adaptujú spoločne (existujúci algoritmus) — sub-indexy používajú tie isté adaptované váhy.
- Negatívny sub-index je prezentovaný v surovej forme (0 = ideálne, 100 = maximum negatívneho správania) bez invertovania — používateľ chápe "minimalizovať červené".
- Databázová migrácia v1→v2 je prvou migráciou v projekte; scaffolding bol navrhnutý pre práve tento účel.
- Feature 003 (farebné osi v radar grafe) je implementovaná pred alebo súčasne s touto feature — radar chart v 004 stavia na farebnom rozlíšení z 003.
- Dual-bar chart na Trend obrazovke nahrádza existujúci single-bar chart; kombinovaný index v trende nie je zobrazený (zjednodušenie).
- Oba sub-indexy sa ukladajú len pre nové záznamy — retroaktívny prepočet historických dát nie je súčasťou MVP tejto feature.

## Constitution Check

- **§ I (Architektúra)**: Výpočet sub-indexov patrí do `IndexCalculator` (domain), ukladanie do `Repository`, zobrazenie do ViewModelov a Composables. Žiadna výpočtová logika v UI.
- **§ II (Domenová logika — NON-NEGOTIABLE)**: Nové výpočtové metódy `computePositiveIndex()` a `computeNegativeIndex()` MUSIA byť kryté unit testami pred mergom. Zmena výpočtovej logiky vyžaduje zdôvodnenie v PR.
- **§ III (Dátový model)**: Rozšírenie `IndexDailyEntity` o `positiveIndex` a `negativeIndex` vyžaduje Room migráciu v1→v2. Scaffolding je povinný.
- **§ IV (UX)**: Duálna metafora znižuje kognitívnu záťaž — jednoduchý signál "maximalizuj zelené, minimalizuj červené" je ADHD-friendly.
- **§ VI (Testovanie)**: Unit testy pre oba nové výpočty sú povinnou podmienkou mergu podľa § II.
- **§ VII (Tech stack)**: Žiadne nové závislosti. Room migrácia v existujúcom Room setup.
