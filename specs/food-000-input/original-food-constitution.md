# Food diary  — Constitution

Toto je Android aplikácia na denné sledovanie stravovania. 
Stravovacie navyky su rozdelene do 6 terminov.
ranajky
desiata, svacina
obed
olovrant , svacina 2
vecera
post vecera

strava sa zadava kazdy den vo formate YYYY-MM-DD
zadavanie stravy je fulltextove, cize zadavanie textu. 
pri zadavani sa pouzva fultextovy search a pokial uz string bol zadany tak sa ponukne na vyber
Zadavat je mozne ktorykolvek termin.

K strave sa pridaju data ako
- vaha, v zatvorke cas merania,
- tlak, v zatvorke cas merania , moze ich byt viac oddelenych ciarkou
- subjektivne problemy ( nazov je definovatelny uzivatelom , moze ich byt viac oddelenych ciarkou, takisto hodnot bude viac oddelenych , hodnoty problemov su 1-10 , kde 1 je vsetko v poriaku, 10 totalny problem 
- symptomy - v pripade zdravotnych problemon , fultextove pole z popisom problemov
- medicaments - lieky , ktore ppobi ten den podane 
- supplements - vyzivove doplnky
- sport - fultextove pole s vyhladavanim v textoch , intenzita 1-5 ku kazdemu zaznmu
- poznamka 

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

**Dôvod:** food  tracker musí byť spoľahlivý offline nástroj s predvídateľnou architekturou, ktorú môže AI agent rozšíriť bez regresu iných vrstiev.

---


### IV. UX a používateľská skúsenosť

Aplikácia slúži ľuďom pre rychle zadavanie  — nízke trenie, predvídateľné vzory, žiadny kognitívny overhead.

---

### VI. Testovanie — záväzné kategórie

Každá zmena doménovej logiky MUSÍ byť krytá testami.

- **Integračné testy (Room in-memory DB):**
  - CRUD pre všetky entity

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

## Správa a governance

Tento dokument má prednosť pred ad-hoc rozhodnutiami. Platí pre všetky spezifikácie, plány a tasky generované v spec-kit workflow.

- **Princípy I–VII sú záväzné gates.** Pri konflikte medzi spec/planom a constitution sa upravuje spec/plan — nie constitution.
- **Zmeny constitution vyžadujú:** explicitné zdôvodnenie, vplyv na existujúce specs/plans, a verziu podľa SemVer.
- **Každý task, ktorý mení doménovú logiku** (index, váhy, ASRS), MUSÍ obsahovať odkaz na príslušný princíp tejto constitution.
- **Jazyk kódu:** Kotlin identifikátory a komentáre v angličtine. UI texty, dokumentácia a specs môžu byť v slovenčine.

## Data sample
v subore data_sample.txt je export z existujuceho food dennika zpracovaneho v google spreadsheet.
Kazdy den zacina datumom a v spreadsheete ma 2 riadky, prvy je primarny druhy doplnkovy.
POuzi data na validaciu aplikacneho navrhu a data mozu byt zmerfovane pre aplikaciu, ako keby den mal 1 riadok 

**Verzia:** 1.0.0 | **Dátum:** 2026-07-25
