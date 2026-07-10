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

### Edge Cases

- Čo ak používateľ zadá neplatnú URL (napr. bez `http://` prefixu)? → App zobrazí validačnú chybu pred odoslaním.
- Čo ak sa JWT token vyprší počas sync operácie? → App automaticky odhlási, lokálne dáta ostanú zachované.
- Čo ak používateľ má dáta v mobile aj na serveri? → Sync LWW rieši konflikt podľa `updated_at` timestamp.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aplikácia MUST umožniť nastavenie server URL v sekcii Settings (prázdna hodnota = server neaktívny).
- **FR-002**: Aplikácia MUST fungovať plnohodnotne offline bez ohľadu na stav server URL.
- **FR-003**: Aplikácia MUST zobraziť Account obrazovku v navigačnom menu ako nový menu item.
- **FR-004**: Prihlásenie v Account obrazovke MUST byť voliteľné — neblokuje prístup k trackeru.
- **FR-005**: Aplikácia MUST zobraziť zrozumiteľnú chybovú správu pri nedostupnosti servera, nesprávnych prihlasovacích údajoch, alebo vypršanom prihlásení — bez technických detailov.
- **FR-006**: Prihlasovací mechanizmus MUST byť identický pre mobilnú aj webovú aplikáciu (rovnaké JWT tokeny, rovnaký server endpoint).

### Rozklad na features

| Feature | Obsah | Branch |
|---------|-------|--------|
| **F1**: Server Settings + Account Screen | URL v settings, Account menu item, voliteľný login (FR-001–006) | `016-application-server-connect` ✅ |
| **F2**: PostgreSQL Migration | Alembic migrácia, `.env` prepínanie, dátová migrácia | `017-migration-to-postgres` |
| **F3**: HTTPS / TLS Setup | Let's Encrypt na serveri, HTTP→HTTPS redirect, dev mode | `018-migration-to-server` |

### Key Entities

- **ServerConfig**: URL servera, stav pripojenia (uložené v lokálnych preferences)
- **UserSession**: JWT access token, email, expiry — uložené bezpečne v mobilnej app (EncryptedSharedPreferences)
- **SyncRecord**: záznamy odoslané / čakajúce na odoslanie, timestamp posledného sync

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Používateľ nastaví server URL a overí pripojenie za menej ako 30 sekúnd.
- **SC-002**: Mobilná app sa spustí a umožní denný záznam do 3 sekúnd bez ohľadu na dostupnosť servera.
- **SC-003**: Prihlásenie v mobilnej app a web app používa rovnaký server endpoint — žiadna duplicitná autentifikačná logika.

---

## Assumptions

- Sync konflikty sa riešia LWW (Last-Write-Wins).
- Constitution Princíp I (Offline-first) zostáva zachovaný — server connectivity je vždy opt-in doplnok.
- TLS/PostgreSQL sú riešené v nadväzujúcich featurách (017, 018).
