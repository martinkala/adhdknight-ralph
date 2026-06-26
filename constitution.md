# ADHD Tracker — Constitution

Toto je Android aplikácia na denné sledovanie behaviorálnych elementov ovplyvňujúcich ADHD stav. Aplikácia vypočítava „ADHD vektor" (behaviorálny index 0–100) z denne zadaných aktivít, prispôsobuje váhy jednotlivých elementov na základe korelácie s celkovým pocitom a upozorňuje používateľa na zanedbané oblasti — bez farmakologickej podpory.

Tieto princípy sú záväzné pre všetky zmeny, specifikácie, plány aj tasky.

---

## Core Principles

### I. Architektúra a kódová disciplína

Aplikácia striktne dodržiava MVVM + Repository pattern. Každá zmena MUSÍ zachovávať túto vrstvovú architektúru.

- **Vrstvová separácia je povinná.** UI (Composables) nesmie priamo volať Room DAO ani vykonávať výpočtovú logiku. Každá vrstva komunikuje výhradne cez svoju susednú vrstvu: `Composable → ViewModel → Repository → DAO`.
- **ViewModel neobsahuje databázovú logiku.** ViewModel drží `StateFlow`/`LiveData` a volá metódy Repository. Transformácie a výpočty patria do doménovej vrstvy (use-case triedy alebo metódy Repository).
- **Repository je jediný prístupový bod k dátam.** Všetky CRUD operácie a výpočty indexov sú za Repository interfejsom. ViewModel nikdy nevolá DAO priamo.
- **Offline-first je základný predpoklad.** Aplikácia MUSÍ fungovať plnohodnotne bez sieťového pripojenia. Server/sync je len voliteľný doplnok (stub v MVP).
- **Kotlin + Compose sú jediné povolené UI technológie.** Žiadny XML layout, žiadny View systém v nových obrazovkách.
- **Room pre perzistenciu, WorkManager pre background tasky.** Notifikačná logika beží výhradne cez WorkManager — nie cez Service ani AlarmManager priamo.

**Dôvod:** ADHD tracker musí byť spoľahlivý offline nástroj s predvídateľnou architekturou, ktorú môže AI agent rozšíriť bez regresu iných vrstiev.

---

### II. Doménová logika indexu — NON-NEGOTIABLE

Výpočtová logika indexu a adaptácia váh sú jadrom produktu. Akákoľvek zmena MUSÍ byť krytá unit testami.

#### Výpočet denného indexu
```
Index_d = 100 × Σ(w_i × e_i) / Σ(w_i)
```
- `e_i` = `value_effective` (0–1): ak `value_scale != null` → `(value_scale - 1) / 4`; inak → `value_binary`
- `w_i` = aktuálna váha elementu (personálna ak existuje, inak default)
- Výsledok sa ukladá do `index_daily`

#### Default váhy (suma = 100)
| Element | Váha |
|---|---|
| celkový pocit | 13 |
| spánok | 15 |
| fyzická aktivita | 11 |
| stres v práci | 13 |
| stres v osobnom živote | 13 |
| strava proteíny | 8 |
| čaj/káva | 6 |
| alkohol | 10 |
| mindfulness/relax | 11 |

#### Adaptácia váh (1× týždenne, po 15 dňoch dát)
```
w_i_new = clamp(w_i_old × (1 + 0.2 × corr_i), 0.5×w_default, 2.0×w_default)
```
- `corr_i` = Pearsonova korelácia `e_i` vs `celkový_pocit` za posledných 15 dní
- Ak počet vyplnení < 5, `corr_i` sa ignoruje
- Ak `|corr_i| < 0.1`, váha sa nemení
- Po update: normalizovať všetky váhy tak, aby `Σw = Σw_default`

#### ASRS re-kalibrácia (1× týždenne)
- ASRS skóre normalizované na 0–100
- Ak `|ASRS - priemer_indexu_14d| > 10` pri 2 po sebe idúcich meraniach → re-kalibrácia
- Re-kalibrácia: zvýšiť `alpha` na 0.3 na 1 cyklus, váhy elementov korelujúcich so zhoršením ASRS sa zvýšia

**Dôvod:** Algoritmus je výsledkom výskumu a rozhodnutí tímu. Zmena parametrov (alpha, clamp rozsah, prahová hodnota ASRS) vyžaduje explicitné zdôvodnenie v PR.

---

### III. Dátový model — zachovaj schému

Room entity MUSIA zodpovedať nasledujúcej schéme. Nová entita alebo stĺpec vyžaduje migráciu.

| Entita | Kľúčové väzby |
|---|---|
| `EventDayEntity` | PK: `id`, unique index na `date` |
| `EventValueEntity` | FK: `eventDayId`, index na `element_key` |
| `SatisfactionEntity` | FK: `eventDayId` |
| `WeightEntity` | `element_key`, `weight_default`, `weight_personal` |
| `IndexDailyEntity` | FK: `eventDayId` |
| `IndexWeeklyEntity` | `week_start`, `week_end` |
| `NotificationLogEntity` | FK: `eventDayId` (nullable), `type`, `sent_at` |
| `AsrsCheckinEntity` | `date`, `score_raw`, `score_normalized` |

- `value_effective` sa MUSÍ ukladať priamo v `EventValueEntity` pre výkon.
- DB verzia začína od `1`. MVP neobsahuje migrácie, ale scaffolding MUSÍ byť pripravený.
- `element_key` používa snake_case anglické názvy: `sleep`, `physical_activity`, `stress_work`, `stress_personal`, `nutrition_protein`, `caffeine`, `alcohol`, `mindfulness`, `overall_feeling`.

---

### IV. UX a používateľská skúsenosť

Aplikácia slúži ľuďom s ADHD — nízke trenie, predvídateľné vzory, žiadny kognitívny overhead.

- **Minimálne kliknutia na denný log.** Hlavná cesta: otvoriť app → vidieť zoznam elementov → prepnúť 0/1 → uložiť. Maximálne 2 obrazovky.
- **Detail 1–5 je voliteľný, nie default.** Binárne hodnoty sú viditeľné ako primárny vstup. Škála 1–5 sa zobrazí len po rozbalení alebo v detailnom režime.
- **„Celkový pocit" je vždy povinný a vždy škála 1–5.** Nesmie byť binárny ani voliteľný.
- **Home obrazovka zobrazuje okamžitú hodnotu.** Denný index (0–100) a úroveň spokojnosti sú viditeľné bez scrolla ihneď po otvorení.
- **Notifikácie sú jemné, nie rušivé.** Max 1 notifikácia za deň. Tiché okno 22:00–08:00 MUSÍ byť rešpektované aj pri oneskorenom workerovi.
- **Chybové stavy sú používateľsky priateľské.** Žiadne technické stacktrace v UI. Ak výpočet zlyhá, zobraziť prázdny stav s CTA na vyplnenie trackera.
- **Obrazovky MVP (v poradí priority):**
  1. Home / Dnešný prehľad
  2. Denný tracker (0/1 + detail 1–5)
  3. Týždenný trend (line chart)
  4. Advanced vektor (radar chart)
  5. Notifikácie nastavenia
  6. Nastavenia (detailný režim, export, sync toggle)

---

### V. Notifikácie — bezpečnostné pravidlá

Notifikačná logika je citlivá na UX. Tieto pravidlá sú záväzné bez výnimky.

| Typ | Trigger | Max frekvencia |
|---|---|---|
| Denné pripomenutie | Deň nie je vyplnený do 20:00 | 1× denne |
| Zanedbaná oblasť | Element = 0 posledné 3 dni | 2× týždenne |
| Stres-recovery | Stres ≥ 4 × 3 dni AND mindfulness = 0 | 1× za 3 dni |

- **Globálny limit: max 1 notifikácia za deň.** Pred odoslaním vždy overiť `notification_log` za daný deň.
- **Ak používateľ vypne notifikácie, WorkManager worker NESMIE byť spustený.** Žiadne background eventy.
- **Notifikácie sa nesmú odosielať spätne** — ak worker s oneskorením zistí, že podmienka platila včera, notifikáciu nevyšle.

---

### VI. Testovanie — záväzné kategórie

Každá zmena doménovej logiky MUSÍ byť krytá testami.

- **Unit testy (JVM):**
  - Výpočet `value_effective` (binary vs scale)
  - Výpočet denného indexu `Index_d`
  - Adaptácia váh (vrátane clamp a normalizácie)
  - Re-kalibrácia ASRS (prahová podmienka)
  - Notifikačná logika (deduplication, tiché okno)

- **Integračné testy (Room in-memory DB):**
  - CRUD pre všetky entity
  - Výpočet indexu z reálnych DB dát

- **Zakázané:** Reálne sieťové volania v testoch. Testy MUSIA byť deterministické a offline-spustiteľné.

- **Pokrytie doménových tried je povinné.** Nová trieda výpočtovej logiky bez testu blokuje merge.

---

### VII. Technický stack — povolené závislosti (MVP)

Akákoľvek nová závislosť vyžaduje zdôvodnenie, prečo existujúca nestačí.

| Kategória | Knižnica | Verzia |
|---|---|---|
| UI | Jetpack Compose BOM | 2024.06.00 |
| UI | Material 3 | via BOM |
| Navigation | Navigation Compose | 2.7.7 |
| DI | — | bez DI frameworku v MVP |
| DB | Room | 2.6.1 |
| DB codegen | KSP | aktuálna |
| Async | Kotlinx Coroutines Android | 1.8.1 |
| Background | WorkManager | 2.9.0 |
| Lifecycle | ViewModel Compose | 2.8.2 |
| Charts | Zatiaľ nešpecifikovaná | TBD pred implementáciou UI |

- **Min SDK: 26, Target SDK: 34, Kotlin JVM target: 17.**
- **KSP je povinné** pre Room — kapt je zakázané.
- **Dependency Injection framework (Hilt, Koin) je mimo MVP scope.** Manual injection cez Composable `remember` alebo Application-level singleton je postačujúce.

---

## Rozsah projektu

### MVP (v scope)
- Denný tracker (9 elementov, binárny + voliteľná škála 1–5)
- Výpočet denného a týždenného indexu
- Adaptácia váh (lokálne, po 15 dňoch)
- ASRS re-kalibrácia (weekly)
- Notifikácie (3 typy)
- Radar chart / line chart
- Export dát (CSV/JSON)
- Sync toggle (stub bez implementácie)

### Post-MVP (mimo scope — nerealizovať bez explicitného rozhodnutia)
- Predikcia ADHD vektora (časové rady)
- Body doubling agent
- Integrácie: Todoist, kalendár, pomodoro
- Serverová logika váh (centralizovaný výpočet)
- Wearables / pasívne meranie

**Ak feature patrí do Post-MVP, nesmie ovplyvniť MVP architektúru** — maximálne pripraviť stub interface s TODO komentárom.

---

## Správa a governance

Tento dokument má prednosť pred ad-hoc rozhodnutiami. Platí pre všetky spezifikácie, plány a tasky generované v spec-kit workflow.

- **Princípy I–VII sú záväzné gates.** Pri konflikte medzi spec/planom a constitution sa upravuje spec/plan — nie constitution.
- **Zmeny constitution vyžadujú:** explicitné zdôvodnenie, vplyv na existujúce specs/plans, a verziu podľa SemVer.
- **Každý task, ktorý mení doménovú logiku** (index, váhy, ASRS), MUSÍ obsahovať odkaz na príslušný princíp tejto constitution.
- **Jazyk kódu:** Kotlin identifikátory a komentáre v angličtine. UI texty, dokumentácia a specs môžu byť v slovenčine.

**Verzia:** 1.0.0 | **Dátum:** 2026-06-26
