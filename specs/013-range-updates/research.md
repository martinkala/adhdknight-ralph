# Research: Range Scale, Day Deletion, Future Date Guard

**Feature**: 013-range-updates | **Date**: 2026-07-03

---

## R-001: Uloženie scale_min / scale_max pre elementy

**Decision**: Rozšíriť `EntityNode` (YAML konfigurácia entít) o polia `scale_min: Int` a `scale_max: Int`. Predvolené hodnoty: `scale_min = 1`, `scale_max = 5` (zachová spätná kompatibilita). Zmena sa prejaví v `entities.yaml` a v Kotlin data class `EntityNode`.

**Rationale**: Konfigurácia entít je už centralizovaná v YAML (entities.yaml načítaný cez `EntityRepository`). Pridanie dvoch polí do YAML a do `EntityNode` data class je minimálna zmena s nulovou migráciou Room DB (scale_min/max nie sú uložené v DB — sú súčasťou konfigurácie, nie dát).

**Alternatives considered**:
- Uložiť scale_min/max do Room `WeightEntity` — zbytočné, konfigurácia a váhy sú rôzne koncepty.
- Hardcoded enumerácia rozsahov — obmedzuje flexibilitu, YAML prístup je rozšíriteľnejší.

---

## R-002: Aktualizácia vzorca value_effective pre záporné škály

**Decision**: Zmeniť výpočet `value_effective` na generický normalizačný vzorec:
```
value_effective = (value_scale - scale_min) / (scale_max - scale_min)
```
Pre škálu -2..+2: `(-2-(-2))/(2-(-2)) = 0.0`, `(0-(-2))/(2-(-2)) = 0.5`, `(2-(-2))/(2-(-2)) = 1.0` ✅

Pre pôvodnú škálu 1..5 (zachová spätná kompatibilita): `(1-1)/(5-1) = 0.0`, `(3-1)/(5-1) = 0.5`, `(5-1)/(5-1) = 1.0` ✅

**Rationale**: Generický vzorec zachová existujúce správanie pre 1-5 a správne normalizuje akýkoľvek rozsah na [0, 1]. ADHD index teda zostane vždy 0-100.

**Alternatives considered**:
- Zachovať `(v-1)/4` a mapovať záporné hodnoty pred výpočtom — zbytočná komplexnosť.
- Offset normalizácia s pevnou škálou — neflexibilné.

**Constitution impact (Principle II)**: Zmena vzorca `value_effective` je NON-NEGOTIABLE zmena domény a MUSÍ byť krytá unit testami. Existujúce testy sa musia rozšíriť o scenáre so zápornou škálou.

---

## R-003: Celkový pocit (overall_feeling) — zachovanie škály 1-5

**Decision**: `overall_feeling` zachová škálu `scale_min=1, scale_max=5` aj po tejto zmene. Constitution (Princip IV) explicitne hovorí: "Celkový pocit je vždy povinný a vždy škála 1-5." Toto sa nemení.

**Rationale**: Zmena škály sa týka iných elementov (napr. `sleep`, `stress_work`). Používateľ v spec.txt nespomenul overall_feeling ako kandidáta. Constitution je nadradená spec.

---

## R-004: Zmazanie dňa — Room CASCADE

**Decision**: Použiť existujúci Room CASCADE `onDelete` na `EventValueEntity` (FK na `EventDayEntity`). Zmazanie `EventDayEntity` automaticky zmaže všetky `EventValueEntity` záznamy pre daný deň. Taktiež zmazať `IndexDailyEntity` (CASCADE existuje). Použiť `confirmDelete` dialog v Compose.

**Rationale**: Room CASCADE je už definovaný v entitách (Princip III). Nevyžaduje sa manuálne mazanie každej hodnoty. Potvrdzovacie dialógové okno je požiadavka spec (FR-006) a súlad s UX princípom IV (nízke trenie, ale ochrana pred nehodou).

**Alternatives considered**:
- Soft delete (príznak `is_deleted`) — zbytočná zložitosť pre lokálnu operáciu, nespomína sa v spec ani constitution.

---

## R-005: Obmedzenie DatePicker na dnešok (Android Compose)

**Decision**: Použiť `DatePickerDefaults.dateValidator` / `SelectableDates` v Material 3 `DatePicker` na zakázanie budúcich dátumov. Konkrétne: `selectableDates = object : SelectableDates { override fun isSelectableDate(utcTimeMillis: Long) = utcTimeMillis <= System.currentTimeMillis() }`.

**Rationale**: Material 3 DatePicker API v Jetpack Compose poskytuje `selectableDates` pre tento účel. Je to štandardný, natívny spôsob bez custom implementácie.

**Alternatives considered**:
- Vlastná implementácia calendar UI — zbytočné.
- Validácia len na strane ViewModel bez UI blokovania — horšia UX, umožňuje kliknúť na budúci dátum a potom dostať chybu.

---

## R-006: Validácia budúceho dátumu na serveri (FastAPI)

**Decision**: Pridať Pydantic validátor na pole `date: str` v `DaySyncItem` a `MigrationDayItem` schemách. Validátor použije `datetime.date.today()` (UTC) na porovnanie. Pri neúspechu vráti HTTP 422 s opisom `"Date cannot be in the future"`.

**Rationale**: Pydantic v2 field validators sú idiomatické riešenie pre FastAPI. Validácia na úrovni schémy zaručí, že nevhodný dátum nikdy nedosiahne servisnú vrstvu. Testy sú jednoznačné (pytest + httpx).

**Affected endpoints**: `POST /api/v1/sync/batch`, `POST /api/v1/migrate`, `POST /api/v1/compute/daily`, `POST /api/v1/compute/range`.

---

## R-007: Room DB migrácia pre value_scale záporné hodnoty

**Decision**: **Žiadna migrácia Room DB nie je potrebná.** Stĺpec `value_scale` v `EventValueEntity` je typ `Int` (nullable) bez CHECK constraint na rozsah. Záporné čísla SQLite akceptuje bez zmeny schémy.

**Rationale**: SQLite nemá CHECK constraints na rozsah cez Room anotácie. Existujúce dáta (hodnoty 1-5) zostanú platné. Nové dáta (-2 až +2) sa uložia bez konfliktu.

**Note**: `value_effective` sa ukladá ako `Float` a bude prepočítaný pri ukladaní s novým vzorcom (R-002). Historické `value_effective` hodnoty (uložené s 1-5 škálou) zostanú nezmenené — netýka sa retroaktívneho prepočtu.
