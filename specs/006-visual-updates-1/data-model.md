# Data Model: Visual UI Updates – Home, Trend, Menu & Tracker

## Zmeny dátového modelu

Táto feature neintrodukuje žiadne nové Room entity ani DB migrácie. Všetky zmeny sú na UI a navigačnej vrstve.

## Existujúce entity relevantné pre túto feature

### DailySubIndexRow (nemodifikovaná)
```
date: String          // ISO dátum "YYYY-MM-DD" — použitý ako nav argument pre Vector stránku
positiveIndex: Double?
negativeIndex: Double?
```

### EventValueEntity (nemodifikovaná)
Vracia `repository.getValuesForDate(date)` — existujúca metóda, bez zmeny.

## Nové navigačné kontrakty (UI-level)

### Nový route: `vector/{date}`
- **Parameter**: `date: String` — ISO formát `YYYY-MM-DD`
- **Zdroj**: `DailySubIndexRow.date` z `TrendViewModel.dualSeries`
- **Cieľ**: `VectorScreen` načítaný pre konkrétny deň
- **Repository call**: existujúci `getValuesForDate(date: String)`

### Rozšírený VectorViewModel
```
entities: MutableState<Map<String, EventValueEntity>>   // existujúce
loadedDate: MutableState<String?>                        // nové — zobrazuje nadpis dátumu
```
Nová metóda `loadForDate(date: String)` – volá existujúci `repository.getValuesForDate(date)`.

## Rozhranie HomeScreen (UI kontrakt)

Nový parameter:
```
onEditClick: () -> Unit    // callback pre navigáciu na tracker
```

## Rozhranie TrendScreen / DualBarChart (UI kontrakt)

Nové parametre:
```
TrendScreen:   onDayClick: (date: String) -> Unit
DualBarChart:  items, onDayClick: (date: String) -> Unit
```
