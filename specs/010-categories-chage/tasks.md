# Tasks: Unified Entity Tree (010-categories-chage)

**Input**: Design documents from `specs/010-categories-chage/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | quickstart.md ✅

**Format**: `[ID] [P?] [Story?] Description — file path`
- **[P]**: Parallelizovateľné (rôzne súbory, žiadne nevyriešené závislosti)
- **[Story]**: Príslušná user story (US1–US4)

---

## Phase 1: Setup

**Purpose**: Aktualizácia YAML konfigurácie na nový jednotný formát. Blocking prerekvizita pre všetky ďalšie fázy.

- [X] T001 Prepísať `entities.yaml` na nový `nodes:` formát — všetky uzly (overall_feeling, sleep, physical_activity, lifestyle, stress_work, stress_personal, head, mindfulness, Adiction, Procrastination, food, caffeine, alcohol, nutrition_protein, vitamins, organisation, pomodoro) podľa data-model.md; odstrániť staré `categories:` a `elements:` sekcie v `android_app/app/src/main/assets/entities.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Nový Kotlin dátový model a loader. MUSÍ byť kompletné pred akýmikoľvek caller updates.

**⚠️ KRITICKÉ**: Žiadna user story nemôže začať pred dokončením tejto fázy.

- [X] T002 Prepísať `ElementConfig.kt` — nahradiť `data class Category(...)`, `data class Element(...)`, `data class ElementConfig(...)` novými `data class EntityNode(key, weight, impact?, parent?, label, active, scale?, clickable)` a `data class EntityConfig(nodes: Map<String, EntityNode>)` vrátane computed properties `negativeKeys`, `positiveKeys`, `trackableNodes`, `groupNodes`, `trackableKeys` podľa data-model.md v `android_app/app/src/main/java/com/example/madhdtracker/domain/model/ElementConfig.kt`
- [X] T003 Prepísať `EntityConfigLoader.kt` — nahradiť parsing `categories:` + `elements:` sekcií novým parserom `nodes:` sekcie; každý uzol číta `label`, `weight`, `impact?`, `parent?`, `active`, `scale?`, `clickable?`; validácia: `weight > 0`, `impact in {null,-1,1}`, `parent` existuje v nodes, no cyklické referencie, `overall_feeling` musí byť prítomný; `buildFallback()` vrátiť EntityConfig s EntityNode objektmi v `android_app/app/src/main/java/com/example/madhdtracker/data/EntityConfigLoader.kt`
- [X] T004 Aktualizovať `EntityConfigLoaderTest.kt` — nahradiť testy pre starý `Category`+`Element` formát testami pre `EntityNode`+`EntityConfig`; pridať test pre `nodes:` YAML formát; overiť validáciu (chýbajúci overall_feeling → fallback) v `android_app/app/src/test/java/com/example/madhdtracker/config/EntityConfigLoaderTest.kt`

**Checkpoint**: `./gradlew :app:compileDebugKotlin` prejde — model je platný.

---

## Phase 3: User Story 1 — Regression-free Refactor (Priority: P1) 🎯 MVP

**Goal**: Všetky callers aktualizované na nové EntityConfig API; aplikácia funguje identicky ako pred refaktorom.

**Independent Test**: Otvoriť Tracker — rovnaký počet entít, rovnaký index pre existujúce záznamy (SC-001, SC-002, SC-003 z quickstart.md).

### Implementation

- [X] T005 [P] [US1] Aktualizovať `TrackerRepository.kt` — nahradiť `elementConfig.elements`, `elementConfig.categories`, `elementConfig.negativeKeys` → `entityConfig.trackableNodes`, `entityConfig.nodes`, `entityConfig.negativeKeys`; v `getAllWeights()` iterovať cez `entityConfig.trackableNodes.values`; v `buildEntityConfig()` zostaviť `EntityConfig` z `UserElementEntity` objektov ako `EntityNode` položky v `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt`
- [X] T006 [P] [US1] Aktualizovať `TrackerViewModel.kt` — nahradiť `elementConfig.categories.keys.forEach { catKey ->` → `entityConfig.groupNodes.keys.forEach { catKey ->`; `elementConfig.elements.values` → `entityConfig.trackableNodes.values`; zachovať logiku zoraďovania (overall_feeling first, potom root nodes, potom group children) — **zachovať** existujúci overall_feeling špeciálny prípad (removal je v T016) v `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt`
- [X] T007 [P] [US1] Aktualizovať `EntityManagementViewModel.kt` — nahradiť `repository.elementConfig.elements.keys` → `repository.elementConfig.trackableKeys` v `android_app/app/src/main/java/com/example/madhdtracker/ui/EntityManagementViewModel.kt`
- [X] T008 [P] [US1] Aktualizovať `EntityBarChart.kt` — nahradiť `elementConfig.elements` → `entityConfig.trackableNodes`; `elementConfig.categories[parentKey]?.label` → `entityConfig.nodes[parentKey]?.label`; `elementConfig.categories` refs v buildBarRows a PieChart v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityBarChart.kt`
- [X] T009 [P] [US1] Aktualizovať `EntityManagementScreen.kt` — nahradiť `elementConfig.categories.entries.forEach { (catKey, category) ->` → `entityConfig.groupNodes.entries.forEach { (catKey, node) ->`; `elementConfig.elements.values.filter { it.parent == catKey }` → `entityConfig.trackableNodes.values.filter { it.parent == catKey }`; `elementConfig.elements.values.filter { it.parent == null }` → `entityConfig.trackableNodes.values.filter { it.parent == null }`; `categories = elementConfig.categories.keys.toList()` → `entityConfig.groupNodes.keys.toList()` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/EntityManagementScreen.kt`
- [X] T010 [P] [US1] Aktualizovať `InfoScreen.kt` — nahradiť `elementConfig.categories` → `entityConfig.groupNodes`; `elementConfig.elements` → `entityConfig.trackableNodes` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/InfoScreen.kt`
- [X] T011 [P] [US1] Aktualizovať `NotificationWorker.kt` a `MainActivity.kt` — nahradiť `elementConfig.elements.keys` → `entityConfig.trackableKeys` na oboch miestach; `notifications/NotificationWorker.kt` a `MainActivity.kt` v `android_app/app/src/main/java/com/example/madhdtracker/`
- [X] T012 [P] [US1] Základný update `IndexCalculator.kt` — preložiť `computeDailyIndexGrouped(values, elementConfig, activeKeys)` na prácu s `EntityConfig`: root trackable nodes (`impact != null && parent == null`) → priamy príspevok; group nodes (`impact == null`) s deťmi → group_avg × groupNode.weight; podpis funkcie ostáva rovnaký okrem `elementConfig: ElementConfig` → `entityConfig: EntityConfig` v `android_app/app/src/main/java/com/example/madhdtracker/domain/logic/IndexCalculator.kt`
- [X] T013 [US1] Aktualizovať `IndexCalculatorGroupTest.kt` — nahradiť `ElementConfig(categories, elements)` → `EntityConfig(nodes)`; overiť, že existujúce testovacie scenáre prechádzajú bez zmeny výsledkov (SC-002) v `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/IndexCalculatorGroupTest.kt`

**Checkpoint**: `./gradlew :app:test` + `./gradlew :app:assembleDebug` prebehne. Aplikácia na zariadení ukazuje rovnaké entity a indexy ako pred feature 010.

---

## Phase 4: User Story 2 — Trackable Parent Logic (Priority: P2)

**Goal**: Root node s `impact != null` a aktívnymi potomkami prispieva k indexu ako vážený priemer potomkov × vlastná váha (nie priama hodnota).

**Independent Test**: Zapnúť root node aj jeho potomka v Trackeri — index sa vypočíta cez group avg potomkov (SC-004 z quickstart.md).

### Implementation

- [X] T014 [P] [US2] Rozšíriť `IndexCalculator.computeDailyIndexGrouped` o trackable parent logiku — pridať prípad: ak root trackable node (`parent == null && impact != null`) má aspoň 1 aktívneho potomka v activeKeys → použiť group_avg aktívnych potomkov × node.weight namiesto priamej hodnoty node; ak žiadni aktívni potomkovia → priama hodnota node (existujúce správanie) podľa D4 v research.md v `android_app/app/src/main/java/com/example/madhdtracker/domain/logic/IndexCalculator.kt`
- [X] T015 [P] [US2] Pridať unit testy pre trackable parent scenár do `IndexCalculatorGroupTest.kt` — test: root node zapnutý + potomok zapnutý → výsledok = group_avg × root.weight; test: root node zapnutý, žiadni potomkovia → priamy príspevok (Constitution §VI vyžaduje testy pre zmeny indexovej logiky) v `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/IndexCalculatorGroupTest.kt`

**Checkpoint**: `./gradlew :app:test` — nové testy prejdú.

---

## Phase 5: User Story 3 — overall_feeling De-hardcoding (Priority: P2)

**Goal**: TrackerViewModel neobsahuje žiadny hardkódovaný `if (key == "overall_feeling")` — zoraďovanie a slider/switch rozhodnutie vychádza z atribútov EntityNode.

**Independent Test**: `overall_feeling` sa stále zobrazuje ako prvý povinný slider 1–5 bez špeciálneho kódu (US3/AC1 z spec.md).

### Implementation

- [X] T016 [US3] Odstrániť hardkódované `overall_feeling` special cases z `TrackerViewModel.kt` — nahradiť `element.key == "overall_feeling"` → `element.scale != null` pre `detailEnabled`; nahradiť `elementConfig.elements["overall_feeling"]?.let { el -> ... }` blok generickým prístupom: zoradiť root nodes podľa `scale != null` first (overall_feeling prirodzene prvý vďaka YAML poradiu), potom root bez scale, potom group children; nahradiť `"overall_feeling" -> Pair(...)` v saveCurrent → generické `if (state.detailEnabled.value) Pair(scaleToInt, scale)` v `android_app/app/src/main/java/com/example/madhdtracker/ui/TrackerViewModel.kt`
- [X] T017 [US3] Build validácia — `./gradlew :app:compileDebugKotlin` musí prechádzať; `grep -r "overall_feeling" src/main/java` okrem YAML a TrackerRepository.kt musí vrátiť 0 výsledkov

**Checkpoint**: žiadne tvrdé referencie na "overall_feeling" string v UI/ViewModel vrstvách.

---

## Phase 6: User Story 4 — UserElementEntity.userId (Priority: P3)

**Goal**: `user_element` tabuľka má `userId` stĺpec pre budúci multi-user; Room AutoMigration 3→4 prebehne bez straty dát.

**Independent Test**: Nainštalovať feature 010 APK cez existujúcu inštaláciu — žiadna crash, `user_element` tabuľka obsahuje `userId TEXT DEFAULT NULL` (SC-001 z quickstart.md).

### Implementation

- [X] T018 [P] [US4] Pridať `val userId: String? = null` do `UserElementEntity` v `android_app/app/src/main/java/com/example/madhdtracker/data/Entities.kt`
- [X] T019 [P] [US4] Aktualizovať `AppDatabase.kt` — zmeniť `version = 3` → `version = 4`; pridať `AutoMigration(from = 3, to = 4)` do `autoMigrations` listu v `android_app/app/src/main/java/com/example/madhdtracker/data/AppDatabase.kt`

**Checkpoint**: `./gradlew :app:assembleDebug` prejde. Inštalácia cez existujúcu verziu nespôsobí crash.

---

## Phase 7: Polish & Validácia

**Purpose**: Build overenie, regresné testy, manuálna validácia.

- [X] T020 Finálny build + testy — `./gradlew :app:test :app:assembleDebug` všetko zelené; žiadne warning/error pre Entity annotations (Room KSP)
- [ ] T021 Manuálna validácia na zariadení podľa quickstart.md — SC-001 (žiadna dátová strata), SC-002 (index numericky rovnaký), SC-003 (rovnaký počet entít), SC-004 (trackable root node), SC-005 (načítanie < 200ms), SC-006 (user entity do 2s)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Žiadne — môže začať okamžite
- **Phase 2 (Foundational)**: Závisí na Phase 1 — **BLOKUJE** všetky user stories
- **Phase 3 (US1)**: Závisí na Phase 2 completion — môže začať po T002+T003+T004
- **Phase 4 (US2)**: Závisí na Phase 3 (T012 musí byť hotové — IndexCalculator base translation)
- **Phase 5 (US3)**: Závisí na Phase 3 (T006 musí byť hotové — TrackerViewModel base)
- **Phase 6 (US4)**: Závisí na Phase 2 — môže bežať paralelne s Phase 3/4/5 (rôzne súbory)
- **Phase 7 (Polish)**: Závisí na všetkých predchádzajúcich fázach

### User Story Dependencies

- **US1 (P1)**: Môže začať po Foundational (Phase 2) — žiadne závislosti na iných stories
- **US2 (P2)**: Závisí na T012 (base IndexCalculator translation z US1)
- **US3 (P2)**: Závisí na T006 (TrackerViewModel base update z US1)
- **US4 (P3)**: Závisí len na Phase 2 (Entities.kt + AppDatabase.kt sú nezávislé od US1-US3)

### Within Each Phase

- Všetky `[P]` tasky v Phase 3 môžu bežať paralelne (rôzne súbory)
- T013 závisí na T012 (nie je `[P]`)
- T014 + T015 sú navzájom paralelné
- T018 + T019 sú navzájom paralelné

---

## Parallel Example: Phase 3 (US1)

```bash
# Spustiť súbežne (rôzne súbory, všetky závisia len na T002/T003):
Task T005: TrackerRepository.kt
Task T006: TrackerViewModel.kt
Task T007: EntityManagementViewModel.kt
Task T008: EntityBarChart.kt
Task T009: EntityManagementScreen.kt
Task T010: InfoScreen.kt
Task T011: NotificationWorker.kt + MainActivity.kt
Task T012: IndexCalculator.kt (base)

# Po dokončení T012:
Task T013: IndexCalculatorGroupTest.kt (závisí na T012)
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Dokončiť Phase 1: entities.yaml
2. Dokončiť Phase 2: EntityNode + EntityConfig + Loader + Loader tests
3. Dokončiť Phase 3: US1 caller updates
4. **STOP a VALIDOVAŤ**: aplikácia funguje rovnako → SC-001, SC-002, SC-003
5. Commit MVP

### Incremental Delivery

1. Phase 1+2 → Foundation ready
2. Phase 3 (US1) → Regression-free refactor ✅
3. Phase 4 (US2) → Trackable parent logic ✅
4. Phase 5 (US3) → overall_feeling de-hardcoded ✅
5. Phase 6 (US4) → userId in user_element ✅

---

## Notes

- `[P]` = rôzne súbory, žiadne nevyriešené závislosti v rámci fázy
- `[Story]` = traceabilita na user stories z spec.md
- Constitution §II: IndexCalculator zmeny (T012, T014) MUSIA mať unit testy (T013, T015)
- Constitution §III: DB migrácia (T018, T019) — AutoMigration bez destructive changes
- Commit po každej dokončenej fáze alebo logickej skupiny taskov

---

## Phase 8: Convergence

- [X] T022 Aktualizovať `HomeViewModel.kt` — zmeniť `import com.example.madhdtracker.domain.model.ElementConfig` na `EntityConfig`; zmeniť `val elementConfig: ElementConfig get() = repository.elementConfig` na `val elementConfig: EntityConfig get() = repository.elementConfig` per FR-009 (missing) v `android_app/app/src/main/java/com/example/madhdtracker/ui/HomeViewModel.kt`
- [X] T023 Aktualizovať `VectorViewModel.kt` — zmeniť `import com.example.madhdtracker.domain.model.ElementConfig` na `EntityConfig`; zmeniť `val elementConfig: ElementConfig get() = repository.elementConfig` na `val elementConfig: EntityConfig get() = repository.elementConfig` per FR-009 (missing) v `android_app/app/src/main/java/com/example/madhdtracker/ui/VectorViewModel.kt`
- [X] T024 Aktualizovať `HomeScreen.kt` — ak T008 premenoval parameter `EntityDoubleBarChart` z `elementConfig` na `entityConfig`, zmeniť `elementConfig = viewModel.elementConfig` na `entityConfig = viewModel.elementConfig` na riadku 186 per plan: Source Code — dotknuté súbory (partial) v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt`
- [X] T025 Aktualizovať `VectorScreen.kt` — ak T008 premenoval parameter `EntityDoubleBarChart`/`PieChart` z `elementConfig` na `entityConfig`, zmeniť oba výskyty `elementConfig = viewModel.elementConfig` na `entityConfig = viewModel.elementConfig` na riadkoch 39, 47 per plan: Source Code — dotknuté súbory (partial) v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/VectorScreen.kt`
