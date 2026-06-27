# Feature Specification: Radar Chart Visual Distinction (Positive/Negative Elements)

**Feature Branch**: `003-radar-visual-distinction`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "do radar grafu v android apke pridaj graficke rozlisenie positive (svetle zelena ciara), a negative (svetlo cervena ciara)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vizuálne rozlíšenie typov elementov v radar grafe (Priority: P1)

Používateľ otvorí obrazovku Advanced vektor (radar chart) a okamžite vidí, ktoré elementy sú pre jeho ADHD stav pozitívne (svetlozelená čiara) a ktoré negatívne (svetločervená čiara). Bez toho, aby musel čítať popisky alebo sa odkazovať na legendu, rozozná na prvý pohľad, v ktorých oblastiach sa mu darí a kde má slabiny.

**Why this priority**: Radar chart je kľúčová vizualizácia ADHD vektora. Farebné rozlíšenie typov elementov priamo znižuje kognitívnu záťaž používateľa s ADHD — hlavný cieľ produktu.

**Independent Test**: Otvoriť obrazovku Advanced vektor po vyplnení denného trackera a overiť, že graf zobrazuje pozitívne elementy svetlozelenou hrubšou čiarou a negatívne elementy svetločervenou tenšou čiarou bez akejkoľvek ďalšej interakcie.

**Acceptance Scenarios**:

1. **Given** používateľ má vyplnený denný tracker so všetkými elementmi, **When** otvorí obrazovku Advanced vektor, **Then** radar chart zobrazuje pozitívne elementy zvýraznené svetlozelenou čiarou a negatívne elementy svetločervenou čiarou.
2. **Given** radar chart je zobrazený, **When** používateľ sleduje vizualizáciu, **Then** legenda alebo iný vizuálny indikátor vysvetľuje, čo svetlozelená a svetločervená čiara znamenajú.
3. **Given** elementy s neutrálnym alebo nedefinovaným vplyvom, **When** sú zobrazené v grafe, **Then** graf ich zobrazuje výrazne odlíšene od pozitívnych aj negatívnych (napríklad sivou alebo predvolenou farbou).

---

### User Story 2 - Dynamická aktualizácia farebného rozlíšenia (Priority: P2)

Ako sa menia adaptované váhy a korelácie elementov s celkovým pocitom v priebehu času, farebné priradenie (pozitívny/negatívny) sa automaticky aktualizuje bez toho, aby musel používateľ čokoľvek nastavovať.

**Why this priority**: Algoritmus adaptácie váh mení relevanciu elementov týždenne. Statické hardcoded rozdelenie by bolo zavádzajúce; dynamické rozdelenie zachováva konzistentnosť s jadrom produktu.

**Independent Test**: Po simulácii zmeny korelačného skóre elementu (napr. z pozitívneho na negatívny) overiť, že pri nasledujúcom otvorení radar chartu sa farba čiary daného elementu zmenila zodpovedajúco.

**Acceptance Scenarios**:

1. **Given** element bol predtým klasifikovaný ako pozitívny (kladná korelácia s celkovým pocitom), **When** sa jeho korelácia po adaptácii zmení na zápornou, **Then** radar chart zobrazuje daný element svetločervenou namiesto svetlozelenú čiarou.
2. **Given** menej ako 5 vyplnení (nedostatok dát na určenie korelácie), **When** je radar chart zobrazený, **Then** všetky elementy sú zobrazené neutrálnou farbou (bez zelená/červenej klasifikácie).

---

### Edge Cases

- Čo ak má element koreláciu blízku nule (|corr| < 0.1 podľa constitution)? Graf ho zobrazí neutrálnou farbou — nie je ani pozitívny ani negatívny.
- Čo ak sú dáta pre daný deň neúplné (niektoré elementy nie sú vyplnené)? Nevyplnené elementy sa zobrazia v grafe so špeciálnym vizuálnym označením (napr. prerušovaná čiara) bez farebnej klasifikácie.
- Čo ak je radar chart zobrazený v tmavom režime? Farby svetlozelená a svetločervená musia byť dostatočne kontrastné voči tmavému pozadiu.
- Čo ak má používateľ poruchu farebného videnia? Radar chart kombinuje farbu aj hrúbku čiary — pozitívne elementy majú hrubšiu čiaru, negatívne tenšiu. Tým je rozlíšenie čitateľné aj bez závislosti na farbe.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Radar chart MUST zobrazovať elementy s kladnou koreláciou s celkovým pocitom svetlozelenú čiarou.
- **FR-002**: Radar chart MUST zobrazovať elementy so zápornou koreláciou s celkovým pocitom svetločervenou čiarou.
- **FR-003**: Radar chart MUST zobrazovať elementy s neutrálnou koreláciou (|corr| < 0.1) alebo bez dostatočných dát predvolenou/neutrálnou farbou (nie zelená ani červená).
- **FR-004**: Farebné rozlíšenie MUST byť konzistentné s adaptovanými váhami a koreláciami vypočítanými podľa algoritmu (viz Constitution § II).
- **FR-005**: Legenda alebo vizuálny popis MUST byť zobrazený v blízkosti grafu a vysvetľovať farebné kódovanie (pozitívny/negatívny vplyv na ADHD index).
- **FR-006**: Farebná klasifikácia MUST byť automaticky aktualizovaná pri každom zobrazení obrazovky bez manuálneho zásahu používateľa.
- **FR-007**: Zmena farebnej klasifikácie sa MUST prejaviť najneskôr pri nasledujúcom otvorení obrazovky po vykonaní adaptácie váh.
- **FR-008**: Vizualizácia MUST zostať funkčná (zobrazovať hodnoty elementov) aj v prípade, keď farebná klasifikácia nie je dostupná (menej ako 5 záznamov).
- **FR-009**: Radar chart MUST odlišovať pozitívne a negatívne elementy aj hrúbkou čiary — pozitívne elementy MUST mať hrubšiu čiaru, negatívne tenšiu. Toto rozlíšenie dopĺňa farebné kódovanie a zaručuje čitateľnosť pre používateľov s poruchou farebného videnia.

### Key Entities

- **Element korelačné skóre**: Pearsonova korelácia medzi hodnotou elementu a celkovým pocitom za posledných 15 dní; určuje farebné zaradenie elementu.
- **Farebná klasifikácia elementu**: Odvodenou hodnotou z korelačného skóre — pozitívny (> +0.1), negatívny (< -0.1), neutrálny (|corr| ≤ 0.1 alebo nedostatok dát).
- **Radar chart vizualizácia**: Existujúca obrazovka Advanced vektor, ktorá bude rozšírená o farebné rozlíšenie čiar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Používateľ dokáže na prvý pohľad (bez čítania popiskov) správne identifikovať aspoň 80 % pozitívnych a negatívnych elementov vo svojom grafe.
- **SC-002**: Farebná klasifikácia sa správne zhoduje s aktuálnymi koreláciami v 100 % prípadov pri zobrazení obrazovky.
- **SC-003**: Zobrazenie radar chartu s farebným rozlíšením netrvá dlhšie ako pri pôvodnej verzii — používateľ nepocíti žiadne spomalenie načítania obrazovky.
- **SC-004**: Legenda je viditeľná bez scrollovania na obrazovkách všetkých podporovaných veľkostí.
- **SC-005**: Pri menej ako 5 dňoch dát sa nezobrazí žiadna farebná klasifikácia a používateľ dostane zrozumiteľnú informáciu o dôvode (napr. "Zbierame dáta pre personalizáciu grafu").

## Assumptions

- Klasifikácia pozitívny/negatívny je odvodzovaná z existujúcich Pearsonových korelácií vypočítaných algoritmom adaptácie váh (Constitution § II) — nie je to statické hardcoded rozdelenie.
- Existujúca implementácia radar chartu je funkčná a táto feature ju rozširuje, nenahrádza.
- Svetlozelená a svetločervená farba sú primerané pre svetlý (light) režim; pre tmavý režim môže byť potrebná úprava odtieňov (toto sa rieši na úrovni implementácie).
- Elementy "celkový pocit" je vždy skála 1-5 a je výstupnou premennou (target), nie vstupnou — preto sa neklasifikuje ako pozitívny/negatívny element v grafe.
- Feature nevyžaduje nové databázové entity ani migrácie — korelácie sú vypočítavané za behu alebo sú uložené v existujúcich štruktúrach.
- Hrúbka čiary je MVP požiadavka (variant B) — kombinovaný vizuálny signál (farba + hrúbka) zaručuje základnú prístupnosť pre používateľov s poruchou farebného videnia bez potreby špeciálneho colorblind módu.

## Constitution Check

- **§ I (Architektúra)**: Farebná logika klasifikácie patrí do domény (Repository/use-case), nie do Composable. UI dostáva iba mapovanie `elementKey -> ChartColor`.
- **§ II (Domenová logika)**: Klasifikácia sa opiera o existujúce korelačné skóre. Žiadna zmena algoritmu indexu ani váh.
- **§ III (Dátový model)**: Nevyžaduje nové entity ani migrácie — korelácia je odvodená hodnota.
- **§ IV (UX)**: Znižuje kognitívnu záťaž priamym vizuálnym signálom — v súlade s ADHD-friendly princípmi.
- **§ VII (Tech stack)**: Chartsová knižnica je TBD; farebné rozlíšenie bude riešené v jej rámci.
