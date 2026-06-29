# Quickstart: App Configuration Layer – Validačný sprievodca

**Feature**: 005-app-config-layer | **Date**: 2026-06-28

Tento dokument popisuje validačné scenáre pre manuálne overenie feature po implementácii. Nie je určený na automatizované testy — tie sú v `AppConfigLoaderTest.kt`.

## Prerekvizity

- Android Studio s nakonfigurovaným emulátором (API 26+) alebo fyzické zariadenie
- Build variant: `debug`
- Logcat filter: `tag:AppConfig`

---

## S1 — Základné načítanie konfigurácie (US1, US3)

**Cieľ**: Overiť, že aplikácia načíta `app_config.json` a zaloguje audit.

**Kroky**:
1. Zabezpečiť, že `assets/app_config.json` existuje s hodnotou `"sleep": 20.0` (iná ako default 15.0)
2. Spustiť aplikáciu
3. Otvoriť Logcat, filter `AppConfig`

**Očakávaný výsledok**:
- Log obsahuje `"config loaded successfully"` alebo `"loaded from config: sleep=20.0"`
- Žiadna `Exception` v Logcat
- Aplikácia sa spustila normálne

---

## S2 — Zmena váhy elementu sa prejaví vo výpočte (US1)

**Cieľ**: SC-001 — zmena parametra nadobudne účinnosť po reštarte.

**Kroky**:
1. Zaznamenať baseline ADHD index cez Tracker (vyplniť, uložiť, zobraziť Home)
2. Zmeniť `"sleep": 20.0` v `app_config.json` (rebuild a reinstall nie je nutný ak je len asset zmenený — postačí `./gradlew installDebug`)
3. Zadať rovnaké hodnoty ako v kroku 1
4. Porovnať ADHD index

**Očakávaný výsledok**: Index sa líši od baseline (vyšší, ak bol sleep plne splnený, pretože vyššia váha = väčší vplyv).

---

## S3 — Chýbajúci konfiguračný súbor → fallback (US2)

**Cieľ**: Aplikácia nesmie crashovať keď súbor chýba.

**Kroky**:
1. Premenovať `app_config.json` na `app_config.json.bak` (alebo vytvoriť prázdny build bez assets)
2. Spustiť aplikáciu

**Očakávaný výsledok**:
- Aplikácia sa spustí bez pádu
- Logcat filter `AppConfig` obsahuje `"config not found, using defaults"`
- Výpočty zodpovedajú pôvodným hardcoded hodnotám

---

## S4 — Neplatný JSON → fallback (US2)

**Cieľ**: Poškodený súbor nesmie crashovať aplikáciu.

**Kroky**:
1. Vložiť do `app_config.json` neplatný obsah: `{ "weights": { invalid`
2. Spustiť aplikáciu

**Očakávaný výsledok**:
- Aplikácia sa spustí
- Logcat obsahuje `"config parse error"` a `"using defaults"`
- Žiadna chybová hláška pre používateľa

---

## S5 — Čiastočná konfigurácia (US2)

**Cieľ**: FR-006 — chýbajúce polia dostanú fallback, prítomné polia sa použijú.

**Kroky**:
1. Nastaviť `app_config.json` len s `adaptation` sekciou (ostatné sekcie vynechať):
   ```json
   { "adaptation": { "alpha": 0.05 } }
   ```
2. Spustiť aplikáciu

**Očakávaný výsledok**:
- Logcat: `alpha` načítané z konfigurácie; váhy, ASRS, notifikácie logujú `"using default"`
- Aplikácia funguje normálne

---

## S6 — Neplatná hodnota → per-parameter fallback (US2)

**Cieľ**: FR-006 — záporná váha alebo alpha > 1 sa nahradí defaultom.

**Kroky**:
1. Nastaviť `"sleep": -5.0` a `"alpha": 2.5`
2. Spustiť aplikáciu

**Očakávaný výsledok**:
- Logcat: `"invalid value for sleep (-5.0), using default 15.0"` a `"invalid value for alpha (2.5), using default 0.2"`
- Výpočty používajú default hodnoty pre tieto parametre

---

## S7 — Audit log identifikuje zdroj každého parametra (US3)

**Cieľ**: SC-005 — vývojár vie do 30s potvrdiť aktívnu konfiguráciu.

**Kroky**:
1. Nastaviť čiastočnú konfiguráciu (napr. len `weights` sekcia so všetkými hodnotami)
2. Spustiť aplikáciu
3. Filtrovať Logcat na `AppConfig`

**Očakávaný výsledok**:
- Pre každý parameter je viditeľný log riadok s jeho hodnotou a zdrojom (`"config"` alebo `"default"`)
- Celkový čas od spustenia po zobrazenie logu < 30 sekúnd

---

## S8 — Klasifikácia elementov cez konfiguráciu (US1, acceptance scenario 3)

**Cieľ**: Zmena `negative_keys` sa prejaví v sub-indexoch.

**Kroky**:
1. Nastaviť `"negative_keys": ["stress_work", "stress_personal", "alcohol"]` (bez `caffeine`)
2. Zadať denné hodnoty kde caffeine = 1 (konzumovaná)
3. Zobraziť Home → Pozitívne / Negatívne hodnoty

**Očakávaný výsledok**: `caffeine` prispeje do pozitívneho sub-indexu (nie negatívneho).

---

## Edge case — Váhy s nesprávnou sumou sa normalizujú

**Kroky**:
1. Nastaviť váhy kde suma = 120 (napr. zvýšiť `sleep` na 35)
2. Spustiť aplikáciu, zadať hodnoty, overiť ADHD index

**Očakávaný výsledok**:
- Logcat: informácia o normalizácii váh
- Index zostane v rozsahu 0-100 (normalizácia zaručuje správnu váhovú sumu)

---

## Referencia

- Schéma konfiguračného súboru: [contracts/app_config_schema.md](contracts/app_config_schema.md)
- Dátový model: [data-model.md](data-model.md)
- Unit testy: `src/test/.../config/AppConfigLoaderTest.kt`
