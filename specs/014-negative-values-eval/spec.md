# Feature Specification: Scale Color Visualization

**Feature Branch**: `023-range-visualization-color-feedback`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "Doplniť vizualizáciu do range entít — viditeľné číslo + farba podľa hodnoty (záporné = červená, kladné = zelená, nula = biela). Opraviť testy pre negative range a ASRS kompatibilitu."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Farebná vizualizácia pre elementy so záporným rangeom (Priority: P1)

Keď používateľ nastavuje v tracker obrazovke element so záporným rozsahom (napr. sleep s hodnotami -2 až 2), chce okamžite vizuálne vnímať, či je hodnota pozitívna alebo negatívna — bez toho, aby musel čítať len číslo. Farba pozadia sa mení plynule: nula = biela, záporné hodnoty = odtiene červenej (čím zápornejšie, tým sýtejšia), kladné hodnoty = odtiene zelenej (čím vyššia, tým sýtejšia). Aktuálne číslo je vždy zobrazené v karte elementu.

**Why this priority**: Záporné hodnoty sú nová funkcionalita (feature 013) bez vizuálnej spätnej väzby — používateľ si musí mentálne prekladať číslo na dopad. Farebný feedback znižuje kognitívnu záťaž, čo je kľúčové pre ADHD profil.

**Independent Test**: Nastaviť sleep na -2 → karta je tmavočervená s číslom "-2". Nastaviť na 0 → biela s "0". Nastaviť na 2 → tmavozelená s "2". Každý krok je testovateľný vizuálne v izolácii.

**Acceptance Scenarios**:

1. **Given** element sleep s rozsahom -2..2, **When** používateľ nastaví slider na -2, **Then** pozadie karty je sýto červené a text zobrazuje "-2"
2. **Given** element sleep s rozsahom -2..2, **When** používateľ nastaví slider na -1, **Then** pozadie karty je jemne červené a text zobrazuje "-1"
3. **Given** element sleep s rozsahom -2..2, **When** používateľ nastaví slider na 0, **Then** pozadie karty je biele (neutrálne) a text zobrazuje "0"
4. **Given** element sleep s rozsahom -2..2, **When** používateľ nastaví slider na 1, **Then** pozadie karty je jemne zelené a text zobrazuje "1"
5. **Given** element sleep s rozsahom -2..2, **When** používateľ nastaví slider na 2, **Then** pozadie karty je sýto zelené a text zobrazuje "2"
6. **Given** element so záporným rozsahom, **When** slider nie je aktivovaný (binary = false), **Then** karta zostáva v predvolenom neutrálnom štýle (bez farby)

---

### User Story 2 — Farebná vizualizácia pre elementy s kladným rozsahom (Priority: P2)

Keď používateľ nastavuje element s iba kladným rozsahom (napr. 0..5 alebo 1..5), chce vidieť aktuálne číslo a farbu zodpovedajúcu sile hodnoty — čím vyššia hodnota, tým sýtejšia farba (zelená pre pozitívny dopad, červená pre negatívny dopad elementu).

**Why this priority**: Nadväzuje na US1 — ak záporné elementy majú vizuál, kladné musia mať konzistentné správanie. Bez toho by UI pôsobilo nejednotne.

**Independent Test**: Nastaviť physical_activity (1..5, pozitívny dopad) na 5 → sýto zelená + "5". Nastaviť stress_work (1..5, negatívny dopad) na 5 → sýto červená + "5". Nastaviť na 1 → bledá verzia príslušnej farby + "1".

**Acceptance Scenarios**:

1. **Given** element s kladným dopadom a kladným rozsahom, **When** používateľ nastaví najvyššiu hodnotu, **Then** karta je sýto zelená s číslom
2. **Given** element s kladným dopadom a kladným rozsahom, **When** používateľ nastaví najnižšiu hodnotu, **Then** karta je bledozelená (slabá sýtosť) s číslom
3. **Given** element s negatívnym dopadom a kladným rozsahom, **When** používateľ nastaví najvyššiu hodnotu, **Then** karta je sýto červená s číslom
4. **Given** element bez scale (binárny), **When** je aktivovaný, **Then** karta ostáva pri pôvodnom farebnom kódovaní (zelená/červená podľa dopadu) bez čísla

---

### User Story 3 — Testy pokrývajúce negative range a ASRS kompatibilitu (Priority: P3)

Vývojár chce mať istotu, že zavedenie záporných rozsahov nenarušilo výpočet ADHD indexu a kompatibilitu s ASRS rekalibrovaním — najmä krajné prípady ako "všetky elementy na minime" alebo "všetky na maxime".

**Why this priority**: Záporné hodnoty menia rozsah `value_effective` (môže zostať v 0–1 vďaka normalizácii), ale správanie pri extrémnych hodnotách a vplyv na ASRS korelačný praný musí byť overený testmi. Bez testov je toto čierna skrinka.

**Independent Test**: Spustiť unit testy — všetky nové testy pre krajné prípady musia prejsť. Dokumentácia ASRS kompatibility musí byť doplnená v kóde alebo spec.

**Acceptance Scenarios**:

1. **Given** všetky elementy sú na minimálnej zápornej hodnote, **When** sa vypočíta denný index, **Then** index je validné číslo v rozsahu 0–100
2. **Given** všetky elementy sú na maximálnej hodnote, **When** sa vypočíta denný index, **Then** index je 100
3. **Given** mix záporných a kladných hodnôt, **When** sa vypočítava index, **Then** výsledok zodpovedá vzorcu z constitution (Princíp II)
4. **Given** situácia, kde by ASRS rekalibracia mohla byť ovplyvnená záporným rozsahom, **Then** dokumentácia popisuje dopad a navrhuje riešenie

---

### Edge Cases

- Čo sa stane, keď sú záporné hodnoty pre elementy s **negatívnym dopadom** (stress)? `value_effective` = 0 pri maxime zápornej hodnoty — toto je žiaduce (maximálny stres = plná negatívna váha), ale treba overiť.
- Čo ak všetky elementy majú záporné hodnoty súčasne? Index môže klesnúť k 0 — validné správanie, ale treba dokumentovať.
- Elementy bez scale (binárne) — žiadna zmena vizuálu, číslo sa nezobrazuje.
- Element `overall_feeling` je vždy 1–5 (Constitution Princíp IV) — NESMIE byť ovplyvnený touto featurou.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Každý aktívny scale element v tracker obrazovke MUST zobrazovať aktuálnu nomedrickú hodnotu slidera viditeľne v karte elementu
- **FR-002**: Pre elementy so záporným rozsahom MUST byť farba pozadia karty dynamická: hodnota 0 = biela, záporné hodnoty = odtiene červenej (intenzita proporcionálna k vzdialenosti od nuly), kladné hodnoty = odtiene zelenej (intenzita proporcionálna k hodnote)
- **FR-003**: Pre elementy s iba kladným rozsahom MUST byť farba pozadia karty dynamická: nižšia hodnota = bledšia, vyššia hodnota = sýtejšia (zelená pre pozitívny dopad, červená pre negatívny dopad elementu)
- **FR-004**: Farebná vizualizácia MUST byť aktívna len keď je element zapnutý (binary = true a scale viditeľný)
- **FR-005**: Binárne elementy (bez scale) NESMÚ byť ovplyvnené novou farebnou logikou
- **FR-006**: Element `overall_feeling` MUST zostať nezmenený — skala 1–5, existujúce farebné správanie
- **FR-007**: Unit testy MUST pokrývať výpočet `value_effective` pre záporné, nulové a kladné hodnoty vo všetkých kombináciách dopadov
- **FR-008**: Unit testy MUST pokrývať krajné prípady: všetky elementy na minime, všetky na maxime, mix záporných a kladných
- **FR-009**: Dokumentácia MUST popisovať dopad záporných rozsahov na ASRS kompatibilitu a navrhovať riešenie pre prípady ohrozenia

### Key Entities

- **ScaleColorMapping**: Logika výpočtu farby pozadia z hodnoty slidera (vstup: hodnota, scaleMin, scaleMax, impact) — výstup: ARGB farba
- **ElementUiState**: Existujúci model (rozšírený v feature 013 o scaleMin/scaleMax) — zostáva nezmenený
- **TrackerScreen Composable**: Primárny vizuálny komponent pre zobraenie kariet elementov

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Používateľ vidí aktuálne číslo hodnoty slidera v karte elementu bez nutnosti ďalšej akcie (0 extra krokov)
- **SC-002**: Farebná zmena pozadia je vizuálne rozoznateľná pre každú diskrétnu hodnotu v rozsahu (min. 2 odlišné odtiene pre záporné a 2 pre kladné)
- **SC-003**: Všetky nové unit testy pre krajné prípady prechádzajú (100% pass rate)
- **SC-004**: Existujúce testy nie sú rozbité — celková test suite prechádza
- **SC-005**: Dokumentácia ASRS kompatibility je doplnená a obsahuje konkrétne príklady dopadu a odporúčané riešenie

## Assumptions

- Farebná logika sa týka len TrackerScreen — iné obrazovky (TrendScreen, VectorScreen) zostávajú nezmenené
- Intenzita farby je lineárna funkcia hodnoty (nie logaritmická) — jednoduchosť implementácie
- Číslo sa zobrazuje priamo v karte element, nie ako overlay na slideri
- Negatívny dopad elementu s zápornou hodnotou (napr. stress na -2) znamená `value_effective` = 0, čo je semanticky správne (minimálny stres) — toto správanie sa NESMIE meniť
- `overall_feeling` ostáva pri pôvodnom správaní (feature scope z constitution Princíp IV)
- Farebné odtiene sú dostatočne kontrastné pre používateľov s farbosleposťou — overenie je mimo scope tejto feature (post-MVP a11y audit)
