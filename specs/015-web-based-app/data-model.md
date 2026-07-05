# Data Model: Web Companion App

Web app je **read-only klient** — nemá vlastnú databázu. Dáta pochádzajú výhradne zo FastAPI servera.

## Dátové štruktúry (API response shapes)

### UserSession (Django session, server-side)
```
jwt_token: str          # Bearer token z FastAPI /auth/login
user_email: str         # Email prihláseného používateľa
token_expires: datetime # Expirácia tokenu
```

### HistoryDay (z GET /api/v1/user/history)
```
date: str               # "YYYY-MM-DD"
index_value: float|null # ADHD index 0-100, null ak nie sú dáta
detail: list[DetailItem]
  element_key: str
  value_effective: float  # 0-1
  weight: float
  contribution: float     # kladný alebo záporný
  impact: int             # 1 alebo -1
```

### UserInfo (z GET /api/v1/user/me — nový endpoint)
```
email: str
created_at: datetime
total_days: int
```

## Tok dát

```
Prehliadač → Django view → FastAPI (JWT Bearer)
                        ← JSON response
           ← HTML template s dátami
```

## Nové FastAPI endpointy (musia byť implementované)

| Endpoint | Metóda | Popis |
|----------|--------|-------|
| `/api/v1/user/history` | GET | Posledných N dní s index_value a detail pre prihláseného používateľa |
| `/api/v1/user/me` | GET | Email a základné info o účte |

Query params pre `/user/history`: `days=30` (default), `days=90` (max)
