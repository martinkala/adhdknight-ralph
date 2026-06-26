<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Modified principles: None (content preserved; formatting/structure only)
- Added sections: Rozsah projektu (explicit section heading), Vyvojove pravidla
- Removed sections: None
- Templates requiring updates:
  - OK /home/martin/projects/ai/agent_try/.specify/templates/plan-template.md
  - OK /home/martin/projects/ai/agent_try/.specify/templates/spec-template.md
  - OK /home/martin/projects/ai/agent_try/.specify/templates/tasks-template.md
  - OK /home/martin/projects/ai/agent_try/.specify/templates/commands/*.md (checked; no changes needed)
- Follow-up TODOs: None
-->
# ADHD Tracker Constitution

Toto je Android aplikacia na denne sledovanie behavioralnych elementov
ovplyvnujucich ADHD stav. Aplikacia vypocitava "ADHD vektor" (behavioralny
index 0-100) z denne zadanych aktivit, prisposobuje vahy jednotlivych
elementov na zaklade korelacie s celkovym pocitom a upozornuje pouzivatela na
zanedbane oblasti - bez farmakologickej podpory.

Tieto principy su zavazne pre vsetky zmeny, specifikacie, plany aj tasky.

---

## Core Principles

### I. Architektura a kodova disciplina

Aplikacia striktne dodrziava MVVM + Repository pattern. Kazda zmena MUST
zachovavat tuto vrstvenu architekturu.

- **Vrstvova separacia je povinna.** UI (Composables) nesmie priamo volat Room
  DAO ani vykonavat vypoctovu logiku. Kazda vrstva komunikuje vyhradne cez svoju
  susednu vrstvu: `Composable -> ViewModel -> Repository -> DAO`.
- **ViewModel neobsahuje databazovu logiku.** ViewModel drzi
  `StateFlow`/`LiveData` a vola metody Repository. Transformacie a vypocty patria
  do domenovej vrstvy (use-case triedy alebo metody Repository).
- **Repository je jediny pristupovy bod k datam.** Vsetky CRUD operacie a
  vypocty indexov su za Repository interfejsom. ViewModel nikdy nevola DAO
  priamo.
- **Offline-first je zakladny predpoklad.** Aplikacia MUST fungovat
  plnohodnotne bez sietoveho pripojenia. Server/sync je len volitelny doplnok
  (stub v MVP).
- **Kotlin + Compose su jedine povolene UI technologie.** Ziadny XML layout,
  ziadny View system v novych obrazovkach.
- **Room pre perzistenciu, WorkManager pre background tasky.** Notifikacna
  logika bezi vyhradne cez WorkManager - nie cez Service ani AlarmManager
  priamo.

**Dovod:** ADHD tracker musi byt spolahlivy offline nastroj s predvidatelnou
architekturou, ktoru moze AI agent rozsirit bez regresu inych vrstiev.

---

### II. Domenova logika indexu - NON-NEGOTIABLE

Vypoctova logika indexu a adaptacia vah su jadrom produktu. Akakolvek zmena
MUST byt kryta unit testami.

#### Vypocet denneho indexu
```
Index_d = 100 x Sum(w_i x e_i) / Sum(w_i)
```
- `e_i` = `value_effective` (0-1): ak `value_scale != null` ->
  `(value_scale - 1) / 4`; inak -> `value_binary`
- `w_i` = aktualna vaha elementu (personalna ak existuje, inak default)
- Vysledok sa uklada do `index_daily`

#### Default vahy (suma = 100)
| Element | Vaha |
|---|---|
| celkovy pocit | 13 |
| spanok | 15 |
| fyzicka aktivita | 11 |
| stres v praci | 13 |
| stres v osobnom zivote | 13 |
| strava proteiny | 8 |
| caj/kava | 6 |
| alkohol | 10 |
| mindfulness/relax | 11 |

#### Adaptacia vah (1x tyzdenne, po 15 dnoch dat)
```
w_i_new = clamp(w_i_old x (1 + 0.2 x corr_i), 0.5xw_default, 2.0xw_default)
```
- `corr_i` = Pearsonova korelacia `e_i` vs `celkovy_pocit` za poslednych 15 dni
- Ak pocet vyplneni < 5, `corr_i` sa ignoruje
- Ak `|corr_i| < 0.1`, vaha sa nemeni
- Po update: normalizovat vsetky vahy tak, aby `Sum(w) = Sum(w_default)`

#### ASRS re-kalibracia (1x tyzdenne)
- ASRS skore normalizovane na 0-100
- Ak `|ASRS - priemer_indexu_14d| > 10` pri 2 po sebe iducich meraniach ->
  re-kalibracia
- Re-kalibracia: zvysit `alpha` na 0.3 na 1 cyklus, vahy elementov
  korelujucich so zhrosenim ASRS sa zvysia

**Dovod:** Algoritmus je vysledkom vyskumu a rozhodnuti timu. Zmena parametrov
(alpha, clamp rozsah, prahova hodnota ASRS) vyzaduje explicitne zdovodnenie v PR.

---

### III. Datovy model - zachovaj schemu

Room entity MUST zodpovedat nasledujucej scheme. Nova entita alebo stlpec
vyzaduje migraciu.

| Entita | Klucove vazby |
|---|---|
| `EventDayEntity` | PK: `id`, unique index na `date` |
| `EventValueEntity` | FK: `eventDayId`, index na `element_key` |
| `SatisfactionEntity` | FK: `eventDayId` |
| `WeightEntity` | `element_key`, `weight_default`, `weight_personal` |
| `IndexDailyEntity` | FK: `eventDayId` |
| `IndexWeeklyEntity` | `week_start`, `week_end` |
| `NotificationLogEntity` | FK: `eventDayId` (nullable), `type`, `sent_at` |
| `AsrsCheckinEntity` | `date`, `score_raw`, `score_normalized` |

- `value_effective` sa MUST ukladat priamo v `EventValueEntity` pre vykon.
- DB verzia zacina od `1`. MVP neobsahuje migracie, ale scaffolding MUST byt
  pripraveny.
- `element_key` pouziva snake_case anglicke nazvy: `sleep`, `physical_activity`,
  `stress_work`, `stress_personal`, `nutrition_protein`, `caffeine`, `alcohol`,
  `mindfulness`, `overall_feeling`.

---

### IV. UX a pouzivatelska skusenost

Aplikacia sluzi ludom s ADHD - nizke trenie, predvidatelne vzory, ziadny
kognitivny overhead.

- **Minimalne kliknutia na denny log.** Hlavna cesta: otvorit app -> vidiet
  zoznam elementov -> prepnut 0/1 -> ulozit. Maximalne 2 obrazovky.
- **Detail 1-5 je volitelny, nie default.** Binarne hodnoty su viditelne ako
  primarny vstup. Skala 1-5 sa zobrazi len po rozbaleni alebo v detailnom
  rezime.
- **"Celkovy pocit" je vzdy povinny a vzdy skala 1-5.** Nesmie byt binarny ani
  volitelny.
- **Home obrazovka zobrazuje okamzitu hodnotu.** Denny index (0-100) a uroven
  spokojnosti su viditelne bez scrolla ihned po otvoreni.
- **Notifikacie su jemne, nie rusive.** Max 1 notifikacia za den. Tiche okno
  22:00-08:00 MUST byt respektovane aj pri oneskorenom workerovi.
- **Chybove stavy su pouzivatelsky priatelske.** Ziadne technicke stacktrace v
  UI. Ak vypocet zlyha, zobrazit prazdny stav s CTA na vyplnenie trackera.
- **Obrazovky MVP (v poradi priority):**
  1. Home / Dnesny prehlad
  2. Denny tracker (0/1 + detail 1-5)
  3. Tyzdenny trend (line chart)
  4. Advanced vektor (radar chart)
  5. Notifikacie nastavenia
  6. Nastavenia (detailny rezim, export, sync toggle)

---

### V. Notifikacie - bezpecnostne pravidla

Notifikacna logika je citliva na UX. Tieto pravidla su zavazne bez vynimky.

| Typ | Trigger | Max frekvencia |
|---|---|---|
| Denne pripomenutie | Den nie je vyplneny do 20:00 | 1x denne |
| Zanedbana oblast | Element = 0 posledne 3 dni | 2x tyzdenne |
| Stres-recovery | Stres >= 4 x 3 dni AND mindfulness = 0 | 1x za 3 dni |

- **Globalny limit: max 1 notifikacia za den.** Pred odoslanim vzdy overit
  `notification_log` za dany den.
- **Ak pouzivatel vypne notifikacie, WorkManager worker NESMIE byt spusteny.**
  Ziadne background eventy.
- **Notifikacie sa nesmu odosielat spatne** - ak worker s oneskorenim zisti, ze
  podmienka platila vcera, notifikaciu nevysle.

---

### VI. Testovanie - zavazne kategorie

Kazda zmena domenovej logiky MUST byt kryta testami.

- **Unit testy (JVM):**
  - Vypocet `value_effective` (binary vs scale)
  - Vypocet denneho indexu `Index_d`
  - Adaptacia vah (vratane clamp a normalizacie)
  - Re-kalibracia ASRS (prahova podmienka)
  - Notifikacna logika (deduplication, tiche okno)

- **Integracne testy (Room in-memory DB):**
  - CRUD pre vsetky entity
  - Vypocet indexu z realnych DB dat

- **Zakazane:** Realne sietove volania v testoch. Testy MUST byt deterministicke
  a offline-spustitelne.

- **Pokrytie domenovych tried je povinne.** Nova trieda vypoctovej logiky bez
  testu blokuje merge.

---

### VII. Technicky stack - povolene zavislosti (MVP)

Akakolvek nova zavislost vyzaduje zdovodnenie, preco existujuca nestaci.

| Kategoria | Kniznica | Verzia |
|---|---|---|
| UI | Jetpack Compose BOM | 2024.06.00 |
| UI | Material 3 | via BOM |
| Navigation | Navigation Compose | 2.7.7 |
| DI | - | bez DI frameworku v MVP |
| DB | Room | 2.6.1 |
| DB codegen | KSP | aktualna |
| Async | Kotlinx Coroutines Android | 1.8.1 |
| Background | WorkManager | 2.9.0 |
| Lifecycle | ViewModel Compose | 2.8.2 |
| Charts | Zatial nespecifikovana | TBD pred implementaciou UI |

- **Min SDK: 26, Target SDK: 34, Kotlin JVM target: 17.**
- **KSP je povinne** pre Room - kapt je zakazane.
- **Dependency Injection framework (Hilt, Koin) je mimo MVP scope.** Manual
  injection cez Composable `remember` alebo Application-level singleton je
  postacujuce.

## Rozsah projektu

### MVP (v scope)
- Denny tracker (9 elementov, binarny + volitelna skala 1-5)
- Vypocet denneho a tyzdenneho indexu
- Adaptacia vah (lokalne, po 15 dnoch)
- ASRS re-kalibracia (weekly)
- Notifikacie (3 typy)
- Radar chart / line chart
- Export dat (CSV/JSON)
- Sync toggle (stub bez implementacie)

### Post-MVP (mimo scope - nerealizovat bez explicitneho rozhodnutia)
- Predikcia ADHD vektora (casove rady)
- Body doubling agent
- Integracie: Todoist, kalendar, pomodoro
- Serverova logika vah (centralizovany vypocet)
- Wearables / pasivne meranie

**Ak feature patri do Post-MVP, nesmie ovplyvnit MVP architekturu** - maximalne
pripravit stub interface s TODO komentarom.

## Vyvojove pravidla

- **Principy I-VII su zavazne gates.** Pri konflikte medzi spec/planom a
  constitution sa upravuje spec/plan - nie constitution.
- **Kazdy task, ktory meni domenovu logiku** (index, vahy, ASRS), MUST obsahovat
  odkaz na prislusny princip tejto constitution.
- **Jazyk kodu:** Kotlin identifikatory a komentare v anglictine. UI texty,
  dokumentacia a specs mozu byt v slovencine.

## Governance

- **Amendment proces MUST obsahovat:** pisomny navrh zmeny, zdovodnenie,
  zhodnotenie dopadu na existujuce specs/plany/tasky, a aktualizaciu verzie
  podla SemVer.
- **Versioning politika:** MAJOR pre nekompatibilne zmeny principov, MINOR pre
  nove alebo materialne rozsirene pravidla, PATCH pre upresnenia bez zmeny
  intentu.
- **Compliance review:** Kazdy spec, plan a tasks dokument MUST obsahovat
  "Constitution Check" a prekazky MUSIA byt explicitne zdovodnene.

**Version**: 1.1.0 | **Ratified**: 2026-06-26 | **Last Amended**: 2026-06-26
