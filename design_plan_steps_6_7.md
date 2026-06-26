# Krok 6–7: Úprava váh + návrh UI obrazoviek (nadväzuje na design_plan_steps_3_5.md)

## Krok 6: Default váhy z dopadových skóre (1–10)
Suma váh = 100. Vypočítané proporčne z `element_impact_scores.md`.

- celkový pocit: 13
- spánok: 15
- fyzická aktivita: 11
- stres v práci: 13
- stres v osobnom živote: 13
- strava proteíny: 8
- čaj/káva: 6
- alkohol: 10
- mindfulness/relax: 11

## Krok 7: Návrh UI obrazoviek (MVP)

### 1) Home / Dnešný prehľad
- Denný ADHD index (0–100)
- Úroveň spokojnosti (1–5)
- Krátky text: „Dnes máš splnené X z Y oblastí“
- CTA: „Vyplniť dnešný tracker“

### 2) Denný tracker
- Zoznam elementov s binárnym 0/1 prepínačom
- Každý element má možnosť „Detail 1–5“ (rozbalenie)
- „Celkový pocit“ vždy ako škála 1–5 (povinné)
- CTA: „Uložiť deň“

### 3) Týždenný trend
- Line chart: denný index
- Týždenný priemer + zmena vs minulý týždeň

### 4) Vektor (Advanced)
- Radar chart so všetkými MVP elementmi
- Zobrazenie „silné“ vs „slabé“ oblasti

### 5) Notifikácie (MVP)
- Nastavenie frekvencie (1× denne, tiché okno)
- Jednoduché pripomienky podľa zanedbaných oblastí

### 6) Nastavenia
- Prepínač „detailné hodnotenie 1–5“
- Export dát (CSV/JSON)
- Sync (ak je zapnutý server)
