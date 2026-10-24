# Specification: food-009 — Export dát a endpoint zmien

## Status: COMPLETE

## Feature: CSV/JSON export na analýzu mimo aplikácie + „zmeny od“ pre budúci Android sync

### Overview
Dáta sa analyzujú mimo aplikácie, preto musí byť export úplný, stabilný a strojovo čitateľný.
JSON export je zároveň vstupný formát importu (food-011) a výstupný formát LLM importu
(`docs/food/import-mapping.md`). Endpoint zmien pripraví API na offline sync Android appky (constitution B2).

### User Stories
- Ako používateľ chcem stiahnuť všetky svoje dáta za obdobie v CSV alebo JSON.
- Ako budúca Android appka chcem dostať iba zmeny od posledného syncu, vrátane zmazaných položiek.

---

## Functional Requirements

### FR-1: JSON export
`GET /api/v1/food/export?format=json&from=YYYY-MM-DD&to=YYYY-MM-DD` (obe voliteľné) →
`application/json`, `Content-Disposition: attachment; filename="food-diary-<from>-<to>.json"`:
```json
{
  "schema_version": "1.0",
  "app_id": "food_diary",
  "exported_at": "2026-10-24T18:00:00Z",
  "days": [
    {
      "date": "2026-10-23",
      "sleep_quality": null, "stool": 6, "gas": 3,
      "entries": {"breakfast": [{"text": "ryza", "quantity": null, "unit": null}],
                  "sport": [{"text": "bike 30 km", "quantity": null, "unit": null, "intensity": 3}], "...": []},
      "weights": [{"kg": 80.6, "measured_at": null, "note": null}],
      "blood_pressures": [{"systolic": 125, "diastolic": 90, "pulse": null, "measured_at": null, "note": null}]
    }
  ]
}
```
Dni zoradené vzostupne. Všetky kategórie D2 sú vždy prítomné (aj prázdne). Bez interných ID
a bez zmazaných dát. Schéma je v OpenAPI ako `FoodExport` (použije ju food-011).

**Acceptance Criteria:**
- [x] API test: export obsahuje iba dni v rozsahu, vzostupne, bez zmazaných dní a záznamov
- [x] API test: všetky kategórie sú prítomné aj prázdne; čísla sú čísla (nie stringy)
- [x] API test izolácie: export nikdy neobsahuje dáta iného používateľa

### FR-2: CSV export
`format=csv` → `text/csv; charset=utf-8` s BOM (otvorí sa v Exceli správne s diakritikou), oddeľovač čiarka,
RFC 4180 úvodzovky. **Dlhý formát** (1 riadok = 1 údaj), stĺpce:
`date,record_type,category,text,quantity,unit,intensity,value,systolic,diastolic,pulse,measured_at,note`
- `record_type` ∈ `entry` | `weight` | `blood_pressure` | `day_value`
- `day_value`: `category` ∈ `sleep_quality|stool|gas`, číslo v `value`
- `weight`: kg v `value`
- desatinná bodka, prázdne bunky pre chýbajúce hodnoty

**Acceptance Criteria:**
- [x] API test: CSV sa dá načítať `csv.DictReader`, hlavička presne podľa spec, BOM na začiatku
- [x] API test: text s čiarkou a úvodzovkami sa správne escapuje
- [x] API test: počet riadkov = počet záznamov + meraní + vyplnených hodnôt dňa

### FR-3: Endpoint zmien
`GET /api/v1/food/changes?since=<ISO8601 UTC>&limit=500` → `{schema_version, server_time,
days: [...], entries: [...], weights: [...], blood_pressures: [...], med_dictionary: [...], has_more}`.
Vráti entity používateľa s `updated_at > since` vrátane zmazaných (`deleted_at` vyplnené), s ID.
`server_time` použije klient ako ďalšie `since`. Bez `since` = všetko. Stránkovanie cez `has_more` + `limit`.
Každá zmena (vrátane soft delete) musí aktualizovať `updated_at`. Over to pre všetky entity.

**Acceptance Criteria:**
- [x] API test: po vytvorení, úprave a zmazaní záznamu vráti `changes?since=T0` záznam s `deleted_at`
- [x] API test: `changes?since=server_time` hneď po predchádzajúcom volaní vráti prázdne zoznamy
- [x] API test izolácie

### FR-4: UI exportu
`/food/export/` (`data-testid="export-form"`): od–do (default celé obdobie), formát CSV/JSON, tlačidlo
Stiahnuť. Django prúdi súbor z API k používateľovi (správny `Content-Type` a `Content-Disposition`).
Odkaz vo food navigácii.

**Acceptance Criteria:**
- [x] e2e: stiahnutie CSV a JSON (Playwright `expect_download`), súbor nie je prázdny a obsahuje zadaný záznam
- [x] Django test: view preposiela hlavičky z API

---

## Success Criteria
- Celý export sa dá načítať do pandas/Excel bez ručných úprav.

## Dependencies
- food-007

## Assumptions
- Objem dát je malý (roky × stovky riadkov), export môže byť generovaný v pamäti.

---

## Completion Signal

### Implementation Checklist
- [x] JSON export + schéma `FoodExport`
- [x] CSV export
- [x] `/changes`
- [x] UI exportu

### Testing Requirements
- [x] `./scripts/test-food.sh` → exit 0

### Iteration Instructions
Ak niečo zlyhá: oprav, spusti testy znova, over kritériá, commitni a pushni. Až keď je všetko zelené: `<promise>DONE</promise>`.

## Implementation notes
- JSON export: každý záznam má vždy kľúč `intensity` (mimo športu `null`), aby mali všetky záznamy rovnaké stĺpce.
- Názov súboru bez `from`/`to`: chýbajúci koniec = prvý/posledný exportovaný deň, bez dní dnešný dátum.
  `from > to` → 422 `invalid_range`.
- CSV poradie v rámci dňa: hodnoty dňa, záznamy v poradí kategórií D2, váhy, tlaky. Konce riadkov CRLF (RFC 4180).
- `/changes`: `limit` max. 1000. Stránka nikdy nerozdelí skupinu zmien s rovnakým `updated_at` (zmazanie dňa
  označí deň aj všetky jeho záznamy jedným časom); ak je skupina väčšia ako `limit`, vráti sa celá.
  Pri `has_more` je `server_time` posledné `updated_at` stránky, inak čas pred dotazmi. `since` bez zóny = UTC.
  Záznamy, váhy a tlaky majú `day_id`, slovník je kľúčovaný `text_norm`.
- UI exportu je GET formulár (sťahovanie, bez CSRF); Django súbor preposiela z pamäte (dáta sú malé).

<!-- NR_OF_TRIES: 1 -->
