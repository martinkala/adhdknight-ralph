# Feature Specification: Unified Entity Input

**Feature Branch**: `009-edit-system-updates`

**Created**: 2026-06-29

**Status**: Draft

**Short name**: `unified-entity-input`

## User Scenarios & Testing

### User Story 1 — Jednotný on/off switch pre každú entitu (Priority: P1)

Ako používateľ denného trackera chcem, aby každá entita mala jasný on/off switch, aby som mohol explicitne rozhodnúť, ktoré aktivity sú pre daný deň relevantné — bez toho, aby som bol nútený hodnotiť veci, ktoré som vôbec nevykonával.

**Why this priority**: Toto je jadro nekonzistencie — entity bez switcha nemožno vylúčiť, čo spôsobuje skreslené dáta a zavádzajúce grafy. Oprava prináša primárnu používateľskú hodnotu.

**Independent Test**: Otvoriť tracker, nájsť akúkoľvek entitu, ktorá dnes zobrazuje len slider (napr. "Pracovný stres"), prepnúť ju na OFF, uložiť deň, otvoriť graf — entita nesmie byť zobrazená.

**Acceptance Scenarios**:

1. **Given** otvorím denný tracker, **When** zobrazím akúkoľvek entitu okrem "Celkový pocit za deň", **Then** vidím jasne viditeľný on/off switch pre túto entitu.
2. **Given** prepnem switch entity na ON, **When** prezerám formulár trackera, **Then** pod switchom sa zobrazí slider 1–5 na zadanie hodnoty.
3. **Given** prepnem switch entity na OFF, **When** prezerám formulár trackera, **Then** slider nie je zobrazený a entita bude uložená bez hodnoty.
4. **Given** uložím deň s entitou X na OFF, **When** znova otvorím tracker pre ten istý dátum, **Then** entita X zostáva na OFF a slider nemá hodnotu.
5. **Given** zobrazím entitu "Celkový pocit za deň", **When** interagujem s trackerom, **Then** žiadny on/off switch sa nezobrazí — vždy je prítomný iba povinný slider 1–5.

---

### User Story 2 — Graf zobrazuje len aktívne entity (Priority: P2)

Ako používateľ prezerajúci denný prehľad chcem, aby bar chart zobrazoval iba entity, s ktorými som v daný deň aktívne interagoval, aby vizualizácia bola zmysluplná a neprehľadná prázdnymi pruhmi.

**Why this priority**: Priamo nadväzuje na US1 — ak entity možno vypnúť, graf musí tento stav rešpektovať.

**Independent Test**: Vypnúť 3 entity, uložiť, otvoriť Home/Detail obrazovku — tých 3 entít nesmie byť prítomných v ani jednej polovici bar chartu.

**Acceptance Scenarios**:

1. **Given** uložím deň s entitou X na OFF, **When** zobrazím Home bar chart, **Then** entita X sa v grafe nezobrazí.
2. **Given** uložím deň s entitou Y na ON (slider = 4), **When** zobrazím Home bar chart, **Then** entita Y sa zobrazí s pruhom úmerným hodnote 4.
3. **Given** všetky entity v jednej impaktovej skupne (negatívne alebo pozitívne) sú OFF, **When** zobrazím príslušnú polovicu grafu, **Then** zobrazí sa prázdny stav bez pádu aplikácie.

---

### User Story 3 — Vizuálne zvýraznenie vyplnených entít v trackeri (Priority: P2)

Ako používateľ denného trackera chcem, aby entity, ktoré som v daný deň už zapol a vyplnil, mali viditeľne tmavšie farebné pozadie, aby som okamžite vedel, čo som už zadal a čo ešte nie — bez toho, aby som musel prechádzať každú entitu znova.

**Why this priority**: Znižuje kognitívnu záťaž pri vypĺňaní trackera — používateľ na prvý pohľad vidí stav „hotovo / ešte nie". Doplnok k US1, keďže závisí na switch stave entity.

**Independent Test**: Otvoriť tracker → prepnúť entity X na ON → okamžite (bez uloženia) pozorovať, že karta entity X má tmavšie pozadie ako karty entít na OFF. Prepnúť späť na OFF → pozadie sa vráti na pôvodnú svetlú farbu.

**Acceptance Scenarios**:

1. **Given** otvorím tracker a entita je na OFF, **When** zobrazím kartu tejto entity, **Then** karta má svetlé pastelové pozadie (pôvodná farba podľa impaktu).
2. **Given** prepnem switch entity na ON, **When** sa karta obnoví, **Then** farba pozadia karty sa stmaví (intenzívnejšia verzia rovnakej farby podľa impaktu — zelená pre pozitívne, červená pre negatívne).
3. **Given** entita je ON a mám otvorený tracker, **When** prepnem switch späť na OFF, **Then** farba pozadia sa okamžite vráti na svetlú pastelovu verziu.
4. **Given** načítam dátum, pre ktorý boli entity predtým uložené ako ON, **When** sa tracker zobrazí, **Then** entity s uloženým stavom ON majú tmavšie pozadie ihneď pri otvorení (bez nutnosti prepínať).
5. **Given** `overall_feeling` je vždy povinný, **When** zobrazím jeho kartu, **Then** má vždy tmavšie pozadie (je vždy "vyplnený").

---

### Edge Cases

- Čo ak sú všetky negatívne alebo všetky pozitívne entity vypnuté? → Príslušná polovica grafu zobrazí prázdny stav (žiadny pád, len prázdna plocha).
- Čo ak používateľ rýchlo prepína switch ON/OFF? → Farba pozadia sa okamžite aktualizuje pri každej zmene stavu (reaktívne, bez oneskorenia).
- Ako vyzerá `overall_feeling`? → Vždy má tmavšie pozadie, keďže je vždy "zapnutý" (povinný).
- Ako sa správa index pre entity na OFF? → OFF entity prispievajú efektívnou hodnotou 0 (rovnaké správanie ako binary=0 dnes), formula indexu sa nemení.
- Čo ak je dátum uložený pred touto zmenou (scale-only entita vždy mala hodnotu)? → Entita s uloženou hodnotou scale sa načíta ako ON; entita bez uloženej hodnoty sa zobrazí ako OFF.
- Čo ak používateľ prepne entitu z ON na OFF pre rovnaký dátum a znova uloží? → Nový save prepisuje predchádzajúci stav; entita je zaznamenaná ako OFF (binary=0, scale=null).

## Requirements

### Functional Requirements

- **FR-001**: Každá entita trackera OKREM `overall_feeling` MUSÍ zobrazovať on/off switch.
- **FR-002**: Keď je switch entity ON, MUSÍ sa zobraziť slider 1–5 a jeho hodnota MUSÍ byť zaznamenaná pri uložení.
- **FR-003**: Keď je switch entity OFF, slider MUSÍ byť skrytý a entita MUSÍ byť uložená s efektívnou hodnotou nula.
- **FR-004**: Bar chart na Home aj Detail obrazovke MUSÍ zobrazovať len entity, ktoré sú na ON (majú aktívnu uloženú hodnotu).
- **FR-005**: `overall_feeling` MUSÍ zostať povinným, vždy viditeľným sliderom 1–5 bez on/off switcha.
- **FR-006**: Pri načítaní predtým uloženého dátumu MUSÍ byť stav switcha každej entity obnovený: ON ak bola uložená scale hodnota, OFF ak nebola uložená žiadna hodnota pre danú entitu.
- **FR-007**: Výpočet denného indexu MUSÍ naďalej považovať entity na OFF za prispievajúce efektívnou hodnotou nula, v súlade s existujúcou formulou indexu.
- **FR-008**: Farebné pozadie karty entity v trackeri MUSÍ vizuálne rozlišovať stav ON (tmavšia verzia impaktovej farby) od stavu OFF (svetlá pastelová verzia impaktovej farby). Zmena farby MUSÍ byť okamžitá pri prepínaní switcha — bez nutnosti uloženia alebo obnovenia obrazovky.

### Design Options Evaluated

Tri prístupy k zjednoteniu vstupu boli vyhodnotené podľa používateľského komfortu (1 = nízky, 3 = vysoký):

| Možnosť | Popis | Rating |
|---------|-------|--------|
| **A — Switch + Slider (zvolená)** | Každá entita okrem overall_feeling dostane on/off switch; slider sa zobrazí len keď je ON. OFF = vylúčená z grafu. | **3/3** — jasná affordancia, plná kontrola, konzistentné s existujúcimi binárnymi entitami |
| **B — Povinný slider + toggle pre graf** | Scale entity si ponechávajú povinný slider (vždy zbierajú hodnotu), ale pribudne checkbox "vylúčiť z grafu". | **2/3** — zabraňuje chýbajúcim dátam, ale núti hodnotiť veci, ktoré používateľ nevykonal; dva odlišné mechanizmy vypnutia pôsobia nekonzistentne |
| **C — Univerzálny slider 0–5 (bez switcha)** | Všetky entity zobrazujú slider 0–5, kde 0 = "nevykonané/nevzťahuje sa". Switche úplne odstraňuje. | **1/3** — nejednoznačnosť (0 = "neurobil som to" vs "urobil som veľmi zle"), žiadny vizuálny stav "off", vyššia kognitívna záťaž |

### Key Entities

- **Stav vstupu entity**: Predstavuje stav formulára pre jednu entitu v danom dni. Dnes rozlišuje "binárne" entity (switch + voliteľný slider) a "scale" entity (povinný slider bez switcha). Po zmene všetky entity okrem `overall_feeling` zdieľajú jednotný stav: switch (on/off) + podmienený slider.
- **Uložená hodnota entity**: Predstavuje perzistovaný záznam dňa pre jednu entitu. Existujúce polia `valueBinary` (0/1) a `valueScale` (null alebo 1–5) sú dostačujúce na vyjadrenie stavu OFF — žiadna zmena schémy nie je potrebná.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100 % entít trackera (okrem `overall_feeling`) zobrazuje on/off switch v dennom trackerovi.
- **SC-002**: 0 entít so switchom=OFF sa zobrazí v Home alebo Detail bar charte po uložení.
- **SC-003**: `overall_feeling` nemá viditeľný on/off switch — vždy zobrazuje len povinný slider 1–5.
- **SC-004**: Načítanie predtým uloženého dátumu obnoví stav switcha a slidera každej entity so 100 % presnosťou.
- **SC-005**: Bar chart sa nevykreslí s pádom, keď sú všetky entity v jednej impaktovej skupine (pozitívne alebo negatívne) na OFF.
- **SC-006**: Farba pozadia karty entity sa zmení okamžite (bez oneskorenia) pri prepnutí switcha — ON zobrazí tmavšiu variantu impaktovej farby, OFF zobrazí svetlú pastelovu variantu.

## Assumptions

- `overall_feeling` je vylúčený zo zmeny on/off switcha; constitution §IV nariaďuje, že zostáva povinný a výhradne scale.
- Spätná kompatibilita: Dni uložené pred touto funkciou (kde scale entity vždy mali hodnotu) sa načítajú so zobrazením ON a obnovenou uloženou hodnotou slidera.
- Žiadna zmena databázovej schémy nie je potrebná — existujúce polia `valueBinary` (0=OFF, 1=ON) a `valueScale` (null keď OFF) už predstavujú požadovaný stav.
- Pole `hasScale` v konfigurácii entít zostáva pre prípadné budúce použitie, ale po tejto zmene nevedie k odlišnej logike vykresľovania pre entity okrem `overall_feeling`.
- Formula indexu (constitution §II) sa nemení — entity na OFF prispievajú efektívnou hodnotou nula, rovnako ako binary=0 dnes.
