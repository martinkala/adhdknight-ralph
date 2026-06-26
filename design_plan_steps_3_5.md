# Krok 3–5: Default váhy, adaptácia váh, dátový model (nadväzuje na design_plan_steps_1_2.md)

## Krok 3: Default váhy pre MVP elementy
Pozn.: Váhy sú štartovacie a budú sa adaptovať po ~15 dňoch. Suma váh = 100.
Vypočítané proporčne z dopadových skóre 1–10 (viď `element_impact_scores.md`).

- celkový pocit: 13
- spánok: 15
- fyzická aktivita: 11
- stres v práci: 13
- stres v osobnom živote: 13
- strava proteíny: 8
- čaj/káva: 6
- alkohol: 10
- mindfulness/relax: 11

## Krok 4: Algoritmus adaptácie váh (konkrétne pravidlá)

### Vstupy
- Denné hodnoty elementov normalizované do 0–1.
- Denná spokojnosť (celkový pocit) tiež 0–1.

### Výpočet indexu
Index_d = 100 * Σ(w_i * e_i) / Σ(w_i)

### Korelácia a update váh (1× týždenne po 15 dňoch dát)
1) Pre každý element i vypočítaj koreláciu corr_i medzi e_i a „celkový pocit“ za posledných 15 dní.
2) Ak je počet vyplnení < 5, corr_i ignoruj (váha ostáva).
3) Aktualizuj váhu:
   w_i_new = clamp(w_i_old * (1 + alpha * corr_i), w_min, w_max)

Parametre:
- alpha = 0.2
- w_min = 0.5 * w_default
- w_max = 2.0 * w_default

4) Po update normalizuj všetky váhy tak, aby Σw = Σw_default.

### Stabilita
- Aktualizácia 1× týždenne, nie denne.
- Ak sa korelácia hýbe málo (napr. |corr| < 0.1), váhu nemeníme.

### Re‑kalibrácia (periodický ASRS check‑in)
Použitie ASRS‑typ škály ako kalibračného signálu (1× týždenne).

Postup:
1) Prepočítať ASRS skóre na škálu 0–100.
2) Porovnať s priemerom denného indexu za posledných 14 dní.
3) Ak rozdiel > 10 bodov pri dvoch po sebe idúcich meraniach, spustiť re‑kalibráciu:
   - zvýšiť váhy elementov, ktoré korelujú so zhoršením ASRS,
   - znížiť váhy elementov bez vzťahu k ASRS,
   - prípadne dočasne zvýšiť alpha (napr. 0.3) na 1 cyklus.

## Krok 5: Dátový model pre 0/1 + 1–5

### Zásady
- Primárny vstup je binárny (0/1).
- Ak používateľ vyplní 1–5, tento údaj nahradí binárny a použije sa v indexe.
- Preddefinovaný default detailného hodnotenia je 3 (iba ak používateľ zvolí detailný režim).

### Príklad dátovej štruktúry (concept)
EventDay
- date (YYYY-MM-DD)
- elements:
  - value_binary (0/1)
  - value_scale (1–5, nullable)
  - value_effective (0–1) =
    - ak value_scale != null → (value_scale - 1) / 4
    - inak → value_binary
- satisfaction (1–5, vždy vyplnené)

### Poznámka k UI
- Používateľ najprv klikne 0/1.
- Voliteľne rozbalí detail a nastaví 1–5.
- Ak detail vyplní, nahradí sa binárna hodnota v indexe.
