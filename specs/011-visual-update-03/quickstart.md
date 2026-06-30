# Quickstart Validation Guide: Visual Update 03

**Date**: 2026-06-30 | **Feature**: 011-visual-update-03

---

## Prerequisites

- Android emulator alebo fyzické zariadenie (API 26+)
- Debug build: `./gradlew :app:installDebug` v `android_app/`
- Prázdna alebo testovacia DB (odporúčané: vymazať dáta appky pred testovaním)

---

## Scenario 1: US1 — Home zobrazuje placeholder keď deň nie je vyplnený

**Cieľ**: Overiť, že Home vždy zobrazuje dáta pre aktuálny deň, nie predchádzajúci.

**Setup**: Vymazať všetky dáta appky (Settings → Clear data).

**Kroky**:
1. Spustiť appku → otvoriť Home
2. **Očakávané**: Bar chart zobrazuje 3 sivé bary naľavo a 3 napravo (rôzne veľkosti), bez popiskov, bez čísel indexu
3. Prejsť do Trackera → vyplniť aspoň 3 entity → prepnúť switch → počkať 1s
4. Vrátiť sa na Home
5. **Očakávané**: Bar chart zobrazuje skutočné farebné bary s entitami

**Edge case**: Zmeniť systémový dátum na zajtra → otvoriť Home → **Očakávané**: sivý placeholder (nie dáta zo včerajška)

---

## Scenario 2: US2 — Auto-save, žiadne tlačidlo "Uložiť deň"

**Cieľ**: Overiť, že prepnutie entity sa okamžite uloží a tlačidlo "Uložiť deň" zmizlo.

**Kroky**:
1. Otvoriť Tracker
2. **Očakávané**: Žiadne tlačidlo "Uložiť deň" nie je viditeľné v hlavičke
3. Prepnúť switch niektorej entity na ON
4. Okamžite navigovať na Home (klik na "Home" v dolnom menu)
5. Vrátiť sa do Trackera (klik na "Tracker")
6. **Očakávané**: Switch je stále ON — dáta boli zachované bez uloženia

**Slider test**:
1. Prepnúť switch entity na ON → zobrazí sa slider
2. Posunúť slider na hodnotu 4
3. Počkať 1 sekundu → navigovať na Home → vrátiť sa na Tracker
4. **Očakávané**: Slider zostáva na hodnote 4

---

## Scenario 3: US3 — Dual bar chart: kategórie, váhy

**Cieľ**: Overiť, že entity z rovnakej kategórie sú vedľa seba a váha je viditeľná v bare.

**Setup**: Vyplniť deň vrátane aspoň 1 negatívnej a 1 pozitívnej entity z tej istej kategórie (ak taká existuje v konfigu).

**Kroky**:
1. Vyplniť entity v Trackeri → navigovať na Home
2. **Očakávané**: Entity z rovnakej kategórie sú zobrazené na rovnakých riadkoch (negatívna naľavo, pozitívna napravo)
3. Pozrieť na ľubovoľný viditeľný bar
4. **Očakávané**: Vo vnútri baru je číslo (váha entity)
5. Ak bar je veľmi krátky (≤ 20% šírky): číslo sa nemusí zobraziť — to je správne správanie

---

## Scenario 4: US4 — Koláčový graf na Denný detail

**Cieľ**: Overiť, že VectorScreen zobrazuje koláčový graf s farebnými výsečami.

**Setup**: Vyplniť aspoň 3 entity v Trackeri (auto-save sa o to postará).

**Kroky**:
1. Navigovať na Denný detail (VectorScreen) — klik na "Trend" → klik na deň, alebo priamo cez navigáciu
2. **Očakávané**: Koláčový graf je viditeľný v hornej časti obrazovky
3. Graf zobrazuje farebné výseče — zelené pre pozitívne entity, červené pre negatívne
4. **Prázdny stav**: Ak žiadne entity nie sú vyplnené → koláčový graf sa nezobrazí

---

## Scenario 5: US5 — Swipe navigácia medzi dňami

**Cieľ**: Overiť, že swipe na Home naviguje medzi dňami.

**Setup**: Mať aspoň 2 rôzne dni vyplnené v DB.

**Kroky**:
1. Na Home — swipnúť doľava (smer ← )
2. **Očakávané**: Zobrazí sa predchádzajúci deň; nadpis sa zmení na "Historické dáta – [dátum]"
3. Swipnúť doprava (smer → )
4. **Očakávané**: Zobrazí sa nasledujúci deň (alebo dnešok)
5. Na najstaršom dni — swipnúť doľava
6. **Očakávané**: Nič sa nestane (žiadny predchádzajúci deň)
7. Na dnešnom dni — swipnúť doprava
8. **Očakávané**: Nič sa nestane (žiadny budúci deň)

---

## Scenario 6: US6 — Info obrazovka

**Cieľ**: Overiť, že Info je prístupné z menu a zobrazuje entity s váhami.

**Kroky**:
1. Kliknúť "Info" v dolnom navigačnom menu
2. **Očakávané**: Otvorí sa Info obrazovka
3. **Očakávané**: Zoznam všetkých entít s názvami, váhami a popismi
4. Ak existujú personalizované váhy: sú zobrazené (nie default)

---

## Scenario 7: US7 — Home ikona v menu

**Cieľ**: Overiť, že Home v menu má ikonu domu.

**Kroky**:
1. Pozrieť na dolné navigačné menu
2. **Očakávané**: Prvá položka má ikonu domu (nie text "H")

---

## Scenario 8: US8 — User-defined entity v trackeri

**Cieľ**: Overiť, že entity pridané cez EntityManagement sa objavujú v Trackeri.

**Kroky**:
1. Navigovať do Settings → Entity Management
2. Pridať novú entitu (napr. "Test entita", impact = 1, váha = 5)
3. Vrátiť sa → navigovať do Tracker
4. **Očakávané**: Nová entita je viditeľná v zozname s on/off switchom
5. Prepnúť switch → auto-save → vrátiť sa na Home
6. **Očakávané**: Home zobrazuje novú entitu v bare (ak je pozitívna, na pravej strane)

---

## Regression checks

Po implementácii všetkých US overiť, že existujúca funkcionalita nie je porušená:

- [ ] Tracker normálne načíta predchádzajúci deň keď sa vyberie dátum
- [ ] Denný index sa správne vypočíta po vyplnení
- [ ] Trend obrazovka zobrazuje historický line chart
- [ ] Notifikácie sa nestratili (settings zostávajú)
- [ ] Export dát funguje (Settings → Export)
