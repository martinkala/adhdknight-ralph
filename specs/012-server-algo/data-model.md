# Data Model: Backend Weight Vector Server

**Date**: 2026-06-30 | **Feature**: 012-server-algo

---

## Entita: User

Každý registrovaný používateľ. Identita je email (unikátny).

| Pole | Typ | Popis |
|------|-----|-------|
| `id` | UUID | PK, auto-generovaný |
| `email` | String (unique, indexed) | Prihlasovací identifikátor |
| `password_hash` | String | bcrypt hash hesla |
| `created_at` | DateTime (UTC) | Čas registrácie |
| `last_sync_at` | DateTime (UTC, nullable) | Posledná úspešná synchronizácia |
| `is_active` | Boolean | Soft-delete / deaktivácia účtu |

**Vzťahy**:
- 1:N → `TrackingDay`
- 1:N → `WeightConfig`
- 1:N → `SyncRecord`

---

## Entita: TrackingDay

Jeden deň trackingu pre jedného používateľa. Zodpovedá `EventDayEntity` v Android Room.

| Pole | Typ | Popis |
|------|-----|-------|
| `id` | UUID | PK |
| `user_id` | UUID (FK → User) | Majiteľ záznamu |
| `date` | Date (indexed) | Dátum dňa (YYYY-MM-DD), unique per user |
| `is_complete` | Boolean | Používateľ označil deň za vyplnený |
| `created_at` | DateTime (UTC) | Prvé vytvorenie záznamu |
| `updated_at` | DateTime (UTC) | Posledná úprava — používa sa pre LWW conflict resolution |
| `device_id` | String (nullable) | Identifikátor zariadenia pre audit |

**Constraints**: `UNIQUE(user_id, date)`

**Vzťahy**:
- N:1 → `User`
- 1:N → `ElementValue`
- 1:1 → `DailyIndex` (nullable — index nemusí byť vypočítaný)

---

## Entita: ElementValue

Hodnota konkrétneho elementu pre daný deň. Zodpovedá `EventValueEntity` v Android Room.

| Pole | Typ | Popis |
|------|-----|-------|
| `id` | UUID | PK |
| `tracking_day_id` | UUID (FK → TrackingDay) | |
| `element_key` | String (indexed) | snake_case identifikátor (napr. `sleep`, `stress_work`) |
| `value_binary` | Integer (0/1) | Splnené áno/nie |
| `value_scale` | Integer (1–5, nullable) | Detail hodnotenie; null = binary-only element |
| `value_effective` | Float (0.0–1.0) | Computed: ak scale → `(scale-1)/4`; inak → binary |
| `updated_at` | DateTime (UTC) | Pre granulárny conflict tracking |

**Constraints**: `UNIQUE(tracking_day_id, element_key)`

**Indexy**: `(tracking_day_id)`, `(element_key)`

---

## Entita: EntityConfig

Konfigurácia hierarchie elementov (nodes). Ukladá sa ako JSON — zodpovedá `entities.yaml` v Android appke.

| Pole | Typ | Popis |
|------|-----|-------|
| `id` | UUID | PK |
| `version` | String | Verzia konfigurácie (napr. `"1.0"`) |
| `nodes` | JSONB / Text (JSON) | Mapa `{key: EntityNode}` — celá konfigurácia |
| `created_at` | DateTime (UTC) | |
| `is_active` | Boolean | Aktuálna verzia konfigurácie |

**EntityNode JSON štruktúra** (v `nodes` poli):
```json
{
  "sleep": {
    "key": "sleep",
    "weight": 15.0,
    "impact": 1,
    "parent": null,
    "label": "Spánok",
    "active": true,
    "scale": true,
    "clickable": true
  }
}
```

**Poznámka**: Pre MVP jedna globálna `EntityConfig` zdieľaná pre všetkých používateľov. Per-user config je post-MVP.

---

## Entita: WeightConfig

Personalizované váhy pre konkrétneho používateľa. Zodpovedá `WeightEntity` v Android Room.

| Pole | Typ | Popis |
|------|-----|-------|
| `id` | UUID | PK |
| `user_id` | UUID (FK → User) | |
| `element_key` | String | |
| `weight_default` | Float | Default váha z konfigurácie |
| `weight_personal` | Float (nullable) | Adaptovaná váha; null = používa sa default |
| `updated_at` | DateTime (UTC) | |

**Constraints**: `UNIQUE(user_id, element_key)`

---

## Entita: DailyIndex

Vypočítaný denný ADHD index. Zodpovedá `IndexDailyEntity` v Android Room.

| Pole | Typ | Popis |
|------|-----|-------|
| `id` | UUID | PK |
| `tracking_day_id` | UUID (FK → TrackingDay, unique) | 1:1 |
| `index_value` | Float (0.0–100.0) | Vypočítaný denný index |
| `detail_json` | JSONB / Text (nullable) | Per-element contribution detail pre debug |
| `computed_at` | DateTime (UTC) | Čas výpočtu |
| `config_version` | String | Verzia EntityConfig použitej pri výpočte |

---

## Entita: SyncRecord

Audit log každej sync operácie.

| Pole | Typ | Popis |
|------|-----|-------|
| `id` | UUID | PK |
| `user_id` | UUID (FK → User) | |
| `device_id` | String (nullable) | Identifikátor zariadenia |
| `sync_type` | Enum: `batch`, `single`, `migration` | Typ sync |
| `records_sent` | Integer | Počet záznamov v requeste |
| `records_accepted` | Integer | Úspešne spracované |
| `records_conflicted` | Integer | Konflikty riešené LWW |
| `records_rejected` | Integer | Odmietnuté (validácia) |
| `conflict_log` | JSONB (nullable) | Detail konfliktov: `[{date, mobile_updated_at, server_updated_at, winner}]` |
| `synced_at` | DateTime (UTC) | |

---

## Vzťahy — ERD prehľad

```
User ──< TrackingDay ──< ElementValue
  │           │
  │           └──── DailyIndex
  │
  ├──< WeightConfig
  └──< SyncRecord

EntityConfig  (globálna, nie FK)
```

---

## Migrácie

- Migrácie spravuje **Alembic** (auto-generované z SQLAlchemy modelov)
- Pravidlo: **additive-only** — žiadne DROP COLUMN, žiadne NOT NULL bez DEFAULT
- Každá migrácia má `upgrade()` aj `downgrade()`
- Verziovanie: `alembic revision --autogenerate -m "add_xxx_column"`

## Mapovanie Android Room → Server DB

| Android Room entita | Server entita | Poznámka |
|-------------------|--------------|---------|
| `EventDayEntity` | `TrackingDay` | `date` field identický |
| `EventValueEntity` | `ElementValue` | `element_key`, `value_binary`, `value_scale`, `value_effective` identické |
| `WeightEntity` | `WeightConfig` | `weight_default`, `weight_personal` identické |
| `IndexDailyEntity` | `DailyIndex` | `index_value` identická hodnota |
| `SatisfactionEntity` | Súčasť `ElementValue` kde `element_key = "overall_feeling"` | Zlúčené |
| `UserElementEntity` | Post-MVP (per-user config) | Mimo scope |
