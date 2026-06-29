# Tasks: Configurable Entities

**Input**: Design documents from `specs/007-comfigurable-entities/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Povinné pre všetky zmeny doménovej logiky (§II, §VI constitution). `EntityConfigLoaderTest`, `IndexCalculatorGroupTest` sú súčasťou implementačných fáz.

**Organization**: Setup + Foundational odblokujú US1. US2 a US3 závisia od US1 (EntityConfig musí byť drôtovaný). US4 závisí od US2 (EntityManagementScreen).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Dá sa spraviť paralelne (rôzne súbory, žiadne závislosti)
- **[Story]**: US1–US4 mapuje na user stories zo spec.md

---

## Phase 1: Setup

**Purpose**: SnakeYAML závislosť + systémový YAML config súbor

- [X] T001 Pridať `implementation("org.yaml:snakeyaml:2.2")` a `testImplementation("org.yaml:snakeyaml:2.2")` do `android_app/app/build.gradle.kts` — sekcia `dependencies` pod existujúcim `testImplementation("org.json:json:20231013")`

- [X] T002 Vytvoriť `android_app/app/src/main/assets/entities.yaml` so všetkými 5 kategóriami a 9 entitami podľa schémy v `specs/007-comfigurable-entities/contracts/entities_yaml_schema.md` — kategórie: `sleep(weight:15.0,clickable:true)`, `physical_activity(weight:11.0,clickable:true)`, `lifestyle(weight:42.0,clickable:false)`, `head(weight:11.0,clickable:false)`, `food(weight:8.0,clickable:false)`; entity: `overall_feeling(weight:13.0,impact:1,parent:null)`, `sleep(15.0,+1,parent:sleep)`, `physical_activity(11.0,+1,parent:physical_activity,scale:[1-5])`, `stress_work(13.0,-1,parent:lifestyle,scale:[1-5])`, `stress_personal(13.0,-1,parent:lifestyle,scale:[1-5])`, `caffeine(6.0,-1,parent:lifestyle,scale:[1-5])`, `alcohol(10.0,-1,parent:lifestyle,scale:[1-5])`, `nutrition_protein(8.0,+1,parent:food)`, `mindfulness(11.0,+1,parent:head)`

**Checkpoint**: `entities.yaml` je platný YAML, čitateľný ľudsky aj strojovo.

---

## Phase 2: Foundational — Domain model + Loader + Room v2 (Blokuje US1–US4)

**Purpose**: Vytvoriť `ElementConfig` dátové triedy, `EntityConfigLoader`, unit testy a rozšíriť Room DB.

**⚠️ CRITICAL**: US1–US4 nemôžu začať, kým nie je táto fáza hotová.

- [X] T003 Vytvoriť `android_app/app/src/main/java/com/example/madhdtracker/domain/model/ElementConfig.kt` — 3 Kotlin data triedy bez Android závislostí: `data class Category(val key: String, val label: String, val clickable: Boolean, val weight: Double)`; `data class Element(val key: String, val weight: Double, val impact: Int, val parent: String?, val description: String, val active: Boolean, val scale: List<Int>?)` — kde `impact` musí byť `1` alebo `-1`; `data class ElementConfig(val categories: Map<String, Category>, val elements: Map<String, Element>)` plus helper `val negativeKeys: Set<String> get() = elements.filter { it.value.impact == -1 }.keys.toSet()` a `val positiveKeys: Set<String> get() = elements.filter { it.value.impact == 1 }.keys.toSet()`

- [X] T004 Vytvoriť `android_app/app/src/main/java/com/example/madhdtracker/data/EntityConfigLoader.kt` — `object EntityConfigLoader` s dvomi metódami: `fun load(assetManager: AssetManager): ElementConfig` (otvára `assets/entities.yaml`, odovzdáva do `load(InputStream?)`); `fun load(stream: InputStream?): ElementConfig` (null/IOException → FALLBACK + `Log.d("EntityConfig","entities.yaml not found, using defaults")`; parse error → FALLBACK + `Log.d("EntityConfig","parse error: $msg")`; parsovanie cez `org.yaml.snakeyaml.Yaml().load(stream)` do `Map<String,Any?>`; validácia každého poľa podľa pravidiel v `contracts/entities_yaml_schema.md`; neznámy `parent` → element ignorovaný + log; `weight <= 0` → ignorovaný + log; `impact` ∉ {1,-1} → ignorovaný + log; `Log.d("EntityConfig","loaded: <key> weight=<w> impact=<i> parent=<p>")` pre každý platný element; `Log.d("EntityConfig","config loaded: N elements, M categories")` na konci; FALLBACK = `ElementConfig` odvodený z `DefaultWeights.kt`) (závisí od T003)

- [X] T005 Vytvoriť `android_app/app/src/test/java/com/example/madhdtracker/config/EntityConfigLoaderTest.kt` — JUnit4 unit testy volajúce `EntityConfigLoader.load(stream: InputStream?)`: (a) platný YAML so všetkými 9 entitami a 5 kategóriami → `elementConfig.elements["sleep"]?.weight == 15.0`, `elementConfig.categories.size == 5`, `negativeKeys == setOf("stress_work","stress_personal","caffeine","alcohol")`; (b) `null` stream → fallback: `elements["sleep"]?.weight == 15.0` (z DefaultWeights); (c) neplatný YAML string → fallback; (d) YAML len s jedným elementom (`sleep: weight: 20.0`) → `elements["sleep"]?.weight == 20.0`, ostatné elementy sú z fallbacku; (e) element s `weight: -5.0` → element ignorovaný (neobjaví sa v `elements`); (f) element s neexistujúcim `parent: xyz` → element ignorovaný (závisí od T003, T004)

- [X] T006 Rozšíriť `android_app/app/src/main/java/com/example/madhdtracker/data/Entities.kt` — pridať dve nové Room entity: `@Entity(tableName="user_element_override") data class UserElementOverrideEntity(@PrimaryKey val elementKey: String, val isActive: Boolean)`; `@Entity(tableName="user_element") data class UserElementEntity(@PrimaryKey(autoGenerate=true) val id: Long = 0, val key: String, val weight: Double, val impact: Int, val parentCategory: String, val description: String?, val scale: String?, val isActive: Boolean)`

- [X] T007 Rozšíriť `android_app/app/src/main/java/com/example/madhdtracker/data/Daos.kt` — pridať dve nové DAO rozhrania: `@Dao interface UserElementOverrideDao { @Query("SELECT * FROM user_element_override") suspend fun getAll(): List<UserElementOverrideEntity>; @Insert(onConflict=OnConflictStrategy.REPLACE) suspend fun upsert(override: UserElementOverrideEntity); @Query("DELETE FROM user_element_override WHERE elementKey=:key") suspend fun delete(key: String) }`; `@Dao interface UserElementDao { @Query("SELECT * FROM user_element") suspend fun getAll(): List<UserElementEntity>; @Insert suspend fun insert(element: UserElementEntity): Long; @Delete suspend fun delete(element: UserElementEntity) }` (závisí od T006)

- [X] T008 Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/data/AppDatabase.kt` — zvýšiť `version` z 2 na 3; pridať `UserElementOverrideEntity::class` a `UserElementEntity::class` do zoznamu `entities`; pridať `userElementOverrideDao(): UserElementOverrideDao` a `userElementDao(): UserElementDao` abstraktné metódy; pridať `@Database(... exportSchema = true)` a `fallbackToDestructiveMigration()` v builderi (závisí od T006, T007)

**Checkpoint**: `EntityConfigLoader.load(null)` vráti platnú `ElementConfig` z DefaultWeights; `load(validYaml)` vráti elementy z YAML; T005 prechádza; AppDatabase kompiluje s novými tabuľkami.

---

## Phase 3: User Story 1 — Hierarchická konfigurácia entít (Priority: P1) 🎯 MVP

**Goal**: App načíta `entities.yaml` pri štarte, TrackerRepository používa entity váhy z YAML namiesto DefaultWeights.

**Independent Test**: Spusti app → Logcat tag `EntityConfig` zobrazuje `loaded: sleep weight=15.0 impact=1 parent=sleep`; Tracker screen zobrazuje entity.

- [X] T009 [US1] Modifikovať `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — pridať `private val elementConfig: ElementConfig` ako tretí konštruktor parameter (za `appConfig`); v metóde `seedDefaultWeightsIfEmpty()` nahradiť `DefaultWeights.weights` za `elementConfig.elements.mapValues { it.value.weight }`; v `computeAndSaveDailyIndex` nahradiť `appConfig.elementClassification.negativeKeys` za `elementConfig.negativeKeys` a `positiveKeys` za `elementConfig.positiveKeys` (závisí od T003)

- [X] T010 [US1] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/MainActivity.kt` — pridať `val elementConfig = remember { EntityConfigLoader.load(context.assets) }` ihneď pred `val repository = ...`; zmeniť `TrackerRepository(db, appConfig)` na `TrackerRepository(db, appConfig, elementConfig)`; pridať import `com.example.madhdtracker.data.EntityConfigLoader` (závisí od T009)

- [X] T011 [US1] Aktualizovať oba `NotificationWorker.kt` súbory (`notifications/` a `ui/`) — pridať `val elementConfig = EntityConfigLoader.load(applicationContext.assets)`; zmeniť `TrackerRepository(db, appConfig)` na `TrackerRepository(db, appConfig, elementConfig)`; pridať import EntityConfigLoader (závisí od T009)

- [ ] T012 [US1] Manuálna validácia scenára S1 z `quickstart.md` — spusti app na emulátori, Logcat filter `tag:EntityConfig` → musíš vidieť `loaded: sleep weight=15.0 impact=1 parent=sleep` a `config loaded: 9 elements, 5 categories`

**Checkpoint**: US1 hotová — app sa spustí, Logcat zobrazuje entity z YAML, Tracker funguje.

---

## Phase 4: User Story 2 — Aktívne/neaktívne entity (Priority: P2)

**Goal**: Používateľ môže deaktivovať entity v Entity Management screen; deaktivácia je perzistovaná.

**Independent Test**: Deaktivovať `caffeine` v Entity Management → entita zmizne z Tracker screenu → po reštarte stále neaktívna.

- [X] T013 [P] [US2] Rozšíriť `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — pridať `suspend fun getActiveElementKeys(): Set<String>` (načíta UserElementOverride z DB, aplikuje na `elementConfig.elements.filter { it.value.active }`, vráti finálnu množinu aktívnych kľúčov); pridať `suspend fun setElementActive(key: String, active: Boolean)` (upsert do `user_element_override` tabuľky) (závisí od T008, T009)

- [X] T014 [P] [US2] Vytvoriť `android_app/app/src/main/java/com/example/madhdtracker/ui/EntityManagementViewModel.kt` a `EntityManagementViewModelFactory.kt` — `EntityManagementViewModel(private val repository: TrackerRepository)` s `StateFlow<Map<String, Boolean>>` pre aktívny stav všetkých elementov (key → isActive); metóda `toggleElement(key: String, currentActive: Boolean)` volá `repository.setElementActive(key, !currentActive)` a aktualizuje StateFlow (závisí od T013)

- [X] T015 [US2] Vytvoriť `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityManagementScreen.kt` — Composable `EntityManagementScreen(viewModel: EntityManagementViewModel)` zobrazujúci elementy zoskupené podľa `elementConfig.categories`; pre každý element `Row` s názvom, popisom a `Switch` prepínačom (isActive); `Switch` volá `viewModel.toggleElement(key, currentState)` (závisí od T014)

- [X] T016 [US2] Pridať route `entity_management` do `android_app/app/src/main/java/com/example/madhdtracker/ui/navigation/AppNavGraph.kt` a `AppRoutes.kt` — pridať `composable(AppRoutes.ENTITIES)` s `EntityManagementScreen`; pridať `EntityManagementViewModel` parameter do `AppNavGraph`; pridať NavigationBarItem "Entities" do `MainActivity.kt` (alebo odkaz zo Settings screenu) (závisí od T015)

- [X] T017 [US2] Upraviť `TrackerRepository.computeAndSaveDailyIndex` — pri výpočte indexu filtrovať `values` na `getActiveElementKeys()` pred odovzdaním do `IndexCalculator` (závisí od T013)

**Checkpoint**: US2 hotová — Entity Management screen zobrazuje prepínače; deaktivácia caffeine → zmizne z Trackeru; po reštarte stav zachovaný.

---

## Phase 5: User Story 3 — Spravodlivý výpočet (FR-006) (Priority: P2)

**Goal**: Kategória s viacerými pod-entitami neprispieva do indexu viac ako kategória s jednou entitou rovnakej celkovej váhy.

**Independent Test**: Pridať 2 sub-entity pod `physical_activity` (každá weight 5.5), označiť všetky ako done — index kategórie nesmie byť výrazne vyšší ako so 1 entitou weight 11.0.

- [X] T018 [P] [US3] Pridať metódu `computeDailyIndexGrouped(values: List<EventValueEntity>, elementConfig: ElementConfig, activeKeys: Set<String>): Double?` do `android_app/app/src/main/java/com/example/madhdtracker/domain/logic/IndexCalculator.kt` — implementácia: (1) filter values na activeKeys; (2) root elementy (parent==null): príspevok = weight × effective; (3) pre každú kategóriu: `group_avg = Σ(weight_i × effective_i) / Σ(weight_i)` (len aktívne v skupine); `category_contribution = group_avg × category.weight`; (4) `index = Σ(contributions) / Σ(active_category_weights + root_weights) × 100`; vráti `null` ak žiadne aktívne elementy

- [X] T019 [P] [US3] Vytvoriť `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/IndexCalculatorGroupTest.kt` — unit testy pre `computeDailyIndexGrouped`: (a) kategória s 1 elementom (weight 11.0, done=1.0) → rovnaký index ako kategória s 3 elementmi (weight 5.5 každý, všetky done=1.0); (b) z 3 aktívnych sub-entít iba 1 done → index kategórie ≈ 1/3 hodnoty ako keby boli všetky done; (c) všetky elementy neaktívne → vracia `null`; (d) root element (parent=null) prispieva priamo bez normalizácie

- [X] T020 [US3] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — v `computeAndSaveDailyIndex` nahradiť volanie `IndexCalculator.computeDailyIndex(values, weightsMap, negativeKeys)` za `IndexCalculator.computeDailyIndexGrouped(values, elementConfig, getActiveElementKeys())` (závisí od T018, T017)

**Checkpoint**: US3 hotová — T019 zelené; index sa nemení výrazne po pridaní sub-entít do kategórie.

---

## Phase 6: User Story 4 — Používateľsky definované entity (Priority: P3)

**Goal**: Používateľ môže pridať vlastnú entitu pod existujúcu top-level kategóriu.

**Independent Test**: Pridať `yoga` pod `physical_activity` cez UI → entita sa objaví v Tracker screene → po reštarte stále existuje.

- [X] T021 [P] [US4] Rozšíriť `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — pridať `suspend fun addUserElement(key: String, weight: Double, impact: Int, parentCategory: String, description: String?, scale: List<Int>?): Boolean` (overí unikátnosť kľúča voči `elementConfig.elements`, vloží do `user_element` tabuľky, vráti `false` pri duplikáte); `suspend fun getUserElements(): List<UserElementEntity>`; `suspend fun removeUserElement(key: String)` (závisí od T008)

- [X] T022 [P] [US4] Rozšíriť `android_app/app/src/main/java/com/example/madhdtracker/ui/EntityManagementViewModel.kt` — pridať `fun addUserElement(key, weight, impact, parentCategory, description, scale)` volajúci `repository.addUserElement(...)`; pridať `StateFlow<List<UserElementEntity>>` pre user-defined entity; `fun removeUserElement(key)` (závisí od T021)

- [X] T023 [US4] Rozšíriť `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityManagementScreen.kt` — pridať `FloatingActionButton` alebo `Button` "Pridať entitu"; pri stlačení zobraziť `AlertDialog` s poľami: `key` (TextField), `weight` (NumberField), `impact` (+1/-1 DropdownMenu), `parentCategory` (Dropdown so systémovými kategóriami), `description` (optional TextField); odoslanie volá `viewModel.addUserElement(...)`; chybová hláška ak kľúč už existuje (závisí od T022)

- [X] T024 [US4] Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — v `getActiveElementKeys()` zahrnúť aj `getUserElements()` (user-defined entity sú vždy aktívne ak `isActive=true`); v `computeAndSaveDailyIndex` pri budovaní `elementConfig`-u pre `computeDailyIndexGrouped` mergovať user elements do `elementConfig.elements` a ich category do `elementConfig.categories` (závisí od T021, T020)

**Checkpoint**: US4 hotová — vlastná entita pridaná v UI sa objaví v Tracker screene a prispeje do indexu.

---

## Final Phase: Polish & Validácia

- [X] T025 [P] Spustiť `JAVA_HOME=/home/martin/.local/share/JetBrains/Toolbox/apps/android-studio/jbr ./gradlew :app:testDebugUnitTest` v `android_app/` — overiť zelené: `EntityConfigLoaderTest` (T005), `IndexCalculatorGroupTest` (T019), všetky existujúce testy
- [ ] T026 [P] Manuálna validácia scenárov S1, S2, S3 z `specs/007-comfigurable-entities/quickstart.md` — S1: Logcat tag EntityConfig; S2: nová entita v YAML bez zmeny kódu; S3: fallback pri chýbajúcom súbore
- [ ] T027 [P] Overiť že `DefaultWeights.kt` zostáva ako sekundárny fallback — `EntityConfigLoader` ho importuje iba pre prípad null/parse-error streamu; nie je primárny zdroj váh

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Žiadne závislosti
- **Foundational (Phase 2)**: Závisí od Phase 1 — **BLOKUJE US1–US4**
- **US1 (Phase 3)**: Závisí od Foundational
- **US2 (Phase 4)**: Závisí od US1 (TrackerRepository musí mať elementConfig)
- **US3 (Phase 5)**: Závisí od US1 (computeDailyIndexGrouped potrebuje elementConfig v Repository)
- **US4 (Phase 6)**: Závisí od US2 (EntityManagementScreen) + US3 (index calculation)
- **Polish**: Závisí od US1–US3 (US4 voliteľné)

### User Story Dependencies

| Story | Závisí od | Môže ísť paralelne s |
|-------|-----------|----------------------|
| US1 (P1) | Foundational | — |
| US2 (P2) | US1 | US3 (rôzne súbory) |
| US3 (P2) | US1 | US2 (rôzne súbory) |
| US4 (P3) | US2 + US3 | — |

### Within Each User Story

- T013, T014 → paralelne (rôzne súbory) → T015 → T016 → T017 (US2)
- T018, T019 → paralelne → T020 (US3)
- T021, T022 → paralelne → T023 → T024 (US4)

---

## Parallel Example: US2 + US3 (po dokončení US1)

```
Paralelne spustiteľné po US1:
  US2: T013 (TrackerRepository override metódy) + T014 (EntityManagementViewModel)
  US3: T018 (IndexCalculator.computeDailyIndexGrouped) + T019 (IndexCalculatorGroupTest)

Po T013+T014: T015 (EntityManagementScreen) → T016 (NavGraph) → T017 (filter aktívnych)
Po T018+T019: T020 (TrackerRepository.computeAndSaveDailyIndex update)
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Phase 1: T001–T002
2. Foundational: T003 → T004 → T005 (paralelne s T006 → T007 → T008)
3. **STOP a VALIDUJ**: T005 zelený, AppDatabase kompiluje
4. US1: T009 → T010 → T011
5. **STOP a VALIDUJ**: S1 scenár z quickstart.md (Logcat EntityConfig)

### Incremental Delivery

1. Setup + Foundational → EntityConfigLoader funguje
2. US1 → MVP; entity z YAML; Logcat audit
3. US2 → Entity management; deaktivácia perzistovaná
4. US3 → Spravodlivý index pre kategórie
5. US4 → User-defined entity (voliteľné)

---

## Notes

- `[P]` tasky = rôzne súbory, žiadne závislosti v rámci fázy
- SnakeYAML 2.2: žiadne ProGuard pravidlá potrebné pre basic `Yaml().load()` s `Map<String,Any?>`
- `overall_feeling` má `parent: null` — je root entita, nepodlieha skupinovej normalizácii FR-006
- AppDatabase version 2 — `fallbackToDestructiveMigration()` je postačujúce pre dev fázu
- Existujúce testy (`AppConfigLoaderTest`, `NotificationRulesTest`, atď.) nesmú regresovať

---

## Phase 8: Convergence

- [X] T028 CRITICAL: Opraviť T008 — `AppDatabase` je JUŽ na `version = 2` s `AutoMigration(from=1, to=2)`; nové tabuľky `user_element_override` a `user_element` vyžadujú `version = 3` a `AutoMigration(from=2, to=3)`; T008 ako napísaný spôsobí runtime crash pri migrácii — upraviť `android_app/app/src/main/java/com/example/madhdtracker/data/AppDatabase.kt` na version=3 + AutoMigration(2→3) per plan: Room schema migration (contradicts)
- [X] T029 Aktualizovať `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt` — nahradiť hardcoded `val elements = listOf(ElementUiState("overall_feeling",...), ...)` dynamickým zoznamom odvodeným z `repository.getElementConfig().elements` (alebo prijatým cez konštruktor ako `elementConfig: ElementConfig`); `ElementUiState.label` nastaviť z `Element.description`; zachovať rovnaké poradie ako v `entities.yaml` (podľa category + key); bez tejto zmeny sa nové entity z YAML nezobrazia v Tracker screene per US1/AC1, FR-001, SC-001 (missing)
- [X] T030 Nahradiť `appConfig.weights.keys` za `elementConfig.elements.keys` v metóde `evaluateNotification()` v `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — riadok kde sa vytvára `NotificationRules(appConfig.notification, appConfig.weights.keys)` → `NotificationRules(appConfig.notification, elementConfig.elements.keys)` per FR-005, US2/AC1, plan: TrackerRepository touch-point (partial)
- [X] T031 Odvodiť `hasScale` z `ElementConfig` v `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt` — `ElementInputState.detailEnabled` inicializovať podľa `elementConfig.elements[key]?.scale != null` namiesto hardcoded `element.isSatisfaction`; `overall_feeling` zostáva scale element (scale != null v entities.yaml); ostatné binárne elementy (bez scale v YAML) dostanú `detailEnabled = false` per FR-001 (`scale` attribute drives UI), US1/AC1 (partial)

---

## Phase 9: Convergence

- [X] T032 Vytvoriť `android_app/app/src/test/java/com/example/madhdtracker/config/UserElementOverrideTest.kt` — JUnit4 unit testy (s mockovaným `UserElementOverrideDao`) pre `TrackerRepository.getActiveElementKeys()` a `setElementActive()`: (a) všetky elementy bez override → vráti všetky keys kde `elementConfig.elements[key].active == true`; (b) override `caffeine` na `isActive=false` → `getActiveElementKeys()` neobsahuje `caffeine`; (c) re-aktivácia `caffeine` cez `setElementActive("caffeine", true)` → `getActiveElementKeys()` opäť obsahuje `caffeine`; (d) override neexistujúceho kľúča → bezpečne ignorovaný; povinné podľa constitution §II a `plan.md:91` (`UserElementOverrideTest.kt (NEW)`) per plan: source structure, Constitution §II (missing)
- [X] T033 Pridať `fun getElementConfig(): ElementConfig` do `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — T029 (TrackerViewModel) volá `repository.getElementConfig().elements` ale T009 definuje `private val elementConfig`; bez tohto verejného getter-u T029 neskompiluje; zmena: z `private val elementConfig: ElementConfig` na `val elementConfig: ElementConfig` (package-internal), alebo pridať explicitnú metódu `fun getElementConfig(): ElementConfig = elementConfig` per T029, US1/AC1 (partial)
