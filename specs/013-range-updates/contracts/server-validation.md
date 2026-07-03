# Contract: Server — Future Date Validation

## Endpoint dopad

Validácia sa aplikuje na všetky endpointy prijímajúce dátum dňa:

| Endpoint | Schéma | Pole |
|----------|--------|------|
| `POST /api/v1/compute/daily` | `ComputeDailyRequest` | `date: str` |
| `POST /api/v1/compute/range` | `DayInput` | `date: str` |
| `POST /api/v1/sync/batch` | `DaySyncItem` | `date: str` |
| `POST /api/v1/migrate` | `MigrationDayItem` | `date: str` |

## Validačné pravidlo

```
date_parsed = date.fromisoformat(date_str)  # formát: "YYYY-MM-DD"
if date_parsed > date.today():              # porovnanie voči UTC dátumu servera
    raise ValueError("Date cannot be in the future")
```

## Response pri porušení

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "date"],
      "msg": "Value error, Date cannot be in the future",
      "input": "2099-01-01"
    }
  ]
}
```

## Test scenarios (povinné)

| # | Input dátum | Očakávaný výsledok |
|---|-------------|-------------------|
| T1 | dnešný dátum (`date.today()`) | 200 OK |
| T2 | zajtrajší dátum | 422 |
| T3 | dátum 1 rok v budúcnosti | 422 |
| T4 | dátum z minulosti (včera) | 200 OK |
| T5 | dátum 2020-01-01 | 200 OK |
