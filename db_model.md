# DB model (MVP) – návrh

## Tabuľka: event_day
- id (PK)
- date (YYYY-MM-DD, unique)
- created_at
- updated_at

## Tabuľka: event_value
- id (PK)
- event_day_id (FK -> event_day.id)
- element_key (TEXT)  # napr. "sleep", "stress_work"
- value_binary (INTEGER 0/1)
- value_scale (INTEGER 1–5, NULL)
- value_effective (REAL 0–1)  # ak value_scale != NULL => (value_scale-1)/4, inak value_binary

## Tabuľka: satisfaction
- id (PK)
- event_day_id (FK -> event_day.id)
- value_scale (INTEGER 1–5)
- value_effective (REAL 0–1)

## Tabuľka: weights
- id (PK)
- element_key (TEXT)
- weight_default (REAL)
- weight_personal (REAL)
- updated_at

## Tabuľka: index_daily
- id (PK)
- event_day_id (FK -> event_day.id)
- index_value (REAL 0–100)

## Tabuľka: index_weekly
- id (PK)
- week_start (YYYY-MM-DD)
- week_end (YYYY-MM-DD)
- index_value (REAL 0–100)

## Tabuľka: notification_log
- id (PK)
- event_day_id (FK -> event_day.id, NULL)
- type (TEXT)  # daily_reminder | neglected_area | stress_recovery
- sent_at

## Tabuľka: asrs_checkin
- id (PK)
- date (YYYY-MM-DD)
- score_raw
- score_normalized (0–100)

## Poznámky
- V `event_value` je uložená každá položka dynamicky podľa `element_key`.
- `value_effective` je uložený pre rýchly výpočet indexu.
- `weights` má default aj personalizované váhy (ak personalizované neexistujú, použije sa default).
