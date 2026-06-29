# Implementation Plan: Configurable Entities

**Branch**: `007-comfigurable-entities` | **Date**: 2026-06-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-comfigurable-entities/spec.md`

---

## Summary

Nahradiť flat JSON váhy (`app_config.json → weights`) hierarchickým YAML entity config súborom (`entities.yaml`). Každá entita dostane rozšírenú definíciu (weight, impact, parent, description, active, scale). Algoritmus výpočtu indexu sa upraví o skupinovú normalizáciu (FR-006). Používateľský stav aktívnosti bude persistovaný v Room DB.

Technický prístup: nový `EntityConfigLoader` (SnakeYAML) + `ElementConfig` domain model + rozšírenie `IndexCalculator` + nová Room tabuľka `user_element_override`. Vzor totožný s `AppConfigLoader` (feature 005).

---

## Technical Context

**Language/Version**: Kotlin, JVM target 17
**Primary Dependencies**: SnakeYAML 2.2 (nová, §VII justified), org.json (existujúca), Room 2.6.1 (existujúca)
**Storage**: Room DB (user overrides + user-defined entities), assets YAML (systémový config)
**Testing**: JUnit4, isReturnDefaultValues = true, org.json:json:20231013 testImplementation
**Target Platform**: Android min SDK 26, target SDK 34
**Project Type**: Mobile app (MVVM + Repository, Jetpack Compose)
**Constraints**: Offline-first (§I), unit testy pre všetky doménové zmeny (§II, §VI), bez DI frameworku (§VII)

---

## Constitution Check

| Princíp | Stav | Poznámka |
|---------|------|----------|
| §I MVVM + Repository | ✅ | EntityConfigLoader → Repository → ViewModel → UI; žiadny priamy DAO prístup z UI |
| §I Offline-first | ✅ | YAML v assets, Room pre user data — žiadna sieť |
| §I Kotlin + Compose | ✅ | Žiadny XML, žiadny View system |
| §I Room + WorkManager | ✅ | User overrides v Room, bez AlarmManager |
| §II Unit testy povinné | ✅ | EntityConfigLoaderTest, IndexCalculatorGroupTest, UserElementOverrideTest |
| §VI Test pokrytie | ✅ | Každá nová doménová trieda má unit test |
| §VII Nová závislosť | ⚠️ | SnakeYAML 2.2 — zdôvodnenie v research.md Decision 1; org.json nepodporuje YAML |

**Výsledok Constitution Check**: PASS s jednou zdôvodnenou výnimkou (SnakeYAML).

---

## Project Structure

### Documentation (this feature)

```text
specs/007-comfigurable-entities/
├── plan.md              ← tento súbor
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── entities_yaml_schema.md
├── checklists/
│   └── requirements.md
└── tasks.md             ← generuje /speckit-tasks
```

### Source Code

```text
android_app/app/src/main/assets/
└── entities.yaml                          (NEW)

android_app/app/src/main/java/com/example/madhdtracker/
├── domain/model/
│   ├── AppConfig.kt                       (existujúci — bez zmeny)
│   └── ElementConfig.kt                   (NEW — Category, Element, ElementConfig)
├── data/
│   ├── DefaultWeights.kt                  (existujúci — zostáva ako fallback)
│   ├── AppConfigLoader.kt                 (existujúci — bez zmeny)
│   ├── EntityConfigLoader.kt              (NEW — SnakeYAML parser, fallback)
│   ├── TrackerRepository.kt               (MODIFIED — dostáva EntityConfig, nový algoritmus)
│   ├── Entities.kt                        (MODIFIED — UserElementOverride, UserElement)
│   ├── Daos.kt                            (MODIFIED — UserElementOverrideDao, UserElementDao)
│   └── AppDatabase.kt                     (MODIFIED — schema version bump na 2)
├── domain/logic/
│   └── IndexCalculator.kt                 (MODIFIED — skupinová normalizácia FR-006)
└── MainActivity.kt                        (MODIFIED — EntityConfigLoader.load(), inject do Repository)

android_app/app/src/test/java/com/example/madhdtracker/
├── config/
│   └── EntityConfigLoaderTest.kt          (NEW)
├── domain/logic/
│   └── IndexCalculatorGroupTest.kt        (NEW)
└── data/
    └── UserElementOverrideTest.kt         (NEW)
```

---

## Architecture Decisions

### EntityConfigLoader (vzor ako AppConfigLoader)

```kotlin
object EntityConfigLoader {
    fun load(assetManager: AssetManager): ElementConfig =
        load(runCatching { assetManager.open("entities.yaml") }.getOrNull())

    fun load(stream: InputStream?): ElementConfig {
        // null → fallback + Log.d("EntityConfig", "entities.yaml not found, using defaults")
        // parse error → fallback + Log.d("EntityConfig", "parse error: $msg")
        // per-field validácia + Log.d pre každý parameter
    }
}
```

### IndexCalculator — skupinová normalizácia (FR-006)

Nová metóda `computeDailyIndexGrouped`:

```
Algoritmus:
1. Filter aktívnych elementov (activeKeys)
2. Root elementy (parent=null): prispievajú priamo s vlastnou váhou
3. Pre každú kategóriu (group):
   group_avg = Σ(weight_i × effective_i) / Σ(weight_i)   [iba aktívne]
   category_contribution = group_avg × category.weight
4. index = Σ(contributions) / Σ(active_category_weights + root_weights) × 100
```

### TrackerRepository — nové parametre

```kotlin
class TrackerRepository(
    private val db: AppDatabase,
    private val appConfig: AppConfig,
    private val elementConfig: ElementConfig   // nový parameter
)
```

### Room schema migration

**Version**: 1 → 2

Nové tabuľky:
- `user_element_override(elementKey TEXT PRIMARY KEY, isActive INTEGER NOT NULL)`
- `user_element(id INTEGER PK AUTOINCREMENT, key TEXT UNIQUE, weight REAL, impact INTEGER, parentCategory TEXT, description TEXT, scale TEXT, isActive INTEGER NOT NULL)`

Migrácia: `fallbackToDestructiveMigration()` v dev fáze; finálna migration script pred release.

### SnakeYAML na Androide

```kotlin
// build.gradle.kts
implementation("org.yaml:snakeyaml:2.2")
testImplementation("org.yaml:snakeyaml:2.2")  // rovnaká verzia v testoch

// Parsing
val yaml = Yaml()
val data: Map<String, Any?> = yaml.load(stream)
```

---

## Dependency Addition Justification (§VII)

**Knižnica**: `org.yaml:snakeyaml:2.2`
**Dôvod**: YAML formát bol explicitne zvolený. Žiadna existujúca závislosť neparsuje YAML.
**Alternatíva zamietnutá**: Vlastný parser → maintenance burden + bezpečnostné riziká.
**Charakteristika**: 0 transitivnych deps, Apache 2.0, Android-tested.

---

## Complexity Tracking

| Zmena | Dôvod | Jednoduchšia alternatíva zamietnutá pretože |
|-------|-------|---------------------------------------------|
| Nová závislosť SnakeYAML | YAML formát zvolený pre čitateľnosť | Vlastný parser — príliš error-prone |
| Room schema v2 | User overrides musia prežiť reboot | SharedPreferences — nestabilné pri backup/restore |
| Nový IndexCalculator algoritmus | FR-006 — fairness pre sub-entity skupiny | Bez normalizácie — inflácia kategórií |
