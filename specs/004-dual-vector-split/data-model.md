# Data Model: Dual Vector Split

## Rozšírené entity

### `IndexDailyEntity` (MODIFY — DB migrácia v1→v2)

**Lokácia**: `android_app/app/src/main/java/com/example/madhdtracker/data/Entities.kt`

| Pole | Typ | Zmena | Popis |
|------|-----|-------|-------|
| `id` | `Long` | existujúce | PK, autoGenerate |
| `eventDayId` | `Long` | existujúce | FK na `EventDayEntity` |
| `indexValue` | `Double` | existujúce | Kombinovaný ADHD index 0–100 |
| `positiveIndex` | `Double?` | **NOVÉ** | Pozitívny sub-index 0–100; NULL pre historické záznamy |
| `negativeIndex` | `Double?` | **NOVÉ** | Negatívny sub-index 0–100 (vyšší=horšie); NULL pre historické záznamy |

**DB migrácia**: Room `@AutoMigration(from = 1, to = 2)` — pridanie dvoch nullable stĺpcov `REAL`.
Vyžaduje `exportSchema = true` v `@Database` a `ksp { arg("room.schemaLocation", ...) }` v `build.gradle.kts`.

---

## Nové domain modely

### `DailySubIndexRow` (NEW)

**Lokácia**: `android_app/app/src/main/java/com/example/madhdtracker/data/Models.kt`

| Pole | Typ | Popis |
|------|-----|-------|
| `date` | `String` | Dátum (ISO-8601) |
| `positiveIndex` | `Double?` | Pozitívny sub-index; null ak nie sú dáta |
| `negativeIndex` | `Double?` | Negatívny sub-index; null ak nie sú dáta |

---

## Nové DAO metódy

### `IndexDao` (MODIFY)

```
// NOVÁ query — vracia dual-index sériu pre Trend screen
getLatestDualWithDate(limit: Int): List<DailySubIndexRow>
```

SQL:
```sql
SELECT event_day.date, index_daily.positiveIndex, index_daily.negativeIndex
FROM index_daily
INNER JOIN event_day ON index_daily.eventDayId = event_day.id
ORDER BY event_day.date DESC
LIMIT :limit
```

Existujúca `getLatestDailyWithDate()` zostáva (používa ju `TrendViewModel` — zachovať pre spätnosť kompatibilitu alebo refaktorovať v tomto kroku).

---

## Rozšírené Repository metódy

### `TrackerRepository` (MODIFY)

**Rozšíriť `computeAndSaveDailyIndex(dayId)`**:
- Teraz počíta aj `positiveIndex` a `negativeIndex` cez nové metódy `IndexCalculator`
- `IndexDailyEntity` sa uloží s hodnotami všetkých troch polí

**Nové metódy**:
```
suspend fun getLatestSubIndices(): Pair<Double?, Double?>
    → vracia (positiveIndex, negativeIndex) z posledného záznamu

suspend fun getLatestDualIndexSeries(limit: Int): List<DailySubIndexRow>
    → volá IndexDao.getLatestDualWithDate(limit)
```

---

## Rozšírená domain logika

### `IndexCalculator` (MODIFY)

**Dve nové metódy** (POVINNÉ unit testy — Constitution § II):

```
fun computePositiveIndex(
    values: List<EventValueEntity>,
    weights: Map<String, WeightEntity>,
    positiveKeys: Set<String>    // DefaultWeights.weights.keys - negativeKeys
): Double?
// Filtrovanie len na positiveKeys; žiadna inverzia; vážený priemer × 100

fun computeNegativeIndex(
    values: List<EventValueEntity>,
    weights: Map<String, WeightEntity>,
    negativeKeys: Set<String>    // DefaultWeights.negativeKeys
): Double?
// Filtrovanie len na negativeKeys; BEZ inverzie (vyšší e_i = horšie správanie); vážený priemer × 100
```

Vzorec pre oba (líšia sa len filtrom kľúčov a tým, že negativeIndex NEINVERTUJE):
```
SubIndex = 100 × Σ(w_i × e_i for i in filteredKeys) / Σ(w_i for i in filteredKeys)
```

---

## ViewModel zmeny

### `HomeViewModel` (MODIFY)

Nové state polia:
```kotlin
val positiveIndex = mutableStateOf<Double?>(null)
val negativeIndex = mutableStateOf<Double?>(null)
```
Naplnené z `repository.getLatestSubIndices()` v `refresh()`.

### `TrendViewModel` (MODIFY)

Nové/zmenené state pole:
```kotlin
val dualSeries = mutableStateOf<List<DailySubIndexRow>>(emptyList())
```
Naplnené z `repository.getLatestDualIndexSeries(7)` v `refresh()`.

---

## Vzťahy — beze zmeny

Všetky existujúce FK väzby (`IndexDailyEntity → EventDayEntity`) zostávajú. Nové stĺpce sú nullable → žiadne NOT NULL constraint problémy pri migrácii.

---

## Klasifikácia kľúčov (zdroj pravdy: `DefaultWeights`)

| Skupina | Kľúče |
|---------|-------|
| Pozitívne | `sleep`, `physical_activity`, `nutrition_protein`, `mindfulness` |
| Negatívne | `stress_work`, `stress_personal`, `alcohol`, `caffeine` |
| Vylúčené z sub-indexov | `overall_feeling` (target variable) |
