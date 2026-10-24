#!/usr/bin/env bash
# Compiles web_app/locale/*/LC_MESSAGES/django.po to django.mo without gettext (food-010).
# The .mo files are committed: deploy does not run compilemessages.
# Usage: web_app/scripts/compile_messages.sh   (needs babel from requirements-dev.txt)
set -euo pipefail

WEB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYBABEL="$WEB/${VENV_NAME:-.venv}/bin/pybabel"
[[ -x "$PYBABEL" ]] || PYBABEL="pybabel"

"$PYBABEL" compile -d "$WEB/locale" -D django --statistics
