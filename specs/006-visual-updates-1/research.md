# Research: Visual UI Updates – Home, Trend, Menu & Tracker

## Decision 1: Dátum na Home stránke

**Decision**: Použiť `java.time.LocalDate.now()` priamo v Composable, formátovať cez `DateTimeFormatter.ofPattern("d. M. yyyy")`.

**Rationale**: Bez ViewModel – dátum je čisto prezentačná hodnota bez závislosti na dátach. Neexistuje riziko nekonzistentnosti.

**Alternatives considered**: Pridanie `currentDate` do `HomeViewModel` – zbytočné, ViewModel nie je nutný pre statickú systémovú hodnotu.

---

## Decision 2: Výmena poradia a veľkosti fontov na Home

**Decision**: Swap kompozičného poradia aj `TextStyle` medzi sekciami:
- Pozitívne/Negatívne: `MaterialTheme.typography.displaySmall` (pôvodne ADHD index)
- ADHD index: `MaterialTheme.typography.titleMedium` + `labelMedium` popis (pôvodne pozitívne/negatívne)

**Rationale**: Obe hodnoty sú v existujúcej Card-e. Stačí zmeniť poradie blokov v Column a prehodiť `TextStyle` referencie. Žiadna nová závislosť.

**Alternatives considered**: Extrahovanie do separátnych komponentov – overengineering pre túto zmenu.

---

## Decision 3: Skratkové tlačidlo na tracker z Home stránky

**Decision**: Pridať `onEditClick: () -> Unit` callback parameter do `HomeScreen`. `AppNavGraph` ho prepojí s `navController.navigate(AppRoutes.TRACKER)`. Tlačidlo bude umiestnené v `Row` vedľa sekcie Pozitívne/Negatívne.

**Rationale**: Rovnaký vzor ako `onSaved` v `TrackerScreen` – konzistentné s existujúcou architektúrou. HomeScreen ostáva bez priamej dependency na `NavController`.

**Alternatives considered**: Priame vloženie `NavController` do `HomeScreen` – porušuje clean separation (Composable nesmie vedieť o navigácii priamo).

---

## Decision 4: Popisky dní v TrendScreen grafe

**Decision**: Zmeniť `DualBarChart` z čistého Canvas na `Column` wrapping Canvas (bary) + `Row` s `Text` labelmi pod ním. Každý label zobrazuje skrátený dátum (napr. "Po 23.6") cez `LocalDate.parse(date).format(DateTimeFormatter.ofPattern("EE d.M", Locale("sk")))`.

**Rationale**: Canvas nativne nepodporuje Composable Text elementy. Pridanie `Row` s Text composables pod canvas je najčistejší spôsob bez nutnosti `drawText` s `android.graphics.Paint` (čo je iný vizuálny systém).

**Alternatives considered**: 
- `drawText` v Canvas: funguje, ale mieša dva vizuálne systémy a je ťažšie na lokalizáciu.
- Plné nahradenie Canvas za Row of Composables: väčšia refaktorácia, mimo scope.

---

## Decision 5: Klikateľné dni v Trende → Vector stránka pre konkrétny deň

**Decision**: 
- Pridať `onDayClick: (date: String) -> Unit` parameter do `TrendScreen` a `DualBarChart`.
- V `DualBarChart` použiť `Modifier.pointerInput(items) { detectTapGestures { offset -> ... } }` na Canvas pre detekciu kliknutého stĺpca podľa X-ej súradnice.
- Pridať nový route `AppRoutes.VECTOR_DATE = "vector/{date}"` do `AppNavGraph`.
- Rozšíriť `VectorViewModel` o metódu `loadForDate(date: String)` využívajúcu existujúcu `repository.getValuesForDate(date)`.
- Pridať nový `composable(AppRoutes.VECTOR_DATE)` v `AppNavGraph`, ktorý číta `date` z nav argumentu a volá `viewModel.loadForDate(date)` cez `LaunchedEffect`.

**Rationale**: `getValuesForDate(date)` v `TrackerRepository` už existuje (riadok 115) – žiadna nová Repository metóda nie je potrebná. `pointerInput` na Canvas je štandardný Compose vzor pre hit-testing.

**Alternatives considered**:
- Nahradenie Canvas za Row clickable composables: čistejšie, ale väčší refaktor. Pointerinput je menší zásah.
- Samostatný ViewModel pre vector-by-date: zbytočné, `VectorViewModel` môže mať `loadForDate`.

---

## Decision 6: Odstránenie Vector z navigačného menu

**Decision**: Odstrániť `VECTOR` z `Screen` enum v `MainActivity.kt`. `AppRoutes.VECTOR` a jeho `composable` v `AppNavGraph` zostávajú (pre prípadný priamy prístup), avšak nový prístup pôjde cez `VECTOR_DATE` route z Trendu.

**Rationale**: Minimálna zmena – len enum item sa vymaže. NavigationBar sa automaticky prestane renderovať pre Vector. Ostatné časti kódu ostávajú nezmenené.

**Alternatives considered**: Úplné vymazanie `AppRoutes.VECTOR` route – zbytočné riziko, ak iné časti kódu na neho odkazujú.

---

## Decision 7: Presun tlačidla Uložiť v TrackerScreen

**Decision**: Zabaliť existujúci `Text("Denný tracker")` do `Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth())` spolu s `Button("Uložiť deň")`. Pôvodný `Button` na spodku Column sa vymaže. Logika onClick ostáva nezmenená – len premiestnená.

**Rationale**: Minimálna zmena. `Button` ako Composable môže byť kdekoľvek v strome bez obmedzení. Logika `onClick` sa len presunie, nie prepíše.

**Alternatives considered**: `TopAppBar` s action buttonom – zbytočná zmena architektúry pre jednoduchý presun tlačidla.
