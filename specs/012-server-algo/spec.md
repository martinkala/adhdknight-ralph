# Feature Specification: Backend Weight Vector Server

**Feature Branch**: `012-server-algo`

**Created**: 2026-06-30

**Status**: Draft

## Constitution Check

Táto feature čiastočne zasahuje do oblasti "Serverova logika vah" ktorá je v constitution označená ako Post-MVP.
Rozsah tejto špecifikácie je však primárne **testovací a vývojový nástroj** — server slúži na regresné testovanie algoritmu bez nutnosti spúšťať Android aplikáciu.
Centralizovaný výpočet pre produkčných používateľov (nahradenie mobilného výpočtu serverom) ostáva Post-MVP a nie je súčasťou tejto feature.
Ciele 8, 9, 10 (migrácia, sync, autentifikácia) sú prípravné kroky pre budúci produkčný server — implementujú sa ako návrh/špecifikácia, nie produkčný kód.

---

## User Scenarios & Testing

### User Story 1 — Regresné testovanie algoritmu (Priority: P1)

Vývojár chce overiť, že serverový výpočet ADHD vektora dáva identické výsledky ako Android aplikácia — bez nutnosti inštalovať emulátor alebo fyzický telefón. Posiela sadu testovacích dát (tracking záznamy za 1, 3, 5, 15 alebo 30 dní) a dostáva spočítaný index s detailmi per-element.

**Why this priority**: Primárny dôvod existencie servera. Ak výpočet nie je identický s appkou, všetko ostatné je zbytočné.

**Independent Test**: Spustiť server lokálne, poslať JSON fixture pre 5 dní, porovnať výstup s hodnotami vypočítanými ručne podľa konštitúcie (vzorec `Index_d = 100 × Σ(w_i × e_i) / Σ(w_i)`).

**Acceptance Scenarios**:

1. **Given** testovací fixture pre 1 deň s hodnotami `sleep=1, physical_activity=0, overall_feeling=4`, **When** vývojár pošle požiadavku na výpočet, **Then** server vráti index zodpovedajúci vzorcu konštitúcie s presnosťou na 2 desatinné miesta.
2. **Given** fixture pre 30 dní vrátane dní s chýbajúcimi hodnotami, **When** vývojár pošle požiadavku, **Then** server vráti denné indexy pre každý deň a označí dni bez dát.
3. **Given** element s definovanými subpoložkami (napr. `sleep` má `sleep_quality` a `sleep_duration`), **When** vývojár pošle dáta so subpoložkami, **Then** server aplikuje dohodnutý algoritmus váženia a výsledok je konzistentný pre 1 aj 3 aj 5 subpoložky rovnakého elementu.
4. **Given** prázdny vstup (nová aplikácia, žiadne dáta), **When** vývojár pošle požiadavku, **Then** server vráti prázdny stav bez chyby, s informáciou o minimálnom počte záznamov pre výpočet adaptácie váh.

---

### User Story 2 — BDD testovacia suita (Priority: P2)

Vývojár chce spustiť sadu BDD (Behavior-Driven Development) testov, ktoré overujú všetky výpočtové scenáre na serveri — vrátane hraničných prípadov — a výsledky sú čitateľné pre netechnického spolupracovníka.

**Why this priority**: BDD testy sú živá dokumentácia výpočtového algoritmu. Slúžia aj ako komunikačný nástroj medzi vývojárom a doménovým expertom.

**Independent Test**: Spustiť BDD test runner, všetky feature súbory prebehnú zeleno na čistej inštalácii.

**Acceptance Scenarios**:

1. **Given** BDD feature súbory s human-editable YAML/JSON fixturami, **When** vývojár spustí test runner, **Then** testy prebehujú bez externých závislostí (offline, deterministické).
2. **Given** scenár "adaptácia váh po 15 dňoch", **When** testy bežia, **Then** výstup obsahuje krok-za-krokom audit trail výpočtu váh.
3. **Given** scenár hraničného prípadu (všetky hodnoty 0, alebo maximálne 5), **When** testy bežia, **Then** server vráti validný výsledok v rozsahu 0–100.

---

### User Story 3 — API komunikácia medzi appkou a serverom (Priority: P3)

Vývojár (a neskôr appka) chce vedieť, na ktorých miestach v Android aplikácii prebieha výpočet a kde by server nahradil lokálny výpočet. Potrebuje zdokumentované API endpointy pre posielanie dát a príjem výsledku.

**Why this priority**: Bez jasného API dizajnu nemožno integrovať Android appku so serverom ani navrhnúť offline sync mechanizmus.

**Independent Test**: Swagger/OpenAPI dokument je prístupný, každý endpoint má príklad volania a odpovede.

**Acceptance Scenarios**:

1. **Given** Android appka dokončí denný tracking, **When** má aktívne spojenie, **Then** vie poslať trackingové dáta na server a dostať späť vypočítaný index.
2. **Given** analýza kódu Android appky, **Then** špecifikácia identifikuje minimálne 3 miesta, kde dochádza k výpočtu a kde by server mohol prevziať rolu (napr. po uložení dňa, pri týždennej adaptácii váh, pri zobrazení history).
3. **Given** rozhodnutie "komunikácia len pri update vs. pri každom zobrazení", **Then** špecifikácia zdokumentuje trade-off oboch prístupov z pohľadu offline použiteľnosti, spotreby batérie a konzistencie dát.

---

### User Story 4 — Lokálne spustenie servera na Linux stroji (Priority: P4)

Vývojár chce spustiť server na akomkoľvek Linux stroji (vrátane localhost) bez zložitej inštalácie a bez cloudovej závislosti.

**Why this priority**: Ak server nie je easy-to-start, nebude sa používať na regresné testovanie.

**Independent Test**: Na čistom Ubuntu 22.04 LTS inštalácia a prvý request prebehnú za menej ako 5 minút podľa README.

**Acceptance Scenarios**:

1. **Given** čistý Linux stroj s nainštalovaným Pythonom (verzia ≥ 3.10), **When** vývojár spustí `make dev` alebo ekvivalentný príkaz, **Then** server beží na `localhost:8000` do 60 sekúnd.
2. **Given** server beží, **When** vývojár otvorí health-check URL, **Then** dostane odpoveď s verziou servera a stavom databázy.
3. **Given** vývojár nemá root/sudo práva, **Then** server beží v user-space bez systemd.

---

### User Story 5 — Autentifikácia používateľa (Priority: P5)

Používateľ sa zaregistruje alebo prihlási pomocou emailu a hesla pred prvou komunikáciou so serverom. Android appka vyžaduje zadanie emailu pred povolením sync funkcie.

**Why this priority**: Každý používateľ musí mať unikátnu identitu pre izoláciu dát a budúce webové rozhranie.

**Independent Test**: Registrácia nového emailu, prihlásenie, pokus o prístup bez tokenu → všetky scenáre prechádzajú.

**Acceptance Scenarios**:

1. **Given** nový používateľ zadá email a heslo v Android appke, **When** potvrdí registráciu, **Then** appka uloží prihlasovacie údaje a umožní sync.
2. **Given** neautentizovaný request na API, **Then** server vráti chybu 401 bez odhalenia dát iných používateľov.
3. **Given** zabudnuté heslo, **Then** existuje reset flow (email alebo admin reset — web UI nie je v scope tejto feature).

---

### User Story 6 — Offline sync a riešenie konfliktov (Priority: P6)

Používateľ bol viac dní offline. Po obnovení spojenia appka syncne všetky neuložené dni naraz. Ak rovnaký deň bol editovaný aj na serveri (napr. budúci web client), systém automaticky rozhodne o "víťazovi".

**Why this priority**: Bez robustného sync mechanizmu je server nepoužiteľný pre reálnych používateľov s nestabilným internetom.

**Independent Test**: Simulácia 5 offline dní + sync + detekcia konfliktu + automatické riešenie — celý flow prebehne bez manuálneho zásahu.

**Acceptance Scenarios**:

1. **Given** appka nahromadila 7 dní offline záznamov, **When** sa obnoví spojenie, **Then** server príjme všetky záznamy v jednej batch požiadavke a odpovie s počtom spracovaných dní.
2. **Given** rovnaký deň existuje na mobile aj na serveri s rôznymi hodnotami, **When** prebehne sync, **Then** systém aplikuje "last-write-wins" pravidlo podľa timestamp záznamu.
3. **Given** budúci web client edituje deň, ktorý mobile syncoval neskôr, **Then** riešenie konfliktu je deterministické a audit log obsahuje obe verzie.

---

### User Story 7 — Migrácia existujúcich dát na server (Priority: P7)

Existujúci používateľ Android appky chce preniesť históriu trackingových dát zo zariadenia na server, aby mal centrálnu zálohu a prístup z web klienta.

**Why this priority**: Bez migračného nástroja by existujúci používatelia stratili históriu pri prechode na serverovú verziu.

**Independent Test**: Export JSON z Android appky → import cez API → overenie, že všetky dni a hodnoty sú na serveri správne.

**Acceptance Scenarios**:

1. **Given** JSON export z Android appky (formát podľa existujúceho exportu), **When** používateľ spustí migráciu cez API, **Then** server importuje záznamy a zachová pôvodné dátumy a hodnoty.
2. **Given** migrovaný záznam pre deň, ktorý na serveri už existuje, **Then** server si vyžiada potvrdenie (alebo pri bulk migrácii aplikuje "mobile is source of truth").
3. **Given** neúplný export (napr. chýba niekoľko dní), **Then** migrácia prebehne pre dostupné dáta a vráti report o úspešne migrovaných vs. preskočených záznamoch.

---

### Edge Cases

- Čo sa stane, keď element má subpoložky ale všetky subpoložky majú váhu 0?
- Ako server spracuje request s neznámym `element_key` (nie je v konfigurácii)?
- Čo ak `overall_feeling` chýba pre daný deň — vypočíta sa index alebo sa deň preskočí?
- Čo ak sync request obsahuje budúci dátum (zariadenie má zlý čas)?
- Čo ak dva zariadenia syncujú súčasne (race condition)?
- Čo ak databáza servera je nedostupná — aký fallback dostane klient?

---

## Requirements

### Functional Requirements

- **FR-001**: Systém MUSÍ implementovať výpočet denného ADHD indexu identický so vzorcom v konštitúcii (`Index_d = 100 × Σ(w_i × e_i) / Σ(w_i)`) vrátane `value_effective` konverzie.
- **FR-002**: Systém MUSÍ podporovať hierarchické elementy (element → subpoložky) s algoritmom, ktorý zaručuje, že váha elementu sa nedelí medikrát podľa počtu subpoložiek.
- **FR-003**: Systém MUSÍ prijímať testovací vstup vo forme sérií 1, 3, 5, 15 a 30 dní a vracať index pre každý deň aj súhrnný výsledok.
- **FR-004**: Systém MUSÍ obsahovať BDD test suitu s human-editable fixturami (YAML alebo JSON) pre všetky kľúčové výpočtové scenáre.
- **FR-005**: Systém MUSÍ byť spustiteľný na akomkoľvek Linux stroji bez root práv, s minimálnymi závislosťami.
- **FR-006**: Systém MUSÍ poskytovať REST API pre posielanie tracking dát a príjem vypočítaného indexu.
- **FR-007**: Systém MUSÍ zdokumentovať všetky miesta v Android appke kde dochádza k výpočtu a analyzovať kde a kedy by server mal byť volaný (update-only vs. on-display).
- **FR-008**: Systém MUSÍ uchovávať používateľské dáta v perzistentnej databáze so schémou kompatibilnou s budúcimi verziami (additive-only migrácie).
- **FR-009**: Systém MUSÍ autentizovať každého používateľa pomocou emailu a hesla pred prístupom k dátam.
- **FR-010**: Systém MUSÍ podporovať batch sync pre offline scenáre s automatickým riešením konfliktov (last-write-wins podľa timestamp).
- **FR-011**: Systém MUSÍ poskytovať API endpoint pre migráciu existujúcich Android dát s reportom o úspešnosti.
- **FR-012**: Výstupný formát API MUSÍ byť navrhnutý pre spätnú kompatibilitu — pridávanie nových polí nesmie narušiť starých klientov.
- **FR-013**: Android appka MUSÍ pri zapnutí server sync vyžadovať zadanie emailu (identifikátor používateľa) pred prvou komunikáciou.
- **FR-014**: Systém MUSÍ správne spracovať stav novej aplikácie (žiadne dáta) bez chyby a s informatívnou odpoveďou.

### Alternatívne prístupy pre rozhodnutie v plánovaní

#### A. Tech stack (3 možnosti)
Výber ovplyvní ease-of-start, udržiavateľnosť a budúcu rozšíriteľnosť:

| Možnosť | Popis | Výhody | Nevýhody |
|---------|-------|--------|----------|
| **A1: FastAPI + Python** | Moderný async Python framework s auto-generated OpenAPI | Čitateľnosť, rýchle prototypovanie, natívna async podpora, výborná dokumentácia | Vyžaduje Python venv setup |
| **A2: Flask + Python** | Minimalistický synchronný framework | Jednoduchosť, zero magic, ľahké debugovanie | Pomalší pre concurrent requests, viac boilerplate |
| **A3: Django + Django REST Framework** | Full-stack framework s batteries included | Admin UI zadarmo, silné ORM, auth out-of-box | Ťažší, viac konfigurácie, overkill pre MVP |

**Odporúčanie pre plán**: A1 (FastAPI) — najlepší pomer výkon/čitateľnosť pre testovacie a budúce produkčné použitie.

#### B. Vstupno-výstupný formát (3 možnosti)
Ovplyvní backward compatibility a human-editability fixturových súborov:

| Možnosť | Popis | Výhody | Nevýhody |
|---------|-------|--------|----------|
| **B1: JSON s verziovaním** | `{"version": "1.0", "data": {...}}` | Priemyselný štandard, ľahko parsovateľný v Androide | Menej čitateľný pre ľudí ako YAML |
| **B2: YAML pre fixture, JSON pre API** | Testy definované v YAML, API komunikácia v JSON | Human-editable testy, machine-friendly API | Dve rôzne formáty = dve serializácie |
| **B3: JSON-LD / JSON Schema validated** | Každý request validovaný proti JSON schéme | Silná typová bezpečnosť, auto-dokumentácia | Komplexnejší setup, viac overhead |

**Odporúčanie pre plán**: B2 — YAML pre testovacie fixturové súbory, JSON pre API komunikáciu.

#### C. Algoritmus pre elementy so subpoložkami (3 možnosti)
Zaručuje, že element s viac subpoložkami nemá neoprávnene väčší vplyv:

| Možnosť | Popis | Vzorec | Vlastnosti |
|---------|-------|--------|-----------|
| **C1: Priemer subpoložiek × váha rodiča** | Vypočítaj priemer aktívnych subpoložiek, výsledok vynásob váhou rodiča | `contribution = parent.weight × avg(children_effective)` | Váha rodiča je konštantná bez ohľadu na počet detí |
| **C2: Distribuovaná váha** | Váha rodiča sa rovnomerne rozdelí medzi aktívne subpoložky | `child_weight = parent.weight / count(active_children)` | Každé dieťa prispieva rovnako, váha rodiča zachovaná |
| **C3: Explicitné váhy subpoložiek s normalizáciou** | Každá subpoložka má vlastnú váhu, normalizovanú aby suma = váha rodiča | `Σ child_weights = parent.weight` (konfigurovaný) | Najflexibilnejší, ale vyžaduje konfiguráciu každej subpoložky |

**Odporúčanie pre plán**: C1 — identické s implementáciou `computeDailyIndexGrouped` v Android appke (súčasný stav kódu), zachováva backward compatibility.

### Key Entities

- **User**: Jedinečný používateľ systému identifikovaný emailom; má prihlasovacie údaje a kolekciu tracking dát
- **TrackingDay**: Jeden deň trackingu pre jedného používateľa; obsahuje dátum, stav vyplnenia a kolekciu hodnôt elementov
- **ElementValue**: Hodnota konkrétneho elementu pre daný deň; `element_key`, `value_binary` (0/1), `value_scale` (1–5 alebo null), `value_effective` (0–1)
- **EntityConfig**: Konfigurácia hierarchie elementov (nodes s váhami, impact, parent); zdieľaná alebo per-user
- **DailyIndex**: Vypočítaný denný index (0–100) pre používateľa a deň; môže obsahovať detail per-element
- **SyncRecord**: Záznam synchronizácie — timestamp, zariadenie, počet záznamov, stav; pre audit a riešenie konfliktov

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Vývojár spustí server na čistom Linux stroji a odošle prvý úspešný request za menej ako 5 minút od klonu repozitára.
- **SC-002**: Serverový výpočet indexu produkuje identické výsledky ako Android appka pre rovnaké vstupy — odchýlka menej ako 0,01 bodu (floating point precision).
- **SC-003**: BDD testovacia suita pokrýva minimálne 10 scenárov vrátane hraničných prípadov a prebehne na čistej inštalácii bez externých sieťových závislostí.
- **SC-004**: Batch sync 30 dní dát prebehne za menej ako 10 sekúnd na bežnom laptop hardvéri.
- **SC-005**: API je navrhnuté tak, že pridanie nového nepovinného poľa do response nespôsobí chybu existujúcim klientom (backward compatibility overená automatickým testom).
- **SC-006**: Konflikty pri sync sú riešené automaticky v 100 % prípadov bez manuálneho zásahu používateľa.
- **SC-007**: Android appka zobrazí chybovú hlášku (nie crash) pri pokuse o sync bez zadaného emailu.

---

## Assumptions

- Server je v tejto fáze primárne vývojový nástroj — SLA, uptime a produkčná škálovateľnosť nie sú v scope.
- Centralizovaný výpočet (server nahradzuje mobilný výpočet pre produkčných používateľov) ostáva Post-MVP podľa konštitúcie.
- Lokálna databáza Android appky zostáva primárna ("offline-first"), server je doplnok — appka funguje plnohodnotne bez servera.
- Bezpečnosť hesiel: bcrypt alebo Argon2 hashing je štandard; pokročilé MFA/OAuth2 je mimo scope tejto feature.
- Databáza servera bude PostgreSQL ako primárna voľba; SQLite ako alternatíva pre localhost-only scenáre.
- Android appka bude vyžadovať email len ak je sync explicitne zapnutý v nastaveniach — sync je opt-in.
- Testovacia suita BDD bude implementovaná v Pythone (behave alebo pytest-bdd); jazyk feature súborov je angličtina.
- Fixturové súbory pre testy budú YAML pre ľahkú editáciu; API bude JSON.
- Conflict resolution v tejto verzii: `last-write-wins` podľa `updated_at` timestamp na úrovni dňa; merge na úrovni jednotlivých hodnôt je post-MVP.
