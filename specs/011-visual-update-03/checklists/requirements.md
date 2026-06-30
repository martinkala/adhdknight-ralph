# Specification Quality Checklist: Visual Update 03

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-06-30
**Feature**: [spec.md](../spec.md)

## Content Quality

- [X] No implementation details (languages, frameworks, APIs)
- [X] Focused on user value and business needs
- [X] Written for non-technical stakeholders
- [X] All mandatory sections completed

## Requirement Completeness

- [X] No [NEEDS CLARIFICATION] markers remain
- [X] Requirements are testable and unambiguous
- [X] Success criteria are measurable
- [X] Success criteria are technology-agnostic (no implementation details)
- [X] All acceptance scenarios are defined
- [X] Edge cases are identified
- [X] Scope is clearly bounded
- [X] Dependencies and assumptions identified

## Feature Readiness

- [X] All functional requirements have clear acceptance criteria
- [X] User scenarios cover primary flows
- [X] Feature meets measurable outcomes defined in Success Criteria
- [X] No implementation details leak into specification

## Constitution Alignment

- [X] §I (MVVM/Repository): Žiadne nové vrstvy; auto-save volá existujúce Repository metódy
- [X] §II (Index formula): Spec nemení výpočet indexu — len filtruje zobrazenie a ukladanie
- [X] §III (DB schema): Auto-save (US2) aktualizuje existujúce polia; žiadna nová entita ani stĺpec
- [X] §IV (UX): Auto-save priamo implementuje "minimálne kliknutia"; Home placeholder je v súlade s "prázdny stav s CTA"
- [X] §VII (No new libraries): Pie chart a dual bar improvements sú realizovateľné cez Canvas (Compose) — žiadna nová závislosť

## Notes

- **US1 (P1)**: Oprava chyby — Home zobrazuje predchádzajúci deň keď dnešok nie je vyplnený. Placeholder: 3 sivé bary na každej strane.
- **US2 (P1)**: Auto-save pri každom prepnutí switcha/slidera; odstránenie tlačidla "Uložiť deň"
- **US3 (P2)**: Dual bar chart — grouping podľa kategórie, protiľahlé páry, váha vo vnútri baru
- **US4 (P2)**: Koláčový graf na VectorScreen s aktívnymi aktivitami
- **US5 (P2)**: Swipe navigácia doľava/doprava na Home medzi dňami s existujúcimi záznamami
- **US6 (P3)**: Info obrazovka s váhami entít v menu
- **US7 (P3)**: Ikona domu v dolnom menu (namiesto "H")
- **US8 (P3)**: Vyšetrovanie — user-defined entity v trackeri (predpokladaný bug)
- Ciel 3 z pôvodného spec.txt bol otázka "bug alebo zámer?" → zahrnutý ako US8 s predpokladom bug
- Ciel 6 pôvodne spomínal "7 bárov" — bolo to zle napísané; správna hodnota je 3 bary na každej strane (explicitne potvrdené ďalším textom v spec.txt)
- FR-016 pokrýva závislosť US8 od EntityManagementScreen — žiadna nová DB entita nie je potrebná
- Všetky položky prešli validáciou — spec je pripravený pre `/speckit-tasks`
