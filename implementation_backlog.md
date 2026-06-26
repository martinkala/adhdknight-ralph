# Implementačné tasky (MVP backlog)

## 1) Dátový model a perzistencia
- Vytvoriť tabuľky podľa `db_model.md`.
- Seedovať default váhy.
- CRUD pre event_day, event_value, satisfaction.

## 2) Výpočet indexu
- Normalizácia dát (0/1 vs 1–5).
- Výpočet denného indexu.
- Výpočet týždenného indexu.

## 3) Adaptácia váh
- Korelácia element vs celkový pocit.
- Update váh 1× týždenne po 15 dňoch.
- Re‑kalibrácia podľa ASRS check‑inu.

## 4) UI – Denný tracker
- Zoznam elementov (0/1) + detail 1–5.
- Povinný „celkový pocit“.
- Uloženie dát.

## 5) UI – Prehľady
- Home (denný index + spokojnosť).
- Týždenný trend (line chart).
- Radar chart (advanced vektor).

## 6) Notifikácie
- Denné pripomenutie trackera.
- Zanedbané oblasti.
- Stres vs recovery.
- Respektovanie tichého okna a limitu 1× denne.

## 7) Nastavenia
- Prepínač detailného režimu.
- Export dát (CSV/JSON).
- Sync toggle (stub).
 - TODO: Export + share cez Android share sheet (FileProvider + ACTION_SEND).

## 8) Testy
- Výpočet indexu (unit).
- Adaptácia váh (unit).
- Notifikácie (logic test).
