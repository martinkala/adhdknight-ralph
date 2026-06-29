# Research: App Configuration Layer

**Feature**: 005-app-config-layer | **Date**: 2026-06-28

## R-001: Config formát — JSON vs Properties vs custom

**Decision**: JSON (`org.json.JSONObject`)

**Rationale**: `org.json` je súčasťou Android SDK od API 1 — žiadna nová závislosť. JSON podporuje hierarchickú štruktúru (grouped by domain: weights, adaptation, asrs, notification), čo je čitateľnejšie ako flat `.properties`. Custom DSL by bol over-engineered pre 40 parametrov.

**Alternatives considered**:
- `.properties` (Java `Properties` class) — flat, bez skupín, slabá čitateľnosť pre 40 parametrov
- YAML — vyžaduje SnakeYAML alebo Jackson, čo by porušilo §VII
- Kotlin DSL file — vyžaduje Kotlin scripting runtime, outside scope
- XML — `android.util.Xml` / `XmlPullParser` dostupný bez dep, ale oveľa viac kódu ako JSON pre rovnaký efekt

**Závěr**: JSON cez `org.json` je najlepší pomer výkon/čitateľnosť/nulové nové závislosti.

---

## R-002: Kde uložiť config súbor

**Decision**: `src/main/assets/app_config.json`

**Rationale**: Android `assets/` sú dostupné cez `AssetManager.open("app_config.json")` — synchronous, no permissions needed, bundled with APK. Zmena vyžaduje rebuild (FR-008: účinok po reštarte, nie hot-reload) — čo je presne požadované správanie. Alternatívny `res/raw/` je ekvivalentný ale `assets/` je konvenčnejší pre config súbory (nie lokalizované rezy).

**Alternatives considered**:
- `SharedPreferences` — určený pre user preferences, nie developer config; bez textovej editácie
- `res/raw/` — rovnako bundled, ale `assets/` je štandardná prax pre config
- External storage — vyžaduje permissions, porušuje offline-first a security
- Network fetch — porušuje §I (offline-first) a §VII scope

---

## R-003: Injekcia AppConfig do závislostí

**Decision**: Konštruktor parameter — `TrackerRepository(db, appConfig)`, `NotificationRules(config)` ako class inštancia

**Rationale**: Bez DI frameworku (§VII) je manuálna injekcia cez konštruktor správny vzor. `AppConfig` sa načíta raz v `MainActivity.AppRoot` cez `remember { AppConfigLoader.load(context.assets) }` — zaručuje jedno načítanie za lifecycle. `NotificationRules` musí byť refaktorovaný z `object` na `class` aby prijal config (aktuálne je to singleton s hardcoded hodnotami).

**Alternatives considered**:
- Application-level singleton (companion object) — ťažšie testovateľné, globálny stav
- Hilt/Koin — explicitne mimo scope v MVP (§VII)
- Re-čítanie zo súboru v každom Repository call — zbytočná I/O réžia

---

## R-004: Fallback stratégia pre neplatné hodnoty

**Decision**: Per-parameter fallback na zabudovanú default hodnotu; žiadny pád; audit log cez `android.util.Log.d`

**Rationale**: FR-006 a FR-007 vyžadujú graceful degradáciu. `DefaultWeights.kt` zostáva ako jediný zdroj pravdy pre fallback hodnoty — tým sa zabezpečí, že `AppConfig` s chýbajúcim súborom produkuje identické správanie ako pred refaktorom (SC-004). Audit log cez `Log.d("AppConfig", ...)` je dostupný v Logcat bez nových závislostí (SC-005).

**Validačné pravidlá**:
- Váhy: záporná hodnota → nahradiť defaultom; ak suma ≠ 100 → normalizovať (rovnaký algoritmus ako pri adaptácii váh)
- `alpha`: ≤ 0 alebo > 1 → nahradiť defaultom (0.2); > 1 je mimo matematicky zmysluplný rozsah
- `clamp_min_factor` ≥ `clamp_max_factor` → nahradiť oboch defaultmi
- `correlation_threshold`: ≤ 0 → nahradiť defaultom
- Časy `quiet_start/end`: hodiny mimo 0-23 → nahradiť defaultmi
- Unknown JSON keys → silently ignored (spätná kompatibilita)

---

## R-005: Testovateľnosť bez AssetManager

**Decision**: `AppConfigLoader` prijme `InputStream?` namiesto `AssetManager` priamo; factory metóda `load(assetManager)` vytvorí stream

**Rationale**: Unit testy (JVM, nie Android instrumented) nemôžu použiť `AssetManager`. Ak loader prijme `InputStream?`, testy môžu injektovať `ByteArrayInputStream` s JSON stringom. `null` stream = chýbajúci súbor = fallback. Toto je štandardný Android testovací pattern pre assets.

**Alternatives considered**:
- Robo­electric — testuje Android komponenty na JVM, ale pridáva závislosť
- Instrumented test — pomalé, vyžaduje emulátor
- Mocking `AssetManager` — verbose, krehké

---

## R-006: Normalizácia váh pri neúplnej konfigurácii

**Decision**: Ak sú prítomné len niektoré váhy a ich suma je mimo rozsahu 95-105, normalizovať rovnakým algoritmom ako `adaptWeights` (`scale = defaultSum / updatedSum`)

**Rationale**: Spec edge case — "ak váhy nesčítajú na 100, normalizovať". Chýbajúce elementy dostanú default váhu (FR-006). Tolerancia ±5% zabezpečuje, že floating point zaokrúhľovacie chyby nespôsobia zbytočnú normalizáciu.
