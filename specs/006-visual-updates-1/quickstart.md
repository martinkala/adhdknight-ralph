# Quickstart & Validation Guide: Visual UI Updates

## Prerekvizity

- Android Studio alebo `./gradlew assembleDebug` v `android_app/`
- Fyzické zariadenie alebo emulátor API 26+
- Aspoň 1 vyplnený denný záznam v DB (pre zobrazenie dát na Home a Trend)

## Spustenie

```bash
cd android_app
./gradlew installDebug
```

Alebo: Run z Android Studio (Shift+F10).

---

## Validačné scenáre

### S1 – Home: Dátum za "Dnešný prehľad"

1. Otvorte aplikáciu → Home tab
2. **Očakávané**: Text hlavičky obsahuje aktuálny dátum, napr. `"Dnešný prehľad – 28. 6. 2026"`
3. **Fail**: Chýba dátum, alebo dátum je nesprávny

---

### S2 – Home: Výmena poradia a veľkosti sekcií

1. Otvorte Home tab (s existujúcimi dátami)
2. **Očakávané**: Sekcia Pozitívne/Negatívne je **prvá** a má **väčší font** (`displaySmall`)
3. **Očakávané**: ADHD index je **pod ňou** s **menším fontom** (`titleMedium`)
4. **Fail**: Poradie je prehodené, alebo fonty ostali nezmenené

---

### S3 – Home: Skratkové tlačidlo → Tracker

1. Otvorte Home tab
2. Stlačte tlačidlo `"Upraviť denný záznam"` (napravo od Pozitívne/Negatívne)
3. **Očakávané**: Aplikácia otvorí Denný tracker priamo (jedno kliknutie)
4. **Fail**: Tlačidlo chýba, alebo naviguje inam

---

### S4 – Trend: Popisky dní v stĺpcoch

1. Otvorte Trend tab
2. **Očakávané**: Pod každým stĺpcom je viditeľný popis dňa (napr. `"Po 23.6"`)
3. **Fail**: Stĺpce sú bez popiskov

---

### S5 – Trend: Kliknutie na deň → Vector pre daný deň

1. Otvorte Trend tab (s dátami za aspoň 2 dni)
2. Kliknite na jeden stĺpec
3. **Očakávané**: Otvorí sa Vector/Radar stránka s nadpisom obsahujúcim dátum kliknutého dňa
4. Stlačte Back
5. **Očakávané**: Návrat na Trend stránku
6. **Fail**: Klik nereaguje, alebo zobrazí dáta nesprávneho dňa

---

### S6 – Menu: Vektor nie je v menu

1. Pozrite sa na spodný NavigationBar
2. **Očakávané**: Položky sú `Home`, `Tracker`, `Trend`, `Settings` – **bez Vektora**
3. **Fail**: Položka `Vector` je stále viditeľná v menu

---

### S7 – Menu: Vektor stránka je stále dostupná cez Trend

1. Otvorte Trend tab
2. Kliknite na ľubovoľný deň (S5)
3. **Očakávané**: Vektor stránka sa zobrazí aj napriek tomu, že nie je v menu
4. **Fail**: Navigácia na vektor stránku nefunguje

---

### S8 – Denný tracker: Tlačidlo Uložiť vedľa nadpisu

1. Otvorte Tracker tab
2. **Očakávané**: Tlačidlo `"Uložiť deň"` je viditeľné **napravo od nadpisu** bez scrollovania
3. Scrollujte na spodok stránky
4. **Očakávané**: Tlačidlo na spodku **neexistuje** (nie je duplikované)
5. Stlačte tlačidlo
6. **Očakávané**: Záznam sa uloží rovnako ako predtým, naviguje na Home
7. **Fail**: Tlačidlo chýba v hlavičke, je duplikované, alebo uloženie nefunguje

---

## Edge case scenáre

### E1 – Home bez dát (prvé spustenie)

1. Spustite aplikáciu bez žiadnych záznamov
2. **Očakávané**: Home zobrazuje dátum správne, prázdny stav pre index a pozitívne/negatívne

### E2 – Trend: klik na deň bez záznamu

1. Kliknite na stĺpec, pre ktorý neexistuje záznam (placeholder stĺpec)
2. **Očakávané**: Vector stránka sa otvorí s prázdnym stavom (nie crash)

### E3 – Navigačný backstack z Vector stránky

1. Trend → klik na deň → Vector stránka
2. Stlačte systémové Back
3. **Očakávané**: Návrat na Trend, nie na Home
