# Ralph v izolovanom kontajneri

`ralph-loop.sh` spúšťa Claude Code s `--dangerously-skip-permissions`. Agent teda môže spustiť
akýkoľvek príkaz. Preto beží v kontajneri, ktorý:

- vidí iba toto repo (`/work`) a vlastný home volume `adhdknight-ralph-home`
  (Claude login, Playwright prehliadač). Nevidí tvoj home, `~/.ssh`, `~/.claude` ani iné projekty.
- **nemá prístup ku skutočnému repu** `martinkala/adhdknight`. `origin` je v kontajneri presmerovaný
  (git `insteadOf`) na sandbox repo `martinkala/adhdknight-ralph` a deploy kľúč existuje iba tam.
  Dôvod: GitHub na súkromnom repe osobného (free) účtu nevynucuje ochranu vetiev, takže deploy kľúč
  na skutočnom repe by mohol pushnúť aj do `master`.
- beží ako bežný používateľ `ralph` s tvojím UID (súbory v repe ostanú tvoje).

## Jednorazové nastavenie

1. **Sandbox repo:** na GitHube vytvor **súkromné** prázdne repo `adhdknight-ralph`
   (bez README). Pushni doň aktuálny stav:
   ```bash
   git push git@github.com:martinkala/adhdknight-ralph.git food-diary master
   ```

2. **Deploy kľúč iba pre sandbox:**
   ```bash
   ssh-keygen -t ed25519 -N "" -C "ralph@adhdknight" -f ~/.ssh/adhdknight_ralph_deploy
   cat ~/.ssh/adhdknight_ralph_deploy.pub
   ```
   GitHub → repo **`adhdknight-ralph`** → Settings → Deploy keys → Add deploy key → vlož `.pub`,
   zaškrtni **Allow write access**. Do `adhdknight` tento kľúč **nepridávaj**.

3. **Image a login:**
   ```bash
   ./scripts/ralph-docker/ralph-docker.sh build
   ./scripts/ralph-docker/ralph-docker.sh login   # v Claude Code: /login, potom /exit
   ```
   Login sa uloží do volume `adhdknight-ralph-home` a nemieša sa s tvojím hostiteľským `~/.claude`.

## Spustenie

```bash
./scripts/ralph-docker/ralph-docker.sh run 40
```

Logy sú v `logs/` v repe. Commity sú lokálne v tvojom repe (bind mount) a zároveň na sandboxe.

## Prevzatie výsledku do skutočného repa

Commity robí kontajner priamo v tvojom lokálnom repe, takže stačí ich skontrolovať a pushnúť:
```bash
git fetch origin                      # obnoví origin/* (kontajner ich prepisuje stavom sandboxu)
git log --oneline origin/food-diary..food-diary
git push origin food-diary
```
 Zastavenie: `Ctrl+C`, prípadne `docker stop` na kontajner `adhdknight-ralph-*`.

## Poznámky

- Kontajner používa vlastné venvy `server/.venv-docker`, `web_app/.venv-docker`, `e2e/.venv-docker`
  (`VENV_NAME=.venv-docker`), oddelené od hostiteľských `.venv`, pretože venv je viazaný na cestu
  k interpreteru. `scripts/test-food.sh` ich vytvorí sám.
- Kontajner má prístup na internet (pip, npm, Claude API, GitHub). Lokálnu sieť a hostiteľské služby
  vidí len cez bežné routovanie Dockeru.
- Úplné vymazanie stavu: `docker volume rm adhdknight-ralph-home`.
