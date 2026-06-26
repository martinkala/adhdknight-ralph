# Krok 1: Revízia zadania + research + 3 alternatívy merania

## Revízia zadania (stručne)
- Cieľ je behaviorálny index (ADHD vektor) založený na denných aktivitách.
- Výsledok má pomáhať znižovať dopady ADHD bez farmak a trénovať návyky.
- Android app má byť jednoduchý denný tracker, server môže prepočítavať váhy.

## Research – existujúce prístupy
- Štandardizované symptomatické škály pre ADHD (napr. ASRS) sú používané na sebahodnotenie príznakov a sú validované v klinickej praxi.
- EMA (ecological momentary assessment) štúdie využívajú opakované krátke dotazníky v priebehu dňa na meranie symptómov a nálady v reálnom čase; v ADHD populácii sa používa aj viac dní po sebe.
- Objektívne merania (actigraphy, wearables) sledujú spánok, pohyb a cirkadiánne rytmy; štúdie ukazujú rozdiely medzi ADHD a kontrolami a ich súvis s kognitívnymi/emocionálnymi symptómami.

## 3 alternatívy merania “ADHD vektora”
1) Symptómová škála (ASRS-typ) ako pravidelný index
- Meria priamo ADHD symptómy cez štandardizované otázky.
- Vysoká klinická interpretovateľnosť, jednoduché porovnanie v čase.
- Nevýhoda: subjektívnosť, dlhšie vyplnenie.

2) EMA / denný denník symptómov
- Krátke opakované merania počas dňa alebo večer (denný súhrn).
- Zachytáva variabilitu a kontext, lepšie pre behaviorálny index.
- Nevýhoda: vyššie zaťaženie používateľa.

3) Pasívne objektívne merania (wearables + actigraphy)
- Spánok, aktivita, HR, cirkadiánne rytmy ako proxy pre stav ADHD.
- Znižuje námahu používateľa, dopĺňa subjektívne dáta.
- Nevýhoda: potreba zariadení, slabšia priama interpretácia bez self-report.


# Krok 2: Elementy – kompletný zoznam + MVP subset

## Plný zoznam elementov zo špecifikácie
- celkový pocit
- spánok
- fyzická aktivita
- stres v práci
- stres v osobnom živote
- strava proteíny
- čaj/káva
- alkohol
- autogénny tréning
- mindfulness
- sociálny kontakt
- obdobia “vypnutého mozgu”
- tréning mozgu (spaced repetition, jazyk, krížovky, sudoku)
- výživové doplnky (proteíny, železo, vitamín D)
- pracovné techniky (2 min, pomodoro, body doubling, accountable partner)

## MVP subset (9 prvkov)
- celkový pocit
- spánok
- fyzická aktivita
- stres v práci
- stres v osobnom živote
- strava proteíny
- čaj/káva
- alkohol
- mindfulness/relax

## Rozšírené moduly (po MVP)
- autogénny tréning
- sociálny kontakt
- obdobia “vypnutého mozgu”
- tréning mozgu
- výživové doplnky
- pracovné techniky
 
## Doplnené rozhodnutia z diskusie
- Všetky elementy budú primárne binárne (0/1). Ak používateľ vyplní hodnotenie 1–5, nahradí binárnu hodnotu; preddefinovaný default je 3.
- Stres bude vždy rozdelený na dve samostatné položky (práca/osobný život).
- Výstup bude denný aj týždenný index + pokročilý viacrozmerný vektor (radar chart).
- Adaptácia váh bude lokálna, server len na sync/backup.
- Notifikácie budú súčasťou MVP.
