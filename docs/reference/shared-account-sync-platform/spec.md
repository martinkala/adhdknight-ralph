# Feature Specification: Shared Account, Login & Sync Platform (Technical Extraction)

**Feature Branch**: `001-shared-account-sync-platform` (assign in the new app's own repo)

**Created**: 2026-07-25

**Status**: Draft — extracted from the existing ADHD tracker implementation, not yet implemented in the new app

**Input**: Extract the technical (non-business) layer of the ADHD tracker Android app + FastAPI server — user management, server login, and data sync — so a new, separately-specced nutrition-focused Android app can reuse it as-is. The new app's business logic already lives in its own constitution; this document intentionally contains **no food/nutrition domain content**. The "Účet" (Account) tab in the new app MUST have the same functionality as the current app's.

---

## Kontext a účel

Táto špecifikácia popisuje **iba technickú vrstvu** existujúcej ADHD tracker aplikácie (android_app + FastAPI server), ktorá je doménovo nezávislá: správa používateľa, prihlásenie, a synchronizácia denných záznamov. Cieľom je, aby nová aplikácia (zameraná na stravu) implementovala **identický** kontrakt, a tak:

- používateľ mohol (ak sa tak rozhodneme) používať **jeden účet naprieč oboma aplikáciami**,
- server-side kód (auth, sync, user) mohol byť **zdieľaný alebo len skopírovaný 1:1** bez úprav,
- budúce zmeny tejto vrstvy (napr. refresh token flow, TLS) sa dali robiť na jednom mieste a preniesť do oboch aplikácií.

Extrahované z: `android_app/app/src/main/java/com/example/madhdtracker/{data/remote,data/repository,ui}` a `server/app/{routers,services,models,schemas}`. Nadväzuje na (ale spresňuje a opravuje) `specs/016-application-server-connect`, `specs/017-migration-to-postgres`, `specs/018-migration-to-server` — tie boli písané pred implementáciou refresh tokenov a preto sú v niektorých detailoch zastarané (pozri **Odchýlky od pôvodných specs** nižšie).

Systém pozostáva z troch komponentov, z ktorých táto špecifikácia sa týka prvých dvoch:
- **Mobilná aplikácia** (Android, nová aj existujúca) — primárny vstup dát, offline-first
- **FastAPI server** — autentifikácia, sync, výpočtová logika (doménovo špecifická časť výpočtu indexu NIE JE súčasťou tejto špecifikácie)
- **Django web app** — mimo scope tohto dokumentu

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Nastaviteľné pripojenie k serveru (Priority: P1)

Používateľ si v nastaveniach aplikácie zadá adresu (URL) servera. Aplikácia sa na server pripojí len keď je dostupný — ak server nedostupný, pokračuje plnohodnotne offline. Bez nastavenej URL zostáva server neaktívny.

**Independent Test**: Zadaj platnú server URL v settings → app sa pokúsi pripojiť. Zmaž URL → app beží offline bez chyby.

**Acceptance Scenarios**:

1. **Given** používateľ otvorí Settings, **When** zadá platnú URL servera, **Then** hodnota sa uloží (trailing slash odstránený) a je dostupná pre login/sync volania.
2. **Given** server URL je nastavená, **When** server nie je dostupný, **Then** aplikácia pokračuje offline bez chybovej hlášky.
3. **Given** server URL nie je nastavená, **When** používateľ sa pokúsi prihlásiť alebo synchronizovať, **Then** dostane správu „Zadajte URL servera v nastaveniach" bez pokusu o sieťové volanie.

### User Story 2 — Účet obrazovka: login, register, sync, logout (Priority: P1)

Aplikácia má obrazovku „Účet" v navigácii, funkčne **identickú** so súčasnou `AccountScreen.kt`. Login je voliteľný — aplikácia funguje plnohodnotne bez prihlásenia.

**Independent Test**: Naviguj na Účet → stav „Neprihlásený" s formulárom (email, heslo, tlačidlá Prihlásiť/Registrovať). Prihlás sa → karta s emailom, počtom dní, dátumom registrácie, tlačidlom Synchronizovať a Odhlásiť. Po úspešnom prihlásení sa automaticky spustí sync.

**Acceptance Scenarios**:

1. **Given** používateľ nie je prihlásený, **When** otvorí Účet, **Then** vidí login formulár (email, heslo skryté cez `PasswordVisualTransformation`, tlačidlo Prihlásiť aktívne len keď obe polia nie sú prázdne, tlačidlo Registrovať aktívne pri hesle ≥ min. dĺžka).
2. **Given** používateľ zadá správne údaje, **When** server je dostupný, **Then** je prihlásený, `access_token`+`refresh_token`+email sa uložia do `EncryptedSharedPreferences`, a automaticky sa spustí `sync()`.
3. **Given** používateľ zadá nesprávne heslo alebo neexistujúci účet, **When** potvrdí, **Then** dostane „Nesprávne prihlasovacie údaje" (nie stack trace).
4. **Given** email je už registrovaný, **When** sa pokúsi zaregistrovať, **Then** dostane „Účet s týmto emailom už existuje".
5. **Given** používateľ je prihlásený, **When** klikne Synchronizovať, **Then** vidí „Synchronizujem..." a po dokončení „✓ Synchronizované: N záznamov" (+ „(M konfliktov)" ak M > 0).
6. **Given** prístupový token vypršal počas syncu (401), **When** dôjde k automatickému pokusu o refresh, **Then** ak refresh uspeje, sync sa zopakuje transparentne; ak refresh zlyhá, používateľ dostane „Prihlásenie vypršalo, prihláste sa znova".
7. **Given** používateľ je prihlásený, **When** klikne Odhlásiť, **Then** session sa vymaže (`clearSession()`), stav sa vráti na Neprihlásený, tracker zostáva plne funkčný offline.
8. **Given** server je nedostupný, **When** sa používateľ pokúsi prihlásiť/registrovať/synchronizovať, **Then** dostane „Server nie je dostupný" (connection error) alebo „Server neodpovedá, skúste neskôr" (timeout) bez crashu.

### Edge Cases

- Neplatná URL bez `http(s)://` prefixu → validácia pred odoslaním (rovnaká ako F1 v `016`).
- Access token vyprší mimo syncu (napr. na `/user/me`) → aplikácia môže buď skúsiť refresh, alebo odhlásiť; **súčasná implementácia refresh flow aplikuje iba v `syncAll()`** — pozri Odchýlky nižšie.
- Používateľ má dáta lokálne aj na serveri pre ten istý deň/element → server rieši LWW podľa `updated_at` (pozri `data-model.md`).
- Budúci dátum v sync batchi → server ho odmietne (`records_rejected`, `resolution: "rejected_future_date"`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aplikácia MUST umožniť nastavenie server URL v Settings; prázdna hodnota = server neaktívny; URL sa normalizuje (trailing slash odstránený).
- **FR-002**: Aplikácia MUST fungovať plnohodnotne offline bez ohľadu na stav server URL alebo prihlásenia.
- **FR-003**: Aplikácia MUST mať obrazovku „Účet" s funkcionalitou identickou bodu User Story 2 vyššie (login, register, logged-in card, sync button, logout).
- **FR-004**: Prihlásenie MUST byť voliteľné — neblokuje prístup k žiadnej trackovacej funkcii appky.
- **FR-005**: Autentifikácia MUST používať rovnaký kontrakt (endpointy, JWT formát, algoritmus HS256) ako existujúci server, viď `contracts/api-contracts.md` — nová appka buď zdieľa server, alebo beží proti vlastnej inštancii s identickým API.
- **FR-006**: `access_token` a `refresh_token` MUST byť uložené v `EncryptedSharedPreferences` (Android Security Crypto, AES256_GCM/AES256_SIV) — nikdy v plain SharedPreferences ani v Room.
- **FR-007**: Po 401 počas sync operácie aplikácia MUST skúsiť raz `refresh_token` a zopakovať request; pri zlyhaní refreshu MUST zobraziť zrozumiteľnú správu bez automatického vymazania session (súčasné správanie — pozri Odchýlky).
- **FR-008**: Chybové stavy (401, 409, connection error, timeout, prázdna URL) MUST byť mapované na užívateľsky zrozumiteľné hlášky — presná mapa je v `contracts/api-contracts.md`.
- **FR-009**: Sync MUST odosielať dáta dávkovo (`POST /api/v1/sync/batch`) pre všetky lokálne dni naraz, s `element_key`/`value_binary`/`value_scale`/`note`/`updated_at` per element — schéma je doménovo neutrálna (`element_key` je voľný string, server neverifikuje proti žiadnemu fixnému zoznamu).
- **FR-010**: Sync konflikty MUST byť riešené server-side cez LWW (Last-Write-Wins) na úrovni jednotlivého elementu (nie celého dňa) podľa `updated_at`.
- **FR-011**: Network timeouts MUST byť: 5s pre auth/me/reachability, 30s pre batch sync (zhoduje sa so súčasným `ApiClient`).
- **FR-012**: Password politika MUST byť konzistentná medzi klientom a serverom — min. 8 znakov, na oboch stranách (opravené aj v existujúcej appke, pozri Odchýlky).
- **FR-013**: Nová appka MUST posielať vlastný `app_id` (napr. `"food_diary"`) vo všetkých volaniach, ktoré zapisujú alebo čítajú dáta scopnuté per appka (`/sync/batch`, `/migrate`, `/user/me`, `/user/history`, `/sync/status`) — umožňuje to zdieľať jeden účet naprieč appkami bez kolízie dát (pozri "Multi-app account scoping" nižšie).

### Non-functional Requirements

- Rovnaká vrstvová architektúra ako existujúca appka (MVVM + Repository, žiadne priame volanie DAO/API z UI) — v súlade s Constitution Princíp I existujúcej appky.
- Žiadne skutočné sieťové volania v testoch (rovnaké pravidlo ako existujúca Constitution Princíp VI).

### Key Entities

- **ServerConfig**: `server_url: String` — plain `SharedPreferences` (`adhd_prefs` alebo ekvivalent v novej appke).
- **UserSession**: `access_token`, `refresh_token`, `user_email` — `EncryptedSharedPreferences` (`adhd_secure_prefs` alebo ekvivalent).
- **AccountUiState** (sealed): `LoggedOut | Loading | LoggedIn(email, totalDays, createdAt) | Error(message)`.
- **SyncUiState** (sealed): `Idle | Syncing | Done(accepted, conflicted) | Error(message)`.
- Server-side entities (`User`, `TrackingDay`, `ElementValue`, `DailyIndex`, `SyncRecord`, `WeightConfig`) — plné detaily v `data-model.md`.

---

## Success Criteria *(mandatory)*

- **SC-001**: Login/register/refresh/sync fungujú proti existujúcemu FastAPI serveru bez akejkoľvek zmeny server-side kódu.
- **SC-002**: Nová appka sa spustí a je plne použiteľná do 3 sekúnd bez ohľadu na dostupnosť servera alebo stav prihlásenia.
- **SC-003**: Rovnaký používateľský účet (email+heslo) funguje v oboch appkách pri zdieľanom serveri, s dátami izolovanými per appka cez `app_id` (implementované, pozri "Multi-app account scoping").
- **SC-004**: UI chybové hlášky sú textovo identické so súčasnou appkou (konzistentný UX naprieč appkami).

---

## Odchýlky od pôvodných specs (016/017/018) — server sa odvtedy posunul

Tento dokument vychádza z **aktuálneho kódu**, nie z pôvodných spec súborov, ktoré sú v týchto bodoch zastarané:

1. **Refresh token existuje.** `016/contracts/api-contracts.md` tvrdí "FastAPI server aktuálne neimplementuje refresh token flow" — už neplatí. `POST /api/v1/auth/refresh` je implementovaný a klient (`UserRepository.refreshAccessToken`) ho už používa (retry-once-on-401 v `syncAll()`).
2. **Password min. dĺžka je 8** (opravené). `AccountScreen.kt` pôvodne povoľovalo Registrovať už pri 6 znakoch napriek serveru vyžadujúcemu 8 — opravené priamo v existujúcej appke (`MIN_PASSWORD_LENGTH = 8`, s inline hláškou pod poľom hesla). Nová appka by mala rovno prevziať rovnakú konštantu.
3. **`TokenResponse` má `schema_version` a `expires_in`.** Nová appka by mala tieto polia parsovať (Android `LoginResponse` ich už má ako voliteľné s defaultmi).
4. **`device_id` je súčasťou kontraktu, ale nikdy sa nepoužíva.** `BatchSyncRequest.device_id` existuje v schéme (server aj klient), no `UserRepository.syncAll()` ho nikdy nenastavuje (vždy `null`). Ak nová appka chce multi-device debugging, treba ho začať posielať — pozri Otvorené otázky.
5. **`GET /api/v1/user/history`** existuje (nie je v pôvodných 016 docs) a vracia `detail: [{element_key, value_effective, weight, contribution, impact}]` — táto štruktúra je **naviazaná na doménový výpočet indexu ADHD trackera** (weight/contribution/impact z `IndexCalculator`), takže nie je priamo prenositeľná 1:1 pre novú appku bez vlastného ekvivalentu tohto výpočtu. Sync samotný (`/sync/batch`) je doménovo neutrálny, `/user/history` nie je.

---

## Multi-app account scoping — vyriešené

Otázka "zdieľaný server/účet, alebo len zdieľaný kontrakt?" je vyriešená pridaním **`app_id`** ako scoping dimenzie priamo do dátového modelu — jeden účet (jeden email+heslo, jeden JWT) funguje naprieč **ľubovoľným počtom appiek**, ale ich denné dáta sa navzájom nemiešajú:

- `tracking_days` a `weight_configs` majú nový stĺpec `app_id: String(50)` (default `"adhd_tracker"` pre spätnú kompatibilitu s existujúcimi dátami/klientmi, ktoré ho neposielajú).
- Unique constraints sú teraz `(user_id, app_id, date)` a `(user_id, app_id, element_key)` namiesto pôvodných `(user_id, date)` / `(user_id, element_key)` — takže `adhd_tracker` aj `food_diary` môžu mať vlastný `TrackingDay` pre ten istý dátum bez kolízie, aj keby náhodou použili rovnaký `element_key` (napr. obe appky majú `"sleep"`).
- `POST /api/v1/sync/batch` a `POST /api/v1/migrate` prijímajú voliteľné `app_id` (default `"adhd_tracker"`); `GET /api/v1/user/me`, `GET /api/v1/user/history`, `GET /api/v1/sync/status` prijímajú `app_id` ako query param (rovnaký default) a vracajú dáta scopnuté len na daný `app_id` — okrem `email`/`created_at`, ktoré sú na úrovni účtu, nie appky.
- Implementované cez Alembic migráciu `c3d4e5f6a7b8_add_app_id_scoping` (batch mode, funguje na SQLite aj PostgreSQL) — otestované upgrade aj downgrade, existujúce riadky sa backfillujú na `"adhd_tracker"`.
- Nová appka jednoducho posiela `app_id = "food_diary"` (alebo vlastný reťazec) vo všetkých volaniach — **žiadna ďalšia zmena schémy nie je pri pridaní ďalšej appky potrebná** (žiadny FK na fixný zoznam appiek, `app_id` je voľný string).
- Pozri `server/tests/api/test_multi_app.py` pre overené scenáre: rovnaký dátum + rovnaký `element_key` v dvoch appkách sa nekonfliktujú, `sync/status` a `user/me` vracajú per-appku počty, `email`/`created_at` sú zdieľané.

Zostávajúce otvorené otázky:

1. **Má nová appka mať vlastný `/user/history`-ekvivalent?** Endpoint je teraz `app_id`-scoped, ale `detail` shape (`weight`/`contribution`/`impact`) je stále viazaný na `IndexCalculator` z ADHD trackera — nová appka pravdepodobne potrebuje analogický endpoint nad svojím vlastným (stravovacím) indexom, mimo scope tohto dokumentu.
2. **`device_id`** — stále sa nikde nenastavuje (`UserRepository.syncAll()` posiela vždy `null`) — nová appka ho môže začať posielať, ak chce multi-device debugging; schéma to už podporuje.

---

## Assumptions

- Sync konflikty sa riešia LWW podľa `updated_at`, per element (nie per deň).
- Nová appka dodržiava rovnaký princíp offline-first ako existujúca appka.
- TLS/produkčné nasadenie servera je mimo scope tohto dokumentu (viď `specs/018-migration-to-server`, platí rovnako pre obe appky bez zmeny klienta).
- Server beží na jednej spoločnej doméne/URL, konfigurovateľnej per appka v Settings (obe appky môžu ukazovať na tú istú alebo rôzne inštancie servera — kontrakt je identický v oboch prípadoch).
