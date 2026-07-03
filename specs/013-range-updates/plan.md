# Implementation Plan: Range Scale, Day Deletion, Future Date Guard

**Branch**: `013-range-updates` | **Date**: 2026-07-03 | **Spec**: [spec.md](spec.md)

## Summary

Tri súvisiace vylepšenia: (1) Konfigurovateľné rozsahy škál pre elementy vrátane záporných hodnôt (napr. sleep: -2..+2), (2) Mazanie celého dňa z detailu dňa v Android appke, (3) Blokácia budúcich dátumov v calendar pickeri a na serveri s automatizovanými testami.

Zmeny sú rozdelené na Android (Kotlin/Compose) a Server (FastAPI/Python). Žiadna Room DB migrácia nie je potrebná — záporné Int hodnoty SQLite akceptuje bez schémy.

## Technical Context

**Language/Version**: Kotlin (Android) + Python 3.11+ (Server)

**Primary Dependencies**:
- Android: Jetpack Compose + Material 3, Room, MVVM
- Server: FastAPI, Pydantic v2, pytest + httpx

**Storage**: Android Room (lokálna DB bez migrácie); FastAPI SQLAlchemy (bez zmeny schémy)

**Testing**:
- Android: Unit testy pre `value_effective` vzorec
- Server: pytest pre future-date validáciu na 4 endpointoch

**Target Platform**: Android 8.0+ (API 26+), Linux server

**Project Type**: Mobile app (Android) + Web API service (Server)

**Performance Goals**: Bez dopadu na výkon — zmeny sú lokálne výpočtové + UI

**Constraints**:
- `overall_feeling` element zachováva škálu 1–5 (Constitution Princip IV)
- Room DB migrácia sa nevyžaduje — `value_scale: Int?` akceptuje záporné hodnoty bez zmeny
- Zmazanie dňa platí len pre lokálnu DB; sync mazania je mimo scope
- Historické ADHD indexy sa neprepočítavajú retroaktívne

## Constitution Check

| Princíp | Stav | Poznámka |
|---------|------|----------|
| I. MVVM architektura | ✅ PASS | Repository pattern zachovaný; žiadna logika v ViewModel nad rámec koordinácie |
| II. Domenova logika indexu | ✅ MUSÍ | Zmena vzorca `value_effective` — POVINNÉ unit testy pre krajné hodnoty zápornej škály |
| III. Datový model | ✅ PASS | Room schéma sa nemení; `scale_min/max` sú konfiguračné hodnoty z YAML (nie DB stĺpce) |
| IV. UX pravidlá (overall_feeling 1-5) | ✅ KRITICKÉ | `overall_feeling` zostáva `scale_min=1, scale_max=5` bez výnimky |
| V. Notifikácie | ✅ N/A | Bez zmeny |
| VI. Testovanie | ✅ MUSÍ | Unit testy pre vzorec + pytest pre server validáciu |
| VII. Tech stack | ✅ PASS | Žiadne nové závislosti — Material 3 `SelectableDates` je súčasť existujúceho compose-material3 |

**Gate**: PASS — zmeny sú aditívne; constitution porušenie nehrozí ak `overall_feeling` zostane 1-5.

## Project Structure

### Documentation (this feature)

```text
specs/013-range-updates/
├── plan.md                ← tento súbor
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── android-ui.md
│   └── server-validation.md
└── tasks.md               ← generuje /speckit-tasks
```

### Source Code

```text
android_app/
├── app/src/main/
│   ├── assets/
│   │   └── entities.yaml                     ← scale_min/scale_max pre sleep
│   └── java/com/adhdtracker/
│       ├── data/model/
│       │   └── EntityNode.kt                 ← pridať scale_min, scale_max polia
│       ├── data/repository/
│       │   └── DayRepository.kt              ← pridať deleteDay(dayId) metódu
│       ├── domain/usecase/
│       │   └── ComputeIndexUseCase.kt        ← aktualizovať value_effective vzorec
│       └── ui/daydetail/
│           ├── DayDetailViewModel.kt         ← pridať deleteDay akciu
│           └── DayDetailScreen.kt           ← delete tlačidlo + dialóg + SelectableDates
└── app/src/test/
    └── java/com/adhdtracker/domain/
        └── ComputeIndexTest.kt               ← rozšíriť o záporné škály

server/
├── app/schemas/
│   ├── compute.py                            ← field_validator pre date
│   ├── sync.py                               ← field_validator pre date
│   └── migrate.py                            ← field_validator pre date
└── tests/api/
    └── test_future_date.py                   ← nový súbor: pytest testy
```

**Structure Decision**: Duálna štruktúra — Android (existujúci projekt) + Server (existujúci projekt). Žiadna nová projekt štruktúra.

## Implementation Strategy

### Fáza 1: Android — záporné škály (US1)
1. Rozšíriť `EntityNode.kt` o `scale_min` a `scale_max` s defaultmi `1` a `5`
2. Aktualizovať `entities.yaml` — sleep: `scale_min=-2, scale_max=2`
3. Aktualizovať `value_effective` výpočet: `(v - scale_min) / (scale_max - scale_min)`
4. Aktualizovať Slider komponent — `valueRange = scale_min.toFloat()..scale_max.toFloat()`
5. Pridať/rozšíriť unit testy pre `value_effective` s zápornou škálou

### Fáza 2: Android — zmazanie dňa (US2)
1. Pridať `deleteDay(dayId: Long)` do `DayRepository` + Room DAO
2. Pridať ViewModel akciu `deleteDay()`
3. Pridať "Zmazať deň" tlačidlo v `DayDetailScreen` s confirm dialógom
4. Navigácia späť po zmazaní (`popBackStack`)

### Fáza 3: Android + Server — budúce dátumy (US3)
1. Android: `SelectableDates` v Material 3 DatePicker
2. Android: ViewModel validácia pri ukladaní — ak dátum > dnes → zobraziť chybu
3. Server: Pydantic `@field_validator` na `date` pole v 4 schemách
4. Server: pytest testy v `tests/api/test_future_date.py`

## Key Decisions

| Rozhodnutie | Voľba | Dôvod |
|-------------|-------|-------|
| scale_min/max umiestnenie | YAML konfigurácia (EntityNode) | Nie Room DB — konfigurácia, nie dáta; bez migrácie |
| Room migrácia | Žiadna | `value_scale: Int?` akceptuje záporné hodnoty |
| Delete stratégia | CASCADE (existujúci) | Room CASCADE na EventValueEntity už existuje |
| Server validácia | Pydantic field_validator | Idiomatické pre FastAPI; validácia pred servisnou vrstvou |
| overall_feeling | Zostáva 1-5 | Constitution Princip IV — non-negotiable |
