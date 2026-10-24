# Specification: food-002 — Účty: pozvánky, dlhá session, zmena hesla, zmazanie účtu, nastavenia

## Feature: Zmeny spoločného účtu potrebné pre Food diary

### Overview
Food diary je osobný zdravotný denník, preto sa registruje iba na pozvánku. Zapisuje sa doň počas
celého dňa, takže web session nesmie vypršať po 15 minútach. Zmeny sú v spoločnom auth, takže sa
dotknú aj ADHD konzoly (constitution A2, B3, B5).

### User Stories
- Ako prevádzkovateľ chcem pozvať človeka CLI príkazom, aby sa nemohol zaregistrovať ktokoľvek.
- Ako používateľ chcem ostať prihlásený celé dni, aby som nemusel pri každom zápise zadávať heslo.
- Ako používateľ chcem zmeniť heslo a zmazať svoj účet.

---

## Functional Requirements

### FR-1: Refresh token vo web session
- Login (`core/views.login_view`) ukladá do session `token`, `refresh_token`, `user_email`.
- Nový helper v `core/api_client.py` (napr. `call_with_refresh(request, fn, *args)`): pri výsledku
  `unauthorized` zavolá raz `POST /api/v1/auth/refresh`, uloží nový pár tokenov do session
  a zopakuje volanie. Ak refresh zlyhá → `session.flush()` a redirect na `login?expired=1`.
- Používajú ho všetky existujúce ADHD views (dashboard, trend, account, debug) aj všetky food views.
- `SESSION_COOKIE_AGE = 30 * 24 * 3600`, `SESSION_SAVE_EVERY_REQUEST = True`.

**Acceptance Criteria:**
- [ ] Django test (mock httpx): API vráti 401, refresh 200 → view vráti 200 a session má nové tokeny
- [ ] Django test: API 401 a refresh 401 → redirect na `/login/?expired=1` a session je prázdna
- [ ] Django test: po logine je v session `refresh_token`
- [ ] `SESSION_COOKIE_AGE` je 30 dní

### FR-2: Pozvánky
- Tabuľka `invitations`: `id` (UUID), `token_hash` (SHA-256 hex, unique), `note` (nullable, max. 200),
  `created_at`, `expires_at`, `used_at` (nullable), `used_by_user_id` (FK users, `SET NULL`, nullable).
  Alembic migrácia (upgrade aj downgrade).
- Settings: `registration_mode: str = "invite"` (`invite` | `open`), `web_base_url: str = "http://127.0.0.1:8000"`.
  Doplniť do `server/.env.example`.
- CLI `server/scripts/create_invitation.py [--days 7] [--note TEXT]` (štýl ako `reset_user_password.py`):
  vygeneruje token (`secrets.token_urlsafe(32)`), uloží iba hash a vypíše
  `{web_base_url}/register/?invite=<token>` a dátum expirácie.
- `POST /api/v1/auth/register` prijíma voliteľné `invite_token`. V režime `invite`:
  chýbajúci token → 403 `{"detail": "invite_required"}`, neplatný/expirovaný/použitý → 403 `{"detail": "invite_invalid"}`.
  Úspešná registrácia nastaví `used_at` a `used_by_user_id` v tej istej transakcii (token sa nedá použiť 2×).
  V režime `open` sa token ignoruje (staré správanie).
- Server testy: autouse fixture v `tests/conftest.py` nastaví pre testy `registration_mode="open"`
  (existujúce testy registrujú bez pozvánky a nesmú sa meniť). Testy pozvánok prepnú na `invite`.
- Django `/register/`: číta `?invite=` do skrytého poľa. Bez pozvánky zobrazí info
  „Registrácia je možná iba na pozvánku“ (`data-testid="invite-required"`) a formulár neukáže.
  Chyby `invite_invalid` / `invite_required` majú zrozumiteľnú hlášku.

**Acceptance Criteria:**
- [ ] API test: register bez tokenu v režime invite → 403 `invite_required`
- [ ] API test: platný token → 201; ten istý token druhýkrát → 403 `invite_invalid`
- [ ] API test: expirovaný token → 403 `invite_invalid`
- [ ] API test: v režime open register bez tokenu → 201
- [ ] Unit test CLI: vytvorí riadok s hashom (nie plain tokenom) a vypíše URL s tokenom
- [ ] Migrácia: `alembic upgrade head` a `alembic downgrade -1` prejdú na SQLite
- [ ] e2e: pozvánka (vytvorená priamo v teste cez CLI alebo DB) → registrácia cez UI → login funguje
- [ ] e2e harness (food-001) beží v režime `invite`, `user_factory` vytvára používateľov cez pozvánku

### FR-3: Zmena hesla
- `POST /api/v1/auth/change-password` (auth) `{old_password, new_password}` → 204;
  zlé staré heslo → 400 `{"detail": "wrong_password"}`; nové < 8 znakov → 422.
- Django stránka Účet: formulár zmeny hesla (`data-testid="change-password-form"`), úspech/chyba ako hláška.

**Acceptance Criteria:**
- [ ] API testy: 204, 400 `wrong_password`, 422; po zmene funguje login iba s novým heslom
- [ ] Django test: formulár zavolá API a zobrazí úspech

### FR-4: Zmazanie účtu
- `DELETE /api/v1/user/me` (auth) body `{password, confirm: "DELETE"}` → 204. Zlé heslo → 400
  `wrong_password`; chýbajúce/zlé `confirm` → 422.
- Zmaže používateľa a **všetky** jeho dáta: ADHD (`tracking_days` s `element_values` a `daily_indices`,
  `weight_configs`, `sync_records`) aj food tabuľky (keď budú existovať: food-003 sa musí napojiť).
  Mazanie je explicitné v service vrstve (`services/account_service.py`), nespolieha sa na DB cascade,
  pretože SQLite bez `PRAGMA foreign_keys=ON` cascade nevynúti.
- Django Účet: sekcia „Zmazať účet“ (`data-testid="delete-account"`) s textom, že sa zmažú **dáta
  ADHD aj Food**, pole heslo, checkbox potvrdenia. Po úspechu `session.flush()` a redirect na login s hláškou.

**Acceptance Criteria:**
- [ ] API test: používateľ s ADHD dátami (sync batch) → DELETE → v DB nie je user ani žiadny jeho riadok v ADHD tabuľkách
- [ ] API test: dáta iného používateľa ostali nedotknuté
- [ ] API test: zlé heslo → 400, bez `confirm` → 422
- [ ] Django test: úspešné zmazanie vyprázdni session

### FR-5: Nastavenia používateľa (jazyk, časová zóna)
- Stĺpce `users.language` (`sk`|`cs`|`en`, default `sk`, NOT NULL, server_default) a `users.timezone`
  (default `Europe/Bratislava`, NOT NULL, server_default). Alembic migrácia.
- `GET /api/v1/user/settings` → `{schema_version, language, timezone}`;
  `PATCH /api/v1/user/settings` `{language}` → 200 (neplatný jazyk → 422). Timezone sa zatiaľ meniť nedá.
- Django po logine načíta settings a uloží `language` do session (použije food-010).

**Acceptance Criteria:**
- [ ] API testy GET/PATCH, 422 pre `de`
- [ ] Existujúci používatelia po migrácii majú `sk` a `Europe/Bratislava`

---

## Success Criteria
- Nikto sa nezaregistruje bez pozvánky. Prihlásený používateľ ostane prihlásený 30 dní pri aktívnom používaní.

## Dependencies
- food-001

## Assumptions
- ADHD Android „Registrovať“ prestane fungovať v režime invite. Je to odsúhlasené (clarification round 3, C3).
- Monitoring účet existuje a neregistruje sa (synthetic checks sa iba prihlasujú).

---

## Completion Signal

### Implementation Checklist
- [ ] Refresh v session + 30-dňová session
- [ ] Invitations: model, migrácia, CLI, register, Django register
- [ ] Change password API + UI
- [ ] Delete account API + UI
- [ ] User settings API + migrácia

### Testing Requirements
- [ ] `./scripts/test-food.sh` → exit 0
- [ ] Všetky existujúce ADHD testy zelené
- [ ] OpenAPI obsahuje nové endpointy (rozšír `tests/api/test_openapi.py`)

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

<!-- NR_OF_TRIES: 0 -->
