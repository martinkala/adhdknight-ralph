# API Contracts: Android App ↔ FastAPI Server (F1)

**Feature**: F1 — Server Settings + Account Screen
**Server base URL**: konfigurovaná v Settings (napr. `http://192.168.1.10:8095`)
**Auth**: JWT Bearer token v `Authorization` hlavičke

---

## Endpoints používané v F1

### POST /api/v1/auth/login

Prihlásenie používateľa.

**Request**:
```json
POST {serverUrl}/api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response — úspech (200)**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Response — chyba (401)**:
```json
{
  "detail": "Incorrect email or password"
}
```

**Správanie klienta**:
- Uloží `access_token` do EncryptedSharedPreferences
- Zavolá `GET /api/v1/user/me` pre doplnenie user info
- Pri 401 zobrazí "Nesprávne prihlasovacie údaje"
- Pri `ConnectException` zobrazí "Server nie je dostupný"

---

### POST /api/v1/auth/register

Registrácia nového účtu.

**Request**:
```json
POST {serverUrl}/api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secret123"
}
```

**Response — úspech (201)**:
```json
{
  "email": "user@example.com",
  "created_at": "2026-07-06T10:00:00"
}
```

**Response — konflikt (409)**:
```json
{
  "detail": "Email already registered"
}
```

**Správanie klienta**:
- Po úspešnej registrácii automaticky zavolá login
- Pri 409 zobrazí "Účet s týmto emailom už existuje"

---

### GET /api/v1/user/me

Informácie o prihlásenom používateľovi.

**Request**:
```
GET {serverUrl}/api/v1/user/me
Authorization: Bearer {access_token}
```

**Response — úspech (200)**:
```json
{
  "email": "user@example.com",
  "created_at": "2026-06-01T08:00:00",
  "total_days": 42
}
```

**Response — neplatný token (401)**:
```json
{
  "detail": "Could not validate credentials"
}
```

**Správanie klienta**:
- Pri 401 vyčistí token + session → zobrazí stav LoggedOut
- Výsledok sa zobrazí na Account obrazovke (email, total_days, created_at)

---

## Chybové stavy — kompletná mapa

| Situácia | HTTP / Exception | UI správa |
|----------|-----------------|-----------|
| Nesprávne heslo | 401 | "Nesprávne prihlasovacie údaje" |
| Neexistujúci účet (login) | 401 | "Nesprávne prihlasovacie údaje" |
| Email už existuje (register) | 409 | "Účet s týmto emailom už existuje" |
| Server nedostupný | ConnectException / IOException | "Server nie je dostupný" |
| Vypršaný token | 401 na /me | Automatické odhlásenie, stav LoggedOut |
| Timeout (>5s) | SocketTimeoutException | "Server neodpovedá, skúste neskôr" |
| Prázdna server URL | (lokálna validácia) | "Zadajte URL servera v nastaveniach" |

---

## Poznámky

- FastAPI server aktuálne neimplementuje refresh token flow — po expirácii access tokenu (default 15 min) musí používateľ znova zadať heslo. V F1 je toto akceptovateľné; refresh flow je post-F1 scope.
- Všetky endpointy majú 5-sekundový timeout na strane klienta.
- HTTP (nie HTTPS) je akceptované pre lokálne dev prostredie (Android `networkSecurityConfig` povolí cleartext pre private IP rozsahy).
