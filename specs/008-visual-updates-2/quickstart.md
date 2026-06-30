# Quickstart Validation Guide: Visual Updates 2

**Feature**: 008-visual-updates-2
**Date**: 2026-06-29

---

## Predpoklady

- Android Studio s pripojeným emulatorom alebo fyzickým zariadením (API 26+)
- App kompiluje bez chýb: `./gradlew assembleDebug`
- Existujúci zaznamenaný deň v databáze (alebo vyplniť cez TrackerScreen)

---

## Scenario 1: Double Bar Chart — HomeScreen (FR-001, FR-002)

**Cieľ**: Overenie nahradenia radar grafu dvojitým stĺpcovým grafom

**Kroky**:
1. Spusti app → otvori HomeScreen
2. Ak nie sú dáta: vyplň TrackerScreen a ulož
3. Na HomeScreen skontroluj sekciu grafov

**Očakávaný výsledok**:
- ✅ Žiadna radar sieť/pavúčí tvar — zobrazí sa horizontálny alebo vertikálny bar chart
- ✅ Stĺpce záporných entít (kofeín, alkohol, stres) sú červené
- ✅ Stĺpce pozitívnych entít (spánok, aktivita, mindfulness) sú zelené
- ✅ Každý stĺpec má label vo formáte `"[kategória] / [entita]"` (napr. `"Potraviny / Kofeín"`)

---

## Scenario 2: Double Bar Chart — VectorScreen / Denný detail (FR-001, FR-002, FR-009)

**Cieľ**: Overenie grafu a premenovaného titulku na detaile dňa

**Kroky**:
1. Otvor TrendScreen → klikni na ľubovoľný deň s dátami

**Očakávaný výsledok**:
- ✅ Titulok zobrazuje `"Denný detail YYYY-MM-DD"` (nie `"Radar ..."`)`
- ✅ Rovnaký double bar chart ako na HomeScreen

---

## Scenario 3: TrendScreen zoradenie a farby (FR-003, FR-004)

**Cieľ**: Overenie zostupného zoradenia a farebných pozadí riadkov

**Kroky**:
1. Zaznamenej dni pre aspoň 3 rôzne dátumy s rôznymi hodnotami
2. Otvor TrendScreen → pozri zoznam dní pod grafom

**Očakávaný výsledok**:
- ✅ Najnovší deň je prvý v zozname (napr. "2026-06-29: 72" pred "2026-06-28: 45")
- ✅ Deň s indexom ≥ 50 má bledozelené pozadie riadku
- ✅ Deň s indexom < 50 má bledočervené pozadie riadku

---

## Scenario 4: TrackerScreen — druhé tlačidlo Uložiť (FR-005)

**Cieľ**: Overenie dostupnosti uloženia bez scrollovania nahor

**Kroky**:
1. Otvor TrackerScreen → vyplň niektoré hodnoty
2. Scrolluj na spodok stránky
3. Stlač druhé tlačidlo "Uložiť deň"

**Očakávaný výsledok**:
- ✅ Druhé tlačidlo "Uložiť deň" je viditeľné na spodku bez scrollovania nahor
- ✅ Po stlačení: app sa vráti na HomeScreen (rovnaké správanie ako horné tlačidlo)
- ✅ Horné tlačidlo zostáva na svojom pôvodnom mieste

---

## Scenario 5: TrackerScreen — farebné pozadia sekcií (FR-006)

**Cieľ**: Overenie pastelových pozadí podľa impact

**Kroky**:
1. Otvor TrackerScreen
2. Vizuálne skontroluj farby kariet sekcie

**Očakávaný výsledok**:
- ✅ Sekcie pre `sleep`, `physical_activity`, `mindfulness` (a ostatné impact=+1) majú bledozelené pozadie
- ✅ Sekcie pre `caffeine`, `alcohol`, `stress_personal`, `stress_work` (impact=-1) majú bledočervené pozadie
- ✅ `overall_feeling` sekcia (ak je impact=+1) má bledozelené pozadie

---

## Scenario 6: HomeScreen kompaktné metriky + premenovanie (FR-007, FR-008)

**Cieľ**: Overenie layoutu a textu

**Kroky**:
1. Otvor HomeScreen

**Očakávaný výsledok**:
- ✅ "Denný ADHD index", "Spokojnosť" a "Vyplnené" sú v jednom riadku (vedľa seba)
- ✅ Text "Splnené" sa nikde nezobrazuje — iba "Vyplnené"
- ✅ Sekcia "Tip dňa" nie je viditeľná

---

## Regresné overenie (SC-006)

Po každom scenári:
- ✅ Notifikácie sa nespustili neočakávane
- ✅ Dáta v databáze zostali konzistentné
- ✅ Index kalkulácia funguje správne (zobrazuje správne číslo na HomeScreen)
- ✅ `./gradlew test` prebehne bez nových zlyhaní
