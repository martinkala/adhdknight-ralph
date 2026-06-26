# Android DB implementačné detaily (MVP)

## Lokálna DB
- Použiť Room (SQLite) ako lokálnu perzistenciu.
- Architektúra: Room DAO + Repository + ViewModel (MVVM).
- Offline‑first, bez závislosti na serveri.

## Entity mapovanie
- `event_day` → `EventDayEntity`
- `event_value` → `EventValueEntity`
- `satisfaction` → `SatisfactionEntity`
- `weights` → `WeightEntity`
- `index_daily` → `IndexDailyEntity`
- `index_weekly` → `IndexWeeklyEntity`
- `notification_log` → `NotificationLogEntity`
- `asrs_checkin` → `AsrsCheckinEntity`

## Kľúče a väzby
- `EventDayEntity.id` je PK.
- `EventValueEntity.eventDayId` FK na `event_day`.
- `SatisfactionEntity.eventDayId` FK na `event_day`.
- Indexy na `event_day.date` a `event_value.element_key`.

## Normalizácia hodnôt
- `value_effective` sa ukladá priamo do DB pre rýchly výpočet indexu.
- Ak `value_scale` != null → `value_effective = (value_scale - 1)/4`.
- Inak → `value_effective = value_binary`.

## Migrácie
- Verzovanie DB od `1`.
- MVP bez migrácií, pripraviť scaffolding.

## Sync (stub)
- Zatiaľ len lokálne ukladanie.
- Sync toggle v nastaveniach (bez implementácie).
