# Data Model: App–Server Connectivity (F1)

**Feature**: F1 — Server Settings + Account Screen
**Date**: 2026-07-06

**Note**: F1 nepridáva žiadne Room entity. Všetky nové dáta sú uložené v SharedPreferences (nie v databáze) — server URL a JWT token sú konfigurácia, nie historické dáta.

---

## Nové hodnoty v SharedPreferences

### ServerConfig (plain SharedPreferences — `adhd_prefs`)

Rozšírenie existujúceho `PreferencesRepository`:

| Kľúč | Typ | Default | Popis |
|------|-----|---------|-------|
| `server_url` | String | `""` | URL FastAPI servera (napr. `http://192.168.1.10:8095`). Prázdny string = server neaktívny. |

### UserSession (EncryptedSharedPreferences — `adhd_secure_prefs`)

Nový šifrovaný prefs súbor pre citlivé dáta:

| Kľúč | Typ | Default | Popis |
|------|-----|---------|-------|
| `access_token` | String | `""` | JWT Bearer token. Prázdny = neprihlásený. |
| `user_email` | String | `""` | Email prihláseného používateľa (pre zobrazenie v UI). |

---

## Doménové modely (in-memory, nie DB)

### UserState (sealed class / UI state)

Stav Account obrazovky:

```
UserState
├── LoggedOut         — neprihlásený, zobrazí login formulár
├── Loading           — prebieha sieťové volanie
├── LoggedIn(
│     email: String,
│     totalDays: Int,
│     createdAt: String
│   )                 — prihlásený, zobrazí info
└── Error(message: String) — chybová správa
```

### ServerConfig (plain data class)

```
ServerConfig(
  url: String       — prázdny = disabled
)
```

### LoginRequest / LoginResponse (API DTO)

Používané len v `ApiClient` — neexponujú sa do UI:

```
LoginRequest(email: String, password: String)
LoginResponse(access_token: String, token_type: String)

RegisterRequest(email: String, password: String)

MeResponse(email: String, created_at: String, total_days: Int)
```

---

## Entita — vzťahy k existujúcemu modelu

F1 nezasahuje do žiadnej Room entity. Existujúce entity ostávajú nedotknuté.

```
PreferencesRepository (existujúci)
  └── + serverUrl: String         ← nová hodnota (plain prefs)

EncryptedPreferencesRepository (nový)
  └── accessToken: String
  └── userEmail: String
```

---

## Validačné pravidlá

| Pole | Validácia |
|------|-----------|
| `server_url` | Musí začínať `http://` alebo `https://`; alebo prázdny. Uloženie s trailing slash je normalizované (odstránená). |
| `email` | Štandardná email validácia (contains `@`). |
| `password` | Minimálne 6 znakov (zodpovedá FastAPI server limitu). |
| `access_token` | Uložený as-is; expirácia sa rieši na strane servera (401 response). |
