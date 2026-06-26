# Data Model: ADHD Tracker MVP Baseline

## Entities (Room)

### EventDayEntity
- id (PK)
- date (unique)

### EventValueEntity
- id (PK)
- eventDayId (FK -> EventDayEntity)
- element_key (indexed)
- value_binary
- value_scale (nullable)
- value_effective

### SatisfactionEntity
- id (PK)
- eventDayId (FK -> EventDayEntity)
- value_scale

### WeightEntity
- element_key (PK)
- weight_default
- weight_personal (nullable)

### IndexDailyEntity
- id (PK)
- eventDayId (FK -> EventDayEntity)
- index_value

### IndexWeeklyEntity
- id (PK)
- week_start
- week_end
- index_avg

### NotificationLogEntity
- id (PK)
- eventDayId (FK -> EventDayEntity, nullable)
- type
- sent_at

### AsrsCheckinEntity
- id (PK)
- date
- score_raw
- score_normalized

## Reference Data (Bundled, Non-Editable)

### ActivityDescription
- element_key (matches EventValueEntity.element_key)
- title
- description_markdown

**Storage**: Bundled app resource file (read-only); not persisted in Room.

## Relationships

- EventDayEntity 1..* EventValueEntity
- EventDayEntity 0..1 SatisfactionEntity
- EventDayEntity 0..1 IndexDailyEntity
- NotificationLogEntity optionally references EventDayEntity
