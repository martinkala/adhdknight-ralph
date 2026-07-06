# Research: App–Server Connectivity (F1)

**Feature**: F1 — Server Settings + Account Screen (mobilná aplikácia)
**Date**: 2026-07-06

---

## Decision 1: HTTP klient pre Android

**Decision**: Ktor-client (io.ktor:ktor-client-android)

**Rationale**:
- Natívna podpora Kotlin coroutines — konzistentné s existujúcim kódom
- Lightweight, žiadny reflection overhead (na rozdiel od Retrofit/Gson)
- Pre 3–4 endpointy nepotrebujeme plný REST framework
- Ktor-client-android používa OkHttp engine, ktorý je Android-optimalizovaný

**Alternatives considered**:
- **Retrofit**: Vhodné pre väčšie API povrchy, ale zbytočne ťažké pre 3 endpointy. Pridalo by reflection + anotácie.
- **OkHttp priamo**: Nižšia abstrakcia, vyžaduje manuálne spracovanie JSON a coroutines bridging.
- **Volley**: Zastaralé, nie coroutines-native.

**Dependencies**:
```
io.ktor:ktor-client-android:2.3.12
io.ktor:ktor-client-content-negotiation:2.3.12
io.ktor:ktor-serialization-kotlinx-json:2.3.12
org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.1
```

---

## Decision 2: Ukladanie JWT tokenu

**Decision**: `EncryptedSharedPreferences` (androidx.security:security-crypto)

**Rationale**:
- Android-štandard pre citlivé dáta v SharedPreferences
- Transparentná AES-256 GCM šifra — žiadna extra logika
- Jednoduchá integrácia s existujúcim `PreferencesRepository` (rovnaké API)
- Dostupné od API 23 (projekt min SDK 26 ✅)

**Alternatives considered**:
- **DataStore (Jetpack Preferences DataStore)**: Modernejší štandard, ale nemá šifrovanie out-of-the-box. Vyžaduje knižnicu `DataStore Security` (experimentálna). Pridalo by komplexitu.
- **Android Keystore + manuálne šifrovanie**: Príliš low-level, zbytočne komplikované.
- **Plain SharedPreferences**: Nevhodné pre JWT token (security riziko).

**Dependency**:
```
androidx.security:security-crypto:1.1.0-alpha06
```

---

## Decision 3: Ukladanie server URL

**Decision**: Plain `SharedPreferences` cez rozšírenie existujúceho `PreferencesRepository`

**Rationale**:
- URL nie je citlivá (nie je to heslo ani token) — plain prefs postačuje
- Konzistentné s existujúcim `PreferencesRepository` vzorom
- Žiadna nová závislosť

**Alternatives considered**:
- **DataStore**: Overengineering pre 1–2 hodnoty, ktoré sa menia zriedkavo.
- **Room entita**: Zbytočné — `ServerConfig` nie je relačná entita.

---

## Decision 4: Account screen — umiestnenie v navigácii

**Decision**: Nový nav item `Účet` v bottom navigation bare (vedľa Settings)

**Rationale**:
- Constitution Príncíp IV vyžaduje minimálne kliknutia; Account dostupný z hlavného nav
- Konzistentné s web app (kde je Account v top nav bar)
- Settings zostáva separátna (export, notifikácie, entity manažment)

**Alternatives considered**:
- **Sub-stránka Settings**: Skrytá za ďalší tap — horšia dostupnosť pre dôležitú funkcionalitu
- **Floating button**: Nevhodné pre navigáciu

---

## Decision 5: Závislosť na serveri — no server changes needed

**Decision**: F1 nevyžaduje žiadne zmeny na FastAPI serveri

**Rationale**:
FastAPI server už má všetky potrebné endpointy:
- `POST /api/v1/auth/login` — prihlásenie (email + password → JWT)
- `POST /api/v1/auth/register` — registrácia
- `GET /api/v1/user/me` — user info (email, created_at, total_days)

**Scope F1 je čisto Android-app zmena.**

---

## Decision 6: Offline-first zachovanie (Constitution I)

**Decision**: Server URL prázdna = server feature kompletne vypnutá; ApiClient sa nikdy nevolá ak URL nie je nastavená

**Rationale**:
- Constitution Príncíp I: "Offline-first je základný predpoklad"
- UserRepository skontroluje `serverUrl.isBlank()` pred každým sieťovým volaním
- Login failure alebo server nedostupnosť nesmie blokovať offline tracker

---

## Decision 7: DI — bez DI frameworku (Constitution VII)

**Decision**: Manuálna injekcia — `AccountViewModel` dostane `UserRepository` cez `remember { UserRepository(...) }` alebo cez `Application`-level singleton

**Rationale**: Constitution VII zakazuje DI framework (Hilt, Koin) v MVP. Existujúce ViewModely používajú rovnaký pattern.

---

## Zhrnutie nových závislostí

| Závislosť | Verzia | Účel |
|-----------|--------|------|
| `io.ktor:ktor-client-android` | 2.3.12 | HTTP volania |
| `io.ktor:ktor-client-content-negotiation` | 2.3.12 | JSON content type |
| `io.ktor:ktor-serialization-kotlinx-json` | 2.3.12 | JSON serializácia |
| `org.jetbrains.kotlinx:kotlinx-serialization-json` | 1.7.1 | JSON runtime |
| `androidx.security:security-crypto` | 1.1.0-alpha06 | Šifrovaný token storage |

Kotlin serialization vyžaduje plugin v `build.gradle.kts`:
```kotlin
plugins {
    id("org.jetbrains.kotlin.plugin.serialization") version "2.0.0"
}
```
