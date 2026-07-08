# Tasks: App–Server Connectivity F1

**Input**: Design documents from `specs/016-application-server-connect/`

**Prerequisites**: spec.md ✓, plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Unit test pre ApiClient (T014) — pokrýva sieťovú logiku bez živého servera.

**Scope**: F1 pokrýva US1 (server URL v Settings) a US2 (Account obrazovka + voliteľný login). US3–US5 sú F2–F4.

**Tech Stack**: Kotlin / Jetpack Compose / Ktor-client / EncryptedSharedPreferences

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Paralelizovateľné (rôzne súbory, žiadne závislosťi)
- **[Story]**: User story podľa spec.md (US1, US2)

---

## Phase 1: Setup (Build konfigurácia + sieťové oprávnenia)

**Purpose**: Pridanie závislostí a sieťovej konfigurácie. Závislosť pre celú implementáciu.

- [X] T001 Add Ktor dependencies to `android_app/app/build.gradle.kts` — pridaj: `io.ktor:ktor-client-android:2.3.12`, `io.ktor:ktor-client-content-negotiation:2.3.12`, `io.ktor:ktor-serialization-kotlinx-json:2.3.12`, `org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.1`, `androidx.security:security-crypto:1.1.0-alpha06`
- [X] T002 Add Kotlin serialization plugin to `android_app/app/build.gradle.kts` — v bloku `plugins { }` pridaj `id("org.jetbrains.kotlin.plugin.serialization") version "2.0.0"`; overiť že plugin je aj v root `build.gradle.kts` ak treba
- [X] T003 Create `android_app/app/src/main/res/xml/network_security_config.xml` — povolí cleartext HTTP pre private IP rozsahy `10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12` a `localhost`; HTTPS povolené všade
- [X] T004 Update `android_app/app/src/main/AndroidManifest.xml` — pridaj `<uses-permission android:name="android.permission.INTERNET" />` ak chýba; do `<application>` pridaj `android:networkSecurityConfig="@xml/network_security_config"`

**Checkpoint**: Gradle sync prebehne bez chýb.

---

## Phase 2: Foundational (Dátová vrstva — blocker pre US1 aj US2)

**Purpose**: Repositories a ApiClient — závislosť pre obe user stories.

**⚠️ CRITICAL**: US1 a US2 nemôžu začať kým táto fáza nie je hotová.

- [X] T005 [P] Create `android_app/app/src/main/java/com/example/madhdtracker/data/repository/EncryptedPreferencesRepository.kt` — konštruktor `(context: Context)`; použije `EncryptedSharedPreferences.create()`; getter/setter pre `accessToken: String` (kľúč `access_token`, default `""`) a `userEmail: String` (kľúč `user_email`, default `""`); metóda `clearSession()` vymaže oba kľúče
- [X] T006 [P] Extend `android_app/app/src/main/java/com/example/madhdtracker/data/repository/PreferencesRepository.kt` — pridaj getter `fun getServerUrl(): String` (kľúč `server_url`, default `""`) a setter `fun setServerUrl(url: String)` (normalizuje trailing slash)
- [X] T007 [P] Create `android_app/app/src/main/java/com/example/madhdtracker/data/remote/ApiClient.kt` — Ktor `HttpClient(Android)` s `ContentNegotiation { json() }` a `HttpTimeout { requestTimeoutMillis = 5000 }`; suspend funkcie: `login(baseUrl, email, password): Result<LoginResponse>`, `register(baseUrl, email, password): Result<RegisterResponse>`, `getMe(baseUrl, token): Result<MeResponse>`; všetky volania obalené v `try/catch` — `IOException`/`ConnectException` → `Result.failure`; `@Serializable` data classes `LoginRequest`, `LoginResponse`, `RegisterResponse`, `MeResponse` definované v rovnakom súbore
- [X] T008 Create `android_app/app/src/main/java/com/example/madhdtracker/data/repository/UserRepository.kt` — konštruktor `(context: Context)`; inštanciuje `ApiClient`, `EncryptedPreferencesRepository`, `PreferencesRepository`; metóda `suspend fun login(email, password): LoginResult` — ak `serverUrl.isBlank()` vráti `LoginResult.NoServer`; volá `ApiClient.login()`; pri úspechu zavolá `getMe()` a uloží token + email; sealed class `LoginResult { Success(email, totalDays, createdAt), Error(message), NoServer, Loading }`; analogicky `register()` a `logout()` (len vyčistí session); `fun getCurrentUser(): UserInfo?` vráti email ak token neprázdny

**Checkpoint**: Projekt sa kompiluje. `UserRepository` je inštanciovateľný.

---

## Phase 3: User Story 1 — Server URL v Settings (Priority: P1) 🎯 MVP

**Goal**: Používateľ nastaví server URL v Settings. URL sa ukladá a načíta po reštarte app.

**Independent Test**: Quickstart Scenár 1 — zadaj URL, zavri app, otvor → URL zachovaná.

- [X] T009 [US1] Update `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/SettingsScreen.kt` — pridaj sekciu "Server" (pred alebo za existujúcimi nastaveniami); `OutlinedTextField` pre server URL s label "URL servera (napr. http://192.168.1.10:8095)"; `Button("Uložiť")` zavolá `PreferencesRepository.setServerUrl()`; `remember { mutableStateOf(prefsRepo.getServerUrl()) }` pre lokálny stav; `PreferencesRepository` dostane `SettingsScreen` cez parameter (rovnaký vzor ako `repository: TrackerRepository`)

**Checkpoint**: Quickstart Scenár 1 prechádza — URL sa ukladá a načíta po reštarte.

---

## Phase 4: User Story 2 — Account obrazovka + voliteľný login (Priority: P2)

**Goal**: Nová Account obrazovka v navigácii. Voliteľný login — tracker funguje bez prihlásenia.

**Independent Test**: Quickstart Scenáre 2–6 — navigácia, login, register, chybové stavy, logout.

- [X] T010 [P] [US2] Create `android_app/app/src/main/java/com/example/madhdtracker/ui/AccountViewModel.kt` — `ViewModel()`; `private val userRepository = UserRepository(application)` cez `AndroidViewModel(application)`; `val uiState: StateFlow<AccountUiState>` kde `AccountUiState` je sealed class `{ LoggedOut, Loading, LoggedIn(email, totalDays, createdAt), Error(message) }`; `fun login(email, password)` spustí coroutine, mapuje `LoginResult` na `AccountUiState`; `fun register(email, password)` analogicky; `fun logout()` volá `userRepository.logout()`, nastaví `LoggedOut`; pri init načíta aktuálny stav z `userRepository.getCurrentUser()`
- [X] T011 [P] [US2] Create `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/AccountScreen.kt` — `@Composable fun AccountScreen(viewModel: AccountViewModel)`; `val state by viewModel.uiState.collectAsState()`; `when(state)`: `LoggedOut` → formulár s `OutlinedTextField` pre email + heslo + `Button("Prihlásiť")` + `TextButton("Registrovať sa")`; `Loading` → `CircularProgressIndicator`; `LoggedIn` → Card s emailom, počtom dní (`Sledovaných dní: X`), dátumom registrácie, `Button("Odhlásiť sa")`; `Error` → červený text s chybou pod formulárom; formulárový stav cez `remember { mutableStateOf("") }`
- [X] T012 [US2] Update `android_app/app/src/main/java/com/example/madhdtracker/ui/navigation/AppNavGraph.kt` — pridaj `const val ACCOUNT = "account"` do `AppRoutes`; pridaj `composable(AppRoutes.ACCOUNT) { AccountScreen(remember { AccountViewModel(application) }) }` do `NavHost`; `AccountViewModel` dostane `application` — použiť `LocalContext.current.applicationContext as Application`
- [X] T013 [US2] Update `android_app/app/src/main/java/com/example/madhdtracker/MainActivity.kt` — pridaj "Účet" do bottom navigation: nový `BottomNavigationItem` s ikonou `Icons.Default.AccountCircle`, label "Účet", route `AppRoutes.ACCOUNT`; poradie nav itemov: Home | Tracker | Trend | Účet | Settings (alebo existujúce poradie + Účet pred Settings)

**Checkpoint**: Quickstart Scenáre 2–6 prechádzajú. Tracker funguje offline bez prihlásenia.

---

## Phase 5: Polish & Validácia

- [X] T014 [P] Create `android_app/app/src/test/java/com/example/madhdtracker/data/remote/ApiClientTest.kt` — Ktor `MockEngine` unit testy (JVM): `loginSuccess_returnsAccessToken`, `loginWrongPassword_returns401_resultIsFailure`, `registerEmailTaken_returns409_resultIsFailure`, `serverUnavailable_connectException_resultIsFailure`; každý test inštanciuje `ApiClient` s `HttpClient(MockEngine { ... })`; žiadne živé sieťové volania
- [X] T015 Manual validation — spusti quickstart.md Scenáre 1–7 a zaznač výsledky; overiť Constitution I (offline-first) a Constitution IV (minimálne kliknutia)

---

## Dependencies & Execution Order

```
T001→T002→T003→T004 (build config, sekvenčné — rovnaký súbor alebo závislosť)
     ↓
T005, T006, T007 [paralelné — rôzne súbory]
     ↓
T008 (UserRepository — závisí na T005+T006+T007)
     ↓
T009 [US1] (závisí na T006)     T010, T011 [paralelné, závisia na T008]
                                      ↓
                                 T012 (závisí na T011)
                                      ↓
                                 T013 (závisí na T012)
T014 [P] (závisí na T007, paralelne s T009–T013)
T015 (po všetkom)
```

### Parallel Opportunities

```
# Fáza 2 — po T001-T004:
T005 (EncryptedPrefsRepo) ‖ T006 (PrefsRepo extend) ‖ T007 (ApiClient)

# Fáza 4 — po T008:
T010 (AccountViewModel) ‖ T011 (AccountScreen)

# Fáza 5 — paralelne s US1/US2:
T014 (ApiClientTest) — môže bežať paralelne s T009-T013
```

---

## Implementation Strategy

### MVP First (US1)

1. Phase 1: Setup (T001–T004) — build konfigurácia
2. Phase 2: Foundational (T005–T008) — dátová vrstva
3. Phase 3: US1 (T009) — server URL v Settings
4. **STOP & VALIDATE**: Scenár 1 prechádza → URL sa ukladá
5. Phase 4: US2 (T010–T013) — Account screen + login

### Incremental Delivery

- Po T009: Server URL funguje → testovateľný checkpoint (bez login UI)
- Po T013: Celé F1 hotové → demo-ready
- T014–T015: Testy + manuálna validácia pred mergom

---

## Notes

- `ApiClient` musí byť testovateľný bez živého servera — preto `MockEngine` (Ktor)
- `UserRepository` ako singleton na úrovni `Application` — manuálna injekcia cez `remember { }` bez DI frameworku (Constitution VII)
- Cleartext HTTP povolené len pre private IP rozsahy (nie pre verejné domény) — `network_security_config.xml`
- Constitution I (offline-first): `serverUrl.isBlank()` guard v `UserRepository` je non-negotiable
- Constitution IV: Account nav item viditeľný z hlavnej navigácie — nie skrytý v Settings

---

## Phase 6: Convergence

- [X] T016 [US1] Implement background auto-sync trigger in `android_app/app/src/main/java/com/example/madhdtracker/data/repository/UserRepository.kt` and `android_app/app/src/main/java/com/example/madhdtracker/ui/AccountViewModel.kt` — when server URL is set and user is logged in, trigger sync automatically (e.g. on app resume / after login) per US1/AC4 (missing)
- [X] T017 [US1] Add "Test connection" button and connection status text to `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/SettingsScreen.kt` — after URL save, show "Pripojený" or "Server nedostupný" status label per US1/AC1 (partial)
- [X] T018 Add `serverUnavailable_connectException_resultIsFailure` test case to `android_app/app/src/test/java/com/example/madhdtracker/data/remote/ApiClientTest.kt` — use `MockEngine` that throws `IOException`; assert `ApiClient.login()` returns failure per T014 spec (missing)
- [X] T019 Add URL format validation to `android_app/app/src/main/java/com/example/madhdtracker/ui/screens/SettingsScreen.kt` — before saving, check that URL starts with `http://` or `https://`; show inline error text if invalid per spec §Edge Cases (missing)
