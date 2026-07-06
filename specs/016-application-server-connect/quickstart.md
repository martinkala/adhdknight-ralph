# Quickstart: App–Server Connectivity F1 — Validačný sprievodca

**Feature**: F1 — Server Settings + Account Screen
**Prerekvizity**: FastAPI server beží na lokálnej sieti (napr. `http://192.168.1.10:8095`)

---

## Setup

### Server
```bash
cd /home/martin/projects/adhdmad/server
make dev      # štartuje FastAPI na porte 8095
```

### Android app
- Build a spusti na emulátore alebo fyzickom zariadení
- MinSDK 26, targetSDK 34

---

## Scenár 1: Nastavenie server URL

**Cieľ**: Overiť, že Settings obsahuje pole pre server URL a ukladá ho.

```
1. Otvor Settings
2. Nájdi sekciu "Server" s textovým poľom pre URL
3. Zadaj: http://10.0.2.2:8095   (emulátor → localhost)
        alebo http://192.168.x.x:8095  (fyzické zariadenie)
4. Ulož / potvrď
5. Znova otvor Settings → URL musí byť zachovaná
6. Zatvor a znova otvor app → URL stále zachovaná
```

**Očakávaný výsledok**: URL je persistentná cez reštart app.

---

## Scenár 2: Account obrazovka — neprihlásený stav

**Cieľ**: Overiť, že Account je dostupný z navigácie a zobrazí login formulár.

```
1. Naviguj na "Účet" (nový nav item)
2. Overiť: zobrazí sa formulár s poľami Email + Heslo
3. Overiť: tracker a ostatné obrazovky sú naďalej dostupné (offline-first)
```

**Očakávaný výsledok**: Formulár zobrazený, zvyšok app funkčný.

---

## Scenár 3: Registrácia nového účtu

**Prerekvizita**: Server URL nastavená, server beží.

```
1. Na Account obrazovke klikni "Registrovať sa"
2. Zadaj email: test@example.com, heslo: secret123
3. Potvrd
4. Očakávaj: automatické prihlásenie, zobrazí sa stav "Prihlásený"
5. Overiť: email a "Počet dní: 0" sú zobrazené
```

**Kontrola na serveri**:
```bash
curl -X POST http://localhost:8095/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123"}'
# → {"email":"test@example.com","created_at":"..."}
```

---

## Scenár 4: Prihlásenie existujúceho účtu

```
1. Na Account obrazovke zadaj existujúce prihlasovacie údaje
2. Klikni "Prihlásiť sa"
3. Očakávaj: stav "Prihlásený" s emailom, počtom dní, dátumom registrácie
```

---

## Scenár 5: Chybové stavy pri prihlásení

```
Test A — nesprávne heslo:
  Zadaj správny email, zlé heslo → správa "Nesprávne prihlasovacie údaje"

Test B — server nedostupný:
  Zastav server (Ctrl+C), pokús sa prihlásiť → správa "Server nie je dostupný"
  App zostáva plne funkčná offline

Test C — prázdna URL:
  V Settings vymaž URL, pokús sa prihlásiť → správa "Zadajte URL servera v nastaveniach"
```

---

## Scenár 6: Odhlásenie

```
1. Prihlásený stav → klikni "Odhlásiť sa"
2. Overiť: stav "Neprihlásený", login formulár zobrazený
3. Znova otvor Account → stale "Neprihlásený" (token vymazaný)
4. Overiť: tracker, home a ostatné obrazovky funkčné
```

---

## Scenár 7: Offline-first zachovanie (Constitution I)

```
1. Zastav server
2. Otvor app → home a tracker fungujú normálne
3. Naviguj na Account → zobrazí login formulár (nie crash)
4. Pokús sa prihlásiť → "Server nie je dostupný"
5. Zadaj denné záznamy v trackeri → ukladajú sa lokálne
```

**Očakávaný výsledok**: Žiadna funkcionalita trackera nie je závislá na serveri.

---

## Overenie dát cez API (po prihlásení)

```bash
# Zober token z logu alebo Scenár 3/4
TOKEN="eyJ..."

# Overiť user info
curl -H "Authorization: Bearer $TOKEN" http://localhost:8095/api/v1/user/me
# → {"email":"test@example.com","created_at":"...","total_days":0}
```

---

## Checklist úspešnej validácie

- [ ] Server URL sa ukladá a načíta po reštarte app
- [ ] Account nav item je viditeľný a navigovateľný
- [ ] Login formulár zobrazený pre neprihlásených
- [ ] Registrácia vytvára účet a auto-prihlási
- [ ] Prihlásenie zobrazí email + total_days
- [ ] Nesprávne heslo → správa (nie crash)
- [ ] Server nedostupný → správa (nie crash)
- [ ] Odhlásenie vyčistí session, login formulár sa zobrazí
- [ ] Tracker funguje offline bez ohľadu na stav prihlásenia
