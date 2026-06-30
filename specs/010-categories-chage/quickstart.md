# Quickstart & Validation Guide: Unified Entity Tree (010-categories-chage)

**Date**: 2026-06-30 | **Data model**: [data-model.md](data-model.md)

Tento dokument popisuje **validačné scenáre** — ako overiť, že implementácia feature 010 funguje správne, bez písania testov. Každý scenár je nezávisle overiteľný na emulátore alebo fyzickom zariadení.

---

## Prerekvizity

- Android Studio s Kotlin 1.9+
- Zariadenie / emulátor so API 26+
- Existujúca DB s aspoň 1 záznamom (pre SC-001)
- Build príkaz: `./gradlew :app:assembleDebug` z `android_app/`
- `JAVA_HOME=/home/martin/.local/share/JetBrains/Toolbox/apps/android-studio/jbr`

---

## SC-001: Žiadna dátová strata po migrácia 3→4

**Cieľ**: Overenie, že Room AutoMigration 3→4 neporuší existujúce záznamy.

**Postup**:
1. Nainštalovať APK so starou verziou (pred feature 010)
2. Vyplniť aspoň 1 deň v Trackeri, uložiť
3. Nainštalovať APK s feature 010 (bez uninstall — App store update simulácia)
4. Otvoriť HomeScreen → dni z kroku 2 musia byť stále viditeľné
5. Otvoriť Weekly Trend → bar chart s existujúcimi dátami

**Očakávaný výsledok**: Všetky záznamy viditeľné, žiadna crash, denný index zobrazený rovnako ako pred update.

---

## SC-002: Numerická ekvivalentnosť indexu

**Cieľ**: Denný index vypočítaný novou logikou musí byť ≤ ±0.01 od predošlého pre rovnaké vstupy.

**Postup**:
1. Vybrať deň s existujúcimi dátami v HomeScreen
2. Zapísať zobrazený index (napr. `73.4`)
3. Po inštalácii feature 010 otvoriť ten istý deň
4. Porovnať index — musí byť v rozsahu `73.39–73.41`

**Manuálny výpočet pre overenie** (príklad pre deň so zapnutým `sleep` a `stress_work`):
```
sleep (root, weight=15, impact=1, value=1.0): 15 × 1.0 = 15.0
lifestyle group (weight=42):
  stress_work (weight=13, impact=-1, value=0.5): effective = 1-0.5 = 0.5
  group_avg = 13×0.5 / 13 = 0.5
  contribution = 0.5 × 42 = 21.0
total = (15.0 + 21.0) / (15 + 42) × 100 = 63.2
```

---

## SC-003: Rovnaký počet trackovateľných entít v Trackeri

**Cieľ**: Tracker musí zobrazovať rovnaké entity ako pred refaktorom.

**Postup**:
1. Otvoriť Tracker pred feature 010 → spočítať entity (switches + sliders)
2. Po inštalácii feature 010 otvoriť Tracker → spočítať entity
3. Počet musí byť rovnaký

**Predpokladaný zoznam** (overiteľný z `entities.yaml` po zmene):
- Celkový pocit (slider)
- Spánok (switch)
- Fyzická aktivita (slider)
- Pracovný stres (slider)
- Osobný stres (slider)
- Mindfulness (switch)
- Závislosti (slider)
- Prokrastinácia (slider)
- Kofeín (slider)
- Alkohol (slider)
- Príjem bielkovín (switch)
- Vitamíny (switch)
- Pomodoro (switch)

---

## SC-004: Top-level kategória trackable — `physical_activity`

**Cieľ**: Overiť, že `physical_activity` (root node s `impact: 1`) sa zobrazuje v Trackeri a správne prispieva k indexu.

**Postup**:
1. Otvoriť Tracker → nájsť „Fyzická aktivita"
2. Zapnúť switch / nastaviť slider na maximum
3. Uložiť deň (automaticky)
4. HomeScreen → index by mal byť vyšší ako bez `physical_activity`

**Verifikácia logiky** (D4 z research.md):
- `physical_activity` je root node bez aktívnych potomkov → prispieva priamo
- `weight = 11.0`, `impact = 1` → pri `value = 1.0`: pridá `11.0` do numerátora a `11.0` do denominátora

---

## SC-005: Čas načítania konfigurácie < 200ms

**Postup**:
1. V Android Studio otvoriť Logcat
2. Filter: `EntityConfig`
3. Nainštalovať a spustiť app
4. Nájsť log line: `config loaded: N nodes`
5. Overiť, že medzi `Application.onCreate()` a log line ubehlo < 200ms

**Alternatívne**: `adb logcat -s EntityConfig` na pripojenom zariadení.

---

## SC-006: User-defined entita viditeľná do 2 sekúnd

**Postup**:
1. Otvoriť EntityManagement (Settings tab)
2. Pridať novú entitu s kľúčom `test_entity`, label `Test`, weight `5.0`, impact `1`
3. Uložiť
4. Bez reštartu prejsť na Tracker
5. `test_entity` musí byť viditeľná < 2 sekundy

**Verifikácia v DB** (voliteľné, cez SQLite browser alebo `adb shell`):
```bash
adb shell "run-as com.example.madhdtracker sqlite3 databases/madhdtracker.db 'SELECT * FROM user_element;'"
```
Entita musí byť prítomná s `userId = null`.

---

## Regresné scenáre

| Scenár | Overenie |
|--------|---------|
| Swipe na HomeScreen | Napriek zmenám v TrackerRepository swipe stále funguje |
| Weekly trend bar chart | Zobrazuje bars pre všetky trackovateľné entity |
| Notifikácie | Trigger sa nezmenil — `entityConfig.trackableKeys` = rovnaké kľúče |
| InfoScreen | Zobrazuje všetky uzly (group + trackable) s ich váhami |

---

## Build & Run

```bash
cd /home/martin/projects/adhdmad/android_app
export JAVA_HOME=/home/martin/.local/share/JetBrains/Toolbox/apps/android-studio/jbr
./gradlew :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Alebo: Android Studio → Run → `app` na connected device.
