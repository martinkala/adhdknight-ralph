# MVP špecifikácia – ADHD tracker

## Cieľ
Jednoduchá Android aplikácia na denný zber aktivít a výpočet „ADHD vektora“ (behaviorálny index) s personalizáciou váh po ~15 dňoch.

## MVP rozsah
- Denný tracker s nízkym trením.
- Výpočet denného a týždenného indexu (0–100).
- Pokročilý viacrozmerný vektor (radar chart).
- Adaptácia váh lokálne, server len na sync/backup.
- Notifikácie sú súčasť MVP.

## Elementy (MVP)
- celkový pocit
- spánok
- fyzická aktivita
- stres v práci
- stres v osobnom živote
- strava proteíny
- čaj/káva
- alkohol
- mindfulness/relax

## Input a škály
- Primárne binárne 0/1.
- Voliteľné detailné hodnotenie 1–5, ktoré nahrádza binárny údaj.
- Default detailného hodnotenia = 3.
- „Celkový pocit“ vždy 1–5.

## Default váhy (MVP, suma = 100)
- celkový pocit: 13
- spánok: 15
- fyzická aktivita: 11
- stres v práci: 13
- stres v osobnom živote: 13
- strava proteíny: 8
- čaj/káva: 6
- alkohol: 10
- mindfulness/relax: 11

## Výpočet indexu
Index_d = 100 * Σ(w_i * e_i) / Σ(w_i)

## Adaptácia váh
- Po 15 dňoch dát, 1× týždenne.
- Korelácia elementov s „celkovým pocitom“.
- w_i_new = clamp(w_i_old * (1 + alpha * corr_i), w_min, w_max)
- alpha = 0.2, w_min = 0.5 * w_default, w_max = 2.0 * w_default.
- Normalizácia váh na Σw = Σw_default.

## Re‑kalibrácia (ASRS check‑in)
- 1× týždenne.
- Ak rozdiel medzi ASRS (0–100) a priemerom indexu za 14 dní > 10 bodov pri 2 po sebe idúcich meraniach, spustiť re‑kalibráciu.

## UX obrazovky (MVP)
- Home: denný index, úroveň spokojnosti, CTA na tracker.
- Denný tracker: 0/1 prepínače + detail 1–5.
- Týždenný trend: line chart + priemer.
- Vektor (Advanced): radar chart.
- Notifikácie: nastavenie frekvencie + tiché okno.
- Nastavenia: detailný režim, export, sync.

## Notifikácie (MVP)
- Denné pripomenutie, ak deň nie je vyplnený do 20:00.
- Zanedbaná oblasť, ak 3 dni po sebe 0.
- Stres-recovery trigger: stres >= 4 tri dni a mindfulness = 0.
- Max 1 notifikácia denne.

## Post‑MVP (mimo scope)
- Predikcia ADHD vektora.
- Body doubling agent.
- Integrácie (Todoist, kalendár, pomodoro).
- Serverová logika váh.

## Referenčné dokumenty
- design_plan_steps_1_2.md
- design_plan_steps_2_research.md
- design_plan_steps_3_5.md
- design_plan_steps_6_7.md
- design_plan_steps_8.md
- notification_triggers.md
- element_impact_scores.md
- post_mvp_steps.md
