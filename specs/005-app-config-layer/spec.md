# Feature Specification: App Configuration Layer

**Feature Branch**: `005-app-config-layer`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "Externalizovať všetky hardcoded algoritmus-parametre z kódu do konfiguračného súboru. Zahŕňa: default váhy elementov, adaptačné parametre (alpha, clamp rozsah, korelačný prah, minimum zápisov), ASRS prahy, klasifikáciu elementov (positiveKeys/negativeKeys), notifikačné prahy. AppConfig načítaná pri štarte aplikácie a injektovaná do výpočtovej logiky. Cieľ: zmena parametrov algoritmu bez rekompilácie."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Zmena algoritmických parametrov bez rekompilácie (Priority: P1)

Vývojár alebo správca chce otestovať iné hodnoty váh elementov alebo adaptačné parametre (napr. zvýšiť alfa alebo zmeniť clamp rozsah). Edituje konfiguračný súbor dodávaný spolu s aplikáciou, reštartuje aplikáciu a nové hodnoty sa okamžite prejavia vo výpočtoch — bez nutnosti meniť kód, kompilovať alebo znova nasadiť.

**Why this priority**: Algoritmus ADHD indexu má viacero parametrov (9 váh, adaptačné koeficienty, ASRS prahy, notifikačné limity) ktoré sú momentálne v kóde. Každá zmena vyžaduje rekompiláciu. Externalizácia umožní rýchle iterácie nad algoritmom a A/B testovanie bez release cyklu.

**Independent Test**: Zmeniť váhu elementu `sleep` v konfiguračnom súbore, reštartovať aplikáciu, zadať rovnaké denné hodnoty ako pred zmenou a overiť, že vypočítaný ADHD index zodpovedá novej váhe.

**Acceptance Scenarios**:

1. **Given** konfiguračný súbor obsahuje váhu `sleep = 20`, **When** aplikácia sa reštartuje a používateľ zadá plný sleep log, **Then** výpočet denného indexu použije váhu 20 namiesto pôvodnej 15.
2. **Given** konfiguračný súbor obsahuje upravený korelačný prah `0.15`, **When** algoritmus adaptácie váh beží, **Then** váhy sa aktualizujú len keď korelácia prekročí 0.15, nie 0.1.
3. **Given** konfiguračný súbor obsahuje zmenenú klasifikáciu (napr. `caffeine` presunutý do pozitívnych), **When** sa počítajú sub-indexy, **Then** `caffeine` prispeje do pozitívneho sub-indexu.
4. **Given** konfiguračný súbor obsahuje iné notifikačné prahy, **When** notifikačná logika vyhodnocuje podmienky, **Then** použije hodnoty z konfigurácie.

---

### User Story 2 - Odolnosť voči neplatnej konfigurácii (Priority: P2)

Aplikácia musí fungovať spoľahlivo aj keď konfiguračný súbor chýba, je poškodený alebo obsahuje čiastočné dáta. V takomto prípade sa automaticky použijú záložné hodnoty totožné s aktuálnymi hardcoded hodnotami — bez pádu aplikácie a bez chybovej hlášky pre používateľa.

**Why this priority**: Vývojári môžu omylom dodať neplatný konfiguračný súbor. Záložné správanie je kľúčové pre spoľahlivosť — aplikácia sa nesmie zrútiť kvôli chybe v konfigurácii.

**Independent Test**: Odstrániť konfiguračný súbor alebo vložiť do neho nevalidný obsah, spustiť aplikáciu a overiť, že beží bez pádu a výpočty zodpovedajú pôvodným hardcoded hodnotám.

**Acceptance Scenarios**:

1. **Given** konfiguračný súbor chýba, **When** aplikácia štartuje, **Then** použije zabudované predvolené hodnoty a spustí sa bez chyby.
2. **Given** konfiguračný súbor obsahuje neplatný formát, **When** aplikácia štartuje, **Then** použije zabudované predvolené hodnoty; pre používateľa nie je viditeľná žiadna chyba.
3. **Given** konfiguračný súbor obsahuje len časť parametrov (napr. chýbajú ASRS prahy), **When** aplikácia štartuje, **Then** použije konfiguráciu pre prítomné parametre a predvolené hodnoty pre chýbajúce.
4. **Given** konfiguračný súbor obsahuje hodnoty mimo povoleného rozsahu (napr. záporná váha), **When** aplikácia načíta konfiguráciu, **Then** nevznikne pád; neplatná hodnota je nahradená predvolenou hodnotou.

---

### User Story 3 - Auditovateľnosť aktívnej konfigurácie (Priority: P3)

Vývojár vie v čase ladenia overiť, aká konfigurácia je aktuálne aktívna — či sa použili hodnoty z konfiguračného súboru alebo predvolené hodnoty. Táto informácia je dostupná bez nutnosti čítať zdrojový kód.

**Why this priority**: Bez auditovateľnosti je ťažké diagnostikovať prečo sa algoritmus správa inak ako očakávané — môže ísť o chybu v konfigurácii alebo v logike. Audit trail skracuje čas ladenia.

**Independent Test**: Spustiť aplikáciu s upraveným konfiguračným súborom a overiť, že systém zaznamená ktoré parametre boli načítané z konfigurácie a ktoré pochádzajú z predvolených hodnôt.

**Acceptance Scenarios**:

1. **Given** aplikácia sa spustí s platným konfiguračným súborom, **When** vývojár skontroluje diagnostický výstup, **Then** vidí ktoré parametre boli načítané z konfigurácie.
2. **Given** aplikácia sa spustí s chýbajúcim alebo neplatným konfiguračným súborom, **When** vývojár skontroluje diagnostický výstup, **Then** vidí, že sa použili predvolené hodnoty a dôvod (chýbajúci súbor / neplatný formát).
3. **Given** konfigurácia sa zmiešava (niektoré hodnoty z konfigurácie, iné predvolené), **When** vývojár skontroluje diagnostický výstup, **Then** je zrejmé ktoré parametre pochádzajú z ktorého zdroja.

---

### Edge Cases

- Čo ak konfiguračný súbor obsahuje neznáme kľúče (budúce parametre)? Neznáme kľúče sú ignorované bez chyby — spätná kompatibilita pri downgrade.
- Čo ak váhy elementov v konfigurácii nesčítajú na 100? Aplikácia ich normalizuje rovnako ako pri adaptácii váh, alebo použije predvolené váhy.
- Čo ak sú positiveKeys a negativeKeys v konfigurácii nekompletné (chýbajú niektoré elementy)? Chýbajúce elementy dostanú predvolenú klasifikáciu.
- Čo ak konfigurácia zmení klasifikáciu elementu (positive ↔ negative)? Zmena sa prejaví v sub-indexoch od nasledujúceho výpočtu — historické dáta sa nepreračítavajú.
- Čo ak je hodnota `alpha` mimo rozumného rozsahu (napr. > 1)? Hodnota je odmietnutá a použije sa predvolená; diagnostický výstup zaznamená odmietnutie.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Systém MUST načítať predvolené váhy všetkých 9 elementov z konfiguračného zdroja pri štarte aplikácie.
- **FR-002**: Systém MUST načítať všetky adaptačné parametre z konfiguračného zdroja: koeficient učenia, clamp rozsah (min/max násobok predvolenej váhy), korelačný prah, minimálny počet zápisov pre adaptáciu.
- **FR-003**: Systém MUST načítať ASRS prahy z konfiguračného zdroja: bodová odchýlka triggera, počet po sebe idúcich meraní, re-kalibračný koeficient.
- **FR-004**: Systém MUST načítať klasifikáciu elementov (ktoré sú pozitívne, ktoré negatívne) z konfiguračného zdroja.
- **FR-005**: Systém MUST načítať notifikačné prahy z konfiguračného zdroja: maximum notifikácií za deň, tichý interval, prahy pre každý typ notifikácie.
- **FR-006**: Systém MUST použiť zabudované predvolené hodnoty pre akýkoľvek parameter ktorý v konfiguračnom zdroji chýba alebo je neplatný.
- **FR-007**: Neplatný alebo chýbajúci konfiguračný zdroj NESMIE spôsobiť pád aplikácie ani zobraziť technickú chybovú hlášku používateľovi.
- **FR-008**: Zmena parametrov v konfiguračnom zdroji MUST nadobudnúť účinnosť po nasledujúcom reštarte aplikácie — bez reinštalovania.
- **FR-009**: Diagnostický výstup MUST zaznamenať zdroj každej načítanej hodnoty (konfigurácia vs. predvolená) dostupný pre vývojára počas ladenia.
- **FR-010**: Všetky výpočtové komponenty MUST prijímať parametre výlučne cez konfiguračnú vrstvu — žiadne hardcoded hodnoty nesmú zostať v doménovej logike.

### Key Entities

- **AppConfig**: Hlavný kontajner všetkých konfigurovateľných parametrov; má vždy platnú hodnotu (nikdy null) vďaka záložným hodnotám.
- **ElementWeightConfig**: Definícia váhy jedného elementu; obsahuje kľúč elementu a číselnú hodnotu váhy.
- **AdaptationConfig**: Parametre adaptácie váh — koeficient učenia, clamp hranice, korelačný prah, minimálny počet zápisov.
- **AsrsConfig**: Parametre ASRS re-kalibrácie — odchýlkový prah, počet meraní, re-kalibračný koeficient.
- **NotificationConfig**: Notifikačné prahy — maximálna frekvencia, tichý interval, podmienky pre každý typ upozornenia.
- **ElementClassification**: Rozdelenie elementov na pozitívne (maximalizovať) a negatívne (minimalizovať).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zmena akéhokoľvek algoritmu-parametra nadobudne účinnosť do jedného reštartu aplikácie — bez rekompilácie alebo reinštalovania.
- **SC-002**: Aplikácia sa spustí rovnako rýchlo po zavedení konfiguračnej vrstvy ako pred ňou — žiadne merateľné spomalenie štartu.
- **SC-003**: 100 % aktuálne hardcoded algoritmu-parametrov je pokrytých konfiguračnou vrstvou — žiadna hardcoded algoritmická hodnota nezostane v doménovej logike.
- **SC-004**: Neplatná alebo chýbajúca konfigurácia neohrozí funkčnosť — aplikácia spustí sa a funguje identicky ako s predvolenou konfiguráciou do 1 sekundy od štartu.
- **SC-005**: Vývojár vie do 30 sekúnd od štartu aplikácie potvrdiť, aká konfigurácia je aktívna — bez čítania zdrojového kódu.

## Assumptions

- Konfiguračný súbor je súčasťou aplikačného balíka (dodávaný spolu s apkou) — vzdialené načítanie konfigurácie je mimo rozsahu MVP.
- V MVP neexistuje žiadne používateľské rozhranie pre editáciu konfigurácie — zmeny sa robia manuálnou úpravou súboru pred buildovaním.
- Existujúce hardcoded hodnoty v `DefaultWeights.kt` a `IndexCalculator.kt` sa stanú záložnými hodnotami (fallback) — správanie aplikácie sa nemení, len parameterizácia.
- Konfigurácia sa číta pri každom štarte aplikácie — zmeny vyžadujú reštart, hot-reload nie je podporovaný v MVP.
- Konfigurácia je globálna pre celú aplikáciu — per-používateľské konfiguračné profily sú mimo rozsahu.
- Žiadna nová externá závislosť pre parsovanie konfigurácie — riešenie musí byť realizovateľné s existujúcou knižnicovou sadou.
- Validácia konfigurácie prebieha pri načítaní — neplatné hodnoty sa nelogujú do perzistentného úložiska, len do diagnostického výstupu.

## Constitution Check

- **§ I (Architektúra)**: Konfiguračná vrstva patrí do doménovej vrstvy; UI a ViewModel ju nevolajú priamo. Injektovaná cez Repository konštruktor.
- **§ II (Domenová logika)**: Žiadna algoritmická zmena — len externalizácia parametrov. Nové parsovanie konfigurácie MUSÍ byť kryté unit testami.
- **§ VI (Testovanie)**: Unit testy pre načítanie konfigurácie, záložné hodnoty a validáciu rozsahov sú povinné.
- **§ VII (Tech stack)**: Žiadne nové závislosti — konfigurácia musí byť parsovateľná existujúcou knižnicovou sadou.
