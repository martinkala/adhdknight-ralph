# UI & Navigation Contracts: Visual UI Updates

## Navigation Routes

| Route | Parametre | Popis |
|-------|-----------|-------|
| `home` | – | Domovská obrazovka (existujúca) |
| `tracker` | – | Denný tracker (existujúci) |
| `trend` | – | Týždenný trend (existujúci) |
| `vector` | – | Vector (existujúci, ostáva pre backward compat) |
| `vector/{date}` | `date: String` ISO `YYYY-MM-DD` | **NOVÝ** – Vector pre konkrétny deň |

## Composable Signatures (kontrakty zmien)

### HomeScreen
```kotlin
@Composable
fun HomeScreen(
    viewModel: HomeViewModel,
    onEditClick: () -> Unit      // NOVÉ – navigácia na tracker
)
```

### TrendScreen
```kotlin
@Composable
fun TrendScreen(
    viewModel: TrendViewModel,
    onDayClick: (date: String) -> Unit   // NOVÉ – navigácia na vector/{date}
)
```

### DualBarChart
```kotlin
@Composable
private fun DualBarChart(
    items: List<DailySubIndexRow>,
    onDayClick: (date: String) -> Unit   // NOVÉ
)
```

### VectorScreen
```kotlin
@Composable
fun VectorScreen(
    viewModel: VectorViewModel,
    date: String? = null    // NOVÉ – ak null, načítaj latest; inak loadForDate(date)
)
```

## VectorViewModel – rozšírenie

```kotlin
val loadedDate = mutableStateOf<String?>(null)    // NOVÉ

fun loadForDate(date: String) {
    // volá repository.getValuesForDate(date) — existujúca metóda
}
```

## NavigationBar – zmeny

Odstrániť `Screen.VECTOR` z enum `Screen` v `MainActivity.kt`.

**Pred:**
```kotlin
enum class Screen { HOME, TRACKER, TREND, VECTOR, SETTINGS }
```

**Po:**
```kotlin
enum class Screen { HOME, TRACKER, TREND, SETTINGS }
```

## AppNavGraph – nový composable

```kotlin
composable(
    route = "vector/{date}",
    arguments = listOf(navArgument("date") { defaultValue = "" })
) { entry ->
    val date = entry.arguments?.getString("date") ?: ""
    LaunchedEffect(date) { vectorViewModel.loadForDate(date) }
    VectorScreen(vectorViewModel, date = date)
}
```
