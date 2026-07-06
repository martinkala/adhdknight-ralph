# Implementation Plan: App–Server Connectivity F1

**Branch**: `009-edit-system-updates` | **Date**: 2026-07-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/016-application-server-connect/spec.md`

---

## Summary

F1 pridáva do mobilnej Android aplikácie tri veci: (1) konfigurovateľnú server URL v Settings, (2) novú Account obrazovku v navigácii s voliteľným loginom cez JWT, a (3) HTTP klient pre komunikáciu s existujúcim FastAPI serverom. Server nevyžaduje žiadne zmeny — všetky potrebné endpointy (`/auth/login`, `/auth/register`, `/user/me`) už existujú. Implementácia je čisto Android-side, zachováva offline-first princíp a nevyžaduje DI framework.

---

## Technical Context

**Language/Version**: Kotlin 2.0, Android min SDK 26, target SDK 34

**Primary Dependencies (nové)**:
- `io.ktor:ktor-client-android:2.3.12` — HTTP klient
- `io.ktor:ktor-client-content-negotiation:2.3.12` — JSON content negotiation
- `io.ktor:ktor-serialization-kotlinx-json:2.3.12` — JSON serializácia
- `org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.1` — JSON runtime
- `androidx.security:security-crypto:1.1.0-alpha06` — EncryptedSharedPreferences pre JWT token
- Kotlin serialization plugin: `org.jetbrains.kotlin.plugin.serialization`

**Storage**:
- Plain `SharedPreferences` (existujúci `PreferencesRepository`) — server URL
- `EncryptedSharedPreferences` (nový) — JWT access token + user email

**Testing**: JVM unit testy; ApiClient testovateľný cez falošnú server URL + mock HTTP engine (Ktor MockEngine)

**Target Platform**: Android (fyzické zariadenie + emulátor)

**Project Type**: Mobile app feature (Android)

**Constraints**:
- Offline-first MUST byť zachovaný (Constitution I) — server URL prázdna = všetky sieťové volania preskočené
- Žiadny DI framework (Constitution VII)
- Žiadne Room entity — SharedPreferences postačujú

**Scale/Scope**: 1 používateľ, 3 API endpointy, 1 nová obrazovka, 2 modifikované obrazovky

---

## Constitution Check

| Princíp | Status | Poznámka |
|---------|--------|----------|
| I. Offline-first | ✅ PASS | Server URL prázdna = HttpClient sa nevolá; login failure neblokuje tracker |
| II. Domenová logika indexu | ✅ N/A | F1 nemodifikuje index výpočet |
| III. Datový model (Room) | ✅ PASS | Žiadne nové Room entity; ServerConfig a UserSession sú prefs |
| IV. UX — minimálne kliknutia | ✅ PASS | Account dostupný z hlavnej navigácie; login je 2-krokový (email+heslo→button) |
| V. Notifikácie | ✅ N/A | F1 nemodifikuje notifikačnú logiku |
| VI. Testovanie | ✅ PASS | ApiClient musí mať unit test s Ktor MockEngine |
| VII. Tech stack — nové závislosti | ✅ JUSTIFIED | Ktor: HTTP volania bez existujúcej alternatívy; security-crypto: šifrovanie tokenu |

**Výsledok Constitution Check: PASS — žiadne bloky.**

---

## Project Structure

### Documentation (this feature)

```text
specs/016-application-server-connect/
├── plan.md              ← tento súbor
├── research.md          ← rozhodnutia o Ktor, EncryptedPrefs, navigácii
├── data-model.md        ← ServerConfig, UserSession, UserState
├── quickstart.md        ← 7 validačných scenárov
├── contracts/
│   └── api-contracts.md ← login, register, /me endpointy + chybová mapa
└── tasks.md             ← generuje /speckit-tasks
```

### Source Code (Android app)

```text
android_app/app/src/main/java/com/example/madhdtracker/
├── data/
│   ├── remote/
│   │   └── ApiClient.kt                    # NOVÝ — Ktor HttpClient wrapper
│   └── repository/
│       ├── PreferencesRepository.kt         # MODIFY — pridaj serverUrl get/set
│       ├── EncryptedPreferencesRepository.kt # NOVÝ — JWT token + userEmail
│       └── UserRepository.kt               # NOVÝ — orchestrácia ApiClient + prefs
├── ui/
│   ├── screens/
│   │   ├── AccountScreen.kt                # NOVÝ — login form / user info
│   │   └── SettingsScreen.kt               # MODIFY — pridaj Server URL sekciu
│   ├── navigation/
│   │   └── AppNavGraph.kt                  # MODIFY — pridaj ACCOUNT route
│   ├── AccountViewModel.kt                 # NOVÝ — login/logout/state
│   └── MainActivity.kt                    # MODIFY — pridaj Account nav item
└── res/xml/
    └── network_security_config.xml         # NOVÝ — povolí HTTP pre private IPs

android_app/app/
├── build.gradle.kts                        # MODIFY — pridaj závislosti
└── src/main/AndroidManifest.xml           # MODIFY — sieťové oprávnenie + NS config
```

### Test files

```text
android_app/app/src/test/java/com/example/madhdtracker/
└── data/remote/
    └── ApiClientTest.kt                    # NOVÝ — Ktor MockEngine unit testy
```

---

## Implementačné fázy

### Fáza 1: Infraštruktúra (závislosť pre všetko ostatné)

1. Pridaj závislosti do `build.gradle.kts` (Ktor + security-crypto + serialization plugin)
2. Vytvor `network_security_config.xml` — povolí cleartext pre `10.0.0.0/8`, `192.168.0.0/16` (dev)
3. Uprav `AndroidManifest.xml` — `INTERNET` oprávnenie + `networkSecurityConfig`
4. Vytvor `EncryptedPreferencesRepository` — `accessToken`, `userEmail` getter/setter
5. Rozšír `PreferencesRepository` — `serverUrl` getter/setter
6. Vytvor `ApiClient` — Ktor HttpClient, metódy `login()`, `register()`, `getMe()`; timeout 5s; error handling
7. Vytvor `UserRepository` — orchestrácia ApiClient + prefs; checkServerUrl guard

### Fáza 2: ViewModel + UI

8. Vytvor `AccountViewModel` — `UserState` StateFlow; `login()`, `logout()`, `register()` funkcie
9. Vytvor `AccountScreen.kt` — LoggedOut stav: formulár; LoggedIn stav: info + logout button; Loading + Error stavy
10. Uprav `SettingsScreen.kt` — pridaj sekciu "Server" s textovým poľom URL + save button
11. Uprav `AppNavGraph.kt` — pridaj `AppRoutes.ACCOUNT` a `AccountScreen` composable
12. Uprav `MainActivity.kt` — pridaj "Účet" item do bottom navigation

### Fáza 3: Testy + validácia

13. Napíš `ApiClientTest.kt` — Ktor MockEngine testy: login success, login 401, register 409, server nedostupný
14. Manuálna validácia cez quickstart.md scenáre 1–7

---

## Dependency Graph

```
Fáza 1 (T001–T007) ──► Fáza 2 (T008–T012) ──► Fáza 3 (T013–T014)
                        (blokuje ViewModel)
T001–T003 (build config) ──► T004–T007 (repositories + ApiClient)
T004 (EncryptedPrefs)    ──► T007 (UserRepository)
T005 (PrefsRepo extend)  ──► T007 (UserRepository)
T006 (ApiClient)         ──► T007 (UserRepository)
T007 (UserRepository)    ──► T008 (AccountViewModel)
T008 (AccountViewModel)  ──► T009 (AccountScreen)
T009 + T010              ──► T011 (AppNavGraph)
T011                     ──► T012 (MainActivity nav item)
```

---

## Complexity Tracking

*Žiadne constitution violations — sekcia nie je potrebná.*
