# Research: Dual Vector Split

## 1. DB Migration stratégia

**Decision**: Room `@AutoMigration(from = 1, to = 2)` — automatická migrácia pri pridaní nullable stĺpcov.

**Rationale**: Pridávame dva nullable stĺpce (`positiveIndex REAL`, `negativeIndex REAL`) do tabuľky `index_daily`. Room 2.4+ podporuje `@AutoMigration` pre jednoduché zmeny schémy (pridanie stĺpca, premenovanie). Žiadna `MigrationSpec` nie je potrebná, keď pridávame len nullable stĺpce bez DEFAULT. Room automaticky vykonáva `ALTER TABLE index_daily ADD COLUMN positiveIndex REAL` a `ADD COLUMN negativeIndex REAL`.

**Požiadavka**: `AppDatabase` musí mať `exportSchema = true` a definovaný `schemaLocation` (v `build.gradle.kts` cez `ksp { arg("room.schemaLocation", ...) }`). Bez toho sa `@AutoMigration` skompiluje, ale Room nebude vedieť porovnať schémy.

**Alternatívy zvažované**:
- **Manuálna migrácia** (`Migration(1, 2)`): Flexibilnejšia, ale zbytočne verbose pre jednoduchú operáciu pridania stĺpca. Odmietnuté.
- **Nová entita `SubIndexDailyEntity`**: Separátna tabuľka pre sub-indexy. Čistejšie oddelenie, ale vyžaduje JOIN pri každom dotaze a komplikuje `IndexDao`. Odmietnuté pre MVP.
- **On-the-fly výpočet** (bez ukladania): Eliminuje migráciu, ale sub-indexy sa musia prepočítavať z raw `event_value` dát pri každom požiadavku — pomalšie, nekonzistentné s existujúcim vzorcom ukladania `indexValue`. Odmietnuté.

---

## 2. Reprezentácia negatívneho sub-indexu

**Decision**: Raw (0 = ideálne, 100 = maximum problémov). Nie invertovaný.

**Rationale**: Používateľ chce "minimalizovať červený vektor". Raw skóre priamo komunikuje "koľko negatívnych vzorov si dnes mal". Invertovaný (100 = perfektný) by bol mätúci — červený stĺpec by bol vysoký pri dobrom dni.

**Výpočet**:
```
NegativeIndex_d = 100 × Σ(w_i × e_i for i in negativeKeys) / Σ(w_i for i in negativeKeys)
```
kde `e_i` je `valueEffective` (0–1) a `w_i` je váha — bez invertovania.

---

## 3. Dual-bar chart layout pre Trend obrazovku

**Decision**: Side-by-side bars per deň — zelený stĺpec (ľavý) + červený stĺpec (pravý) pre každý deň.

**Rationale**: Side-by-side je najbežnejší pattern pre porovnanie dvoch metrík per časovú jednotku. Stacked bars by skryli individuálne hodnoty (zelená + červená by nemusela dávať zmysel ako súčet). Stacked odmietnuté.

**Implementácia**: `DualBarChart` composable — každý deň dostane dve rects vedľa seba, každé s 40% šírky dňa + 10% medzera medzi stĺpcami.

---

## 4. Radar chart — dva polygóny

**Decision**: Dva oddelené uzavreté `Path` objekty — zelený polygon spájajúci len pozitívne osi, červený polygon spájajúci len negatívne osi.

**Rationale**: Existujúci radar chart (feature 003) farbí individuálne osi. Feature 004 pridáva dva farebné polygóny. Kreslia sa oba na rovnaký Canvas, s translucent fill — zelený polygon s ~30% alpha zelená, červený s ~30% alpha červená.

**Poradie kreslenia**: Grid rings → Axes → Zelený fill polygon → Červený fill polygon → Zelené stroke → Červené stroke → Dots → Labels. Fill polygóny sú pod stroke líniami.

**Úprava `RadarChart` composable**: Existujúci single `dataPath` sa rozdelí na `positivePath` a `negativePath`. Každý spája len príslušné osi (v poradí, v akom sa vyskytujú na radare — nie súvisle, ale to je vizuálne akceptovateľné pre 4-axisové skupiny).

---

## 5. Výpočet sub-indexov — integrácia do existujúceho flow

**Decision**: Rozšíriť `computeAndSaveDailyIndex(dayId)` o výpočet a uloženie oboch sub-indexov v jednom DB write.

**Rationale**: Sub-indexy sú vždy konzistentné s kombinovaným indexom (rovnaké vstupné dáta, rovnaký čas výpočtu). Separátna metóda `computeAndSaveSubIndices()` by mohla byť zabudnutá zavolať. Rozšírením existujúcej metódy garantujeme, že všetky tri hodnoty sú vždy spolu.

**Zmena**: `IndexDailyEntity(eventDayId, indexValue)` → `IndexDailyEntity(eventDayId, indexValue, positiveIndex, negativeIndex)` kde `positiveIndex` a `negativeIndex` sú `Double?` (NULL pre historické záznamy pred migráciou).

---

## 6. HomeScreen layout

**Decision**: Ponechať veľké číslo kombinovaného indexu + pridať dva menšie farebné indikátory (zelený / červený) v `Row` pod ním.

**Rationale**: Kombinovaný index je primárna metrika (Constitution § IV — Home obrazovka zobrazuje okamžitú hodnotu). Sub-indexy sú doplnkový pohľad. Nahradenie by narušilo UX konzistenciu existujúcich používateľov.

**Layout**:
```
Denný ADHD index
    [72]              ← veľké číslo, kombinovaný index
[↑ 85 Pozitívne]  [↓ 31 Negatívne]  ← zelené/červené menšie čísla
```
