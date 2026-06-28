# Feature Specification: Visual UI Updates – Home, Trend, Menu & Tracker

**Feature Branch**: `006-visual-updates-1`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "Vizuálne úpravy UI: oprava zobrazovania dátumu na Home stránke, výmena pozícií sekcie ADHD indexu a pozitívne/negatívne, skratkové tlačidlo pre tracker, doplnenie popisov dní v grafe Trendu s klikateľnými detailmi, odstránenie položky Vektor z menu, presunutie tlačidla Uložiť deň v Dennom trackeri."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Oprava Home stránky: dátum, výmena sekcií a skratkové tlačidlo (Priority: P1)

Používateľ otvorí domovskú obrazovku a ihneď vidí:
- správne zobrazený dátum za textom „Dnešný prehľad",
- sekciu pozitívne/negatívne na prominentnom mieste (veľký font, kde bol predtým denný ADHD index),
- denný ADHD index na mieste, kde bola sekcia pozitívne/negatívne (menší font),
- tlačidlo „Upraviť denný záznam" napravo od sekcie pozitívne/negatívne, ktoré ho prenesie priamo na stránku Denného trackera.

**Why this priority**: Home stránka je prvá vec, ktorú používateľ vidí každý deň. Chybný dátum a nesprávna vizuálna hierarchia narúšajú dôveru v dáta. Skratkové tlačidlo znižuje počet kliknutí na primárnu akciu.

**Independent Test**: Dá sa otestovať otvorením aplikácie a overením, že dátum je správny, sekcie sú na správnych miestach so správnou veľkosťou fontu, a tlačidlo naviguje na Denný tracker.

**Acceptance Scenarios**:

1. **Given** domovská obrazovka je otvorená, **When** používateľ si pozrie hlavičku sekcie „Dnešný prehľad", **Then** vidí za textom správne zobrazený aktuálny dátum (napr. „Dnešný prehľad – 28. 6. 2026").
2. **Given** domovská obrazovka je otvorená, **When** používateľ sa pozrie na stred obrazovky, **Then** sekcia pozitívne/negatívne má veľkosť fontu, ktorá bola predtým priradená dennému ADHD indexu, a ADHD index má veľkosť fontu, ktorá bola predtým priradená sekcii pozitívne/negatívne.
3. **Given** domovská obrazovka je otvorená, **When** používateľ stlačí tlačidlo „Upraviť denný záznam", **Then** aplikácia otvorí stránku Denného trackera bez ďalšieho kliknutia.

---

### User Story 2 – Trend: popisky dní v stĺpcoch a klikateľné dni (Priority: P2)

Používateľ si otvorí stránku Trendu, v grafe vidí pri každom stĺpci informáciu o konkrétnom dni. Po kliknutí na stĺpec (deň) sa zobrazí stránka s vektorom daného dňa.

**Why this priority**: Bez popiskov dní je graf neinterpretovateľný – používateľ nevie, ktorý stĺpec zodpovedá ktorému dňu. Klikateľné dni pridávajú hodnotu bez extra navigácie.

**Independent Test**: Otvorením stránky Trendu, overením že každý stĺpec obsahuje označenie dňa, a kliknutím na ľubovoľný stĺpec overiť, že sa zobrazí stránka vektora pre príslušný deň.

**Acceptance Scenarios**:

1. **Given** stránka Trendu je otvorená, **When** používateľ sa pozrie na stĺpcový graf, **Then** každý stĺpec obsahuje viditeľný popis dňa (napr. skrátený dátum alebo názov dňa).
2. **Given** stránka Trendu je otvorená, **When** používateľ klikne na konkrétny stĺpec dňa, **Then** aplikácia zobrazí stránku s detailom vektora pre daný deň.
3. **Given** stránka Trendu je otvorená a pre daný deň neexistujú žiadne dáta, **When** používateľ klikne na príslušný stĺpec, **Then** aplikácia zobrazí prázdny stav so správou, že záznam pre daný deň neexistuje.

---

### User Story 3 – Menu: odstránenie položky Vektor (Priority: P3)

Položka „Vektor" zmizne z navigačného menu. Stránka vektora zostáva dostupná výhradne cez klik na deň v Trende.

**Why this priority**: Zjednodušenie menu znižuje kognitívnu záťaž. Vektor je kontextuálna stránka – dáva zmysel len k špecifickému dňu, nie ako samostatná položka v menu.

**Independent Test**: Otvorením bočného alebo spodného menu a overením, že položka „Vektor" sa tam nenachádza, ale stránka vektora je stále dostupná cez Trend.

**Acceptance Scenarios**:

1. **Given** aplikácia je spustená, **When** používateľ otvorí navigačné menu, **Then** položka „Vektor" sa v menu nenachádza.
2. **Given** stránka Trendu je otvorená, **When** používateľ klikne na deň v grafe, **Then** stránka vektora pre daný deň sa zobrazí (stránka je funkčná, len nie je v menu).

---

### User Story 4 – Denný tracker: presunutie tlačidla Uložiť deň (Priority: P4)

Tlačidlo „Uložiť deň" sa presunie napravo od nadpisu „Denný tracker", aby ho používateľ videl bez scrollovania hneď po otvorení stránky.

**Why this priority**: Používatelia s ADHD majú sklon zabudnúť uložiť záznam, ak tlačidlo nie je okamžite viditeľné. Toto je priame zníženie trenia pri primárnej akcii.

**Independent Test**: Otvorením stránky Denného trackera a overením, že tlačidlo „Uložiť deň" je viditeľné v hornej časti obrazovky vedľa nadpisu bez nutnosti scrollovať.

**Acceptance Scenarios**:

1. **Given** stránka Denného trackera sa otvorí, **When** používateľ sa pozrie na obrazovku (bez scrollovania), **Then** tlačidlo „Uložiť deň" je viditeľné napravo od nadpisu „Denný tracker".
2. **Given** tlačidlo „Uložiť deň" je na novom mieste, **When** používateľ ho stlačí, **Then** záznam sa uloží rovnako ako predtým (funkcionalita uloženia je nezmenená).

---

### Edge Cases

- Čo sa stane, ak dáta pre Home stránku ešte nie sú k dispozícii (prvé spustenie)? → Dátum sa zobrazí správne aj bez dát; sekcie zobrazujú prázdny stav.
- Čo sa stane, ak stĺpec v Trende zodpovedá dňu, pre ktorý nebol vyplnený žiadny záznam? → Stĺpec je vizuálne označený, ale klik zobrazí prázdny stav s výzvou na vyplnenie.
- Čo sa stane, ak používateľ naviguje na Vektor priamo cez deep link alebo záložku (nie cez Trend)? → Stránka zostáva funkčná; backstack naviguje späť na Trend alebo Home.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Home stránka MUSÍ zobrazovať aktuálny dátum bezprostredne za textom „Dnešný prehľad".
- **FR-002**: Home stránka MUSÍ zobraziť sekciu pozitívne/negatívne na pozícii, kde bol predtým denný ADHD index, s väčším fontom (pôvodná veľkosť ADHD indexu).
- **FR-003**: Home stránka MUSÍ zobraziť denný ADHD index na pozícii, kde bola predtým sekcia pozitívne/negatívne, s menším fontom (pôvodná veľkosť pozitívne/negatívne).
- **FR-004**: Home stránka MUSÍ obsahovať tlačidlo „Upraviť denný záznam" napravo od sekcie pozitívne/negatívne, ktoré naviguje priamo na stránku Denného trackera.
- **FR-005**: Stránka Trendu MUSÍ zobrazovať pri každom stĺpci grafu viditeľný popis dňa (dátum alebo skrátený názov dňa).
- **FR-006**: Každý stĺpec v grafe Trendu MUSÍ byť klikateľný a kliknutím otvoriť stránku vektora pre daný deň.
- **FR-007**: Navigačné menu NESMIE obsahovať položku „Vektor".
- **FR-008**: Stránka vektora MUSÍ zostať dostupná a funkčná (len prístup cez Trend, nie z menu).
- **FR-009**: Tlačidlo „Uložiť deň" na stránke Denného trackera MUSÍ byť umiestnené napravo od nadpisu „Denný tracker" a viditeľné bez scrollovania pri načítaní stránky.
- **FR-010**: Funkcionalita uloženia dňa MUSÍ zostať nezmenená – presun tlačidla nemení logiku uloženia.

### Key Entities

- **DenníZáznam (EventDay)**: Existujúca entita; nie je menená. Relevantná pre klikateľné dni v Trende.
- **VektorDňa**: Existujúca obrazovka/dáta vektora; dostupnosť sa nemení, mení sa len navigačná cesta.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Používateľ vidí správny dátum na Home stránke bez akejkoľvek interakcie – overiteľné okamžite po otvorení aplikácie.
- **SC-002**: Používateľ sa dostane na Denný tracker z Home stránky jedným kliknutím (skratkové tlačidlo) namiesto dvoch.
- **SC-003**: Používateľ identifikuje konkrétny deň v grafe Trendu bez ďalšieho kontextu – každý stĺpec má viditeľný popis dňa.
- **SC-004**: Používateľ sa dostane na detail vektora konkrétneho dňa kliknutím priamo na stĺpec Trendu – bez navigácie cez menu.
- **SC-005**: Tlačidlo „Uložiť deň" je viditeľné na stránke Denného trackera bez scrollovania na 100 % bežne používaných veľkostiach obrazoviek (testované na min. 3 veľkostiach).
- **SC-006**: Navigačné menu má o jednu položku menej (Vektor odstránená) – menu je prehľadnejšie.

---

## Assumptions

- Všetky zmeny sú čisto UI/navigačné – žiadna zmena domenovej logiky indexu, vah ani dátového modelu.
- Existujúce Composables sú modifikovateľné; nevyžaduje sa prepísanie celých obrazoviek.
- Navigácia z Trendu na Vektor je realizovateľná cez existujúci Navigation Compose (nie nová závislosť).
- Veľkosť fontu pre sekcie na Home stránke je definovaná v existujúcom theme/style systéme a dá sa jednoducho vymeniť.
- Stránka vektora akceptuje identifikátor dňa ako navigačný argument (alebo toto bude potrebné doimplementovať).
- Mobilná orientácia je portrait; landscape nie je v scope tejto zmeny.

---

## Constitution Check

- **Princip I (Architektúra)**: Všetky zmeny zostávajú na UI vrstve (Composables). Navigácia používa Navigation Compose. Žiadna zmena v Repository ani DAO.
- **Princip II (Doménová logika)**: Nedotknutá – žiadna zmena výpočtov.
- **Princip III (Dátový model)**: Nedotknutý – žiadna nová entita ani migrácia.
- **Princip IV (UX)**: Zmeny priamo znižujú trenie (menej kliknutí na tracker, viditeľné tlačidlo uloženia) – v súlade s princípom minimálnych kliknutí.
- **Princip VII (Stack)**: Používané iba povolené závislosti (Compose, Navigation Compose). Žiadna nová závislosť.
