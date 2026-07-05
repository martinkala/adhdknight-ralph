# Feature Specification: Web Companion App

**Feature Branch**: `015-web-based-app`

**Created**: 2026-07-04

**Status**: Draft

**Input**: Webová aplikácia zobrazujúca dáta z ADHD trackeru — read-only dashboard, autentifikácia, denný trend, info, používateľský účet. Alfa platforma pre testovanie nových grafov a algoritmov.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Autentifikácia (Priority: P1)

Používateľ sa zaregistruje alebo prihlási emailom a heslom. Po úspešnom prihlásení je presmerovaný na hlavnú stránku. Neautentifikovaný používateľ nevidí žiadne dáta.

**Why this priority**: Bez autentifikácie nie je možné zobraziť personalizované dáta z servera. Všetky ostatné user stories na nej závisia.

**Independent Test**: Otvor webovú aplikáciu bez prihlásenia → zobrazia sa len stránky registrácie/prihlásenia. Zaregistruj nový účet, prihlás sa → dostaneš sa na dashboard.

**Acceptance Scenarios**:

1. **Given** používateľ nie je prihlásený, **When** otvorí web app, **Then** vidí prihlasovaciu stránku, nie dáta
2. **Given** formulár registrácie, **When** zadá platný email a heslo, **Then** účet je vytvorený a používateľ je prihlásený
3. **Given** existujúci účet, **When** zadá správny email a heslo, **Then** je prihlásený a vidí dashboard
4. **Given** existujúci účet, **When** zadá nesprávne heslo, **Then** dostane zrozumiteľnú chybovú správu
5. **Given** prihlasovací formulár, **When** zadá email ktorý neexistuje, **Then** dostane zrozumiteľnú chybovú správu
5. **Given** prihlásený používateľ, **When** sa odhlási, **Then** je presmerovaný na prihlasovaciu stránku

---

### User Story 2 — Hlavný dashboard s double-sided grafom (Priority: P2)

Prihlásený používateľ vidí hlavnú stránku s double-sided bar chartom zobrazujúcim dáta nahraté na serveri. Stránka je čisto read-only — žiadne vstupné prvky pre pridávanie záznamov.

**Why this priority**: Toto je primárny cieľ v1 — vizualizácia existujúcich dát. Tracker (zadávanie hodnôt) nie je súčasťou web verzie.

**Independent Test**: Prihlás sa → hlavná stránka zobrazí double-sided bar chart z dát dostupných na serveri. Žiadne tlačidlá na pridávanie záznamov nie sú viditeľné.

**Acceptance Scenarios**:

1. **Given** prihlásený používateľ, **When** otvorí hlavnú stránku, **Then** vidí double-sided bar chart s dátami zo servera
2. **Given** hlavná stránka, **When** server nemá dáta pre daného používateľa, **Then** zobrazí sa prázdny stav s informatívnou správou
3. **Given** hlavná stránka, **When** server nie je dostupný, **Then** zobrazí sa zrozumiteľná chyba (nie technický stack trace)
4. **Given** hlavná stránka, **When** hľadá vstupné prvky trackera, **Then** nenájde ich — tracker nie je dostupný

---

### User Story 3 — Denný trend (Priority: P3)

Prihlásený používateľ si môže zobraziť denný trend ADHD indexu — prehľad vývoja v čase.

**Why this priority**: Kľúčový analytický pohľad na dáta po dashboarde. Umožňuje vidieť vzory v čase.

**Independent Test**: Prihlás sa → naviguj na "Denný trend" → zobrazí sa čiarový alebo stĺpcový graf s hodnotami ADHD indexu za posledné dni.

**Acceptance Scenarios**:

1. **Given** prihlásený používateľ, **When** otvorí stránku denného trendu, **Then** vidí graf s historickými hodnotami indexu
2. **Given** stránka trendu, **When** sú k dispozícii dáta z viacerých dní, **Then** graf zobrazuje vývoj v čase v chronologickom poradí

---

### User Story 4 — Používateľský účet (Priority: P4)

Prihlásený používateľ si môže zobraziť informácie o svojom účte (email, dátum registrácie).

**Why this priority**: Štandardná súčasť web aplikácie. Nízka komplexnosť, ale potrebná pre kompletný UX.

**Independent Test**: Prihlás sa → naviguj na "Účet" → vidíš email a základné info o účte.

**Acceptance Scenarios**:

1. **Given** prihlásený používateľ, **When** otvorí stránku účtu, **Then** vidí svoj email a základné info
2. **Given** stránka účtu, **When** sa chce odhlásiť, **Then** nájde tlačidlo odhlásenia

---

### User Story 5 — Info stránka (Priority: P5)

Používateľ si môže zobraziť informácie o aplikácii — popis projektu, verzia.

**Why this priority**: Podporná stránka, nízka priorita. Kopíruje info stránku z mobilnej aplikácie.

**Independent Test**: Naviguj na "Info" → zobrazí sa statická stránka s popisom projektu.

**Acceptance Scenarios**:

1. **Given** používateľ (prihlásený alebo nie), **When** otvorí info stránku, **Then** vidí popis aplikácie

---

### Edge Cases

- Čo ak server na 127.0.0.1:8095 nie je dostupný? → Zobraziť stav chyby pripojenia, nie prázdnu stránku
- Čo ak platnosť session vyprší počas používania? → Presmerovanie na prihlásenie bez straty kontextu stránky
- Čo ak používateľ nemá žiadne dáta na serveri? → Prázdny stav s vysvetlením (napr. "Zatiaľ žiadne záznamy — zadaj dáta cez mobilnú aplikáciu")
- Čo ak registračný email už existuje? → Zrozumiteľná chybová správa bez odhalenia technických detailov

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Systém MUST umožniť registráciu nového používateľa pomocou emailu a hesla
- **FR-002**: Systém MUST umožniť prihlásenie existujúceho používateľa pomocou emailu a hesla
- **FR-003**: Systém MUST umožniť odhlásenie prihláseného používateľa
- **FR-004**: Neautentifikované požiadavky na chránené stránky MUST byť presmerované na prihlásenie
- **FR-005**: Hlavná stránka MUST zobrazovať double-sided bar chart s dátami prihláseného používateľa zo servera
- **FR-006**: Web aplikácia MUST byť read-only — zadávanie, úprava ani mazanie záznamov nie je dostupné
- **FR-007**: Tracker obrazovka MUST byť explicitne vylúčená z navigácie web aplikácie
- **FR-008**: Aplikácia MUST zobrazovať stránku denného trendu s historickými hodnotami ADHD indexu
- **FR-009**: Aplikácia MUST zobrazovať stránku používateľského účtu s emailom a možnosťou odhlásenia
- **FR-010**: Aplikácia MUST zobrazovať info stránku s popisom projektu
- **FR-011**: Aplikácia MUST komunikovať so serverom na konfigurovateľnej adrese (default: 127.0.0.1:8095)
- **FR-012**: Chybové stavy (server nedostupný, neplatné prihlásenie) MUST byť zobrazené používateľsky priateľsky bez technických detailov

### Key Entities

- **Používateľ**: email, autentifikačné údaje — spravované serverom
- **Session**: autentifikačný token platný počas relácie
- **DennyZaznam**: read-only dáta zo servera (index, hodnoty elementov, dátum)
- **ServerConfig**: adresa servera (default 127.0.0.1:8095), konfigurovateľná

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Registrácia a prihlásenie sú dokončené do 2 minút vrátane vyplnenia formulára
- **SC-002**: Dashboard s grafom sa načíta do 3 sekúnd pri lokálnom serveri
- **SC-003**: Každá stránka je dostupná maximálne na 2 kliknutia od hlavnej stránky
- **SC-004**: Neautentifikovaný používateľ nemá prístup k žiadnym dátam — 100% chránené endpointy
- **SC-005**: Chybový stav (server offline) je zobrazený do 5 sekúnd bez pádu aplikácie

## Assumptions

- Server (FastAPI, feature 012) je funkčný a poskytuje API pre autentifikáciu aj dáta — web app je čistý klient
- Dáta sú do systému zadávané výhradne cez mobilnú aplikáciu; web zobrazuje len existujúce záznamy
- Aplikácia beží v desktop prehliadači; mobilná responzivita je nice-to-have, nie požiadavka v1
- Server adresa 127.0.0.1:8095 je výchozí pre lokálny vývoj; v budúcnosti bude konfigurovateľná
- Autentifikácia využíva existujúci serverový auth systém (JWT tokeny podľa feature 012)
- Webová aplikácia je samostatný projekt (nie súčasť Android kódu); existujúca Android architektúra (MVVM, Room) sa naň nevzťahuje
- Technologická preferencia: Python backend (Django) + HTML/JS frontend — finálny stack je predmetom plánovacej fázy
- Alfa platforma — produkčná robustnosť (škálovateľnosť, SSO) nie je v scope v1
