# Django Page Routes Contract

Všetky stránky sú server-side rendered (Django templates). Chránené routes vyžadujú JWT v Django session.

## Verejné stránky

| URL | View | Template | Popis |
|-----|------|----------|-------|
| `/` | `redirect → /dashboard` alebo `/login` | — | Redirect podľa auth stavu |
| `/login/` | `LoginView` | `login.html` | Prihlasovací formulár |
| `/register/` | `RegisterView` | `register.html` | Registračný formulár |
| `/info/` | `InfoView` | `info.html` | Statická info stránka |

## Chránené stránky (vyžadujú aktívnu session)

| URL | View | Template | Popis |
|-----|------|----------|-------|
| `/dashboard/` | `DashboardView` | `dashboard.html` | Double-sided bar chart (posledných 30 dní) |
| `/trend/` | `TrendView` | `trend.html` | Denný trend — line chart |
| `/account/` | `AccountView` | `account.html` | Info o účte, odhlásenie |

## Auth flow

| URL | Metóda | Popis |
|-----|--------|-------|
| `/login/` | POST | Form submit → volá FastAPI `/api/v1/auth/login` → uloží JWT do session → redirect `/dashboard/` |
| `/register/` | POST | Form submit → volá FastAPI `/api/v1/auth/register` → auto-login → redirect `/dashboard/` |
| `/logout/` | POST | Vymaže Django session → redirect `/login/` |

## Chybové stavy

| Stav | Správanie |
|------|-----------|
| FastAPI nedostupný | Zobraziť chybovú stránku s textom "Server nie je dostupný" |
| JWT expirovaný | Redirect na `/login/` so správou "Prihlásenie vypršalo" |
| Nesprávne heslo (login) | Zobraziť chybu vo formulári (správa z FastAPI) |
| Neexistujúci účet (login) | Zobraziť chybu vo formulári |
| Email existuje (register) | Zobraziť chybu vo formulári |
| Žiadne dáta na serveri | Zobraziť prázdny stav s vysvetlením |
