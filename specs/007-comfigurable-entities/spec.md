# Feature Specification: Configurable Entities

**Feature Branch**: `007-comfigurable-entities`

**Created**: 2026-06-28

**Status**: Done

**Input**: Zmena definície entít na hierarchickú, štruktúrovanú, rozšíriteľnú konfiguráciu

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hierarchická konfigurácia entít (Priority: P1)

Vývojár/admin definuje entity v config súbore s plnou sadou atribútov (weight, impact, parent, description, scale) a hierarchiou (kategória → entita → pod-entita). Aplikácia načíta konfiguráciu pri štarte a správne vybuduje strom entít.

**Why this priority**: Bez hierarchickej konfigurácie nie je možné implementovať žiadnu z ostatných user stories. Je to základ celého feature.

**Independent Test**: Pridať novú entitu `pushups` pod `physical_activity` do config súboru, rebuild → entita sa zobrazí v trackeri pod fyzickou aktivitou s correct weight.

**Acceptance Scenarios**:

1. **Given** platný config súbor s entitami a ich atribútmi, **When** sa aplikácia spustí, **Then** všetky entity sú dostupné v trackeri so správnymi hodnotami weight, impact, parent a scale
2. **Given** entita má `parent: physical_activity`, **When** sa zobrazuje v trackeri, **Then** je zoskupená pod kategóriou `physical_activity`
3. **Given** config súbor chýba alebo je neplatný, **When** sa aplikácia spustí, **Then** sa použijú defaultné entity (rovnaký fallback mechanizmus ako v app_config.json)
4. **Given** nová entita je pridaná do config súboru s `parent: head`, **When** rebuild, **Then** entita sa objaví v správnej kategórii bez zmeny kódu

---

### User Story 2 - Aktívne/neaktívne entity (Priority: P2)

Používateľ môže aktivovať alebo deaktivovať jednotlivé entity. Deaktivované entity sa nezobrazujú v dennom trackeri a nezahŕňajú sa do výpočtu indexu. Keď je rodičovská kategória neaktívna, pod-entity sa nezobrazujú.

**Why this priority**: Rôzni používatelia majú rôzne relevatné entity. Možnosť deaktivácie zlepšuje relevantnosť indexu.

**Independent Test**: Deaktivovať entitu `caffeine` → entita zmizne z trackera a jej váha sa neuvažuje v dennom výpočte.

**Acceptance Scenarios**:

1. **Given** entita `caffeine` je aktívna, **When** ju používateľ deaktivuje, **Then** zmizne z denného trackera a jej váha sa vynuluje v indexe
2. **Given** rodičovská kategória `physical_activity` je neaktívna, **When** sa zobrazuje tracker, **Then** ani pod-entity (`pushups`, `running`) sa nezobrazujú
3. **Given** používateľ deaktivuje entitu, **When** aplikácia reštartuje, **Then** nastavenie aktívnosti je zachované (persistované)
4. **Given** všetky entity v kategórii sú deaktivované, **When** sa počíta index, **Then** kategória neprispieva do výpočtu

---

### User Story 3 - Spravodlivý výpočet pre viacej pod-entít (Priority: P2)

Algoritmus výpočtu indexu ošetrí prípad, keď má rodičovská kategória viac aktívnych pod-entít — príspevok celej kategórie do indexu zostane proporcionálny a neinflatuje výsledok.

**Why this priority**: Bez tejto úpravy by kategória s 3 pod-entitami (pushups, running, cycling) mala 3× väčší vplyv ako kategória s 1 entitou — výsledok by bol skreslený.

**Independent Test**: Kategória `physical_activity` má 3 pod-entity s weight 5.0 každá. Kategória `sleep` má 1 entitu s weight 15.0. Označiť všetky entity ako done → príspevok `physical_activity` do indexu nesmie byť výrazne vyšší ako príspevok `sleep`.

**Acceptance Scenarios**:

1. **Given** kategória má 3 aktívne pod-entity každá s weight 5.0, **When** sa počíta index, **Then** celkový príspevok kategórie je ekvivalentný jednej entite s weight ~15.0 (vážený priemer, nie súčet)
2. **Given** kategória má 1 aktívnu pod-entitu z 3, **When** sa počíta index, **Then** príspevok kategórie zodpovedá iba aktívnej pod-entite
3. **Given** nová pod-entita je pridaná do existujúcej kategórie, **When** rebuild, **Then** algoritmus automaticky prepočíta váhový priemer bez manuálnej zmeny kódu

---

### User Story 4 - Používateľsky definované entity (Priority: P3)

Používateľ môže pridať vlastné entity pod existujúce top-level kategórie. Top-level kategórie sú nemenné — používateľ ich nemôže pridávať ani modifikovať.

**Why this priority**: Umožňuje personalizáciu bez narušenia štruktúry systému. P3 pretože je to rozšírenie nad rámec základnej funkčnosti.

**Independent Test**: Používateľ pridá entitu `yoga` pod kategóriu `physical_activity` → entita sa zobrazí v trackeri a zahrnie sa do výpočtu.

**Acceptance Scenarios**:

1. **Given** používateľ chce pridať vlastnú entitu, **When** zadá kľúč, weight, impact a vyberie rodičovskú kategóriu, **Then** entita sa uloží a je dostupná v trackeri
2. **Given** používateľ sa pokúsi pridať novú top-level kategóriu, **When** odošle formulár, **Then** akcia je zamietnutá s vysvetlením
3. **Given** vlastná entita je pridaná, **When** aplikácia reštartuje, **Then** vlastná entita je stále dostupná
4. **Given** vlastná entita má `parent: head`, **When** kategória `head` je neaktívna, **Then** vlastná entita sa tiež nezobrazuje

---

### Edge Cases

- Čo ak entita má `parent` ktorý neexistuje v config? → entita sa zaradí do fallback kategórie alebo sa ignoruje s logom
- Čo ak váhový priemer pod-entít v kategórii je 0 (všetky deaktivované)? → kategória neprispieva do indexu
- Čo ak používateľ deaktivuje všetky entity? → index sa nezobrazuje alebo zobrazuje N/A
- Čo ak dva používatelia majú rovnaký kľúč pre vlastnú entitu? → v prvej verzii nie je multi-user, kľúče sú unikátne v rámci zariadenia
- Čo ak config súbor obsahuje kruhovú referenciu (entita je vlastným rodičom)? → config sa odmietne, použijú sa defaulty
- Čo ak `scale` nie je definovaný pre entitu? → entita je binárna (checkbox, nie slider)

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Config súbor MUST definovať každú entitu s atribútmi: `key` (unikátny identifikátor), `weight` (kladné číslo), `impact` (+1 alebo -1), `parent` (kľúč rodičovskej kategórie), `description` (text), `active` (boolean, default true), `scale` (zoznam hodnôt, voliteľný)
- **FR-002**: Systém MUST podporovať dvojúrovňovú hierarchiu: top-level kategória → entity (a prípadne pod-entity)
- **FR-003**: Top-level kategórie MUST byť definované v systémovom config súbore a NESMÚ byť modifikovateľné používateľom
- **FR-004**: Systém MUST načítať entitný config pri štarte aplikácie s fallback na default entity pri chybe
- **FR-005**: Algoritmus výpočtu indexu MUST používať len aktívne entity
- **FR-006**: Algoritmus MUST aplikovať vážený priemer v rámci kategórie tak, aby počet pod-entít v kategórii neinflatoval príspevok kategórie do celkového indexu
- **FR-007**: Formát config súboru MUST byť identický pre Android app aj budúci server (zdieľaná schéma)
- **FR-008**: Stav aktívnosti entity (active: true/false) MUST byť persistovaný na úrovni používateľa oddelene od systémového configu
- **FR-009**: Používateľ MUST mať možnosť pridávať vlastné entity pod existujúce top-level kategórie v P3 scope
- **FR-010**: Systém MUST logovať ktoré entity boli načítané z configu a ktoré sú defaultné (rovnaký audit log vzor ako AppConfigLoader)
- **FR-011**: Entitný config MUST umožňovať pridanie nových atribútov bez nutnosti zmeny parser kódu pre existujúce atribúty

### Key Entities

- **Category**: top-level zoskupenie (head, food, physical_activity, sleep, lifestyle) — systémom definované, nemenné; atribúty: key, label, clickable (či je samostatná sledovateľná entita)
- **Element**: sledovateľná entita; atribúty: key, weight, impact, parent, description, active, scale (voliteľný)
- **UserElement**: používateľom definovaná entita rozširujúca Category; rovnaké atribúty ako Element, uložená oddelene od systémového configu
- **ElementTree**: výsledný strom Categories a Elements načítaný pri štarte — základ pre tracker, algoritmus aj UI

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Vývojár môže pridať novú entitu do config súboru a vidieť ju v tracker UI bez zmeny Kotlin kódu
- **SC-002**: Algoritmus produkuje rovnaký celkový index pre kategóriu s 1 entitou (weight 15) a kategóriu s 3 pod-entitami (weight 5 každá) pri rovnakom správaní
- **SC-003**: Deaktivácia entity sa prejaví v trackeri a v indexe do 1 reštartu aplikácie
- **SC-004**: Config súbor je čitateľný a editovateľný človekom bez špeciálnych nástrojov
- **SC-005**: Rovnaký config súbor je parsovateľný bez modifikácie na Android platforme aj v budúcom serveri (JVM kompatibilita)
- **SC-006**: Používateľom pridaná vlastná entita je dostupná v trackeri po reštarte bez straty dát

---

## Assumptions

- Top-level kategórie sú fixné v MVP: `sleep`, `physical_activity`, `head`, `food`, `lifestyle` — ďalšie sa môžu pridať v budúcnosti len cez systémový config
- Dvojúrovňová hierarchia (kategória → entita) je postačujúca pre MVP; hlbšia hierarchia nie je v scope
- Stav aktívnosti entity je lokálny pre zariadenie, nie synchronizovaný (v súlade s offline-first princípom §I)
- `overall_feeling` zostáva špeciálna entita — vždy aktívna, nie kategorizovateľná, slúži ako korelačný referenčný bod pre adaptáciu váh
- Config súbor entity je oddelený od `app_config.json` (algoritmické parametre) — čistejšia separácia zodpovedností
- Používateľsky definované entity (US4) sú ukladané do samostatného súboru / DB záznamu, nie do systémového config súboru
- Config súbor entít je vo formáte **YAML** — najčitateľnejší pre človeka, podporuje inline komentáre, prirodzená hierarchia. Vyžaduje novú závislosť (SnakeYAML alebo ekvivalent) — zdôvodnenie nutné v pláne per §VII constitution.

---
