# Contract: Compute API

Endpointy pre výpočet ADHD denného indexu.

---

## POST /api/v1/compute/daily

Vypočíta denný index pre jeden deň na základe poskytnutých hodnôt a konfigurácie.
Určené primárne pre regresné testovanie — nepotrebuje autentifikáciu (public compute endpoint).

### Request

```json
{
  "schema_version": "1.0",
  "date": "2026-06-30",
  "entity_config": {
    "overall_feeling": { "weight": 13.0, "impact": 1, "parent": null, "scale": true },
    "sleep": { "weight": 15.0, "impact": 1, "parent": null, "scale": true },
    "physical_activity": { "weight": 11.0, "impact": 1, "parent": null, "scale": false },
    "stress_work": { "weight": 13.0, "impact": -1, "parent": null, "scale": false },
    "stress_personal": { "weight": 13.0, "impact": -1, "parent": null, "scale": false },
    "nutrition_protein": { "weight": 8.0, "impact": 1, "parent": null, "scale": false },
    "caffeine": { "weight": 6.0, "impact": -1, "parent": null, "scale": false },
    "alcohol": { "weight": 10.0, "impact": -1, "parent": null, "scale": false },
    "mindfulness": { "weight": 11.0, "impact": 1, "parent": null, "scale": false }
  },
  "values": [
    { "element_key": "overall_feeling", "value_binary": 1, "value_scale": 4 },
    { "element_key": "sleep", "value_binary": 1, "value_scale": 3 },
    { "element_key": "physical_activity", "value_binary": 1, "value_scale": null },
    { "element_key": "stress_work", "value_binary": 0, "value_scale": null },
    { "element_key": "mindfulness", "value_binary": 1, "value_scale": null }
  ],
  "active_keys": ["overall_feeling", "sleep", "physical_activity", "stress_work", "mindfulness"]
}
```

**Polia**:
- `entity_config` — mapa elementov s váhami; `parent: null` = root node
- `values` — iba elementy, ktoré boli vyplnené (ostatné sa ignorujú)
- `active_keys` — list kľúčov, ktoré sú aktívne pre daného používateľa

### Response 200

```json
{
  "schema_version": "1.0",
  "date": "2026-06-30",
  "index_value": 68.42,
  "detail": [
    {
      "element_key": "overall_feeling",
      "value_effective": 0.75,
      "weight": 13.0,
      "contribution": 9.75,
      "impact": 1
    },
    {
      "element_key": "sleep",
      "value_effective": 0.5,
      "weight": 15.0,
      "contribution": 7.5,
      "impact": 1
    }
  ],
  "active_weight_sum": 52.0,
  "skipped_keys": ["stress_personal", "nutrition_protein", "caffeine", "alcohol"]
}
```

### Response 422

```json
{
  "detail": [
    { "loc": ["body", "values", 0, "element_key"], "msg": "unknown element key: xyz", "type": "value_error" }
  ]
}
```

---

## POST /api/v1/compute/range

Vypočíta indexy pre sériu dní (1, 3, 5, 15, 30). Určené pre BDD testy.

### Request

```json
{
  "schema_version": "1.0",
  "entity_config": { "...": "rovnaká štruktúra ako v /daily" },
  "days": [
    {
      "date": "2026-06-28",
      "values": [ {"element_key": "sleep", "value_binary": 1, "value_scale": 4} ],
      "active_keys": ["sleep", "overall_feeling"]
    },
    {
      "date": "2026-06-29",
      "values": [],
      "active_keys": ["sleep", "overall_feeling"]
    },
    {
      "date": "2026-06-30",
      "values": [ {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 5} ],
      "active_keys": ["sleep", "overall_feeling"]
    }
  ]
}
```

### Response 200

```json
{
  "schema_version": "1.0",
  "results": [
    { "date": "2026-06-28", "index_value": 72.5, "status": "computed" },
    { "date": "2026-06-29", "index_value": null, "status": "no_data" },
    { "date": "2026-06-30", "index_value": 100.0, "status": "computed" }
  ],
  "summary": {
    "days_requested": 3,
    "days_computed": 2,
    "days_no_data": 1,
    "average_index": 86.25
  }
}
```

**Stavy pre `status` pole**:
- `computed` — index vypočítaný
- `no_data` — žiadne hodnoty pre daný deň
- `partial` — menej ako 3 aktívne elementy vyplnené

---

## GET /api/v1/health

Health check — nevyžaduje autentifikáciu.

### Response 200

```json
{
  "status": "ok",
  "version": "0.1.0",
  "db": "connected",
  "timestamp": "2026-06-30T10:00:00Z"
}
```
