# Research: Configurable Entities

**Feature**: 007-comfigurable-entities  
**Date**: 2026-06-29

---

## Decision 1: YAML Parser knižnica

**Decision**: `org.yaml:snakeyaml:2.2`

**Rationale**: 
- Jediná produkčne overená JVM YAML knižnica bez tranzitívnych závislostí (Apache 2.0)
- Android-kompatibilná od API 21+, testovaná na min SDK 26
- 0 tranzitívnych závislostí
- SnakeYAML má identické API na JVM aj Android — zdieľaná schéma entities.yaml bude parsovateľná aj na budúcom serveri bez zmeny kódu

**§VII Justification** (constitution): Existujúca závislosť `org.json` parsuje len JSON, nie YAML. Formát YAML bol explicitne zvolený používateľom pre čitateľnosť a inline komentáre. Alternatíva — vlastný YAML subset parser — by priniesla maintenance burden a bezpečnostné riziká. `snakeyaml` je priemyselný štandard s 0 transitivnými závislosťami.

**Alternatives considered**:
- `org.json` — existuje, ale nepodporuje YAML
- `kaml` (Kotlin YAML) — vyžaduje snakeyaml-engine aj kotlinx.serialization; 2 nové deps namiesto 1
- Vlastný parser — zamietnutý: príliš náchylný na chyby pre full YAML gramatiku

---

## Decision 2: Algoritmus pre skupiny pod-entít (FR-006)

**Decision**: Kategória má explicitný `weight` (budget). Index je vážený priemer cez kategórie. Príspevok kategórie = `avg(active sub-entity effective values)` × `category.weight`.

**Rationale**:
Pridanie nových pod-entít pod kategóriu nesmie inflatovať jej vplyv na index. Explicitný `category.weight` fixuje celkový príspevok kategórie bez ohľadu na počet pod-entít.

Príklad:
- Kategória `physical_activity` má `weight: 11.0`
- Sub-entity: `pushups(5)`, `running(5)`, `cycling(5)` — definované váhy sú relatívne v rámci skupiny
- Len `pushups` aktívny a splnený: priemer skupiny = 1.0, príspevok = 1.0 × 11.0 = 11.0
- Všetky 3 splnené: priemer = (5×1 + 5×1 + 5×1)/(5+5+5) = 1.0, príspevok = 11.0
- Len `pushups` splnený z 3 aktívnych: priemer = (5×1 + 5×0 + 5×0)/15 = 0.33, príspevok = 3.67

**Algoritmus**:
```
total_index = sum(category.weight × group_avg(active sub-entities)) / sum(active category weights) × 100
```

**Alternatives considered**:
- Absolútne váhy bez normalizácie → pridanie 3 pod-entít by strojnásobilo vplyv kategórie (zamietnuté)
- Normalizácia cez aktívne sub-entity count → deaktivácia sub-entity "boost-uje" ostatné (zmätočné pre používateľa)

---

## Decision 3: Perzistencia stavu aktívnosti (user overrides)

**Decision**: Room DB tabuľka `user_element_override(elementKey, isActive)` ako user-level override

**Rationale**:
- Konzistentné s existujúcim Room stackom (§I constitution)
- Prežije app update aj clear cache (na rozdiel od SharedPreferences)
- Room tabuľka umožňuje v budúcnosti pridať timestamp, sync flag a ďalšie atribúty bez migrácie

**Alternatives considered**:
- SharedPreferences — rýchlejšie, ale stráca sa pri backup/restore; nedáva query flexibility
- Súbor user_overrides.json — zamietnutý: ďalší custom parser, bez atomicity

---

## Decision 4: Separácia entity configu od app_config.json

**Decision**: Nový súbor `assets/entities.yaml` pre entity definície. `app_config.json` zostáva pre algoritmické parametre (alpha, thresholds). `AppConfig.weights` sa v budúcnosti odvodí z `EntityConfig`.

**Rationale**:
- Čistá separácia zodpovedností: algoritmus ↔ obsah
- Môžu sa meniť nezávisle (nové entity vs. ladenie alpha)
- `DefaultWeights.kt` zostáva ako fallback pre AppConfigLoader (backward compat)
- entities.yaml nahradí sekciu `weights` v app_config.json v ďalšom kroku (mimo scope tohto PR)

**Migration path**:
1. Tento PR: pridať entities.yaml + EntityConfigLoader → TrackerRepository dostáva EntityConfig
2. Budúci PR: odstrániť `weights` z AppConfig, AppConfig.weights sa generuje z EntityConfig

---

## Decision 5: Sharing schema medzi Android a budúcim serverom

**Decision**: entities.yaml je umiestnený v `android_app/app/src/main/assets/entities.yaml`. Budúci server bude čítať rovnaký súbor z classpath (SnakeYAML na JVM identický).

**Rationale**:
- Rovnaký YAML súbor, rovnaký SnakeYAML parser → guaranteed parity (FR-007)
- Žiadna custom serialization logika, len YAML Map parsing

---

## Decision 6: overall_feeling ako špeciálna root entita

**Decision**: `overall_feeling` zostáva mimo kategóriového systému — je to korelačný referenčný bod pre adaptáciu váh. Nie je pod žiadnou kategóriou a nepodlieha FR-006 normalizácii.

**Rationale**:
- Ak by bol overall_feeling pod kategóriou, adaptačný algoritmus by nemal priamy prístup k osi korelácie
- §II constitution: logika indexu je non-negotiable — zaradenie overall_feeling do kategórie by vyžadovalo úpravu AdaptationConfig, čo je mimo scope
