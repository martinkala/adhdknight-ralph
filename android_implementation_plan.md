# Implementačný plán Android aplikácie (MVP)

## 1. Základ projektu
- Založiť Android projekt (Kotlin, Compose).
- Nastaviť architektúru (MVVM + Repository).
- Pripraviť databázu podľa `db_model.md`.

## 2. Dátová vrstva
- Implementovať entity/tabuľky: `event_day`, `event_value`, `satisfaction`, `weights`, `index_daily`, `index_weekly`, `notification_log`, `asrs_checkin`.
- Vytvoriť DAO pre CRUD.
- Seednúť default váhy z `design_plan_steps_6_7.md`.

## 3. Doménová logika
- Normalizácia hodnôt 0/1 vs 1–5.
- Výpočet denného indexu.
- Výpočet týždenného indexu.
- Adaptácia váh (po 15 dňoch, týždenne).
- Re‑kalibrácia podľa ASRS check‑inu.

## 4. UI – Core
- Home: denný index + spokojnosť.
- Denný tracker: 0/1 + detail 1–5, povinný „celkový pocit“.
- Týždenný trend: line chart.
- Advanced vektor: radar chart.

## 5. Notifikácie
- Denné pripomenutie (20:00, ak chýba vstup).
- Zanedbané oblasti (3 dni 0).
- Stres‑recovery trigger.
- Respect tiché okno a max 1 notifikácia/deň.

## 6. Nastavenia
- Prepínač detailného režimu.
- Export dát (CSV/JSON).
- Sync toggle (stub).

## 7. Testy
- Unit testy: výpočet indexu, adaptácia váh, re‑kalibrácia.
- Testy notifikačnej logiky.
