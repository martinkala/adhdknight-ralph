# Contract: Android UI — Range Scale & Day Deletion

## Slider s konfigurovateľným rozsahom

### Input
```
element: EntityNode  // obsahuje scale_min, scale_max
currentValue: Int    // aktuálna hodnota (môže byť záporná)
onValueChange: (Int) -> Unit
```

### Behavior
- Slider zobrazuje hodnoty od `element.scale_min` do `element.scale_max`
- Krok (step): 1
- Zobrazuje aktuálnu hodnotu ako label (napr. "-1")
- Mapuje Float pozíciu slidera na Int hodnotu v rozsahu [scale_min, scale_max]

### Output (pri uložení)
```
value_scale: Int   // skutočná hodnota (napr. -1)
value_effective: Float  // = (value_scale - scale_min) / (scale_max - scale_min)
```

---

## Zmazanie dňa — UI kontrakt

### Trigger
Tlačidlo/akcia "Zmazať deň" v `DayDetailScreen` — viditeľná len ak deň existuje v DB.

### Confirm Dialog
```
Title: "Zmazať deň?"
Message: "Všetky záznamy pre [dátum] budú vymazané."
Buttons:
  - "Zrušiť" (dismiss, no action)
  - "Zmazať" (destructive, red)
```

### Post-delete navigation
Po úspešnom zmazaní: `navController.popBackStack()` → návrat na predchádzajúcu obrazovku.

---

## DatePicker — future date restriction

### Contract
```kotlin
SelectableDates {
    isSelectableDate(utcTimeMillis: Long): Boolean
    // Returns: utcTimeMillis <= today_midnight_utc
}
```

### Error state (fallback)
Ak by bol budúci dátum predaný programaticky (nie cez picker):
```
UI error: Snackbar / Toast: "Nemožno zadať budúci dátum"
Action: Uloženie je zablokované, dátum sa nenastaví
```
