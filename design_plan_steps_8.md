# Krok 8: Pravidlá notifikácií (MVP)

## Ciele
- Jemné pripomenutie, nie spam.
- Primárny cieľ: vyplnenie denného trackera a vyrovnávanie zanedbaných oblastí.

## Typy notifikácií
1) Denné pripomenutie trackera
- Trigger: ak do 20:00 (lokálny čas) nie je vyplnený deň.
- Text: „Nezabudni na dnešný tracker (1–2 min).“
- Frekvencia: max 1× denne.

2) Zanedbaná oblasť (weekly)
- Trigger: ak element i má hodnotu 0 posledné 3 dni po sebe.
- Text: „Zdá sa, že [element] bol posledné dni nízko. Skús malý krok.“
- Frekvencia: max 2× týždenne.

3) Zanedbaný stres-recovery balance
- Trigger: ak stres (práca alebo osobný) >= 4 tri dni po sebe a mindfulness = 0.
- Text: „Stres je vyššie a relax nízky. Skús dnes 5–10 min mindfulness.“
- Frekvencia: max 1× za 3 dni.

## Nastavenia v appke
- Čas denného pripomenutia (default 20:00).
- Tiché okno (default 22:00–08:00).
- Prepínač: „len denné pripomenutie“ vs „denné + zanedbané oblasti“.

## Bezpečnostné pravidlá
- Nikdy neposielať viac než 1 notifikáciu za deň.
- Ak používateľ vypne notifikácie, žiadne background eventy sa nesmú spúšťať.

## Poznámky k implementácii
- Logika sa počíta lokálne.
- Pred odoslaním notifikácie vždy overiť, či už nebola poslaná v daný deň.
