# Specification: food-003 — Dátový model a čisté doménové funkcie

## Status: COMPLETE

## Feature: Food tabuľky, migrácia a parsery (normalizácia, množstvo, tlak, „dnes“)

### Overview
Základ food domény na serveri: SQLAlchemy modely, Alembic migrácia a čisté funkcie, na ktorých
stoja API a UI v ďalších specs. Bez HTTP endpointov. Pravidlá sú v constitution časti D a B2.

### User Stories
- Ako vývojár chcem jednoznačný a otestovaný dátový model, aby ďalšie specs iba pridávali endpointy a UI.

---

## Functional Requirements

### FR-1: Modely (`server/app/models/food.py`)
Všetky tabuľky: `id` String(36) UUID PK (default `uuid4`, môže prísť od klienta), `created_at`,
`updated_at` (DateTime tz, UTC, `onupdate`), `deleted_at` (DateTime tz, nullable).

| Tabuľka | Stĺpce | Obmedzenia / indexy |
|---|---|---|
| `food_days` | `user_id` FK users, `date` String(10) `YYYY-MM-DD`, `sleep_quality` Int null (1–3), `stool` Int null (1–10), `gas` Int null (1–10) | unique (`user_id`,`date`); index (`user_id`,`date`) |
| `food_entries` | `day_id` FK food_days, `user_id` FK users (denormalizované kvôli autocomplete), `category` String(30), `text` String(200), `text_norm` String(200), `quantity` Numeric(10,3) null, `unit` String(5) null, `intensity` Int null (1–5, iba `sport`), `position` Int | index (`user_id`,`category`,`text_norm`); index (`day_id`) |
| `food_weights` | `day_id`, `user_id`, `kg` Numeric(5,1), `measured_at` String(5) null `HH:MM`, `note` String(200) null | index (`day_id`) |
| `food_blood_pressures` | `day_id`, `user_id`, `systolic` Int, `diastolic` Int, `pulse` Int null, `measured_at` String(5) null, `note` String(200) null | index (`day_id`) |
| `food_med_dictionary` | `user_id`, `text_norm` String(200), `display_text` String(200), `kind` String(12) (`medication`\|`supplement`) | unique (`user_id`,`text_norm`) |

- `category` je jedna z hodnôt constitution D2; `unit` ∈ {`ks`,`l`,`ml`,`g`,`kg`} alebo null.
- Konštanty kategórií a skupín (`FOOD_CATEGORIES`, `MEDS_CATEGORIES`, `SPORT_CATEGORIES`, `NOTE_CATEGORIES`,
  `CATEGORY_GROUP`) v `server/app/services/food_constants.py`, jediný zdroj pravdy pre ďalšie specs.
- Modely zaregistrované v `app/models/__init__.py`.
- Mazanie účtu (food-002 `account_service`) maže aj všetky food tabuľky používateľa.

**Acceptance Criteria:**
- [x] Alembic migrácia `add_food_tables`: `upgrade head` aj `downgrade -1` prejdú na SQLite (test v `tests/unit`)
- [x] Unique (`user_id`,`date`) vynútené: druhý insert rovnakého dňa → IntegrityError
- [x] Test: zmazanie účtu odstráni food riadky používateľa a nechá food riadky iného používateľa
- [x] `tests/conftest.py` vytvorí aj food tabuľky (cez `Base.metadata`)

### FR-2: Normalizácia textu (`services/food_text.py`)
- `clean_text(s)`: trim, zlúčené biele znaky na jednu medzeru.
- `normalize(s)`: `clean_text`, malé písmená (`casefold`), NFKD a odstránenie kombinujúcich znakov.

**Acceptance Criteria:**
- [x] `normalize("  Smažený   Tuniak ")` == `"smazeny tuniak"`
- [x] `normalize("Ryža")` == `normalize("ryza")` == `"ryza"`; `normalize("ČOKOLÁDA")` == `"cokolada"`
- [x] `clean_text("chipsy ")` == `"chipsy"`

### FR-3: Rozdelenie vstupu na záznamy (`services/food_text.py`)
`split_entries(raw) -> list[str]`: delí podľa čiarky a nového riadku, každú časť `clean_text`,
prázdne zahodí. **Neopravuje preklepy.**

**Acceptance Criteria:**
- [x] `split_entries("kolac 2 perniky, ")` == `["kolac 2 perniky"]`
- [x] `split_entries("kava,cola")` == `["kava", "cola"]`
- [x] `split_entries("a\nb, ,c")` == `["a","b","c"]`

### FR-4: Parser množstva (`services/food_quantity.py`)
`parse_quantity(text) -> (quantity: Decimal | None, unit: str | None, text: str)` iba zo začiatku textu
(constitution D6). Desatinná čiarka aj bodka; zlomok `a/b`; `x` alebo `×` hneď za číslom; jednotky
`ks, l, ml, g, kg` (aj bez medzery `200g`). Ak by po odobratí množstva ostal prázdny text, množstvo
sa nerozpozná (celý vstup je text).
`merge_duplicates(items)`: rovnaký `normalize(text)` v jednom vstupe → 1 položka so súčtom množstiev
(chýbajúce množstvo = 1 ks), ak sa zhodujú jednotky (inak ostanú zvlášť).

**Acceptance Criteria (unit testy, každý riadok = test):**
- [x] `"2 toasty"` → (2, None, "toasty")
- [x] `"2x jablko"`, `"2× jablko"`, `"2 x jablko"` → (2, None, "jablko")
- [x] `"1/2 rohlika"` → (0.5, None, "rohlika")
- [x] `".5 l kofoly"`, `"0,5 l kofoly"`, `"0.5l kofoly"` → (0.5, "l", "kofoly")
- [x] `"0.7 l ceresnovy kompot"` → (0.7, "l", "ceresnovy kompot")
- [x] `"200 g ryza"`, `"200g ryza"` → (200, "g", "ryza")
- [x] `"slane oplatky 20"` → (None, None, "slane oplatky 20")
- [x] `"3"` → (None, None, "3"); `"pho bo"` → (None, None, "pho bo")
- [x] `"4x after eight - cokolada"` → (4, None, "after eight - cokolada")
- [x] `merge_duplicates` na `["emanera","prestarium","emanera"]` → emanera množstvo 2, prestarium bez množstva

### FR-5: Parser tlaku (`services/food_measurements.py`)
`parse_blood_pressure(raw) -> {systolic, diastolic, pulse|None, measured_at|None}` alebo `ValueError`
s kódom chyby (`bp_format`, `bp_range`). Formáty: `130/85`, `130/85 72`, `130/85 72 7:30`, `130/85 7:30`
(čas sa rozpozná podľa `:`). Validácia podľa constitution D4. Čas sa normalizuje na `HH:MM`.
`validate_weight(kg)`: 20–300, zaokrúhlenie na 1 desatinné miesto, inak `ValueError("weight_range")`.

**Acceptance Criteria:**
- [x] `"130/85"` → 130, 85, None, None; `"130/85 72 7:30"` → 130, 85, 72, "07:30"; `"130/85 7:30"` → pulz None, čas "07:30"
- [x] `"145/02"` → `bp_range`; `"85/130"` → `bp_range` (sys musí byť > dia); `"abc"` → `bp_format`
- [x] `validate_weight(80.64)` → 80.6; `validate_weight(10)` → `weight_range`

### FR-6: „Dnes“ podľa časovej zóny (`services/food_time.py`)
`today_for(user) -> date` podľa `users.timezone` (zoneinfo), `is_future(date_str, user) -> bool`.
Funkcie berú voliteľný `now` (pre testy).

**Acceptance Criteria:**
- [x] Pre `now = 2026-10-24T22:30Z` a `Europe/Bratislava` (CEST, UTC+2) je dnes `2026-10-25`
- [x] Pre `now = 2026-12-31T22:59Z` (CET, UTC+1) je dnes `2026-12-31`, pre `23:01Z` je `2027-01-01`
- [x] `is_future` vráti True pre zajtrajšok, False pre dnešok

---

## Success Criteria
- Doménové pravidlá z constitution D2–D6 sú zachytené v kóde a pokryté unit testami.

## Dependencies
- food-002 (account_service, users.timezone)

## Assumptions
- Numeric na SQLite sa vracia ako Decimal/float. Testy porovnávajú hodnoty číselne.

## Implementation notes
- Index (`user_id`,`date`) na `food_days` netvorím zvlášť: unique constraint `uq_food_days_user_date`
  už je index (zbytočná duplicita na PostgreSQL).
- FK `day_id` aj `user_id` majú `ON DELETE CASCADE`, ale `delete_account` maže food tabuľky explicitne
  (SQLite bez `PRAGMA foreign_keys` cascade nevynucuje).
- `parse_quantity` vracia pre kusy (`ks` alebo bez jednotky) `unit=None` (constitution: žiadna jednotka = kusy).
  Nulové množstvo (`0 jablk`) a delenie nulou (`1/0`) sa nerozpoznajú, celý vstup ostane textom.
  Zlomky sa zaokrúhľujú na 3 desatinné miesta (Numeric(10,3)).
- `merge_duplicates` berie `ParsedItem` alebo reťazce (tie najprv prejdú `parse_quantity`); položka bez
  duplikátu si nechá množstvo `None`.
- Chyby parsera tlaku/váhy sú `MeasurementError(ValueError)` s atribútom `code` (`bp_format`, `bp_range`,
  `weight_range`, `time_format`). Neplatný čas v rýchlom zápise tlaku (`25:00`) = `bp_format`.
- `today_for` pri neznámej časovej zóne používa `Europe/Bratislava`.
- Existujúci test migrácie food-002 teraz robí downgrade na `187ee05ae8ff` (namiesto `-1`), lebo head je food-003.

---

## Completion Signal

### Implementation Checklist
- [x] `models/food.py` + registrácia + migrácia
- [x] `food_constants.py`, `food_text.py`, `food_quantity.py`, `food_measurements.py`, `food_time.py`
- [x] Napojenie na mazanie účtu

### Testing Requirements
- [x] `./scripts/test-food.sh` → exit 0
- [x] Všetky acceptance kritériá FR-2 až FR-6 majú vlastný unit test

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

<!-- NR_OF_TRIES: 1 -->
