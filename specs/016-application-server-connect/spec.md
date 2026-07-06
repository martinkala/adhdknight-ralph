# Feature Specification: App–Server Connectivity Analysis

**Feature Branch**: `009-edit-system-updates`

**Created**: 2026-07-05

**Status**: Draft

**Input**: Analytický dokument pre prepojenie mobilnej aplikácie a servera, vrátane migrácie dát, bezpečnostného modelu, voliteľného loginu a migrácie DB.

---

## Kontext a účel

Táto špecifikácia je **analytický dokument**, ktorý zodpovedá otvorené architektonické otázky a navrhuje rozklad na 1–4 implementovateľné features. Samotná implementácia prebehne v nadväzujúcich featurách.

Systém pozostáva z troch komponentov:
- **Mobilná aplikácia** (Android) — primárny vstup dát, offline-first
- **FastAPI server** (:8095) — autentifikácia, sync, výpočtová logika
- **Django web app** (:8000) — vizualizácia dát z servera

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Nastaviteľné pripojenie k serveru (Priority: P1)

Používateľ si v nastaveniach mobilnej aplikácie zadá adresu (URL / IP) servera. Aplikácia sa na server pripojí len keď je dostupný — ak server nedostupný, pokračuje plnohodnotne offline. Bez nastavenej URL server zostáva neaktívny.

**Why this priority**: Toto je základná podmienka pre akúkoľvek komunikáciu medzi mobilnou app a serverom. Bez konfigurovateľnej URL nie je možné testovať ani nasadiť žiadnu inú server-side funkcionalitu.

**Independent Test**: Zadaj platnú server URL v settings → app sa pokúsi pripojiť a zobrazí stav pripojenia (pripojený / nepripojený). Zmaž URL → app beží offline bez chyby.

**Acceptance Scenarios**:

1. **Given** používateľ otvorí Settings, **When** zadá platnú URL servera a potvrdí, **Then** aplikácia overí dostupnosť servera a zobrazí stav „Pripojený" alebo „Server nedostupný".
2. **Given** server URL je nastavená, **When** server nie je dostupný, **Then** aplikácia pokračuje offline bez chybovej hlášky, sync je odložený.
3. **Given** server URL nie je nastavená, **When** používateľ otvorí Settings, **Then** sync sekcia je zobrazená ale neaktívna, s výzvou na zadanie URL.
4. **Given** platná URL je nastavená, **When** server je dostupný a používateľ je prihlásený, **Then** denné záznamy sa synchronizujú automaticky na pozadí.

---

### User Story 2 — Voliteľný login a Account obrazovka v mobilnej app (Priority: P2)

V mobilnej aplikácii pribudne nová obrazovka „Účet" v navigačnom menu. Login je voliteľný — aplikácia funguje plnohodnotne bez prihlásenia (offline-first zostáva zachované). Po prihlásení sa unlockne sync s serverom.

**Why this priority**: Account obrazovka je vstupný bod pre sync. Musí byť jasné, že prihlásenie nie je povinné a nemenní základnú funkcionalitu trackera.

**Independent Test**: Naviguj na Account → zobrazí sa stav „Neprihlásený" s tlačidlom Prihlásiť sa. Prihlás sa → zobrazí sa email a tlačidlo Odhlásiť. Odhláš sa → app funguje normálne offline.

**Acceptance Scenarios**:

1. **Given** používateľ nie je prihlásený, **When** otvorí Account obrazovku, **Then** vidí stav „Neprihlásený" a môže zadať email + heslo.
2. **Given** používateľ zadá správne prihlasovacie údaje, **When** server je dostupný, **Then** je prihlásený, Account zobrazí email a dátum registrácie.
3. **Given** používateľ zadá neexistujúce konto, **When** potvrdí, **Then** dostane zrozumiteľnú chybovú správu (nie technický stack trace).
4. **Given** používateľ je prihlásený, **When** klikne Odhlásiť, **Then** je odhlásený, sync sa zastaví, tracker zostáva funkčný offline.
5. **Given** server je nedostupný, **When** sa pokúsi prihlásiť, **Then** dostane správu „Server nie je dostupný" bez crashu aplikácie.

---

### User Story 3 — Migrácia existujúcich dát na server (Priority: P3)

Existujúce lokálne dáta (1 používateľ) sa importujú na server. Akceptované sú dve cesty: (A) sieťová migrácia priamo z app, alebo (B) import existujúceho CSV súboru cez utilitu na serveri + pripojenie app k serveru.

**Why this priority**: Historické dáta sú cenné pre analýzu trendov. Migrácia musí prebehnúť pred prvým reálnym použitím synchronizácie, inak by web dashboard bol prázdny.

**Independent Test**: Spusti migráciu (cestu A alebo B) → skontroluj, že web dashboard zobrazuje rovnaké dáta ako mobilná app pred migráciou. Počet dní a hodnoty indexu sa musia zhodovať.

**Acceptance Scenarios**:

1. **Given** existuje export CSV z mobilnej app, **When** administrátor spustí importnú utilitu na serveri, **Then** dáta sú importované do serverovej DB pre daného používateľa.
2. **Given** migrácia prebehla, **When** používateľ sa prihlási na web dashboard, **Then** vidí historické dáta zhodné s mobilnou app (dátumy, index hodnoty).
3. **Given** sieťová migrácia je implementovaná, **When** používateľ zvolí „Importovať dáta na server" v app, **Then** lokálne záznamy sú odoslané na server a potvrdenie je zobrazené.
4. **Given** migrácia zlyhá (napr. výpadok spojenia), **When** nastane chyba, **Then** lokálne dáta ostanú nedotknuté a používateľ je informovaný.

---

### User Story 4 — Bezpečná komunikácia (Priority: P4)

Komunikácia medzi klientmi (mobilná app, web app) a serverom je zabezpečená štandardným HTTPS/TLS. Certifikáty sú spravované automaticky (Let's Encrypt) na strane servera. Klienti nevyžadujú vlastné certifikáty.

**Why this priority**: Bezpečnosť je prerekvizitou pre produkčné nasadenie, ale v lokálnom/dev prostredí postačuje HTTP. Analýza jasne definuje, čo sa implementovať nemá (vlastné E2E šifrovanie), aby sa predišlo zbytočnej komplexnosti.

**Independent Test**: Nasaď server s HTTPS certifikátom → mobilná app aj web app sa pripoja bez chybového hlásenia. Certifikát vyprší a obnoví sa automaticky → klienti pokračujú bez zmeny.

**Acceptance Scenarios**:

1. **Given** server beží na HTTPS doméne s platným certifikátom, **When** mobilná app odošle dáta, **Then** komunikácia prebehne bez varovania o certifikáte.
2. **Given** certifikát sa automaticky obnoví (napr. Let's Encrypt každých 90 dní), **When** k obnove dôjde, **Then** mobilná app ani web app nevyžadujú žiadnu aktualizáciu.
3. **Given** server beží lokálne na HTTP (dev prostredie), **When** app sa pripojí, **Then** app akceptuje HTTP pripojenie v dev móde bez nutnosti inštalovať vlastný certifikát.

**Architektonická odpoveď — E2E šifrovanie:**

Odporúčanie je **neimplementovať vlastné end-to-end šifrovanie** (kde by ani server nevidel dáta). Dôvody:
- ADHD tracker dáta nie sú kriticky citlivé (nie sú to napr. bankové dáta alebo zdravotné záznamy podliehajúce regulácii).
- Vlastné E2E šifrovanie vyžaduje správu klientských kľúčov, čo výrazne komplikuje: obnovu konta, viacero zariadení, zálohovanie a budúce funkcie (analýza dát na serveri, weight adaptation).
- **TLS (HTTPS) poskytuje šifrovanie v transporte** — dáta sú čitateľné len na serveri (nie na sieti). Toto je štandardný a dostatočný model pre väčšinu SaaS aplikácií.
- Certifikátový pinning v mobilnej app sa **odporúča vynechať** — pri zmene certifikátu by starší klienti prestali fungovať bez aktualizácie app. Let's Encrypt auto-renew funguje transparentne bez pinningu.

**Web app vs. mobilná app z pohľadu TLS:** Oba klienti používajú rovnaký server-side TLS certifikát. Rozdiel neexistuje — TLS je na transportnej vrstve, nie na úrovni klienta. Prihlásenie (JWT) funguje identicky pre oba klienty.

---

### User Story 5 — Migrácia servera na PostgreSQL (Priority: P5)

Server prejde z SQLite na PostgreSQL databázu. SQLite zostáva pre lokálny vývoj a testovanie. PostgreSQL sa použije pre produkčné nasadenie.

**Why this priority**: SQLite má limity pri viacerých súbežných pripojeniach a nie je vhodný pre produkčné nasadenie na vzdialenom serveri. Migrácia je potrebná pred produkčným nasadením, ale nie blokuje dev/test fázu.

**Independent Test**: Spusti server s PostgreSQL konfiguráciou → existujúce API testy prechádzajú bez zmeny. Dáta importované do SQLite sú prenesené do PostgreSQL bez straty.

**Acceptance Scenarios**:

1. **Given** PostgreSQL je nainštalovaný a nakonfigurovaný v `.env`, **When** server štartuje, **Then** všetky API endpointy fungujú identicky ako so SQLite.
2. **Given** existujú dáta v SQLite dev databáze, **When** prebehne migračný skript, **Then** všetky záznamy sú prenesené do PostgreSQL bez straty dát.
3. **Given** server beží s PostgreSQL, **When** sa spustia existujúce testy, **Then** všetky prechádzajú bez zmeny testovacieho kódu.

---

### Edge Cases

- Čo ak používateľ zadá neplatnú URL (napr. bez `http://` prefixu)? → App zobrazí validačnú chybu pred odoslaním.
- Čo ak sa JWT token vyprší počas sync operácie? → App automaticky odhlási, lokálne dáta ostanú zachované.
- Čo ak migrácia CSV importuje duplikátne záznamy? → Server použije LWW (Last-Write-Wins) stratégiu — rovnaká politika ako pri štandardnom sync.
- Čo ak PostgreSQL migrácia zlyhá na polovici? → Alembic transakcie zabezpečia rollback — databáza ostane v konzistentnom stave.
- Čo ak používateľ má dáta v mobile aj na serveri (po migrácii a novom zázname)? → Sync LWW rieši konflikt podľa `updated_at` timestamp.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aplikácia MUST umožniť nastavenie server URL v sekcii Settings (prázdna hodnota = server neaktívny).
- **FR-002**: Aplikácia MUST fungovať plnohodnotne offline bez ohľadu na stav server URL.
- **FR-003**: Aplikácia MUST zobraziť Account obrazovku v navigačnom menu ako nový menu item.
- **FR-004**: Prihlásenie v Account obrazovke MUST byť voliteľné — neblokuje prístup k trackeru.
- **FR-005**: Aplikácia MUST zobraziť zrozumiteľnú chybovú správu pri nedostupnosti servera, nesprávnych prihlasovacích údajoch, alebo vypršanom prihlásení — bez technických detailov.
- **FR-006**: Existujúce dáta (1 používateľ) MUST byť importovateľné na server; akceptovaná cesta: CSV import cez serverovú utilitu.
- **FR-007**: Komunikácia medzi klientmi a serverom MUST byť zabezpečená TLS (HTTPS) v produkčnom prostredí.
- **FR-008**: Certifikáty MUST byť spravované automaticky bez nutnosti aktualizovať mobilnú app.
- **FR-009**: Server MUST byť nasaditeľný s PostgreSQL databázou v produkcii; SQLite zostáva pre lokálny vývoj.
- **FR-010**: Prihlasovací mechanizmus MUST byť identický pre mobilnú aj webovú aplikáciu (rovnaké JWT tokeny, rovnaký server endpoint).

### Navrhovaný rozklad na features (1–4)

| Feature | Obsah | Priorita |
|---------|-------|----------|
| **F1**: Server Settings + Account Screen | URL v settings, Account menu item, voliteľný login (FR-001–005, FR-010) | P1 – blocker |
| **F2**: Data Migration | CSV import utilita, prípadne in-app sieťová migrácia (FR-006) | P2 – pred prvým prod sync |
| **F3**: HTTPS / TLS Setup | Let's Encrypt na serveri, HTTP→HTTPS redirect, dev mode (FR-007–008) | P3 – pred prod nasadením |
| **F4**: PostgreSQL Migration | Alembic migrácia, `.env` prepínanie, dátová migrácia (FR-009) | P4 – pred prod nasadením |

**Odporúčané poradie implementácie**: F1 → F2 → F3 → F4. F1 je testovateľné lokálne (HTTP), F3 a F4 sú prerekvizity pre produkciu.

### Key Entities

- **ServerConfig**: URL servera, stav pripojenia (uložené v lokálnych preferences)
- **UserSession**: JWT access token, email, expiry — uložené bezpečne v mobilnej app (EncryptedSharedPreferences)
- **SyncRecord**: záznamy odoslané / čakajúce na odoslanie, timestamp posledného sync

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Používateľ nastaví server URL a overí pripojenie za menej ako 30 sekúnd.
- **SC-002**: Mobilná app sa spustí a umožní denný záznam do 3 sekúnd bez ohľadu na dostupnosť servera.
- **SC-003**: Migrácia existujúcich dát prebehne bez straty — 100% záznamov je po migrácii viditeľných na web dashboarde.
- **SC-004**: Obnova certifikátu nevyžaduje žiadnu aktualizáciu mobilnej app ani web app.
- **SC-005**: Prihlásenie v mobilnej app a web app používa rovnaký server endpoint — žiadna duplicitná autentifikačná logika.
- **SC-006**: Po migrácii na PostgreSQL prechádzajú všetky existujúce API testy bez zmeny testovacieho kódu.

---

## Assumptions

- Produkčné nasadenie servera bude na doméne s verejnou IP (nie len lokálna sieť) — potrebné pre Let's Encrypt certifikáty.
- Pre lokálny vývoj a testovanie sa naďalej používa HTTP (localhost) — app bude mať dev mód bez TLS vyžadovania.
- Vlastné end-to-end šifrovanie (kde server nevidí plaintext dáta) sa **neimplementuje** — HTTPS/TLS je dostatočná úroveň zabezpečenia pre tento use case.
- Certifikátový pinning v mobilnej app sa **neimplementuje** — systémový trust store je dostatočný a umožňuje bezproblémovú obnovu certifikátov.
- Existuje práve 1 používateľ s existujúcimi dátami — migrácia nie je multi-tenant.
- Sync konflikty sa riešia LWW (Last-Write-Wins) — rovnaká politika ako v existujúcom sync systéme.
- SQLite zostáva default pre lokálny vývoj aj po migrácii servera na PostgreSQL.
- Constitution Princíp I (Offline-first) zostáva zachovaný — server connectivity je vždy opt-in doplnok.
