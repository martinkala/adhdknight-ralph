# Tasks: Dual Vector Split (Positive/Negative ADHD Sub-Indices)

**Input**: Design documents from `specs/004-dual-vector-split/`

**Prerequisites**: [plan.md](plan.md) · [spec.md](spec.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/ui-contracts.md](contracts/ui-contracts.md)

**Závislosť**: Feature 003 (`003-radar-visual-distinction`) musí byť implementovaná pred Phase 5 — `RadarElementData` a `ElementClassification` sú potrebné pre US3.

**Constitution gates (§ II + § VI)**: T007 a T012 sú povinné pred mergom.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Môže bežať paralelne (rôzne súbory, žiadne závislosti)
- **[Story]**: Ktorej user story task patrí (US1, US2, US3)

---

## Phase 1: Setup (Room export schema)

**Purpose**: Aktivovať Room `exportSchema` a pripraviť scaffolding pre `@AutoMigration`. Musí prebehnúť pred akýmikoľvek DB zmenami.

- [x] T001 Pridať `ksp { arg("room.schemaLocation", "$projectDir/schemas") }` do `android_app/app/build.gradle.kts`
- [x] T002 Zmeniť `exportSchema = false` na `exportSchema = true` v `android_app/app/src/main/java/com/example/madhdtracker/data/AppDatabase.kt` a spustiť build na vygenerovanie `app/schemas/.../1.json` (v1 snapshot)

**Checkpoint**: `app/schemas/` adresár existuje a obsahuje `1.json` — Room vie porovnať schémy pre AutoMigration.

---

## Phase 2: Foundational (DB schéma + domain logika)

**Purpose**: Core zmeny ktoré blokujú všetky user stories. Musí byť kompletné pred akoukoľvek obrazovkou.

**⚠️ CRITICAL**: Fázy US1–US3 nemôžu začať kým táto fáza nie je hotová.

- [x] T003 Pridať `val positiveIndex: Double? = null` a `val negativeIndex: Double? = null` do `IndexDailyEntity` v `android_app/app/src/main/java/com/example/madhdtracker/data/Entities.kt`
- [x] T004 Aktualizovať `AppDatabase.kt`: nastaviť `version = 2` a pridať `autoMigrations = [AutoMigration(from = 1, to = 2)]` (po dokončení T002 — `1.json` musí existovať)
- [x] T005 [P] Pridať `fun computePositiveIndex(values, weights, positiveKeys): Double?` do `android_app/app/src/main/java/com/example/madhdtracker/domain/logic/IndexCalculator.kt` — výpočet: `100 × Σ(w_i × e_i for positiveKeys) / Σ(w_i for positiveKeys)`, bez inverzie
- [x] T006 [P] Pridať `fun computeNegativeIndex(values, weights, negativeKeys): Double?` do `android_app/app/src/main/java/com/example/madhdtracker/domain/logic/IndexCalculator.kt` — rovnaký vzorec pre negativeKeys, bez inverzie (vyšší = horšie správanie)
- [x] T007 Pridať unit testy pre `computePositiveIndex` a `computeNegativeIndex` do `android_app/app/src/test/java/com/example/madhdtracker/domain/logic/IndexCalculatorTest.kt` — **§ II GATE: blokuje merge** · testy musia pokrývať: správnu hodnotu z mixu vstupov, ignorovanie kľúčov mimo skupiny, `null` pri prázdnych vstupoch
- [x] T008 Pridať `data class DailySubIndexRow(val date: String, val positiveIndex: Double?, val negativeIndex: Double?)` do `android_app/app/src/main/java/com/example/madhdtracker/data/Models.kt`
- [x] T009 Pridať `@Query` metódu `getLatestDualWithDate(limit: Int): List<DailySubIndexRow>` do `IndexDao` v `android_app/app/src/main/java/com/example/madhdtracker/data/Daos.kt` — JOIN `index_daily` s `event_day`, vrátiť `date`, `positiveIndex`, `negativeIndex`
- [x] T010 Rozšíriť `computeAndSaveDailyIndex(dayId)` v `android_app/app/src/main/java/com/example/madhdtracker/data/TrackerRepository.kt` — po výpočte `indexValue` vypočítať aj `positiveIndex` (cez `IndexCalculator.computePositiveIndex`) a `negativeIndex` (cez `IndexCalculator.computeNegativeIndex`); uložiť všetky tri hodnoty do `IndexDailyEntity`; `positiveKeys = DefaultWeights.weights.keys - DefaultWeights.negativeKeys`
- [x] T011 [P] Pridať `suspend fun getLatestSubIndices(): Pair<Double?, Double?>` do `TrackerRepository.kt` — vrátiť `(positiveIndex, negativeIndex)` z posledného `IndexDailyEntity` záznamu
- [x] T012 [P] Pridať `suspend fun getLatestDualIndexSeries(limit: Int): List<DailySubIndexRow>` do `TrackerRepository.kt` — volá `db.indexDao().getLatestDualWithDate(limit)`
- [x] T013 Napísať Room migration test `MigrationTest` v `android_app/app/src/test/java/com/example/madhdtracker/data/MigrationTest.kt` — **§ VI GATE: blokuje merge** · overiť: DB v1 s historickým záznamom → migrácia na v2 → stĺpce `positiveIndex` a `negativeIndex` existujú a sú `NULL` pre historický záznam

**Checkpoint**: `./gradlew test` prechádza — všetky unit testy aj migration test zelené. DB v2 schema je správna.

---

## Phase 3: User Story 1 — Home obrazovka dual index (Priority: P1) 🎯 MVP

**Goal**: Používateľ vidí zelený pozitívny index a červený negatívny index na Home obrazovke bez scrollovania.

**Independent Test**: Vyplniť tracker, otvoriť Home obrazovku, overiť 2 farebné indikátory (scenár 1 z quickstart.md).

- [x] T014 [US1] Pridať `val positiveIndex = mutableStateOf<Double?>(null)` a `val negativeIndex = mutableStateOf<Double?>(null)` do `android_app/app/src/main/java/com/example/madhdtracker/ui/HomeViewModel.kt`
- [x] T015 [US1] Rozšíriť `HomeViewModel.refresh()` o volanie `repository.getLatestSubIndices()` a naplnenie nových state polí v `android_app/app/src/main/java/com/example/madhdtracker/ui/HomeViewModel.kt`
- [x] T016 [US1] Pridať dual-index `Row` do `HomeScreen.kt` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/HomeScreen.kt` — pod existujúci `displaySmall` index text; zelený indikátor: farba `Color(0xFF81C784)`, popisok "Pozitívne ↑", hodnota z `positiveIndex`; červený indikátor: farba `Color(0xFFE57373)`, popisok "Negatívne ↓", hodnota z `negativeIndex`; ak `null` → zobraziť "—"

**Checkpoint**: Home obrazovka zobrazuje oba farebné indikátory. Kombinovaný index zostáva nezmenený.

---

## Phase 4: User Story 2 — Trend dual-bar chart (Priority: P2)

**Goal**: Trend obrazovka zobrazuje zelené a červené stĺpce per deň — vizuálne porovnanie oboch vektorov v čase.

**Independent Test**: 3+ dni dát → Trend obrazovka → každý deň má zelený aj červený stĺpec (scenár 2 z quickstart.md).

- [x] T017 [US2] Pridať `val dualSeries = mutableStateOf<List<DailySubIndexRow>>(emptyList())` do `android_app/app/src/main/java/com/example/madhdtracker/ui/TrendViewModel.kt`
- [x] T018 [US2] Rozšíriť `TrendViewModel.refresh()` o volanie `repository.getLatestDualIndexSeries(7)` a naplnenie `dualSeries` v `android_app/app/src/main/java/com/example/madhdtracker/ui/TrendViewModel.kt`
- [x] T019 [US2] Implementovať `DualBarChart` private composable v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrendScreen.kt` — stacked bar chart: zelená časť (pozitívny index) dole, červená (negatívny) hore, každá s číslom hodnoty
- [x] T020 [US2] Nahradiť `SimpleBarChart(series.map { it.indexValue })` za `DualBarChart(dualSeries)` v `TrendScreen` composable v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrendScreen.kt`
- [x] T021 [US2] Pridať legendu pod `DualBarChart` v `TrendScreen.kt` — `Row` s dvoma malými farebnými indikátormi: zelená bodka + "Pozitívne" a červená bodka + "Negatívne"

**Checkpoint**: Trend obrazovka zobrazuje dual-bar chart. Denné hodnoty zodpovedajú zadaným dátam.

---

## Phase 5: User Story 3 — Radar chart dva polygóny (Priority: P3)

**Goal**: Advanced vektor zobrazuje zelený polygon (pozitívne osi) a červený polygon (negatívne osi) oddelene.

**Závislosť**: Vyžaduje dokončenie feature 003 — `RadarElementData`, `ElementClassification` a aktualizovaný `VectorViewModel` musia byť implementované.

**Independent Test**: Otvoriť Advanced vektor → dva oddelené farebné polygóny viditeľné (scenár 3 z quickstart.md).

- [x] T022 [US3] Rozdeliť existujúci `dataPath` v `RadarChart` composable na `positivePath` a `negativePath` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/RadarChart.kt` — `positivePath` spája osi kde kľúč nie je v `DefaultWeights.negativeKeys`, `negativePath` kde áno
- [x] T023 [US3] Pridať kreslenie oboch polygónov do `RadarChart` Canvas v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/RadarChart.kt` — fill alpha 25%, stroke 2.5f, zelená pre pozitívne, červená pre negatívne; pôvodný single-path render odstránený
- [x] T024 [US3] Overiť, že `VectorScreen.kt` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/VectorScreen.kt` správne odovzdáva `viewModel.elements.value` do aktualizovaného `RadarChart` — bez funkčnej regresie

**Checkpoint**: Radar chart zobrazuje 2 oddelené farebné polygóny. Osi ostávajú farebné per feature 003.

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Validácia, edge cases, konzistencia.

- [x] T025 [P] Validovať scenár 4 (historické dáta pred migráciou) z `specs/004-dual-vector-split/quickstart.md` — kód overený: HomeScreen zobrazuje "—" pre null indexy, TrendScreen vykresľuje sivý placeholder stĺpec pre dni bez dát, fallbackToDestructiveMigration odstránený
- [ ] T026 [P] Overiť, že `HomeScreen` ostáva viditeľný bez scrollovania po pridaní dual-index Row — otestovať na malom emulátore (napr. Pixel 3a, 5.6")
- [x] T027 Spustiť `./gradlew test` z `android_app/` — všetky unit testy vrátane T007 gate testov a T013 migration testu musia prejsť
- [x] T028 Skontrolovať, že `SimpleBarChart` (pôvodný) nie je referencovaný nikde inde pred prípadným odstránením z `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrendScreen.kt`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Žiadne závislosti — začať ihneď
- **Phase 2 (Foundational)**: Závisí na Phase 1 (T002 musí byť hotové pred T004) — **blokuje US1–US3**
- **Phase 3 (US1)**: Závisí na Phase 2 completion
- **Phase 4 (US2)**: Závisí na Phase 2 completion — môže bežať paralelne s US1
- **Phase 5 (US3)**: Závisí na Phase 2 + feature 003 completion
- **Phase 6 (Polish)**: Závisí na všetkých desired US fázach

### Vnútri Phase 2

```
T001 → T002 → T003 → T004   (séria: build → schema → entity → DB version)
T002 → T005 [P]              (IndexCalculator metódy môžu bežať po T002)
T002 → T006 [P]
T005+T006 → T007             (unit testy po implementácii)
T003 → T008                  (DAO query závisí na novej entite)
T008+T005+T006 → T010        (Repository rozšírenie závisí na DAO + kalkulátore)
T010 → T011 [P]
T010 → T012 [P]
T004 → T013                  (migration test závisí na DB v2 definícii)
```

### User Story závislosti

- **US1 (P1)**: Závisí iba na Phase 2 — žiadne závislosti na US2/US3
- **US2 (P2)**: Závisí iba na Phase 2 — môže bežať paralelne s US1
- **US3 (P3)**: Závisí na Phase 2 **a** feature 003 — posledná

---

## Parallel Example: Phase 2 Foundational

```
# Tieto môžu bežať súčasne (rôzne súbory):
Task T005: computePositiveIndex() v IndexCalculator.kt
Task T006: computeNegativeIndex() v IndexCalculator.kt

# Po dokončení T010 môžu bežať súčasne:
Task T011: getLatestSubIndices() v TrackerRepository.kt
Task T012: getLatestDualIndexSeries() v TrackerRepository.kt

# Po dokončení Phase 2 môžu bežať súčasne:
Task T014-T016: HomeViewModel + HomeScreen (US1)
Task T017-T021: TrendViewModel + DualBarChart (US2)
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Dokončiť Phase 1: Setup (T001–T002)
2. Dokončiť Phase 2: Foundational (T003–T013) — všetky testy zelené
3. Dokončiť Phase 3: US1 (T014–T016) — dual index na Home obrazovke
4. **STOP a VALIDOVAŤ**: Home obrazovka zobrazuje oba farebné indikátory
5. Môžeš shipovaťMVP bez US2 a US3

### Incremental Delivery

1. Phase 1+2 → Foundation (DB + domain) hotová
2. + Phase 3 (US1) → Home dual index → MVP hotový ✓
3. + Phase 4 (US2) → Trend dual-bar chart → Bohatší trend pohľad ✓
4. + Phase 5 (US3, po feature 003) → Radar dual polygóny → Kompletný vizuálny zážitok ✓
5. Phase 6: Polish → Produkčná kvalita ✓

---

## Phase 7: Convergence

- [x] T029 Odstrániť `.fallbackToDestructiveMigration()` z `android_app/app/src/main/java/com/example/madhdtracker/MainActivity.kt` — s definovanou `@AutoMigration(from=1,to=2)` táto metóda rizikovo ničí všetky dáta pri zlyhaní migrácie, čo priamo odporuje FR-008 a SC-004 (contradicts)
- [x] T030 Pridať vizuálny placeholder pre dni bez sub-indexov do `DualBarChart` v `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/TrendScreen.kt` — dni kde `positiveIndex==null` a `negativeIndex==null` sú momentálne neviditeľné; nakresliť nízky šrafovaný alebo svetlosivý stĺpec ako indikátor chýbajúcich dát per US2/AC4 (partial)

---

## Notes

- [P] = rôzne súbory, žiadne závislosti — môžu bežať paralelne
- [USn] = mapuje task na user story pre traceabilitu
- **T007 a T013 sú constitution gates** — merge je blokovaný kým neprejdú
- `positiveIndex` je raw (0 = ideálne), `negativeIndex` je raw (0 = ideálne, 100 = maximum problémov)
- Farby konzistentné s feature 003: `#81C784` (zelená), `#E57373` (červená)
- `SimpleBarChart` môže byť odstránený po nahradení za `DualBarChart` v T020
