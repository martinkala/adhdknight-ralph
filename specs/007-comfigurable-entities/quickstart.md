# Quickstart: Configurable Entities — Validačné scenáre

**Feature**: 007-comfigurable-entities  
**Prerequisity**: Android Studio, emulátor/zariadenie, ADB

---

## Setup

```bash
cd android_app
JAVA_HOME=/home/martin/.local/share/JetBrains/Toolbox/apps/android-studio/jbr ./gradlew :app:installDebug
adb shell am start -n com.example.madhdtracker/.MainActivity
```

Logcat filter pre túto feature: `tag:EntityConfig`

---

## S1 — Základné načítanie entít z YAML

**Čo testuje**: FR-001, FR-004, US1/AC1  
**Prerekvizita**: platný `entities.yaml` so všetkými 9 entitami

1. Spusti app
2. Logcat filter `tag:EntityConfig` → musíš vidieť:
   ```
   D EntityConfig  loaded from config: sleep (weight=15.0, impact=+1, parent=sleep)
   D EntityConfig  loaded from config: stress_work (weight=13.0, impact=-1, parent=lifestyle)
   ...
   D EntityConfig  config loaded: 9 elements, 5 categories
   ```
3. Otvor Tracker screen → 9 entít viditeľných, zoskupených podľa kategórií

**Expected**: Všetkých 9 entít načítaných, Logcat obsahuje záznam pre každú

---

## S2 — Pridanie novej entity bez zmeny kódu

**Čo testuje**: FR-001, FR-011, SC-001, US1/AC4  
**Prerekvizita**: editovateľný `entities.yaml`

1. Pridaj do `entities.yaml` pod `elements:`:
   ```yaml
   pushups:
     weight: 5.0
     impact: 1
     parent: physical_activity
     description: "Kliky"
     active: true
   ```
2. `./gradlew :app:installDebug` (rebuild)
3. Otvor Tracker → entita `pushups` sa zobrazí pod `physical_activity`
4. Logcat: `loaded from config: pushups (weight=5.0, impact=+1, parent=physical_activity)`

**Expected**: Nová entita viditeľná bez zmeny Kotlin kódu

---

## S3 — Fallback pri chýbajúcom súbore

**Čo testuje**: FR-004, US1/AC3

1. Premenuj `entities.yaml` na `entities.yaml.bak`
2. Rebuild + spusti
3. Logcat: `entities.yaml not found, using defaults`
4. Tracker zobrazuje 9 defaultných entít (z `DefaultWeights.kt`)

**Expected**: App sa nespustí v crash, defaultné entity sú dostupné

---

## S4 — Deaktivácia entity (user override)

**Čo testuje**: FR-005, FR-008, US2/AC1, US2/AC3

1. V Settings/Entity management deaktivuj `caffeine`
2. Tracker screen → `caffeine` zmizne
3. Zadaj denné hodnoty → index sa vypočíta bez `caffeine`
4. Reštartuj app → `caffeine` stále neaktívna

**Expected**: Deaktivácia perzistovaná, index neobsahuje `caffeine`

---

## S5 — FR-006: Fairness pri viacerích pod-entitách

**Čo testuje**: FR-006, US3/AC1, SC-002

1. Pridaj do `entities.yaml`:
   ```yaml
   pushups:
     weight: 5.5
     impact: 1
     parent: physical_activity
     active: true
   running:
     weight: 5.5
     impact: 1
     parent: physical_activity
     active: true
   ```
   *(pôvodná entita `physical_activity` zostane, teraz má 2 pod-entity v kategórii)*
2. Rebuild
3. Zadaj deň: všetky entity splnené (binary=1)
4. Porovnaj index s baseline (bez pod-entít)

**Expected**: Kategória `physical_activity` neprispieva výrazne viac ako s 1 entitou — difference < 5% celkového indexu

---

## S6 — Logcat audit: čiastočný YAML

**Čo testuje**: FR-010, US3 (audit log)

1. Uprav `entities.yaml` — odober sekciu `categories`, nechaj len `elements`
2. Rebuild + spusti
3. Logcat filter `tag:EntityConfig` → mix `"loaded from config"` a `"using default for categories"`

**Expected**: Jasný audit log čo pochádza z YAML a čo je default

---

## Unit Test Validácia

```bash
cd android_app
JAVA_HOME=/home/martin/.local/share/JetBrains/Toolbox/apps/android-studio/jbr \
  ./gradlew :app:testDebugUnitTest
```

Očakávané nové test triedy:
- `EntityConfigLoaderTest` — načítanie YAML, fallback, validácia
- `IndexCalculatorGroupTest` — FR-006 algoritmus pre skupiny sub-entít
- `UserElementOverrideTest` — Room DAO pre user overrides

**Expected**: Všetky testy zelené
