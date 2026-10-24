#!/usr/bin/env bash
# Runs the whole test suite (server, Django web, Playwright e2e) with one command.
# Usage: ./scripts/test-food.sh [--no-e2e]
# Venv directory name comes from VENV_NAME (default .venv; the Ralph container uses .venv-docker).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${VENV_NAME:-.venv}"
RUN_E2E=1

for arg in "$@"; do
    case "$arg" in
        --no-e2e) RUN_E2E=0 ;;
        -h|--help) echo "Usage: $0 [--no-e2e]"; exit 0 ;;
        *) echo "Unknown argument: $arg" >&2; exit 2 ;;
    esac
done

# Creates <component>/<venv> if missing or broken and (re)installs requirements
# only when requirements changed (hash stored inside the venv). requirements-dev.txt
# (dev tools such as babel) is used instead of requirements.txt when it exists.
ensure_venv() {
    local dir="$ROOT/$1"
    local venv="$dir/$VENV"
    local req="$dir/requirements.txt"
    [[ -f "$dir/requirements-dev.txt" ]] && req="$dir/requirements-dev.txt"
    local stamp="$venv/.requirements.sha256"

    # pip check also catches venvs left over from another Python version (interpreter runs, packages missing)
    if ! "$venv/bin/python" -m pip --version >/dev/null 2>&1; then
        echo ">> Creating $1/$VENV"
        rm -rf "$venv"
        python3 -m venv "$venv"
    fi
    local want
    want="$(cat "$dir/requirements.txt" "$req" | sha256sum | cut -d' ' -f1)"
    if [[ ! -f "$stamp" || "$(cat "$stamp")" != "$want" ]]; then
        echo ">> Installing $1/$(basename "$req") into $1/$VENV"
        "$venv/bin/python" -m pip install -q --upgrade pip
        "$venv/bin/python" -m pip install -q -r "$req"
        echo "$want" > "$stamp"
    fi
}

ensure_venv server
ensure_venv web_app
if [[ $RUN_E2E -eq 1 ]]; then
    ensure_venv e2e
    # Chromium is downloaded once into the Playwright cache (~/.cache/ms-playwright).
    if ! "$ROOT/e2e/$VENV/bin/python" - <<'PY' >/dev/null 2>&1
import os, sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    sys.exit(0 if os.path.exists(p.chromium.executable_path) else 1)
PY
    then
        echo ">> Installing Playwright Chromium"
        "$ROOT/e2e/$VENV/bin/playwright" install chromium
    fi
fi

server_status=FAIL
web_status=FAIL
e2e_status=SKIPPED

echo "== server tests"
if (cd "$ROOT/server" && "$VENV/bin/pytest" tests/unit tests/api -q); then
    server_status=OK
fi

echo "== web tests"
if (cd "$ROOT/web_app" && "$VENV/bin/python" manage.py test -v 1); then
    web_status=OK
fi

if [[ $RUN_E2E -eq 1 ]]; then
    echo "== e2e tests"
    e2e_status=FAIL
    if (cd "$ROOT" && VENV_NAME="$VENV" "e2e/$VENV/bin/pytest" e2e -q); then
        e2e_status=OK
    fi
fi

echo
echo "server: $server_status, web: $web_status, e2e: $e2e_status"
[[ $server_status == OK && $web_status == OK && $e2e_status != FAIL ]]
