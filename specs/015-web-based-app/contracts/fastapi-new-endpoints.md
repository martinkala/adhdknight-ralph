# FastAPI — Nové endpointy pre Web App

Tieto endpointy treba pridať do existujúceho FastAPI servera (`server/app/routers/`).

## GET /api/v1/user/history

Vracia posledných N dní s denným indexom a detailom pre prihláseného používateľa.

**Auth**: Bearer JWT (existujúci `get_current_user`)

**Query params**:
- `days: int = 30` — počet dní späť od dnes (max 90)

**Response 200**:
```json
{
  "schema_version": "1.0",
  "days": [
    {
      "date": "2026-07-04",
      "index_value": 72.5,
      "detail": [
        {
          "element_key": "sleep",
          "value_effective": 0.75,
          "weight": 15.0,
          "contribution": 11.25,
          "impact": 1
        }
      ]
    }
  ],
  "total_days": 28
}
```

**Response 401**: Neplatný alebo chýbajúci token

**Implementácia**: Načítať `TrackingDay` + `DailyIndex` + `ElementValue` z DB pre `current_user.id`, zoradiť zostupne podľa `date`, obmedziť na `days` záznamy.

---

## GET /api/v1/user/me

Vracia základné info o prihlásenom používateľovi.

**Auth**: Bearer JWT

**Response 200**:
```json
{
  "email": "user@example.com",
  "created_at": "2026-01-15T10:00:00Z",
  "total_days": 42
}
```

**Response 401**: Neplatný token

**Implementácia**: `current_user.email` + `current_user.created_at` + count `TrackingDay` pre daného používateľa.
