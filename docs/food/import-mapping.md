# Food diary — mapovanie historických dát (pre LLM import)

Tento dokument opisuje, ako previesť historické exporty z Google Sheets (2022–2026) do dátového
modelu Food diary (constitution, časť D). Použije ho **LLM import mimo aplikácie** a ako referenciu
aj spec `food-011` (import v appke).

Vzorky: `specs/food-000-input/2022.csv` … `2026.csv` (oddeľovač TAB) a `data_sample.txt` (CSV).

---

## 1. Všeobecné pravidlá

1. **Mapuj podľa názvu stĺpca, nie podľa pozície.** Poradie sa menilo aj v rámci roka
   (`data_sample.txt` má `medical note, pils`, `2026.csv` má `oills, medical note`).
   Názvy porovnávaj po trim, bez ohľadu na veľkosť písmen.
2. **Deň začína riadkom s dátumom `YYYY-MM-DD` v 1. stĺpci** a pokračuje všetkými ďalšími riadkami
   bez dátumu až po ďalší dátum. Deň má 1 až 4 riadky (nie vždy 2). Bunky toho istého stĺpca zo
   všetkých riadkov dňa sa spoja.
3. **Oddeľovače záznamov v bunke:** čiarka `,` a nový riadok vo vnútri bunky (`"…\n…"`).
   Každý záznam: trim, zlúčené medzery, prázdny záznam zahodiť (`"kolac 2 perniky, "` → 1 záznam).
   - `/` v jedlách (`kacica, kura/ kendlik`) = tiež oddeľovač.
   - `=` (`dzigvaizy = slane cipsy`) = alias: ulož ľavú stranu, pravú daj do poznámky dňa.
   - ` - ` (`Ryba - prazma`, `4x after eight - cokolada`) ponechať ako súčasť textu.
4. **Výnimka: stĺpec stolica/vetry sa podľa čiarky NEDELÍ** (2022 používa `2,4` ako oddeľovač dvojice).
5. **Množstvo** podľa constitution D6 (iba zo začiatku textu): `2 toasty`, `2x jablko`, `1/2 rohlika`,
   `.5 l kofoly`, `0.7 l kompot`. Číslo na konci (`slane oplatky 20`, `20 mandli`) LLM môže previesť na
   množstvo (`20 mandli` → 20 × `mandle`), ale len ak je to jednoznačné; inak ponechať v texte.
6. **Preklepy** (`tioasty`, `sosvocpova`, `jalbkovy`, `parika`, `konzzervy`, `opaltky`) LLM opraví
   proti najčastejšiemu správnemu tvaru v celej histórii používateľa. Každú opravu zapíše do reportu.
7. **Duplicitná položka v jednej bunke liekov** (`emanera , prestarium, emanera`) = 1 záznam s množstvom 2.
8. **Prázdny deň** (iba dátum, žiadne hodnoty) sa **preskočí**.
9. **Ten istý dátum vo viacerých súboroch** (napr. `2026-01-02` v `2025.csv` aj `2026.csv`) → zlúčiť
   podľa pravidiel merge (spec food-011: zoznamy zjednotiť bez duplicít, pri konflikte jednej
   hodnoty uprednostniť novší súbor a zapísať do reportu).
10. Medzery v dátumoch sú normálne.

---

## 2. Formát A — 2022, 2023, 2024

Hlavička: `"", wlk, d, pos, str, "", ranajky, desiata, obed, olovrant, vecera, "", end, problemy (1-10) s/v, w, sweet, kafe, "", <vzorec>, zelemina/ovocie, clanky, videa, "", spokojnost, poznamka, random, ""`

| Stĺpec | Príklad | Cieľ | Pravidlo |
|---|---|---|---|
| 1. stĺpec | `2022-12-31` | dátum dňa | |
| `wlk` | `1` | `sport`: „chôdza“ | `1` → záznam „chôdza“; prázdne/0 → nič |
| `d` | `10.5`, `4.2` | text športu „chôdza“ | km chôdze → `chôdza 10.5 km` (ak `wlk` prázdne a `d` vyplnené, vytvor chôdzu tiež) |
| `pos` | `1`, `0.5` | `sport`: „posilňovanie“ | `>0` → záznam |
| `str` | `1` | `sport`: „strečing“ | `>0` → záznam |
| bez názvu (6.) | `8:30` | — | čas prvého jedla, **neuchováva sa** |
| `ranajky` | | `breakfast` | |
| `desiata` | | `morning_snack` | |
| `obed` | | `lunch` | |
| `olovrant` | | `afternoon_snack` | |
| `vecera` | | `dinner` | |
| bez názvu (12.) | | — | ignorovať |
| `end` | `19:00`, `2200` | — | čas posledného jedla, **neuchováva sa** |
| `problemy (1-10) s/v` | `2,4`, `6,10`, `7:10` | `stool`, `gas` | oddeľovač `,` alebo `/`; `7:10` = Sheets skonvertoval `7/10` na čas → stool 7, gas 10 (zapísať do reportu) |
| `w` | `90.1` | váha | bez času |
| `sweet` | `zakusky, cokoladky` | `unassigned` | `--` = nič. **2022: obsahuje `probiio, lieky`** (posunutý stĺpec) → `medication`/`supplement` podľa slovníka (`probiio` = doplnok, `lieky` = liek, nahlásiť ako podozrivé) |
| `kafe` | `0`, `2`, `3` | `unassigned`: „káva“ s množstvom N | `0`, prázdne, `--` → nič |
| `#REF!` / `#DIV/0!` / `8.983050847` | `6` | — | chybný vzorec, ignorovať |
| `zelemina/ovocie` | `banan`, `redkovka` | `unassigned` | |
| `clanky, videa` | | — | ignorovať |
| `spokojnost` | | — | ignorovať |
| `poznamka` | `zachod poobede` | `note` | |
| `random` | `vinea`, `oplatky, 5 zakuskov` | `unassigned` | |

Poznámka: v 2022 poznámke sa vyskytujú viacnásobné hodnoty stolica/vetry („s/v - rano, poobede 6,5“).
Do `stool/gas` sa nedávajú, ostávajú v poznámke.

## 3. Formát B — 2025

Hlavička: `"", wlk, d, pos, str, Ranajky, desiata, obed, olovrant, vecera, "", "", "", problemy (1-10) s/v, w, fat, sport`

| Stĺpec | Cieľ | Pravidlo |
|---|---|---|
| `wlk`, `d`, `pos`, `str` | `sport` | ako formát A |
| `Ranajky` … `vecera` | food kategórie | ako formát A |
| bez názvu (11.–13.), hodnoty `137/79` | **tlak** | každá hodnota `sys/dia` v ktoromkoľvek riadku dňa = 1 meranie. Validácia D4; `145/02` je mimo rozsahu → nahlásiť, neukladať |
| `problemy (1-10) s/v` | `stool`, `gas` | oddeľovač `/` |
| `w` | váha | |
| `fat` | `note` | ako text `fat: <hodnota>` |
| `sport` | `sport` | |

## 4. Formát C — 2026 (aktuálny)

Hlavička: `"", pohyb, spanok, Ranajky, desiata, obed, olovrant, vecera, post vecera, oills|pils, medical note, presure, dig problemy (1-10) s/v, symptoms 12, symptoms 2, w, sport, note`

| Stĺpec | Cieľ | Pravidlo |
|---|---|---|
| `pohyb` | — | ignorovať |
| `spanok` | `sleep_quality` | 1 zlý / 2 priemer / 3 ok |
| `Ranajky` … `vecera` | food kategórie | |
| `post vecera` | `after_dinner` | |
| `oills` / `pils` / `pills` | `medication` / `supplement` | podľa slovníka: `zn`, `mg`, `omega`, `fe`, `D`, `probiio` = doplnky; `prestarium`, `emanera`, `normix` = lieky. `omega+fe+D` rozdeliť podľa `+` na 3 doplnky |
| `medical note` | `note` | |
| `presure` | tlak | `125/90` |
| `dig problemy (1-10) s/v` | `stool`, `gas` | `6/3` |
| `symptoms 12`, `symptoms 2` | `note` | |
| `w` | váha | |
| `sport` | `sport` | `eBike 60 km`, `bike 30 km` ako text |
| `note` | `note` | |

**Validácia obsahu:** ak sa v stĺpci objaví hodnota, ktorá tam zjavne nepatrí (napr. `pistacie`
v `medical note` v `data_sample.txt` 2026-07-06, 2. riadok), LLM ju presunie do `unassigned`
a zapíše do reportu.

---

## 5. Výstup LLM importu

1. Dáta vo formáte JSON, ktorý prijíma API importu (`food-011`) alebo export JSON (`food-009`):
   jeden objekt na deň s kategóriami, meraniami a hodnotami dňa.
2. **Report** (markdown): opravené preklepy (pôvodný → nový tvar, počet), podozrivé hodnoty,
   preskočené hodnoty, konflikty pri duplicitných dňoch, hodnoty mimo rozsahu.
