# Implementation Plan: App Configuration Layer

**Branch**: `005-app-config-layer` | **Date**: 2026-06-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-app-config-layer/spec.md`

## Summary

Externalizovať všetky hardcoded algoritmické parametre (9 váh elementov, adaptačné koeficienty, ASRS prahy, klasifikácia elementov, notifikačné prahy) do JSON súboru dodávaného s aplikáciou (`assets/app_config.json`). Súbor je parsovaný cez `org.json.JSONObject` (súčasť Android SDK — žiadna nová závislosť) pri štarte, výsledok je `AppConfig` dátová trieda injektovaná do `TrackerRepository`. Každá neplatná alebo chýbajúca hodnota sa ticho nahradí zabudovanou záložnou hodnotou; audit log zapisuje zdroj každého parametra cez `android.util.Log`.

## Technical Context

**Language/Version**: Kotlin, Android min SDK 26 / target SDK 34, JVM target 17

**Primary Dependencies**: Jetpack Compose BOM 2024.06.00, Room 2.6.1, Coroutines 1.8.1, WorkManager 2.9.0 — žiadna nová závislosť; parsing cez `org.json.JSONObject` (Android SDK)

**Storage**: JSON súbor v `src/main/assets/app_config.json` (read-only bundled asset); Room DB sa nemení

**Testing**: JUnit4 JVM unit testy (existujúca infraštruktúra v `src/test/`)

**Target Platform**: Android (offline-first, single-device)

**Project Type**: Mobile app (Android, MVVM + Repository pattern)

**Performance Goals**: Načítanie konfigurácie prebieha synchrónne na hlavnom vlákne počas `remember {}` bloku v `AppRoot` — musí byť pod 50 ms (JSON parse < 1 kB súboru je rádovo rýchlejší)

**Constraints**: Žiadna nová externá závislosť (§VII). Offline-first (§I). Žiadna zmena Room schémy — žiadna DB migrácia. Konfigurácia je read-only za runtime.

**Scale/Scope**: 1 JSON súbor (~40 parametrov), 1 trieda loader, 4 data class skupiny, ~5 refaktorovaných tried

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princíp | Status | Poznámka |
|---------|--------|---------|
| §I – MVVM + Repository | ✅ | `AppConfig` injektovaný do `TrackerRepository`; UI/ViewModel ho nevidia priamo |
| §I – Vrstvová separácia | ✅ | `AppConfig` je v `domain/model/`; `AppConfigLoader` v `data/` (má `AssetManager` dep) |
| §I – Offline-first | ✅ | Bundled asset, žiadne sieťové volanie |
| §II – Doménová logika | ✅ | Žiadna algoritmická zmena — len parameterizácia existujúcich vzorcov |
| §II – Unit testy | ✅ | Unit testy pre config loading, fallback, validáciu sú povinné (nová trieda) |
| §III – DB schéma | ✅ | Žiadna zmena Room entity ani migrácia |
| §VI – Testovanie | ✅ | Každá nová trieda s logikou (AppConfigLoader, validácia) musí mať testy |
| §VII – Tech stack | ✅ | `org.json` je súčasť Android SDK, nie nová závislosť |

**Violations**: žiadne — žiadne zdôvodňovanie potrebné.

## Project Structure

### Documentation (this feature)

```text
specs/005-app-config-layer/
├── plan.md              # Tento súbor
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── app_config_schema.md   # JSON schéma konfiguračného súboru
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code

```text
android_app/app/src/main/
├── assets/
│   └── app_config.json                          # Konfiguračný súbor (nový)
└── java/com/example/madhdtracker/
    ├── domain/
    │   └── model/
    │       └── AppConfig.kt                     # Data triedy (nové)
    ├── data/
    │   ├── AppConfigLoader.kt                   # JSON loader + fallback (nový)
    │   └── DefaultWeights.kt                    # Zostáva — fallback konštanty
    ├── domain/
    │   └── logic/
    │       ├── IndexCalculator.kt               # Refaktor: params cez AppConfig
    │       └── AsrsRecalibrator.kt              # Refaktor: params cez AppConfig
    ├── notifications/
    │   └── NotificationRules.kt                 # Refaktor: object → class(AppConfig)
    ├── data/
    │   └── TrackerRepository.kt                 # Refaktor: + AppConfig konštruktor param
    └── MainActivity.kt                          # Refaktor: konštruuje AppConfig pred Repository

android_app/app/src/test/java/com/example/madhdtracker/
├── config/
│   └── AppConfigLoaderTest.kt                   # Unit testy (nové)
└── notifications/
    └── NotificationRulesTest.kt                 # Existuje — rozšíriť o config testy
```

**Structure Decision**: Existujúca štruktúra `domain/model/`, `data/`, `domain/logic/` sa zachováva. Nové súbory zapadajú do existujúcich balíkov bez nových balíkových úrovní.

## Implementation Approach

### Fáza A — AppConfig data model + loader

1. Vytvoriť `domain/model/AppConfig.kt` — čisté Kotlin data triedy bez Android závislostí
2. Vytvoriť `assets/app_config.json` — všetky aktuálne hardcoded hodnoty ako východiskové hodnoty
3. Vytvoriť `data/AppConfigLoader.kt` — parsuje JSON cez `org.json`, aplikuje fallback, loguje audit

### Fáza B — Refaktor doménovej logiky

4. Refaktorovať `IndexCalculator.adaptWeights` — nahradiť default parametre `AppConfig.AdaptationConfig`
5. Refaktorovať `AsrsRecalibrator` — nahradiť hardcoded hodnoty `AppConfig.AsrsConfig`
6. Refaktorovať `NotificationRules` — `object` → `class(config: AppConfig.NotificationConfig)` + použiť `config.elementKeys` namiesto `DefaultWeights.weights.keys`

### Fáza C — Wiring

7. Refaktorovať `TrackerRepository` — pridať `AppConfig` konštruktor param, odstrániť priame referencie na `DefaultWeights` (presunúť cez `appConfig.elementClassification`, `appConfig.adaptationConfig`)
8. Aktualizovať `MainActivity.AppRoot` — načítať `AppConfigLoader.load(context.assets)` v `remember {}` pred `TrackerRepository`

### Fáza D — Testy

9. Vytvoriť `AppConfigLoaderTest` — platný JSON, chýbajúci súbor, neplatné hodnoty, čiastočný JSON
10. Rozšíriť `NotificationRulesTest` — overiť, že NotificationRules používa config hodnoty

## Complexity Tracking

> Žiadne constitution violations — sekcia prázdna.
