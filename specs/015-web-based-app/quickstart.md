# Quickstart: Web Companion App

## Predpoklady

- Python 3.11+
- FastAPI server beží na `127.0.0.1:8095` (z `server/` adresára: `uvicorn app.main:app --port 8095`)
- Aspoň jeden používateľ so záznamami syncovanými na server

## Štruktúra projektu

```
web_app/
├── manage.py
├── requirements.txt
├── adhd_web/
│   ├── settings.py          # SERVER_URL = "http://127.0.0.1:8095"
│   └── urls.py
├── core/
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       ├── base.html        # Bootstrap navbar, CSS CDN
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html   # Double-sided Chart.js bar chart
│       ├── trend.html       # Line chart
│       ├── account.html
│       └── info.html
└── static/
    └── js/
        └── charts.js
```

## Spustenie

```bash
cd web_app
pip install -r requirements.txt
python manage.py migrate        # len Django session/admin tabulky
python manage.py runserver 8000
```

Otvoriť: `http://127.0.0.1:8000`

## Validačné scenáre

### 1. Registrácia a prihlásenie
```
Otvor: http://127.0.0.1:8000/register/
Zadaj: testuser@example.com, heslo (min 8 znakov)
Očakávané: redirect na /dashboard/
```

### 2. Prihlásenie s neexistujúcim účtom
```
Otvor: http://127.0.0.1:8000/login/
Zadaj: neexistuje@example.com, ľubovoľné heslo
Očakávané: chybová správa vo formulári, žiadny redirect
```

### 3. Dashboard — double-sided chart
```
Predpoklad: prihlásený, server má dáta pre používateľa
Otvor: http://127.0.0.1:8000/dashboard/
Očakávané: Chart.js graf s pozitívnymi (zelené) a negatívnymi (červené) stĺpcami
           Načítanie do 3 sekúnd
```

### 4. Prázdny stav
```
Predpoklad: prihlásený, no dáta na serveri
Otvor: http://127.0.0.1:8000/dashboard/
Očakávané: informácia "Zatiaľ žiadne záznamy — zadaj dáta cez mobilnú aplikáciu"
```

### 5. Server offline
```
Zastav FastAPI server
Otvor: http://127.0.0.1:8000/dashboard/
Očakávané: stránka so správou "Server nie je dostupný", nie 500 error
```

### 6. Denný trend
```
Otvor: http://127.0.0.1:8000/trend/
Očakávané: line chart s ADHD indexom za posledných 30 dní, os X = dátumy, os Y = 0-100
```

### 7. Tracker nie je dostupný
```
Otvor: http://127.0.0.1:8000/ (alebo hľadaj Tracker v navigácii)
Očakávané: žiadny odkaz na tracker, žiadna možnosť zadávať záznamy
```

### 8. Odhlásenie
```
Otvor: http://127.0.0.1:8000/account/
Klikni: Odhlásiť sa
Očakávané: redirect na /login/, session vymazaná
```

## Konfigurácia

`web_app/adhd_web/settings.py`:
```python
SERVER_URL = "http://127.0.0.1:8095"  # FastAPI server adresa
SESSION_COOKIE_AGE = 86400             # 24h session
```
