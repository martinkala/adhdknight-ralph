# Tasks: App Configuration Layer

**Input**: Design documents from `specs/005-app-config-layer/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Povinné pre všetky zmeny doménovej logiky (§II, §VI constitution). `AppConfigLoaderTest`, rozšírenie `IndexCalculatorTest`, nový `AsrsRealibratorTest`, rozšírenie `NotificationRulesTest` sú súčasťou implementačných fáz.

**Organization**: Foundational fáza odblokuje US1; US2 a US3 sú nezávislé na sebe a závisia len od Foundational (US2) resp. US1 (US3). T005–T007 sú paralelizovateľné, T008 závisí od všetkých troch.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Dá sa spraviť paralelne (rôzne súbory, žiadne závislosti)
- **[Story]**: US1–US3 mapuje na user stories zo spec.md

---

## Phase 1: Setup – Konfiguračný súbor

**Purpose**: Vytvoriť bundled asset `app_config.json` so všetkými aktuálnymi hardcoded hodnotami — základ pre načítanie konfigurácie.

- [x] T001 Vytvoriť `android_app/app/src/main/assets/app_config.json` so všetkými aktuálnymi hodnotami zo `DefaultWeights.kt`, `IndexCalculator.kt`, `AsrsRecalibrator.kt`, `NotificationRules.kt` presne podľa schémy v `specs/005-app-config-layer/contracts/app_config_schema.md`

**Checkpoint**: Súbor existuje, je validný JSON, obsahuje všetkých 30+ parametrov.

---

## Phase 2: Foundational – AppConfig dátové triedy a loader (Blokuje US1–US3)

**Purpose**: Vytvoriť `AppConfig` dátové triedy a `AppConfigLoader` — nevyhnutné pred akýmkoľvek refaktorom konzumentov.

**⚠️ CRITICAL**: US1, US2, US3 nemôžu začať, kým nie je táto fáza hotová.

- [x] T002 Vytvoriť `android_app/app/src/main/java/com/example/madhdtracker/domain/model/AppConfig.kt` — 5 Kotlin data class bez Android závislostí: `AppConfig(weights: Map<String,Double>, elementClassification: ElementClassification, adaptation: AdaptationConfig, asrs: AsrsConfig, notification: NotificationConfig)`, `ElementClassification(negativeKeys: Set<String>, positiveKeys: Set<String>)`, `AdaptationConfig(alpha, clampMinFactor, clampMaxFactor, correlationThreshold, minHistoryDays, minSeriesSize)`, `AsrsConfig(deltaThreshold, consecutiveMeasurements, recalibrationAlpha)`, `NotificationConfig(quietStartHour, quietStartMinute, quietEndHour, quietEndMinute, stressThresholdScale, neglectedAreaDays, stressRecoveryDays)`; hodnoty polí podľa `specs/005-app-config-layer/data-model.md`

- [x] T003 Vytvoriť `android_app/app/src/main/java/com/example/madhdtracker/data/AppConfigLoader.kt` — `object AppConfigLoader` s dvomi metódami: `fun load(assetManager: AssetManager): AppConfig` (otvára `assets/app_config.json`, odovzdáva stream do `load(InputStream?)`); `fun load(stream: InputStream?): AppConfig` (null stream alebo IOException → FALLBACK_ALL; neplatný JSON → FALLBACK_ALL; parsovanie cez `org.json.JSONObject`; per-parameter validácia a fallback podľa pravidiel v `data-model.md`; normalizácia váh ak suma mimo rozsahu 95–105; `android.util.Log.d("AppConfig", "loaded from config: key=value")` pre každý parameter z JSON, `"using default for key: value"` pre fallback; `"config loaded"` / `"config not found"` / `"config parse error: msg"` ako úvodný log) (závisí od T002)

- [x] T004 Vytvoriť `android_app/app/src/test/java/com/example/madhdtracker/config/AppConfigLoaderTest.kt` — JUnit4 unit testy volajúce `AppConfigLoader.load(stream: InputStream?)`: (a) platný JSON so všetkými sekciami → všetky hodnoty AppConfig zodpovedajú JSON hodnotám; (b) `null` stream → všetky hodnoty sú defaulty z `DefaultWeights`; (c) neplatný JSON string → všetky hodnoty sú defaulty; (d) čiastočný JSON (len `adaptation` sekcia s `alpha: 0.05`) → `adaptation.alpha == 0.05`, váhy a ostatné sekcie zodpovedajú defaultom (závisí od T002, T003)

**Checkpoint**: `AppConfigLoader.load(null)` vráti platnú `AppConfig` s default hodnotami; `load(validJson)` vráti hodnoty zo JSON; T004 prechádza.

---

## Phase 3: User Story 1 – Zmena algoritmických parametrov nadobudne účinnosť po reštarte (Priority: P1) 🎯 MVP

**Goal**: Refaktorovať všetkých konzumentov hardcoded hodnôt, aby prijímali parametre výlučne cez `AppConfig` injektovaný do `TrackerRepository`.

**Independent Test**: Zmeniť `"sleep": 20.0` v `app_config.json`, rebuild, zadať rovnaké denné hodnoty — ADHD index sa líši od baseline (vyšší ak bol sleep splnený); Logcat obsahuje `"loaded from config: sleep=20.0"`.

### Implementácia US1

- [x] T005 [P] [US1] Refaktorovať `android_app/app/src/main/java/com/example/madhdtracker/domain/logic/IndexCalculator.kt` — v `adaptWeights` odstrániť default params `alpha: Double = 0.2`, `0.5`, `2.0`, `0.1`, `15`, `5` a nahradiť ich za explicitný param `adaptation: AdaptationConfig` z package `com.example.madhdtracker.domain.model`; nahradiť všetky hardcoded hodnoty za `adaptation.alpha`, `.clampMinFactor`, `.clampMaxFactor`, `.correlationThreshold`, `.minHistoryDays`, `.minSeriesSize`; rozšíriť `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/IndexCalculatorTest.kt` — pridať test, ktorý volá `adaptWeights` s `AdaptationConfig(alpha=0.5, ...)` a overuje, že sa použila hodnota `0.5` namiesto `0.2` (závisí od T002)

- [x] T006 [P] [US1] Refaktorovať `android_app/app/src/main/java/com/example/madhdtracker/domain/logic/AsrsRecalibrator.kt` — `shouldRecalibrate(asrsScores, indexAverages, config: AsrsConfig)` nahradí hardcoded `10.0` za `config.deltaThreshold` a `2` za `config.consecutiveMeasurements`; `alphaForRecalibration(config: AsrsConfig)` nahradí hardcoded `0.3` a `0.2` za `config.recalibrationAlpha` a `config.alpha` (alebo default alpha z `AdaptationConfig`); vytvoriť `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/AsrsRealibratorTest.kt` — overiť `shouldRecalibrate` s `deltaThreshold=5.0` (triggerhuje pri rozdiele >5) a `consecutiveMeasurements=3` (vyžaduje 3 merania) (závisí od T002)

- [x] T007 [P] [US1] Refaktorovať `android_app/app/src/main/java/com/example/madhdtracker/notifications/NotificationRules.kt` — zmeniť `object NotificationRules` na `class NotificationRules(private val config: NotificationConfig, private val allElementKeys: Set<String>)`; nahradiť `LocalTime.of(22, 0)` za `LocalTime.of(config.quietStartHour, config.quietStartMinute)`, `LocalTime.of(8, 0)` za `LocalTime.of(config.quietEndHour, config.quietEndMinute)`; nahradiť hardcoded `4` za `config.stressThresholdScale`; nahradiť hardcoded `3` (počet dní) za `config.neglectedAreaDays` a `config.stressRecoveryDays`; nahradiť `DefaultWeights.weights.keys` za `allElementKeys`; odstrániť `import com.example.madhdtracker.data.DefaultWeights` (závisí od T002)

- [x] T008 [US1] Refaktorovať `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — pridať `private val appConfig: AppConfig` ako druhý konštruktor param; v `seedDefaultWeightsIfEmpty` použiť `appConfig.weights` namiesto `DefaultWeights.weights`; v `computeAndSaveDailyIndex` použiť `appConfig.elementClassification.negativeKeys` a `appConfig.elementClassification.positiveKeys` namiesto `DefaultWeights.*`; volania `IndexCalculator.adaptWeights` doplniť o `appConfig.adaptation`; `AsrsRecalibrator.shouldRecalibrate` a `alphaForRecalibration` doplniť o príslušné config params; v `evaluateNotification` nahradiť `NotificationRules.method(...)` za `NotificationRules(appConfig.notification, appConfig.weights.keys).method(...)`; odstrániť priame importy `DefaultWeights` (závisí od T005, T006, T007)

- [x] T009 [US1] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/MainActivity.kt` — v `AppRoot()` pridať `val appConfig = remember { AppConfigLoader.load(context.assets) }` ihneď pred `val repository = ...`; zmeniť `TrackerRepository(db)` na `TrackerRepository(db, appConfig)`; pridať importy `com.example.madhdtracker.data.AppConfigLoader` a `com.example.madhdtracker.domain.model.AppConfig` (závisí od T008)

**Checkpoint**: US1 hotová — aplikácia sa spustí, Logcat filter `AppConfig` zobrazuje načítané hodnoty, ADHD index sa mení po zmene váhy v `app_config.json` + rebuild.

---

## Phase 4: User Story 2 – Odolnosť voči neplatnej konfigurácii (Priority: P2)

**Goal**: Overiť a doplniť, že AppConfigLoader robustne zvláda boundary values, záporné hodnoty, neplatnú sumu váh a extrémne vstupy — bez pádu aplikácie.

**Independent Test**: Vložiť `"sleep": -5.0` a `"alpha": 2.5` do `app_config.json`, spustiť `./gradlew :app:test` — testy musia prejsť; spustiť aplikáciu — nesmie crashnúť, Logcat zobrazuje "invalid value" správy.

**Note**: Kód fallback logiky je v `AppConfigLoader` (T003). Táto fáza pridáva boundary value testy overujúce edge case správanie.

### Implementácia US2

- [x] T010 [P] [US2] Rozšíriť `android_app/app/src/test/java/com/example/madhdtracker/config/AppConfigLoaderTest.kt` — pridať boundary value testy: (a) `"sleep": -5.0` → `appConfig.weights["sleep"] == 15.0` (default); (b) `"alpha": 2.5` → `appConfig.adaptation.alpha == 0.2` (default); (c) `clamp_min_factor: 2.0, clamp_max_factor: 1.0` (min ≥ max) → oba defaulty `0.5` a `2.0`; (d) `quiet_start_hour: 25` → `appConfig.notification.quietStartHour == 22` (default); (e) váhy so sumou 120 → po načítaní je suma `appConfig.weights.values.sum()` v rozsahu (95.0, 105.0) (závisí od T003, T004)

- [x] T011 [P] [US2] Rozšíriť `android_app/app/src/test/java/com/example/madhdtracker/notifications/NotificationRulesTest.kt` — pridať testy overujúce, že `NotificationRules(config, elementKeys)` skutočne používa config hodnoty: (a) `config.quietStartHour=20` → `isQuietWindow(LocalTime.of(21, 0)) == true`; (b) `config.stressThresholdScale=3` → `stressRecoveryNeeded` triggeruje keď valueScale=3; (c) `config.neglectedAreaDays=2` → `neglectedArea` triggeruje po 2 dňoch s nulovou aktivitou (závisí od T007)

**Checkpoint**: US2 hotová — `./gradlew :app:test` zelené; záporné a out-of-range hodnoty v JSON nespôsobia crash ani nesprávne výpočty.

---

## Phase 5: User Story 3 – Auditovateľnosť aktívnej konfigurácie (Priority: P3)

**Goal**: Vývojár vie do 30 sekúnd od štartu aplikácie potvrdiť (cez Logcat), aká konfigurácia je aktívna — ktoré parametre pochádzajú z JSON a ktoré sú defaulty.

**Independent Test**: Spustiť aplikáciu s čiastočným `app_config.json` (len `adaptation` sekcia) → Logcat filter `AppConfig` zobrazí pre `alpha` log `"loaded from config"` a pre váhy `"using default"`.

**Note**: Kód audit logu je implementovaný v `AppConfigLoader` (T003 — `android.util.Log.d`). Táto fáza je validačná.

### Implementácia US3

- [x] T012 [US3] Manuálna validácia audit logu podľa scenárov S1, S3, S7 z `specs/005-app-config-layer/quickstart.md` — spustiť aplikáciu na emulátori/zariadení: (a) s platným `app_config.json` s `sleep: 20.0` → Logcat tag `AppConfig` musí obsahovať `"loaded from config: sleep=20.0"`; (b) s premenovaným (chýbajúcim) `app_config.json` → Logcat musí obsahovať `"config not found, using defaults"`; (c) s čiastočným JSON (len `adaptation`) → Logcat zobrazuje mix `"loaded from config"` a `"using default"` pre rôzne parametre; pri zlyhaní scenára doplniť chýbajúce `Log.d` volanie do `AppConfigLoader.kt`

**Checkpoint**: US3 hotová — vývojár vidí zdroj každého parametra v Logcat bez čítania zdrojového kódu.

---

## Final Phase: Polish & Validácia

**Purpose**: Spustiť testy, manuálne validovať kľúčové scenáre, overiť, že `DefaultWeights.kt` zostáva ako čistý fallback zdroj.

- [x] T013 [P] Spustiť `./gradlew :app:test` v `android_app/` a overiť, že sú zelené: `AppConfigLoaderTest` (T004 + T010), rozšírený `IndexCalculatorTest` (T005), nový `AsrsRealibratorTest` (T006), rozšírený `NotificationRulesTest` (T011)
- [x] T014 [P] Manuálna validácia scenárov S2 a S8 z `specs/005-app-config-layer/quickstart.md` — S2: zmeniť `sleep: 20.0`, rebuild, overiť rozdiel ADHD indexu; S8: odstrániť `caffeine` z `negative_keys`, overiť posun do pozitívneho sub-indexu
- [x] T015 [P] Overiť, že `android_app/app/src/main/java/com/example/madhdtracker/data/DefaultWeights.kt` je nezmenený a stále obsahuje všetky fallback konštanty — `AppConfigLoader` ho importuje, ale nevytvára naň žiadnu novú doménovú závislosť

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Žiadne závislosti — môže začať ihneď
- **Foundational (Phase 2)**: Závisí od Phase 1 — **BLOKUJE US1, US2, US3**
- **US1 (Phase 3)**: Závisí od dokončenia Foundational
- **US2 (Phase 4)**: Závisí od dokončenia Foundational; nezávisí od US1
- **US3 (Phase 5)**: Závisí od dokončenia US1 (AppConfigLoader + TrackerRepository musí byť drôtovaný)
- **Polish (Final)**: Závisí od US1 + US2 + US3

### User Story Dependencies

| Story | Závisí od | Môže ísť paralelne s |
|-------|-----------|----------------------|
| US1 (P1) | Foundational | US2 (rôzne súbory) |
| US2 (P2) | Foundational | US1 |
| US3 (P3) | US1 (TrackerRepository musí byť drôtovaný) | – |

### Within Each User Story

- T005, T006, T007 → paralelne (rôzne súbory, žiadne závislosti medzi nimi)
- T005 + T006 + T007 → T008 (TrackerRepository závisí od všetkých troch)
- T008 → T009 (MainActivity závisí od TrackerRepository signatúry)
- T010, T011 → paralelne (rôzne súbory)

---

## Parallel Example: US1

```
Paralelne spustiteľné po Foundational:
  Task T005: IndexCalculator.adaptWeights + IndexCalculatorTest (IndexCalculator.kt)
  Task T006: AsrsRecalibrator + AsrsRealibratorTest (AsrsRecalibrator.kt)
  Task T007: NotificationRules refactor (NotificationRules.kt)

Po T005 + T006 + T007:
  Task T008: TrackerRepository — použiť AppConfig (TrackerRepository.kt)

Po T008:
  Task T009: MainActivity — wire AppConfigLoader (MainActivity.kt)
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Phase 1: T001 (app_config.json)
2. Foundational: T002 → T003 → T004
3. **STOP a VALIDUJ**: `./gradlew :app:test` — T004 zelený
4. US1: T005 + T006 + T007 (paralelne) → T008 → T009
5. **STOP a VALIDUJ**: Scenár S2 z quickstart.md (zmena sleep váhy)

### Incremental Delivery

1. Setup + Foundational → odblokuje všetko
2. US1 (P1) → MVP; zmena parametrov funguje
3. US2 (P2) → robustnosť; boundary value testy zelené
4. US3 (P3) → observabilita; audit log overený

### Odporúčané poradie pre jedného vývojára

```
T001 → T002 → T003 → T004
T005 → T006 → T007 (paralelne)
T008 → T009
T010 → T011 (paralelne)
T012
T013 → T014 → T015 (paralelne)
```

---

## Notes

- `[P]` tasky = rôzne súbory, žiadne závislosti v rámci fázy
- `[Story]` label mapuje task na konkrétnu user story pre traceability
- `org.json.JSONObject` je súčasťou Android SDK — žiadna nová závislosť
- `android.util.Log.d` nie je testovateľný v JVM unit testoch — US3 je primárne manuálna validácia
- `DefaultWeights.kt` zostáva nezmenený — je zdrojom fallback konštánt pre `AppConfigLoader`
- Commit po každej dokončenej user story (Foundational → US1 → US2 → US3)

---

## Phase 6: Convergence

- [x] T016 Lokalizovať a vyriešiť absenciu call-site pre `AsrsRecalibrator` pred implementáciou AsrsRecalibrator-súvisiacej časti T008 — spustiť `grep -rn "AsrsRecalibrator" android_app/app/src/` a (a) ak call site existuje, aktualizovať ho aby prešiel `appConfig.asrs`; (b) ak call site neexistuje, pridať volanie `AsrsRecalibrator.shouldRecalibrate(asrsScores, indexAverages, appConfig.asrs)` do vhodnej metódy v `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` (napr. `computeAndSaveWeeklyIndex`), alebo explicitne zdokumentovať že ASRS integrácia je mimo scope tohto PR a odstrániť zmienku o AsrsRecalibrator z popisu T008 per FR-003, FR-010 (partial)
