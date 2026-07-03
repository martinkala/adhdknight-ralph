# Feature Specification: Range Scale, Day Deletion, Future Date Guard

**Feature Branch**: `013-range-scale-delete-future`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Cieľ 1: Upraviť range (škálu) hodnotení aby mohli byť aj záporné hodnoty — sleep môže mať hodnoty -2,-1,0,1,2, podobne ostatné elementy s scale môžu mať zápornú definíciu škály. Cieľ 2: Pridať možnosť zmazať deň v detaile dna. Cieľ 3: Deň v budúcnosti nebude možné pridať — limit na strane calendar pickera, aplikácia vyhodí chybu, implementovať aj na strane servera, pridať testy."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Záporné hodnoty škály (Priority: P1)

Používateľ hodnotí spánok hodnotou -2 (veľmi zlý) až +2 (veľmi dobrý) namiesto súčasnej škály 1–5. Všetky elementy s nastavenou škálou môžu mať rozsah definovaný ako dvojicu `(min, max)` kde min môže byť záporný. Aplikácia zobrazí slider s týmto rozsahom a správne premietne hodnotu do výpočtu indexu.

**Why this priority**: Záporné hodnoty umožňujú presnejšie zachytiť zlé dni — dnes škála 1 (minimum) nezachytí rozdiel medzi "normálny deň" a "extrémne zlý deň". Toto je jadrová zmena dátového modelu.

**Independent Test**: Nastaviť spánok na škálu -2 až +2, zadať hodnotu -1, overiť že sa uloží a správne zobrazí; overiť že výpočet ADHD indexu zostane v rozsahu 0–100.

**Acceptance Scenarios**:

1. **Given** element má definovanú škálu s min=-2 a max=2, **When** používateľ pohybuje sliderom, **Then** slider zobrazuje hodnoty -2, -1, 0, 1, 2 a uloží vybranú hodnotu
2. **Given** používateľ zadal hodnotu -1 pre spánok, **When** sa zobrazí denný detail, **Then** hodnota -1 je viditeľná a slider je nastavený na správnu pozíciu
3. **Given** element má záporné hodnoty, **When** sa počíta ADHD index, **Then** index zostáva v rozsahu 0–100 (záporné hodnoty prispievajú negatívne)
4. **Given** existujúce záznamy so škálou 1–5, **When** sa schema zmení na -2 až +2, **Then** existujúce dáta zostanú konzistentné (migrácia alebo zachovanie starých hodnôt)

---

### User Story 2 — Zmazanie dna (Priority: P2)

Používateľ môže v detailnom zobrazení konkrétneho dňa zmazať celý záznam dňa. Po potvrdení sa všetky hodnoty elementov pre daný deň odstránia a deň sa vráti do stavu "bez záznamu".

**Why this priority**: Používateľ môže omylom vytvoriť záznam pre nesprávny deň alebo chce vymazať testovací/neúplný záznam. Bez tejto funkcie niet spôsobu opravy.

**Independent Test**: Otvoriť existujúci vyplnený deň, kliknúť "Zmazať deň", potvrdiť — deň sa zobrazuje ako prázdny v kalendári.

**Acceptance Scenarios**:

1. **Given** deň má aspoň jeden vyplnený element, **When** používateľ stlačí "Zmazať deň" a potvrdí, **Then** všetky hodnoty dňa sa odstránia a deň je prázdny
2. **Given** používateľ stlačí "Zmazať deň", **When** sa zobrazí potvrdzovacie dialógové okno, **Then** zmazanie nastane len po explicitnom potvrdení (nie náhodným dotykom)
3. **Given** deň bol zmazaný, **When** používateľ otvorí kalendár, **Then** deň nie je označený ako vyplnený
4. **Given** deň bol zmazaný, **When** sa počíta ADHD index za dané obdobie, **Then** zmazaný deň sa nezapočítava

---

### User Story 3 — Zákaz budúcich dátumov (Priority: P3)

Používateľ nemôže vytvoriť ani uložiť záznam pre dátum v budúcnosti. Calendar picker obmedzí výber na dnešok a minulosť. Ak by aplikácia dostala budúci dátum inak (napr. cez API), vyhodí chybu.

**Why this priority**: Záznamy budúcich dní nemajú zmysel — ADHD tracking je retrospektívny. Ide o integritu dát. Server musí tiež validovať, pretože API je verejné.

**Independent Test**: Pokus o výber zajtrajšieho dátumu v calendar pickeri → nie je možný; pokus cez API s budúcim dátumom → 422 chyba.

**Acceptance Scenarios**:

1. **Given** calendar picker je otvorený, **When** používateľ sa pokúsi vybrať dátum v budúcnosti, **Then** budúce dátumy sú zašednuté/nedostupné a výber nie je možný
2. **Given** aplikácia prijme budúci dátum akoukoľvek cestou, **When** sa pokúsi uložiť záznam, **Then** zobrazí chybovú hlášku "Nemožno zadať budúci dátum" a neuloží
3. **Given** API požiadavka obsahuje dátum v budúcnosti, **When** server spracováva požiadavku, **Then** vráti chybu 422 s popisom "Date cannot be in the future"
4. **Given** automatizovaný test posiela budúci dátum na API, **When** test beží, **Then** test overí že server vrátil 422

---

### Edge Cases

- Čo ak je čas zariadenia nastavený nesprávne (budúci čas)? — Aplikácia sa spolieha na systémový čas; server porovnáva s UTC časom servera.
- Čo ak sa používateľ pokúsi zmazať deň, ktorý ešte nebol vyplnený? — Akcia zmaže prázdny záznam, výsledok je rovnaký (prázdny deň).
- Čo ak škála má min = max? — Validácia pri konfigurácii elementu zabrání min ≥ max.
- Migrácia existujúcich dát pri zmene škály: existujúce hodnoty (napr. 3 na škále 1–5) sa pri zmene schémy nemapujú automaticky — hodnoty zostanú nezmenené, interpretácia sa zmení. Dokumentovať ako breaking change.
- Záporná hodnota + negatívny impact: element so záporným impactom a zápornou hodnotou — efektívna hodnota bude dvojito záporná (zlepšenie stavu) — správanie musí byť explicitne definované v algoritme.

---

## Requirements *(mandatory)*

### Functional Requirements

**Záporné škály (US1)**

- **FR-001**: Každý element s nastavenou škálou MUSÍ mať konfigurovateľný rozsah `(scale_min, scale_max)` kde `scale_min` môže byť záporné celé číslo a `scale_max` kladné celé číslo, pričom `scale_min < scale_max`.
- **FR-002**: Slider v dennom formulári MUSÍ zobrazovať hodnoty podľa `(scale_min, scale_max)` definovaných pre daný element, nie pevné 1–5.
- **FR-003**: Výpočet ADHD indexu MUSÍ normalizovať záporné hodnoty na rozsah 0–1 (napr. hodnota `v` na škále `[min, max]` → `(v - min) / (max - min)`), čím výsledný index zostane 0–100.
- **FR-004**: Dátový model MUSÍ uložiť skutočnú hodnotu škály (napr. -1) nie normalizovanú, aby bolo možné ju zobraziť v UI.

**Zmazanie dňa (US2)**

- **FR-005**: Detail dňa MUSÍ obsahovať akciu "Zmazať deň" dostupnú používateľovi.
- **FR-006**: Pred zmazaním MUSÍ byť zobrazené potvrdzovacie dialógové okno s možnosťou zrušenia.
- **FR-007**: Po potvrdení zmazania MUSÍ byť odstránené všetky hodnoty elementov pre daný deň z lokálnej databázy.
- **FR-008**: Po zmazaní MUSÍ byť používateľ presunutý späť na predchádzajúcu obrazovku (kalendár/zoznam).

**Zákaz budúcich dátumov (US3)**

- **FR-009**: Calendar picker MUSÍ mať nastavenú hornú hranicu na dnešný dátum — budúce dátumy NESMÚ byť vybrateľné.
- **FR-010**: Ak aplikácia prijme budúci dátum akoukoľvek cestou, MUSÍ zobraziť používateľsky zrozumiteľnú chybovú hlášku a odmietnuť uloženie.
- **FR-011**: Server MUSÍ validovať dátum v každej požiadavke na vytvorenie/aktualizáciu záznamu a vrátiť chybu 422 pre budúce dátumy.
- **FR-012**: Server MUSÍ mať automatizované testy pokrývajúce: (a) platný dnešný dátum → úspech, (b) budúci dátum → 422, (c) dátum z minulosti → úspech.

### Key Entities

- **ElementConfig**: Definícia elementu — rozšírená o `scale_min: Int` a `scale_max: Int` (predvolene -2 a +2 pre elementy so škálou, alebo zachovanie 1–5 pre existujúce).
- **ElementValue**: Záznam hodnoty elementu pre deň — `value_scale` uchováva skutočnú hodnotu (môže byť záporná).
- **TrackingDay**: Denný záznam — pri zmazaní sa odstránia všetky `ElementValue` záznamy pre daný deň.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Používateľ zadá hodnotu -2 pre spánok a hodnota je správne zobrazená pri opätovnom otvorení dňa — 100% presnosť uloženia.
- **SC-002**: ADHD index zostane v rozsahu 0–100 aj pri kombináciách záporných a kladných hodnôt — overiteľné testom pre všetky krajné hodnoty.
- **SC-003**: Používateľ zmaže deň v menej ako 3 krokoch (detail → zmazať → potvrdiť).
- **SC-004**: 100% požiadaviek na server s budúcim dátumom je odmietnutých (0 výnimiek).
- **SC-005**: Automatizované testy pokrývajú všetky tri scenáre future-date validácie na serveri.

---

## Assumptions

- Škála pre spánok a ostatné elementy sa zmení na -2 až +2; existujúce záznamy so starými hodnotami (1–5) zostanú v databáze nezmenené — mapovanie je zodpovednosťou používateľa pri migrácii.
- "Deň v budúcnosti" je definovaný voči UTC dátumu servera; na mobile voči lokálnemu systémovému dátumu zariadenia.
- Zmazanie dňa sa vzťahuje len na lokálnu databázu (Android); ak bol deň synchronizovaný na server, server záznam zostáva (sync mazania je mimo scope tejto funkcie).
- Zmena normalizácie škály (FR-003) sa týka len nových výpočtov; historické indexy uložené v DB sa neprepočítavajú automaticky.
- Testy servera (FR-012) sú pytest/httpx testy pridané do existujúcej testovacej suity v `server/tests/`.
