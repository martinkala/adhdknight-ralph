# Contract: Migration API

Import existujúcich Android dát na server. Vyžaduje autentifikáciu.

---

## POST /api/v1/migrate

Hromadný import historických dát z Android appky. Použiteľné jednorazovo alebo inkrementálne.

### Request

```json
{
  "schema_version": "1.0",
  "source": "android_export",
  "migration_strategy": "mobile_source_of_truth",
  "days": [
    {
      "date": "2026-01-15",
      "is_complete": true,
      "updated_at": "2026-01-15T22:00:00Z",
      "values": [
        {
          "element_key": "sleep",
          "value_binary": 1,
          "value_scale": 4,
          "value_effective": 0.75,
          "updated_at": "2026-01-15T21:00:00Z"
        },
        {
          "element_key": "overall_feeling",
          "value_binary": 1,
          "value_scale": 3,
          "value_effective": 0.5,
          "updated_at": "2026-01-15T21:00:00Z"
        }
      ]
    }
  ],
  "weight_config": [
    { "element_key": "sleep", "weight_personal": 18.0 },
    { "element_key": "stress_work", "weight_personal": 10.0 }
  ]
}
```

**Polia**:
- `migration_strategy`:
  - `"mobile_source_of_truth"` — ak deň existuje na serveri, mobile vždy prepíše (odporúčané pre prvú migráciu)
  - `"skip_existing"` — existujúce dni na serveri sa preskočia
- `weight_config` — personalizované váhy z `WeightEntity` v Android Room (voliteľné)

### Response 200

```json
{
  "schema_version": "1.0",
  "migration_id": "migration-record-uuid",
  "processed_at": "2026-06-30T10:10:00Z",
  "summary": {
    "days_received": 180,
    "days_imported": 178,
    "days_skipped": 2,
    "days_failed": 0,
    "weights_imported": 9
  },
  "skipped": [
    { "date": "2026-03-15", "reason": "already_exists_server_newer" },
    { "date": "2026-04-01", "reason": "invalid_element_key: xyz_unknown" }
  ],
  "errors": []
}
```

### Response 422

```json
{
  "detail": "Invalid migration_strategy: must be 'mobile_source_of_truth' or 'skip_existing'"
}
```

---

## GET /api/v1/migrate/{migration_id}

Získa výsledok konkrétnej migrácie (pre overenie po importe).

### Response 200

```json
{
  "schema_version": "1.0",
  "migration_id": "migration-record-uuid",
  "status": "completed",
  "processed_at": "2026-06-30T10:10:00Z",
  "summary": { "...": "rovnaký objekt ako v POST response" }
}
```

---

## Poznámky k migrácii

- Migrácia je idempotentná s `migration_strategy: "skip_existing"` — bezpečné spustiť viackrát
- Maximálna veľkosť jedného requestu: 1000 dní (pre väčší objem rozbiť na batch)
- `value_effective` sa môže prepočítať zo `value_binary`/`value_scale` ak nie je poskytnuté
