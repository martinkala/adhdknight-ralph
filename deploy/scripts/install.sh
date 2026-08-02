#!/usr/bin/env bash
# Production install/deploy script for adhdmad (feature 018-migration-to-server).
# Run ON the production Debian server, as root (or via sudo), from the repo checkout.
#
# Usage:
#   ./deploy/scripts/install.sh                 # run every step, in order
#   ./deploy/scripts/install.sh --step <name>    # run a single step (see STEP NAMES below)
#
# STEP NAMES (in execution order):
#   packages            install_packages          - apt-get install nginx, postgresql, certbot, rsync, etc.
#   postgres            setup_postgres           - FR-006: Postgres listens on localhost only
#   databases           create_databases          - create adhd_server / adhd_web DBs+roles
#   deps-and-migrate     install_deps_and_migrate  - venv, pip install, alembic/django migrate, collectstatic, start services
#   migrate-data         migrate_data              - invoke 017's SQLite->Postgres data migration tool
#   nginx-and-certs       setup_nginx_and_certs     - install site configs, obtain Let's Encrypt certs
#   certbot-timer         enable_certbot_timer      - enable auto-renewal
#   basic-auth            setup_basic_auth          - create placeholder htpasswd for console
#
# This script is idempotent where practical, but it is an install runbook, not a
# general-purpose config-management tool — re-running it is expected to be safe,
# but it does not attempt to detect/undo manual changes made directly on the server.

set -euo pipefail

REPO_ROOT="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_ROOT="/opt/adhknight"
APP_USER="adhdmad"
SERVER_DIR="$APP_ROOT/server"
WEB_DIR="$APP_ROOT/web_app"
# The interpreter used to create the venvs. MUST live somewhere world-readable —
# venvs always resolve their stdlib back to this interpreter's own install prefix
# at runtime (even with --copies), so if this points into e.g. /root/.pyenv/...,
# the systemd services (running as $APP_USER, not root) fail with
# "ModuleNotFoundError: No module named 'encodings'" because they can't read it.
# Override on a per-server basis, e.g.: PYTHON_BIN=/opt/python/3.12.4/bin/python3
PYTHON_BIN="${PYTHON_BIN:-python3}"
# Django 6 requires PostgreSQL 14+. Debian's own repos track whatever major
# version shipped with the release (13 on Debian 11) — too old — so we pin a
# modern version from the official PGDG repo instead of the distro default.
PG_VERSION="${PG_VERSION:-16}"

log() { echo "==> $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Step 0: install the system packages everything else here depends on.
# Idempotent — apt-get install on an already-installed package is a no-op.
# ---------------------------------------------------------------------------
install_packages() {
    log "Installing required system packages (nginx, certbot, rsync, apache2-utils, python3-venv)"
    sudo apt-get update
    sudo apt-get install -y \
        nginx \
        certbot python3-certbot-nginx \
        apache2-utils \
        rsync \
        python3-venv python3-pip \
        postgresql-common

    if command -v psql >/dev/null && [[ "$(psql --version | grep -oE '[0-9]+' | head -1)" -ge 14 ]]; then
        log "PostgreSQL $(psql --version | grep -oE '[0-9]+' | head -1) already installed (>= 14, OK)"
        return
    fi

    log "Installing PostgreSQL $PG_VERSION via the PGDG repo (distro default is too old for Django 6)"
    log "NOTE: if an older PostgreSQL cluster (e.g. distro-default 13) is already running on this"
    log "host, the new cluster will NOT get port 5432 automatically — see 'pg_lsclusters' and"
    log "'pg_dropcluster <old-version> main --stop' (safe only if that old cluster has no real data)."
    sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
    sudo apt-get update
    sudo apt-get install -y "postgresql-$PG_VERSION" "postgresql-contrib-$PG_VERSION"
}

# ---------------------------------------------------------------------------
# Phase 2 (Foundational) — T005: PostgreSQL localhost-only binding (FR-006)
# ---------------------------------------------------------------------------
setup_postgres() {
    log "Verifying PostgreSQL listen_addresses is localhost-only"
    local pg_conf
    pg_conf="$(sudo -u postgres psql -tAc "SHOW config_file;")"
    local listen_addr
    listen_addr="$(sudo -u postgres psql -tAc "SHOW listen_addresses;" | tr -d '[:space:]')"

    if [[ "$listen_addr" != "localhost" ]]; then
        log "listen_addresses is '$listen_addr' — setting to 'localhost' in $pg_conf"
        sudo sed -i "s/^#\?listen_addresses.*/listen_addresses = 'localhost'/" "$pg_conf"
        NEEDS_PG_RESTART=1
    else
        log "listen_addresses already 'localhost' — Debian default, no change needed"
    fi

    local hba_conf
    hba_conf="$(sudo -u postgres psql -tAc "SHOW hba_file;")"
    log "Confirm $hba_conf only allows 'local' (peer) and 'host ... 127.0.0.1/32' connections."
    log "This script does not rewrite pg_hba.conf automatically — review it manually:"
    log "  sudo cat $hba_conf | grep -v '^#' | grep -v '^$'"
    log "Expected: no 'host all all 0.0.0.0/0 ...' or equivalent wide-open line."

    if [[ "${NEEDS_PG_RESTART:-0}" == "1" ]]; then
        sudo systemctl restart postgresql
        log "Restarted postgresql after listen_addresses change"
    fi
}

# ---------------------------------------------------------------------------
# T006: create adhd_server (FastAPI, owned by 017) and adhd_web (Django) DBs
# ---------------------------------------------------------------------------
create_databases() {
    log "Creating adhd_server and adhd_web databases/roles (idempotent)"
    sudo -u postgres psql <<'SQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'adhd_server') THEN
        CREATE ROLE adhd_server LOGIN PASSWORD 'CHANGE_ME_adhd_server';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'adhd_web') THEN
        CREATE ROLE adhd_web LOGIN PASSWORD 'CHANGE_ME_adhd_web';
    END IF;
END
$$;
SQL
    sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='adhd_server'" | grep -q 1 \
        || sudo -u postgres psql -c "CREATE DATABASE adhd_server OWNER adhd_server;"
    sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='adhd_web'" | grep -q 1 \
        || sudo -u postgres psql -c "CREATE DATABASE adhd_web OWNER adhd_web;"

    log "Databases ready. CHANGE the placeholder passwords above (ALTER ROLE ... PASSWORD ...)"
    log "and set matching DATABASE_URL / DJANGO_DATABASE_URL in server/.env and web_app/.env."
}

# ---------------------------------------------------------------------------
# T011: venv + deps + migrate + collectstatic + start services
# ---------------------------------------------------------------------------
install_deps_and_migrate() {
    # --copies: venv's python must NOT be a symlink out to whatever interpreter
    # created it (e.g. a pyenv install under /root/.pyenv) — the systemd units
    # run as $APP_USER, which typically cannot traverse another user's home dir,
    # so a symlinked interpreter causes "203/EXEC: Permission denied" at start.
    log "Installing FastAPI server (venv, deps, alembic migrate)"
    (cd "$SERVER_DIR" && "$PYTHON_BIN" -m venv --copies .venv --upgrade-deps 2>/dev/null || "$PYTHON_BIN" -m venv --copies .venv)
    "$SERVER_DIR/.venv/bin/pip" install --quiet -r "$SERVER_DIR/requirements.txt"
    [[ -f "$SERVER_DIR/.env" ]] || die "$SERVER_DIR/.env missing — copy from .env.example and set DATABASE_URL to adhd_server (see create_databases step)"
    (cd "$SERVER_DIR" && .venv/bin/alembic upgrade head)

    log "Installing Django web console (venv, deps, migrate, collectstatic)"
    (cd "$WEB_DIR" && "$PYTHON_BIN" -m venv --copies .venv --upgrade-deps 2>/dev/null || "$PYTHON_BIN" -m venv --copies .venv)
    "$WEB_DIR/.venv/bin/pip" install --quiet -r "$WEB_DIR/requirements.txt"
    [[ -f "$WEB_DIR/.env" ]] || die "$WEB_DIR/.env missing — copy from .env.example and set DJANGO_* vars (see create_databases step)"
    set -a; source "$WEB_DIR/.env"; set +a
    (cd "$WEB_DIR" && .venv/bin/python manage.py migrate)
    (cd "$WEB_DIR" && .venv/bin/python manage.py collectstatic --noinput)

    log "Fixing ownership: $APP_ROOT -> $APP_USER:$APP_USER (systemd units run as $APP_USER)"
    id "$APP_USER" >/dev/null 2>&1 || die "system user '$APP_USER' does not exist — create it first: sudo useradd -r -s /usr/sbin/nologin $APP_USER"
    sudo chown -R "$APP_USER:$APP_USER" "$APP_ROOT"

    log "Installing systemd units"
    sudo install -m 644 "$REPO_ROOT/deploy/systemd/adhd-api.service" /etc/systemd/system/adhd-api.service
    sudo install -m 644 "$REPO_ROOT/deploy/systemd/adhd-web.service" /etc/systemd/system/adhd-web.service
    sudo systemctl daemon-reload
    sudo systemctl enable --now adhd-api.service
    sudo systemctl enable --now adhd-web.service
    log "adhd-api and adhd-web running on 127.0.0.1:8095 / 127.0.0.1:8000 (not yet reachable from outside — Nginx not configured yet)"
}

# ---------------------------------------------------------------------------
# T010: invoke 017's SQLite->PostgreSQL migration tool. 018 does NOT
# reimplement this logic (see spec.md "Vzťah k 017", research.md Decision 8).
# ---------------------------------------------------------------------------
migrate_data() {
    local migration_tool="$SERVER_DIR/scripts/migrate_sqlite_to_postgres.py"
    if [[ ! -f "$migration_tool" ]]; then
        die "017 migration tool not found at $migration_tool — see specs/017-migration-to-postgres. 018 calls this tool but does not implement it; it must be delivered by 017 before this step can run."
    fi
    log "Running SQLite->PostgreSQL migration via $migration_tool"
    # cd into SERVER_DIR first — get_settings() resolves ".env" relative to cwd,
    # not to the script's location, so running from elsewhere silently falls
    # back to the SQLite default and the tool rejects the run.
    (cd "$SERVER_DIR" && .venv/bin/python "$migration_tool")
}

# ---------------------------------------------------------------------------
# T012-T014: Nginx site configs + Let's Encrypt certs (certbot --nginx plugin
# rewrites these files in place on the server to add the TLS block + redirect)
# ---------------------------------------------------------------------------
setup_nginx_and_certs() {
    log "Installing Nginx site configs"
    sudo install -m 644 "$REPO_ROOT/deploy/nginx/api.adhdknight.com.conf" /etc/nginx/sites-available/api.adhdknight.com.conf
    sudo install -m 644 "$REPO_ROOT/deploy/nginx/console.adhdknight.com.conf" /etc/nginx/sites-available/console.adhdknight.com.conf
    sudo ln -sf /etc/nginx/sites-available/api.adhdknight.com.conf /etc/nginx/sites-enabled/api.adhdknight.com.conf
    sudo ln -sf /etc/nginx/sites-available/console.adhdknight.com.conf /etc/nginx/sites-enabled/console.adhdknight.com.conf

    assert_api_has_no_basic_auth

    sudo nginx -t || die "nginx -t failed — fix the config before reloading (see quickstart.md rollback note)"
    sudo systemctl reload nginx

    command -v certbot >/dev/null || die "certbot not installed — run: sudo apt-get install -y certbot python3-certbot-nginx"

    log "Requesting Let's Encrypt certificate for api.adhdknight.com"
    sudo certbot --nginx -d api.adhdknight.com --non-interactive --agree-tos -m martinkala@outlook.com
    log "Requesting Let's Encrypt certificate for console.adhdknight.com"
    sudo certbot --nginx -d console.adhdknight.com --non-interactive --agree-tos -m martinkala@outlook.com

    sudo nginx -t && sudo systemctl reload nginx
}

# T020: guard against api.adhdknight.com ever getting a Basic Auth directive (SC-004)
assert_api_has_no_basic_auth() {
    # Strip comments first — grepping the raw file would also match this
    # check's own explanatory comments in the .conf file, not just a real
    # directive.
    if grep -vE '^\s*#' "$REPO_ROOT/deploy/nginx/api.adhdknight.com.conf" | grep -qE '\bauth_basic\b'; then
        die "deploy/nginx/api.adhdknight.com.conf must NOT contain auth_basic (FR-005 / SC-004) — API uses JWT, not Basic Auth."
    fi
}

# ---------------------------------------------------------------------------
# T015: certbot renewal — Debian's certbot package ships certbot.timer already;
# this just makes sure it's enabled.
# ---------------------------------------------------------------------------
enable_certbot_timer() {
    log "Enabling certbot.timer for automatic renewal (FR-002)"
    sudo systemctl enable --now certbot.timer
    systemctl status certbot.timer --no-pager || true
    log "NOTE: if this server has no public IP for the HTTP-01 challenge, use DNS-01 instead:"
    log "  sudo certbot certonly --manual --preferred-challenges dns -d <domain>"
}

# ---------------------------------------------------------------------------
# T019: placeholder Basic Auth credential for the console (FR-005)
# ---------------------------------------------------------------------------
setup_basic_auth() {
    command -v htpasswd >/dev/null || sudo apt-get install -y apache2-utils

    if [[ -f /etc/nginx/.htpasswd_console ]]; then
        log ".htpasswd_console already exists — leaving it untouched (not overwriting a real password)"
    else
        sudo htpasswd -cb /etc/nginx/.htpasswd_console admin admin
        log "Created /etc/nginx/.htpasswd_console with PLACEHOLDER credentials admin/admin"
    fi

    echo
    echo "############################################################################"
    echo "# ACTION REQUIRED: the console Basic Auth password is still the placeholder #"
    echo "# admin/admin. Change it now, interactively, on this server:               #"
    echo "#   sudo htpasswd /etc/nginx/.htpasswd_console admin                       #"
    echo "# Never commit the real password to the repository (FR-005).               #"
    echo "############################################################################"
    echo
}

# ---------------------------------------------------------------------------
main() {
    local step="${2:-}"
    if [[ "${1:-}" == "--step" ]]; then
        case "$step" in
            packages) install_packages ;;
            postgres) setup_postgres ;;
            databases) create_databases ;;
            deps-and-migrate) install_deps_and_migrate ;;
            migrate-data) migrate_data ;;
            nginx-and-certs) setup_nginx_and_certs ;;
            certbot-timer) enable_certbot_timer ;;
            basic-auth) setup_basic_auth ;;
            *) die "unknown --step '$step' — see header comment for valid names" ;;
        esac
        exit 0
    fi

    install_packages
    setup_postgres
    create_databases
    install_deps_and_migrate
    migrate_data
    setup_nginx_and_certs
    enable_certbot_timer
    setup_basic_auth

    log "Install complete. Run specs/018-migration-to-server/quickstart.md scenarios to validate."
}

main "$@"
