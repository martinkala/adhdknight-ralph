# Contract: Sync API

Offline batch sync a riešenie konfliktov. Vyžaduje autentifikáciu.

---

## POST /api/v1/sync/batch

Odošle tracking záznamy nahromadené počas offline obdobia.

### Request

```json
{
  "schema_version": "1.0",
  "device_id": "android-device-uuid-123",
  "days": [
    {
      "date": "2026-06-25",
      "is_complete": true,
      "updated_at": "2026-06-25T22:15:00Z",
      "values": [
        {
          "element_key": "sleep",
          "value_binary": 1,
          "value_scale": 4,
          "value_effective": 0.75,
          "updated_at": "2026-06-25T21:30:00Z"
        },
        {
          "element_key": "overall_feeling",
          "value_binary": 1,
          "value_scale": 3,
          "value_effective": 0.5,
          "updated_at": "2026-06-25T21:30:00Z"
        }
      ]
    },
    {
      "date": "2026-06-26",
      "is_complete": false,
      "updated_at": "2026-06-26T20:00:00Z",
      "values": []
    }
  ]
}
```

**Poznámky**:
- `device_id` — pre audit, nie pre autentifikáciu
- `updated_at` na úrovni dňa aj na úrovni hodnoty — pre granulárny conflict tracking
- Prázdny `values` = deň bol vytvorený ale nevyplnený

### Response 200

```json
{
  "schema_version": "1.0",
  "sync_id": "sync-record-uuid",
  "processed_at": "2026-06-30T10:05:00Z",
  "summary": {
    "days_received": 2,
    "days_accepted": 2,
    "days_conflicted": 0,
    "days_rejected": 0
  },
  "conflicts": [],
  "computed_indices": [
    { "date": "2026-06-25", "index_value": 68.5 },
    { "date": "2026-06-26", "index_value": null }
  ]
}
```

### Response s konfliktom

```json
{
  "schema_version": "1.0",
  "sync_id": "sync-record-uuid",
  "summary": {
    "days_received": 1,
    "days_accepted": 1,
    "days_conflicted": 1,
    "days_rejected": 0
  },
  "conflicts": [
    {
      "date": "2026-06-25",
      "resolution": "mobile_wins",
      "mobile_updated_at": "2026-06-25T22:15:00Z",
      "server_updated_at": "2026-06-25T20:00:00Z",
      "reason": "mobile timestamp is newer"
    }
  ],
  "computed_indices": [
    { "date": "2026-06-25", "index_value": 68.5 }
  ]
}
```

**Conflict resolution pravidlo**: `last-write-wins` podľa `updated_at`
- `mobile_wins`: mobile timestamp > server timestamp → server prepíše
- `server_wins`: server timestamp >= mobile timestamp → mobile dáta sa ignorujú

---

## GET /api/v1/sync/status

Vráti stav poslednej synchronizácie pre autentizovaného používateľa.

### Response 200

```json
{
  "schema_version": "1.0",
  "last_sync_at": "2026-06-30T10:05:00Z",
  "last_sync_id": "sync-record-uuid",
  "total_days_on_server": 45,
  "pending_days_mobile": null
}
```

---

## GET /api/v1/sync/indices

Stiahne vypočítané indexy zo servera pre dané obdobie (mobile si ich natiahne po sync).

### Query params

- `from_date` (required): `YYYY-MM-DD`
- `to_date` (required): `YYYY-MM-DD`

### Response 200

```json
{
  "schema_version": "1.0",
  "indices": [
    { "date": "2026-06-25", "index_value": 68.5, "computed_at": "2026-06-30T10:05:00Z" },
    { "date": "2026-06-26", "index_value": null, "computed_at": null }
  ]
}
```
