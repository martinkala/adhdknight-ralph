# UI Contracts: Dual Vector Split

## HomeScreen — dual index display

**Nové state vstupy** (z `HomeViewModel`):
```
positiveIndex: Double?   — null ak nie sú dáta
negativeIndex: Double?   — null ak nie sú dáta
```

**Vizuálny kontrakt**:
- Kombinovaný index zostáva ako veľké primárne číslo (existujúce `displaySmall`)
- Pod ním `Row` s dvoma menšími indikátormi:
  - Zelený indikátor: popisok "Pozitívne ↑", hodnota `positiveIndex.roundToInt()` alebo "—"
  - Červený indikátor: popisok "Negatívne ↓", hodnota `negativeIndex.roundToInt()` alebo "—"
- Zelený indikátor použije farbu `Color(0xFF81C784)` (Material Green 300 — konzistentné s 003)
- Červený indikátor použije farbu `Color(0xFFE57373)` (Material Red 300 — konzistentné s 003)
- Oba indikátory sú viditeľné bez scrollovania

**Invarianty**:
- Ak `positiveIndex == null` a `negativeIndex == null`: zobrazí sa rovnaký prázdny stav ako doteraz (bez crasha)
- Ak len jeden z indexov je null: zobrazí "—" len pre daný indikátor

---

## TrendScreen — DualBarChart

**Nové state vstupy** (z `TrendViewModel`):
```
dualSeries: List<DailySubIndexRow>
    DailySubIndexRow(date: String, positiveIndex: Double?, negativeIndex: Double?)
```

**Vizuálny kontrakt** — `DualBarChart` composable:
- Každý deň = dve side-by-side rects v Canvas:
  - Ľavý stĺpec: `positiveIndex` → `Color(0xFF81C784)`, výška proporčná k maxHodnotě v sérii
  - Pravý stĺpec: `negativeIndex` → `Color(0xFFE57373)`, výška proporčná k maxHodnotě v sérii
- Šírka stĺpca: `(dayWidth × 0.4f)` pre každý, medzera `dayWidth × 0.1f` medzi nimi
- Ak `positiveIndex == null`: ľavý stĺpec nie je nakreslený (prázdne miesto)
- Ak `negativeIndex == null`: pravý stĺpec nie je nakreslený
- Maximálna výška = `max(všetky positiveIndex + negativeIndex)`, min 100.0
- Pod grafom: malá legenda — zelená bodka "Pozitívne" + červená bodka "Negatívne"
- Existujúce `SimpleBarChart` zostáva v kóde ak je inde používané, inak môže byť odstránené

**Invarianty**:
- Prázdny `dualSeries`: Canvas sa nevykreslí, zobrazí sa prázdny stav
- `dualSeries.size >= 1`: chart sa renderuje

---

## RadarChart — dva polygóny

**Rozšírenie existujúceho `RadarChart` composable** (z feature 003):

**Nový kontrakt** (nad rámec feature 003):
- Pozitívne osi (`sleep`, `physical_activity`, `nutrition_protein`, `mindfulness`): ich dátové body sú spojené uzavretým `positivePath`
- Negatívne osi (`stress_work`, `stress_personal`, `alcohol`, `caffeine`): ich dátové body sú spojené uzavretým `negativePath`

**Vizuálny kontrakt polygónov**:
| Polygon | Fill | Fill Alpha | Stroke | Stroke Width |
|---------|------|-----------|--------|-------------|
| Pozitívny | `#81C784` | 25% | `#4CAF50` | 2.5f |
| Negatívny | `#E57373` | 25% | `#F44336` | 2.5f |

- Existujúci single `dataPath` je nahradený dvoma polygónmi
- Poradie kreslenia: grid → osi → positiveFill → negativeFill → positiveStroke → negativeStroke → dots → labels
- Dots zostávajú farebné podľa klasifikácie (z feature 003)

**Vstupný kontrakt** pre `RadarChart`:
```kotlin
// Zostáva z feature 003:
elements: List<RadarElementData>
    RadarElementData(key, label, value: Double, classification: ElementClassification)
// Komposable odvodí pozitívne/negatívne osi z classification field — bez nových parametrov
```

**Invarianty**:
- Polygón sa kreslí aj keď má menej ako 4 body (ak niektoré hodnoty chýbajú → 0.0)
- Ak sú všetky hodnoty skupiny 0.0: polygon degeneruje do bodu v strede — vizuálne OK
