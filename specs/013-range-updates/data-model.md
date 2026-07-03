# Data Model: Range Scale, Day Deletion, Future Date Guard

**Feature**: 013-range-updates | **Date**: 2026-07-03

---

## Zmeny v existujúcich entitách

### EntityNode (Kotlin data class + YAML)

Rozšírenie konfiguračného objektu pre element. Nie je Room entita — načítava sa z `entities.yaml`.

```
EntityNode:
  + scale_min: Int = 1        // nové pole: minimálna hodnota škály (môže byť záporná)
  + scale_max: Int = 5        // nové pole: maximálna hodnota škály
  [existujúce polia zostávajú nezmenené]
```

**Validačné pravidlá**:
- `scale_min < scale_max` — povinné
- `scale_min` a `scale_max` sú relevantné len ak `hasScale = true`
- Predvolené hodnoty `(1, 5)` zachovávajú spätná kompatibilitu pre všetky existujúce elementy

**Dotknuté elementy v entities.yaml**:
| Element | Stará škála | Nová škála |
|---------|-------------|------------|
| `sleep` | 1–5 | -2–+2 |
| ostatné scale elementy | 1–5 | podľa rozhodnutia (môžu zostať 1–5) |
| `overall_feeling` | 1–5 | **zostáva 1–5** (constitution) |

---

### EventValueEntity (Room)

**Žiadna zmena schémy.** Stĺpec `value_scale: Int?` akceptuje záporné hodnoty bez migrácie.

Zmena sa týka len výpočtu `value_effective` pri ukladaní:

```
// Starý vzorec (hardcoded 1-5):
value_effective = (value_scale - 1) / 4.0f

// Nový vzorec (generický):
value_effective = (value_scale - scale_min).toFloat() / (scale_max - scale_min).toFloat()
```

**Dopad**: `value_effective` zostáva v rozsahu [0.0, 1.0] → ADHD index zostáva 0-100.

---

### EventDayEntity (Room)

**Žiadna zmena schémy.** Mazanie dňa využíva existujúci CASCADE:

```
EventDayEntity (id, date, ...)
  └── EventValueEntity (onDelete = CASCADE)
  └── IndexDailyEntity (onDelete = CASCADE)
  └── SatisfactionEntity (onDelete = CASCADE)
```

Mazanie `EventDayEntity` automaticky odstraňuje všetky závislé záznamy.

---

## Server-side schema zmeny

### DaySyncItem (FastAPI schema)

```python
class DaySyncItem(BaseModel):
    date: str
    ...
    
    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: str) -> str:
        from datetime import date
        if date.fromisoformat(v) > date.today():
            raise ValueError("Date cannot be in the future")
        return v
```

**Aplikovať na**: `DaySyncItem`, `MigrationDayItem`, `ComputeDailyRequest`, `DayInput` (v `ComputeRangeRequest`).

---

## Stavový diagram: Zmazanie dňa

```
[Deň s dátami] 
    → používateľ klikne "Zmazať deň"
    → [Confirm Dialog]
        → "Zrušiť" → [Deň s dátami] (nezmenený stav)
        → "Potvrdiť" → Repository.deleteDay(dayId)
            → Room CASCADE maže EventValueEntity, IndexDailyEntity, SatisfactionEntity
            → ViewModel notifikuje UI
            → [Navigácia späť na kalendár]
            → [Deň bez dát v kalendári]
```
