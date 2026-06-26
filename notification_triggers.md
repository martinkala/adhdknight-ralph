# Notifikačné triggery (MVP)

## 1) Denné pripomenutie trackera
- Trigger: ak do 20:00 (lokálny čas) nie je vyplnený deň.
- Frekvencia: max 1× denne.

## 2) Zanedbaná oblasť (weekly)
- Trigger: ak element i má hodnotu 0 posledné 3 dni po sebe.
- Frekvencia: max 2× týždenne.

## 3) Stres vs recovery
- Trigger: ak stres (práca alebo osobný) >= 4 tri dni po sebe a mindfulness = 0.
- Frekvencia: max 1× za 3 dni.

## Bezpečnostné limity
- Nikdy neposielať viac než 1 notifikáciu za deň.
- Ak používateľ vypne notifikácie, žiadne background eventy sa nesmú spúšťať.
