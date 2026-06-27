# Quickstart Validation Guide: Dual Vector Split

## Prerequisites

- Android Studio (Hedgehog+), emulátor alebo fyzické zariadenie API 26+
- `./gradlew assembleDebug installDebug` z `android_app/`
- Pre scenáre s dátami: aspoň 3 dni vyplneného trackera

---

## Scenario 1 — Home obrazovka zobrazuje oba sub-indexy (P1 core)

1. Vyplniť denný tracker s mixom pozitívnych aj negatívnych elementov
2. Otvoriť Home obrazovku

**Expected**:
- Zelený indikátor "Pozitívne ↑" s hodnotou 0–100
- Červený indikátor "Negatívne ↓" s hodnotou 0–100
- Oba viditeľné bez scrollovania
- Deň s dobrým spánkom a cvičením → zelená hodnota vyššia
- Deň so stresom a alkoholom → červená hodnota vyššia

---

## Scenario 2 — Trend dual-bar chart (P2)

1. Mať vyplnené aspoň 3 dni dát
2. Otvoriť Trend obrazovku

**Expected**:
- Každý deň má zelený stĺpec (ľavý) a červený stĺpec (pravý)
- Legenda pod grafom: zelená bodka "Pozitívne" + červená bodka "Negatívne"
- Deň s dobrými návykmi: zelený stĺpec vyšší ako červený
- Deň s problémami: červený stĺpec výraznejší

---

## Scenario 3 — Radar chart — dva polygóny (P3)

1. Vyplniť denný tracker
2. Otvoriť Advanced vektor obrazovku

**Expected**:
- Svetlozelený polygon spája dátové body pre: Spánok, Aktivita, Proteíny, Mindful.
- Svetločervený polygon spája dátové body pre: Kofeín, Alkohol, Stres os., Stres pr.
- Oba polygóny sú odlíšiteľné (transparentný fill + farebný stroke)

---

## Scenario 4 — Historické dáta pred migráciou (edge case FR-008)

1. Inštalovať build pred feature 004 a vyplniť niekoľko dní dát (DB v1)
2. Aktualizovať na build s feature 004 (DB v2 — automatická migrácia)
3. Otvoriť Home a Trend obrazovku

**Expected**:
- Aplikácia sa nespustí do crash
- Historické dni: sub-indexy sa zobrazia ako "—" alebo prázdne stĺpce
- Nový deň po aktualizácii: oba sub-indexy sa správne vypočítajú a zobrazia

---

## Scenario 5 — Unit testy (Constitution § II gate)

```bash
cd android_app
./gradlew test
```

**Expected**: Testy `computePositiveIndex` a `computeNegativeIndex` v `IndexCalculatorTest` prechádzajú:
- Pozitívny index z len pozitívnych elementov = správna vážená hodnota
- Negatívny index z len negatívnych elementov = správna vážená hodnota (bez inverzie)
- Prázdne vstupy → `null`
- Elementy mimo skupiny sú ignorované

---

## Scenario 6 — DB migrácia v1→v2 (schema test)

```bash
cd android_app
./gradlew test --tests "*MigrationTest*"
```

**Expected**: Room migration test prechádza — tabuľka `index_daily` po migrácii obsahuje stĺpce `positiveIndex` a `negativeIndex` (nullable REAL).

---

## Build & install

```bash
cd android_app
./gradlew assembleDebug installDebug
```
