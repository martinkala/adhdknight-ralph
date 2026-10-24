# Specification: food-010 — Viacjazyčné UI (sk / cs / en)

## Feature: Preklady food časti a spoločného layoutu, voľba jazyka v účte

### Overview
UI Food diary a spoločné časti konzoly (navigácia, login, registrácia, účet) budú v slovenčine
(default), češtine a angličtine. Jazyk sa ukladá v profile používateľa (`users.language`, food-002),
takže ho neskôr prevezme aj Android appka (constitution B4).

### User Stories
- Ako používateľ chcem prepnúť jazyk aplikácie v nastaveniach účtu.

---

## Functional Requirements

### FR-1: Django i18n infraštruktúra
- `LANGUAGE_CODE = "sk"`, `LANGUAGES = [("sk", "Slovenčina"), ("cs", "Čeština"), ("en", "English")]`,
  `LOCALE_PATHS = [BASE_DIR / "locale"]`, `USE_I18N = True`.
- Middleware (za `SessionMiddleware`) aktivuje jazyk zo `session["language"]`, inak `sk`.
  Neprihlásený používateľ (login, registrácia): jazyk z cookie `django_language` alebo `sk`.
- Súbory `web_app/locale/{sk,cs,en}/LC_MESSAGES/django.po` a skompilované `django.mo` sú **commitnuté**
  (deploy nespúšťa `compilemessages`).
- Kompilácia bez gettextu: `babel` v `web_app/requirements-dev.txt`, skript `web_app/scripts/compile_messages.sh`
  (`pybabel compile -d locale -D django`). Ak je dostupný gettext, `manage.py makemessages` funguje tiež.
  Zapíš postup do `docs/food/README.md`.

**Acceptance Criteria:**
- [ ] `.po` a `.mo` pre sk, cs, en existujú; `.mo` sú aktuálne (test porovná, že každý msgid z `.po` je v `.mo`)
- [ ] Django test: session `language=cs` → stránka má `<html lang="cs">`

### FR-2: Preklady
- Preložiť všetky texty v `web_app/food/` (šablóny, views, formuláre, hlášky chýb z API kódov ako
  `day_exists`, `future_date`, `bp_range`, `invite_invalid`, …), v `core/templates/base.html`,
  `login.html`, `register.html`, `account.html` a vo views, ktoré tieto stránky renderujú.
- Názvy kategórií (D2), mesiacov a dní v týždni (kalendár), formát dátumu (sk/cs `24. 10. 2026`, en `24 Oct 2026`)
  a desatinná čiarka (sk/cs) vs. bodka (en) pri zobrazení čísel.
- Zvyšné ADHD stránky (dashboard, trend, info, debug) môžu ostať po slovensky.
- Test pokrytia: žiadny prázdny `msgstr` v sk a cs `.po` súboroch.

**Acceptance Criteria:**
- [ ] Unit test: sk a cs `.po` nemajú prázdne `msgstr` (okrem hlavičky) ani `fuzzy` záznamy
- [ ] Django test: obrazovka dňa v sk obsahuje „Raňajky“, v cs „Snídaně“, v en „Breakfast“
- [ ] Django test: chyba `day_exists` sa zobrazí v jazyku session

### FR-3: Voľba jazyka
- Stránka Účet: výber jazyka (`data-testid="language-select"`), uloží cez `PATCH /api/v1/user/settings`,
  aktualizuje session a cookie `django_language`, stránka sa prekreslí v novom jazyku.
- Po logine sa jazyk načíta z API (food-002 FR-5).
- Login a registrácia majú malý prepínač jazyka (iba cookie).

**Acceptance Criteria:**
- [ ] e2e: prepnutie na en → navigácia a obrazovka dňa sú po anglicky; odhlásenie a prihlásenie → stále en
- [ ] e2e: e2e testy z predchádzajúcich specs prechádzajú vo všetkých jazykoch (selektory `data-testid`), pusti smoke test v cs a en

---

## Success Criteria
- Používateľ nenájde vo food časti ani v spoločnom layoute nepreložený text.

## Dependencies
- food-009

## Assumptions
- Čeština a angličtina sú preklady pripravené agentom. Používateľ ich neskôr môže upraviť v `.po`.

---

## Completion Signal

### Implementation Checklist
- [ ] i18n nastavenia + middleware
- [ ] `.po` / `.mo` sk, cs, en + compile skript
- [ ] Preklady food, layoutu, login, registrácie, účtu
- [ ] Voľba jazyka

### Testing Requirements
- [ ] `./scripts/test-food.sh` → exit 0

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

<!-- NR_OF_TRIES: 0 -->
