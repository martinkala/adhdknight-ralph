# Quickstart: Range Scale, Day Deletion, Future Date Guard

**Feature**: 013-range-updates | **Date**: 2026-07-03

---

## Prerequisites

- Android Studio s projektom `android_app/`
- Python 3.11+ pre server testy
- `server/.venv` aktivovaný alebo `make install` spustený

---

## SC-001: Záporná hodnota škály sa uloží a zobrazí

**Setup**: Element `sleep` má `scale_min=-2`, `scale_max=2` v `entities.yaml`

**Kroky**:
```
1. Otvoriť aplikáciu → dnesny tracker
2. Aktivovať "Sleep" (Switch → ON)
3. Posunúť slider na hodnotu -1
4. Uložiť
5. Znova otvoriť deň
```

**Očakávaný výsledok**: Slider zobrazuje -1, zápisom sa vytvorí `value_scale=-1`, `value_effective=0.25`

**Výpočet**: `(-1 - (-2)) / (2 - (-2)) = 1/4 = 0.25` ✅

---

## SC-002: ADHD index zostáva 0-100 s negatívnou hodnotou

**Setup**: Spánok na -2 (minimum), ostatné elementy OFF

**Kroky**:
```
1. Nastaviť sleep = -2
2. Všetky ostatné elementy = 0 / OFF
3. Skontrolovať index na home obrazovke
```

**Očakávaný výsledok**: Index = 0.0 (nie záporné číslo, nie >100)

---

## SC-003: Zmazanie dňa

**Setup**: Existujúci deň s aspoň jednou hodnotou

**Kroky**:
```
1. Otvoriť detail dňa
2. Kliknúť "Zmazať deň"
3. V dialógu kliknúť "Zmazať"
4. Vrátiť sa na kalendár
```

**Očakávaný výsledok**: Deň nie je označený ako vyplnený, všetky hodnoty sú vymazané

---

## SC-004: Zrušenie zmazania dňa

**Kroky**:
```
1. Otvoriť detail dňa
2. Kliknúť "Zmazať deň"
3. V dialógu kliknúť "Zrušiť"
```

**Očakávaný výsledok**: Deň zostáva nezmenený, hodnoty sú zachované

---

## SC-005: DatePicker nedovolí budúci dátum

**Kroky**:
```
1. Otvoriť výber dátumu
2. Pokúsiť sa kliknúť na zajtrajší dátum
```

**Očakávaný výsledok**: Zajtrajší dátum je zašednutý, klik nemá efekt

---

## SC-006: Server odmietne budúci dátum (pytest)

```bash
cd server
make test
# alebo priamo:
.venv/bin/pytest tests/api/test_future_date.py -v
```

**Očakávaný výsledok**:
```
tests/api/test_future_date.py::test_compute_daily_future_date PASSED
tests/api/test_future_date.py::test_sync_batch_future_date PASSED
tests/api/test_future_date.py::test_compute_daily_today_ok PASSED
tests/api/test_future_date.py::test_compute_daily_past_ok PASSED
```

---

## SC-007: Spätná kompatibilita — overall_feeling zostáva 1-5

**Kroky**:
```
1. Otvoriť dnesny tracker
2. Nastaviť "Celkový pocit" slider
```

**Očakávaný výsledok**: Slider zobrazuje rozsah 1-5 (nie -2 až +2)
