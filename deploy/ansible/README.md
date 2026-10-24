# Ansible deployment

Idempotent "ship a build" playbook for the two services this project runs in
production: `adhd-api` (FastAPI) and `adhd-web` (Django), plus their nginx
site configs. Re-running it against a server already at the target state
reports no changes (FR-014).

**Out of scope, by design** (FR-013 — no unrelated services): OS packages,
PostgreSQL, and Let's Encrypt/certbot setup are one-time system provisioning,
already handled idempotently by `deploy/scripts/install.sh`. Run that once
per new server, then use this playbook for every subsequent deploy.

**No GitHub credentials on the server**: like `deploy/scripts/push-deploy.sh`,
this playbook pushes the current git checkout's *committed* content to the
server via rsync (`ansible.posix.synchronize`) instead of `git clone`/`pull`
on the server — a compromised server can't reach the source repository.

## Prerequisites

```bash
ansible-galaxy collection install -r requirements.yml
```

Edit `inventory/hosts.ini` with the real server hostname/user.

## Secrets (FR-015/FR-016)

Real secret values (`vault_*` variables — DB passwords, `SECRET_KEY`,
`DJANGO_SECRET_KEY`, the monitoring account's credentials) are **never**
committed to this repository. `group_vars/all/vault.yml.example` documents
the variable names with placeholder values only — copy it *outside* this
repo, fill in real values, and encrypt it:

```bash
cp group_vars/all/vault.yml.example ~/adhknight-secrets/vault.yml   # outside the repo
# edit ~/adhknight-secrets/vault.yml with real values
ansible-vault encrypt ~/adhknight-secrets/vault.yml
```

Rotating a secret: edit the decrypted file (`ansible-vault edit ...`) and
re-run the playbook — the `.env` templates re-render and the affected
service restarts automatically (see the `restart adhd-api`/`restart adhd-web`
handlers in `roles/app`).

## Running

```bash
ansible-playbook site.yml \
  -e @~/adhknight-secrets/vault.yml \
  --ask-vault-pass
```

## Verifying idempotency (T033)

Run the command above twice in a row against the same target. The second
run's recap should show `changed=0` for every task except the ones that are
inherently "always report changed" no-ops on purpose (the Alembic/Django
migration and `collectstatic` commands — neither framework gives Ansible a
clean idempotency signal, so they're marked `changed_when: true` and simply
re-run harmlessly at the current migration head / same static files).

## Secret-scan safeguard (FR-016a)

See the repository root `.pre-commit-config.yaml` — `detect-secrets` runs on
every commit and flags likely secret values before they reach git history,
so FR-016 ("no production secrets ever committed") is machine-checked rather
than relying on remembering to gitignore `.env` files.
