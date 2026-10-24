<!--
Sync Impact Report
- Version change: 1.1.0 -> 2.0.0 (MAJOR: constitution sa mení z jednej Android appky na monorepo s modulmi)
- Modified: pôvodný obsah 1.1.0 (ADHD Android) presunutý bez zmeny do
  .specify/memory/constitution-adhd-android.md a platí ako modul pre android_app/
- Added sections: Kontext a režimy, Spoločné princípy, Modul Server + Web, Modul Food diary,
  Ralph Wiggum workflow
- Removed sections: none (nič z 1.1.0 sa nestratilo)
- Impact on existing specs: ADHD specs 001-025 (podpriečinky specs/NNN-*) sa nemenia a Ralph loop ich NEspracúva
- Follow-up TODOs: none
-->
# AdhdKnight Constitution

Monorepo osobných zdravotných trackerov so **spoločným účtom**:

- **ADHD tracker** — Android appka (`android_app/`) + výpočet indexu na serveri.
- **Food diary** — denník stravy, liekov, pohybu a zdravotných problémov. Fáza 1 = web,
  fáza 2 = Android appka nad rovnakým API. Zozbierané dáta sa analyzujú mimo aplikácie,
  preto je hlavným cieľom **rýchle a jednoduché zadávanie a editácia záznamov**.

Komponenty: `server/` (FastAPI, auth + API všetkých appiek), `web_app/` (Django web konzola,
tenký klient nad API), `android_app/` (ADHD Android), `deploy/` (nginx, systemd, ansible).

---

## Kontext a režimy

**Ralph Loop režim** (spustený cez `scripts/ralph-loop.sh`):
- Pracuj **výhradne** na súboroch `specs/food-NNN-*.md` (pozri sekciu Ralph Wiggum workflow).
- Implementuj, otestuj, commitni a pushni na branch `food-diary`.
- `<promise>DONE</promise>` vypíš až keď je spec na 100 % hotová.
- `<promise>ALL_DONE</promise>` vypíš, keď už žiadna `specs/food-*.md` nie je nedokončená.

**Interaktívny režim** (bežná konverzácia): pomáhaj, navrhuj, píš specs. Nič neimplementuj bez požiadavky.

---

## Časť A — Spoločné princípy (záväzné pre celé repo)

### A1. Izolácia používateľov — NON-NEGOTIABLE
Každý dotaz na dáta je filtrovaný podľa prihláseného používateľa (`user_id` z JWT). Používateľ
nikdy nevidí, nenájde (ani v autocomplete, exporte, štatistikách) a nezmení dáta iného
používateľa. Prístup k cudziemu záznamu cez ID vracia **404** (nie 403, aby sa neprezradila existencia).
Každý nový endpoint MUSÍ mať test izolácie (používateľ B nevidí/nezmení dáta A).

### A2. Spoločný účet a appky
- Jedna tabuľka `users`, jeden auth (FastAPI `/api/v1/auth/*`, JWT HS256: access 15 min, refresh 30 dní).
- Dáta appiek sa oddeľujú cez `app_id` (`adhd_tracker`, `food_diary`) alebo vlastné tabuľky s prefixom appky.
- Všetci používatelia majú prístup ku všetkým appkám. Zapínanie a vypínanie appiek per používateľ
  je **budúca požiadavka**: neimplementovať, ale nič nesmie brániť jej neskoršiemu pridaniu.
- Nová appka = nový FastAPI router + vlastné tabuľky + nový Django app + položka v prepínači appiek.
  Auth sa nemení.

### A3. Testy sú backpressure
- Žiadna spec nie je hotová bez zelených testov: `./scripts/test-food.sh` (od food-001) +
  existujúce testy (`cd server && make test`, `cd web_app && .venv/bin/python manage.py test`).
- Existujúce ADHD testy sa NESMÚ rozbiť ani vypnúť.
- Testy sú deterministické, offline a bez reálnych externých služieb. Server testy bežia nad SQLite
  in-memory, preto **žiadne Postgres-only funkcie** (unaccent, pg_trgm, JSONB operátory, ARRAY)
  v doménovej logike. Kód musí fungovať na SQLite aj PostgreSQL.
- E2E testy (Playwright) spúšťajú skutočný FastAPI + Django proti dočasnej SQLite DB.

### A4. Bezpečnosť
- Heslá: bcrypt (existujúci `auth_service`), min. 8 znakov na serveri aj v UI.
- Tajomstvá iba v `.env` (nikdy v gite); `.env.example` aktualizovať pri každej novej premennej.
- Zdravotné dáta sa nelogujú (ani text záznamov v request logoch na úrovni INFO).
- Formuláre v Django majú CSRF. HTMX požiadavky posielajú CSRF token.

### A5. Databáza a migrácie
- Server: SQLAlchemy 2 async + Alembic. Každá zmena schémy = nová Alembic migrácia s funkčným
  `upgrade` aj `downgrade`, kompatibilná so SQLite (batch mode) aj PostgreSQL.
- Nové modely sa registrujú v `server/app/models/__init__.py` (inak ich nenájde Alembic ani testy).
- Django web nemá doménové dáta, iba sessions.

### A6. Jazyk a štýl
- Identifikátory, komentáre a commit správy po anglicky. Specs a dokumentácia môžu byť po slovensky.
- UI texty cez i18n (pozri B4). Píš kód ako okolitý kód (rovnaké vzory, pomenovanie, hustota komentárov).

### A7. Závislosti
Nová závislosť vyžaduje zdôvodnenie v commite. Schválené pre Food diary: `htmx` (statický súbor,
bez CDN), `playwright` + `pytest-playwright` (iba dev/test), `babel` (iba dev, kompilácia .po bez gettextu).

### A8. Git
- Ralph pracuje iba na branch `food-diary` a pushuje iba ju. **Nikdy** nepushuje na `master` ani neprepisuje históriu (no force push).
- Jeden commit = jedna logická zmena, správa po anglicky v imperatíve.

---

## Časť B — Modul Server (FastAPI) + Web (Django)

### B1. Architektúra
- **Všetka doménová logika je vo FastAPI** (validácia, parsovanie, merge, autocomplete, export).
  Django iba zobrazuje a volá API. Android vo fáze 2 musí vedieť robiť všetko cez to isté API.
- Vrstvy servera: `routers/` (HTTP) → `services/` (logika) → `models/` (SQLAlchemy). Router neobsahuje
  doménovú logiku. Pydantic schémy v `schemas/`.
- Food API: prefix `/api/v1/food`, tag `food`, súbory `routers/food*.py`, `services/food_*.py`,
  `models/food.py`, `schemas/food.py`.
- API-first: každý endpoint má Pydantic request/response model (je v OpenAPI `/openapi.json`)
  s príkladom. Odpovede majú `schema_version: "1.0"`, ako existujúce endpointy.

### B2. Pripravenosť na sync (Android fáza 2)
Každá food entita má `id` (UUID string, môže ho poslať klient), `created_at`, `updated_at` (UTC)
a `deleted_at` (soft delete). Mazanie cez API = nastavenie `deleted_at`. Bežné čítanie vracia iba
nezmazané. Endpoint „zmeny od“ vracia aj zmazané (tombstones).

### B3. Web konzola (Django)
- Jedna konzola `console.adhdknight.com`, food pod `/food/`, ADHD na súčasných URL.
  Spoločný login, layout a prepínač appiek `ADHD | Food` v navigácii.
- Session obsahuje `token`, `refresh_token` a `user_email`. Pri 401 z API klient raz zavolá
  `/auth/refresh`, uloží nové tokeny a zopakuje request. Až keď zlyhá refresh, nasleduje odhlásenie
  s `?expired=1`. Session cookie platí 30 dní.
- Interaktivita: HTMX + minimum vanilla JS, bez build kroku a bez CDN (súbory vo `web_app/static/`).
- Responzívny dizajn, **mobil je primárne zariadenie**: ovládacie prvky min. 44 px, bez horizontálneho
  scrollu pri šírke 360 px.

### B4. Jazyk a čas
- UI jazyky: `sk` (default), `cs`, `en` (Django i18n, `gettext`). Voľba sa uloží v `users.language`
  a po prihlásení sa prenesie do session. Prekladá sa food časť a spoločný layout (navigácia, login,
  registrácia, účet). Ostatné ADHD stránky môžu ostať po slovensky.
- Časová zóna: `users.timezone`, default `Europe/Bratislava` (CET/CEST). Zmenu cez UI zatiaľ neimplementovať.
  „Dnes“ a zákaz budúcich dátumov sa počítajú v časovej zóne používateľa, **na serveri**.
- Dátum dňa = `YYYY-MM-DD` string. Časy merania = lokálny čas `HH:MM` bez zóny.

### B5. Účty
- Registrácia **iba na pozvánku** (`REGISTRATION_MODE=invite`, default). Pozvánku vytvorí CLI
  `server/scripts/create_invitation.py` a vypíše registračný link (SMTP neexistuje). Platnosť 7 dní,
  jednorazová. `REGISTRATION_MODE=open` zachová staré správanie (pre dev).
- Zmena hesla prihláseným používateľom (staré + nové heslo). Zabudnuté heslo rieši
  `server/scripts/reset_user_password.py`. Emailový reset je budúca požiadavka.
- Zmazanie účtu používateľom zmaže **celý zdieľaný účet vrátane ADHD dát** (cascade). Vyžaduje heslo
  a výslovné potvrdenie, že sa zmažú dáta všetkých appiek.

---

## Časť C — Modul ADHD Android

Pre `android_app/` platí bez zmeny `.specify/memory/constitution-adhd-android.md`.
Food diary specs NESMÚ meniť `android_app/`.

---

## Časť D — Modul Food diary (doména)

### D1. Deň
- Jeden deň na používateľa a dátum (`food_days`, unique `user_id + date`). Budúce dátumy sú zakázané.
- Vytvorenie existujúceho dňa → chyba „Deň už existuje“ (API 409 `day_exists`). Ak bol deň zmazaný
  (soft delete), vytvorenie ho obnoví prázdny.
- Deň sa vytvorí aj prázdny. Predvolený dátum je „dnes“.
- Mazanie dňa: **2 potvrdenia** v UI (druhé = prepísanie dátumu dňa). Mazanie jednotlivého záznamu: jedno ťuknutie, bez potvrdenia.

### D2. Kategórie záznamov (zoznamy, ľubovoľný počet záznamov)
| Kód | UI (sk) | Skupina autocomplete | Poznámka |
|---|---|---|---|
| `breakfast` | Raňajky | food | |
| `morning_snack` | Desiata | food | |
| `lunch` | Obed | food | |
| `afternoon_snack` | Olovrant | food | |
| `dinner` | Večera | food | |
| `after_dinner` | Po večeri | food | |
| `unassigned` | Nezaradené / počas dňa | food | aj pre ručné zadávanie |
| `medication` | Lieky | meds | |
| `supplement` | Doplnky | meds | |
| `sport` | Šport | sport | voliteľná intenzita 1–5 |
| `note` | Poznámky | — (bez autocomplete) | symptómy + zdravotná poznámka + poznámka |

Záznam: `text` (povinný, trim, max. 200 znakov), voliteľné `quantity` (desatinné > 0) a `unit`
(`ks`, `l`, `ml`, `g`, `kg`; žiadna jednotka = kusy), poradie `position`, `text_norm` (D5).

### D3. Hodnoty dňa (jedna hodnota za deň, všetky voliteľné)
- `sleep_quality`: 1 = zlý, 2 = priemer, 3 = ok.
- `stool`, `gas` (tráviace problémy stolica/vetry): 1–10, 1 = všetko OK, 10 = najhoršie.

### D4. Merania (viac za deň)
- Váha: `kg` 20–300 (1 desatinné miesto), voliteľný čas `HH:MM` a poznámka.
- Tlak: `systolic` 60–260, `diastolic` 30–160, `systolic > diastolic`, voliteľný `pulse` 30–220,
  čas `HH:MM` a poznámka. Rýchly zápis jedným reťazcom: `130/85`, `130/85 72`, `130/85 72 7:30`
  (parsovanie na serveri).

### D5. Normalizácia a autocomplete
- `text_norm` = text → trim → zlúčené medzery → malé písmená → bez diakritiky (Unicode NFKD,
  odstránené kombinujúce znaky), vypočítané v Pythone pri každom uložení.
- Autocomplete hľadá `text_norm` od začiatku textu alebo od začiatku ktoréhokoľvek slova, iba
  v skupine kategórie (food / meds / sport), iba nezmazané záznamy prihláseného používateľa.
  Zoraďuje podľa počtu výskytov (zostupne), pri zhode podľa posledného použitia. Zobrazí
  najčastejší pôvodný tvar textu pre daný `text_norm`. Max. 10 návrhov.
- Množstvo: ťuk na množstvo ponúkne najčastejšie množstvá (quantity + unit) použité pre daný
  `text_norm` + ručné zadanie.

### D6. Parsovanie množstva pri zadaní (iba zo začiatku textu)
`2 toasty` → 2 ks · `2x jablko` / `2× jablko` → 2 ks · `1/2 rohlika` → 0,5 ks · `.5 l kofoly` / `0,5 l kofoly` → 0,5 l ·
`0.7 l kompot` → 0,7 l · `200 g ryža` / `200g ryža` → 200 g. Číslo kdekoľvek inde v texte (`slane oplatky 20`)
ostáva súčasťou textu. Parser je čistá funkcia na serveri s unit testami.

### D7. Lieky a doplnky
Slovník `liek / doplnok` patrí používateľovi (podľa `text_norm`). Pri zadaní položky, ktorá nie je
v slovníku, sa UI spýta „liek alebo doplnok?“ a odpoveď uloží. Neskôr ju pozná a zaradí ju sama.
Opakovaná položka v jednom vstupe (`emanera, prestarium, emanera`) = 1 záznam s množstvom 2.

### D8. Import (najnižšia priorita)
Prvotný import histórie robí LLM mimo aplikácie podľa `docs/food/import-mapping.md`. Aplikácia
NEOPRAVUJE preklepy. Import v appke: vložený text TSV alebo CSV, merge s náhľadom
(pravidlá v spec food-011).

### D9. Export
CSV a JSON za zvolené obdobie, všetky kategórie a merania, iba vlastné dáta. Slúži na analýzu mimo appky.

---

## Ralph Wiggum workflow

### Zdroj práce
- Ralph spracúva **iba** súbory `specs/food-NNN-*.md` priamo v `specs/`.
  Podpriečinky `specs/NNN-*/` (ADHD) a `specs/food-000-input/` sú len referencia: **nikdy ich neimplementuj ani nemeň.**
- Vyber nedokončenú spec s najnižším číslom. Spec je dokončená, ak obsahuje riadok `## Status: COMPLETE`.
- Pred začatím si prečítaj `history.md` a relevantné `history/*.md`.
- Ak spec závisí od nedokončenej spec, najprv dokonči tú.

### Postup jednej iterácie
1. Prečítaj spec, súvisiaci kód a túto constitution.
2. Implementuj všetky funkčné požiadavky.
3. Napíš testy (unit / API / Django / e2e podľa spec) a spusti `./scripts/test-food.sh`, kým nie je zelený.
4. Over každé acceptance kritérium a zaškrtni ho v spec (`- [x]`).
5. Pridaj `## Status: COMPLETE` pod nadpis spec, pridaj 1 riadok do `history.md` a vytvor
   `history/YYYY-MM-DD--food-NNN-nazov.md` (rozhodnutia, problémy, poučenia).
6. Commitni a pushni na `food-diary`.
7. Vypíš `<promise>DONE</promise>`.

Ak nie si istý zadaním, vyber riešenie najbližšie tejto constitution, zapíš ho do sekcie
`## Implementation notes` v spec a pokračuj. Nezastavuj sa kvôli otázkam.

### NR_OF_TRIES
Na konci spec udržuj `<!-- NR_OF_TRIES: N -->`, pri každom pokuse ho zvýš o 1. Od 10 je spec príliš
veľká: rozdeľ ju na menšie `food-NNNa-*.md`, `food-NNNb-*.md` a do pôvodnej pridaj
`## Status: COMPLETE (rozdelená na food-NNNa, food-NNNb)`.

### Autonómia
YOLO Mode: ENABLED
Git Autonomy: ENABLED (iba branch `food-diary`)

### Completion signal
Všetky acceptance kritériá overené, všetky testy zelené, zmeny commitnuté a pushnuté →
`<promise>DONE</promise>`. Nikdy skôr.

---

## Governance
- Pri konflikte spec vs. constitution sa upravuje spec. Zmena constitution vyžaduje zdôvodnenie,
  dopad na specs a novú verziu podľa SemVer.
- Ralph constitution NEMENÍ.

**Version**: 2.0.0 | **Ratified**: 2026-06-26 | **Last Amended**: 2026-10-24
