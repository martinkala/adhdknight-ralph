# Contract: Auth API

Registrácia a prihlásenie používateľa. JWT-based autentifikácia.

---

## POST /api/v1/auth/register

### Request

```json
{
  "email": "user@example.com",
  "password": "min8chars"
}
```

**Validácia**:
- `email`: valid RFC 5322 email, unique
- `password`: min 8 znakov

### Response 201

```json
{
  "schema_version": "1.0",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Response 409 (email existuje)

```json
{ "detail": "Email already registered" }
```

---

## POST /api/v1/auth/login

### Request

```json
{
  "email": "user@example.com",
  "password": "min8chars"
}
```

### Response 200

```json
{
  "schema_version": "1.0",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Response 401

```json
{ "detail": "Invalid credentials" }
```

---

## POST /api/v1/auth/refresh

Obnoví access token pomocou refresh tokenu.

### Request

```json
{ "refresh_token": "eyJ..." }
```

### Response 200

```json
{
  "schema_version": "1.0",
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

## Autentifikácia chránených endpointov

Všetky endpointy okrem `/auth/*`, `/compute/*` a `/health` vyžadujú:

```
Authorization: Bearer <access_token>
```

Chybová odpoveď pri chýbajúcom/neplatnom tokene:
```json
{ "detail": "Not authenticated" }
```

---

## Token TTL

| Token | Platnosť |
|-------|----------|
| Access token | 15 minút |
| Refresh token | 30 dní |
