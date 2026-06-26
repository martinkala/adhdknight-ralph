# Post-MVP implementačné kroky (z `goal.md`)

## 1) Predikcia ADHD vektora
- Pridať prediktívny model (napr. jednoduché časové rady) na odhad indexu pre nasledujúce dni.
- Využiť trend za posledných 7–30 dní + volatilitu.

## 2) Agent pre body doubling
- Návrh jednoduchého „focus partnera“:
- režim 25/5 (pomodoro)
- check-in na začiatku a na konci bloku
- logovanie dokončených blokov

## 3) Integrácie (Todoist, kalendár, pomodoro)
- Import dát o dokončených úlohách a fokus blokoch.
- Prepojiť s trendmi ADHD vektora.

## 4) Serverová logika váh (ak sa ukáže potreba)
- Presun adaptácie váh na server (centralizovaný výpočet, synchronizácia viac zariadení).
- API pre výpočet váh + audit zmeny.
