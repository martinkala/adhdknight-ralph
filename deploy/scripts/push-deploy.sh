#!/usr/bin/env bash
# Run this ON YOUR DEV MACHINE, not on the server.
#
# Pushes the current (or given) git ref straight to the production server
# over the SSH access you already use for admin. No GitHub credentials are
# ever placed on the server — deliberate, see specs/018-migration-to-server:
# a compromised server should not be able to reach the GitHub repo.
#
# Usage:
#   ./deploy/scripts/push-deploy.sh                     # push HEAD to root@app01 (default)
#   ./deploy/scripts/push-deploy.sh 10.10.10.10          # push HEAD to root@10.10.10.10
#   ./deploy/scripts/push-deploy.sh deploy@10.10.10.10   # push HEAD to a specific user@host
#   ./deploy/scripts/push-deploy.sh 10.10.10.10 master   # push a specific ref to that host
#   DEPLOY_SERVER=root@1.2.3.4 ./deploy/scripts/push-deploy.sh
#
# Only syncs what's actually committed to git (via `git archive`) — your
# local uncommitted changes and gitignored files never reach the server.
# Server-side state (venv, .env, dev.db, staticfiles) is left untouched.

set -euo pipefail

SERVER_ARG="${1:-}"
if [[ -n "$SERVER_ARG" ]]; then
    if [[ "$SERVER_ARG" == *@* ]]; then
        SERVER="$SERVER_ARG"
    else
        SERVER="root@$SERVER_ARG"
    fi
else
    SERVER="${DEPLOY_SERVER:-root@app01}"
fi
REMOTE_PATH="${DEPLOY_PATH:-/opt/adhknight}"
REF="${2:-HEAD}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> Exporting $REF (committed content only, via git archive)"
git archive --format=tar "$REF" | tar -x -C "$WORKDIR"

echo "==> Syncing to $SERVER:$REMOTE_PATH (rsync --delete, server-only state preserved)"
ssh "$SERVER" "mkdir -p '$REMOTE_PATH'"
rsync -avz --delete \
  --exclude '.venv/' \
  --exclude '.env' \
  --exclude 'dev.db' \
  --exclude 'db.sqlite3' \
  --exclude 'staticfiles/' \
  --exclude '__pycache__/' \
  "$WORKDIR/" "$SERVER:$REMOTE_PATH/"

echo "==> Done. Next, run the install/update steps on the server:"
echo "    ssh $SERVER"
echo "    cd $REMOTE_PATH && ./deploy/scripts/install.sh"
