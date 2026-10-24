# Specification: food-008 — Prehľad: kalendár a zoznam

## Status: COMPLETE

## Feature: Mesačný kalendár s farbou podľa tráviacich problémov a zoznamový pohľad (UC1)

### Overview
Domovská obrazovka Food diary je mesačný kalendár. Bodka značí existujúci deň, farba ukazuje
horšiu z hodnôt stolica/vetry. Zoznamový pohľad ukazuje dni pod sebou so stručným obsahom.

### User Stories
- Ako používateľ chcem na prvý pohľad vidieť, ktoré dni mám zapísané a kedy som mal problémy.
- Ako používateľ chcem rýchlo otvoriť ktorýkoľvek deň.

---

## Functional Requirements

### FR-1: API
- `GET /api/v1/food/calendar?month=YYYY-MM` → `{schema_version, month, today, days: [{date, stool, gas, entry_count}]}`,
  iba existujúce nezmazané dni daného mesiaca. Neplatný mesiac → 422.
- `GET /api/v1/food/days?page=1&page_size=30` → `{schema_version, page, page_size, total, days: [DaySummary]}`,
  zoradené od najnovšieho. `DaySummary = {date, stool, gas, sleep_quality, weights: [kg...], bp: ["130/85"...],
  food_preview: [text...] (prvých 8 food textov v poradí sekcií), entry_count}`. `page_size` 1–100.

**Acceptance Criteria:**
- [x] API testy: kalendár vráti iba dni daného mesiaca a používateľa, zmazané nie
- [x] API testy: stránkovanie (`total`, poradie, posledná stránka)
- [x] API testy izolácie pre oba endpointy

### FR-2: Kalendár `/food/` (nahrádza dočasnú stránku z food-004)
- Mriežka mesiaca, týždeň začína pondelkom (`data-testid="calendar"`, bunky `data-testid="cal-day"`
  s atribútom `data-date`). Navigácia ‹ › medzi mesiacmi (`data-testid="cal-prev"`, `"cal-next"`).
  Budúce mesiace sú nedostupné. Dnešok je zvýraznený.
- Bodka (`data-testid="cal-dot"`) iba pri existujúcom dni. Farba podľa `max(stool, gas)`:
  1–3 zelená, 4–6 oranžová, 7–10 červená, bez hodnôt sivá (`data-severity="ok|mid|bad|none"`).
  Legenda pod kalendárom. Farby majú dostatočný kontrast a nie sú jediný nosič informácie
  (`title`/`aria-label` s hodnotami).
- Ťuk na existujúci deň → detail dňa. Ťuk na neexistujúci minulý deň alebo dnešok → vytvorí ho a otvorí
  (rovnako ako „Dnes“). Budúce dni nie sú klikateľné.
- Nad kalendárom ostane tlačidlo „Dnes“ (`data-testid="open-today"`) a prepínač Kalendár | Zoznam (`data-testid="view-toggle"`).
- URL `?month=YYYY-MM` drží zvolený mesiac. Návrat z detailu dňa vráti na jeho mesiac.

**Acceptance Criteria:**
- [x] e2e: dni s (stool 2, gas 3), (4, 1), (2, 9) a deň bez hodnôt → severity ok, mid, bad, none
- [x] e2e: ťuk na neexistujúci minulý deň ho vytvorí a otvorí detail
- [x] e2e: budúci deň nemá odkaz; `cal-next` je v aktuálnom mesiaci neaktívne
- [x] e2e (mobil 360 px): mriežka sa zmestí bez horizontálneho scrollu, bunky ≥ 44 px
- [x] Django test: `?month=2026-02` vykreslí február s 28 dňami a správnym prvým dňom v týždni

### FR-3: Zoznam `/food/list/`
- Dni od najnovšieho, 30 na stránku, stránkovanie (`data-testid="list-day"`, `"list-next-page"`).
- Riadok: dátum + deň v týždni, bodka závažnosti, stolica/vetry („4/6“), spánok, váha, tlak, náhľad jedál
  (skrátený na 1–2 riadky). Ťuk otvorí detail.

**Acceptance Criteria:**
- [x] e2e: 35 dní → prvá stránka 30, druhá 5, poradie od najnovšieho
- [x] Django test: riadok obsahuje `food_preview` a stolicu/vetry

---

## Success Criteria
- Otvorenie ľubovoľného dňa v posledných 3 mesiacoch: ≤ 3 ťuknutia.

## Dependencies
- food-005

## Assumptions
- Názvy mesiacov a dní sa lokalizujú cez Django (food-010 doplní preklady).

---

## Completion Signal

### Implementation Checklist
- [x] Calendar + days list API
- [x] Kalendár na `/food/`
- [x] Zoznam `/food/list/`

### Testing Requirements
- [x] `./scripts/test-food.sh` → exit 0
- [x] Žiadne JS chyby v konzole

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

## Implementation notes
- `severity` (`ok|mid|bad|none`) is computed on the server and added to both calendar days and `DaySummary`
  (constitution B1: Android gets the same bands without its own logic).
- `month` is optional in `GET /calendar` (default = the user's current month), so the web needs one call
  for both the grid and `today`. A future month in the web URL redirects to `/food/`.
- Missing past days in the grid are submit buttons of one form posting to `days/new/` with `open_existing=1`
  (a day created in the meantime just opens). The "Add a day" date form stays below the calendar
  for days in older months.
- The day screen has a "‹ Calendar" link to `/food/?month=YYYY-MM`; deleting a day returns to its month.

<!-- NR_OF_TRIES: 1 -->
