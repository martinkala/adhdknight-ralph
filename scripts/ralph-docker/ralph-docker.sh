#!/bin/bash
#
# Run the Ralph loop inside an isolated Docker container.
#
#   ./scripts/ralph-docker/ralph-docker.sh build        # build the image
#   ./scripts/ralph-docker/ralph-docker.sh login        # one-time interactive Claude Code login
#   ./scripts/ralph-docker/ralph-docker.sh run [N]      # ralph-loop.sh with max N iterations (default 40)
#   ./scripts/ralph-docker/ralph-docker.sh shell        # debug shell in the same environment
#
# Env:
#   RALPH_DEPLOY_KEY  private deploy key with write access to the SANDBOX repo only
#                     (default ~/.ssh/adhdknight_ralph_deploy)
#   RALPH_SANDBOX_URL sandbox repo the container pushes to instead of origin
#                     (default git@github.com:martinkala/adhdknight-ralph.git)
#
# GitHub does not enforce branch protection on private repos of free personal accounts, so the
# container never gets access to the real repo: inside it, origin is rewritten to the sandbox
# and the deploy key exists only on the sandbox. You review the result and push it yourself.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMAGE="adhdknight-ralph"
HOME_VOLUME="adhdknight-ralph-home"
DEPLOY_KEY="${RALPH_DEPLOY_KEY:-$HOME/.ssh/adhdknight_ralph_deploy}"
SANDBOX_URL="${RALPH_SANDBOX_URL:-git@github.com:martinkala/adhdknight-ralph.git}"

build() {
    docker build \
        --build-arg UID="$(id -u)" --build-arg GID="$(id -g)" \
        -t "$IMAGE" "$SCRIPT_DIR"
}

run_container() {
    local tty_flags=(-i)
    [ -t 0 ] && tty_flags=(-it)

    if [ ! -f "$DEPLOY_KEY" ]; then
        echo "Deploy key not found: $DEPLOY_KEY (see scripts/ralph-docker/README.md)" >&2
        exit 1
    fi

    local git_name git_email origin_url
    origin_url="$(git -C "$REPO_DIR" remote get-url origin)"
    git_name="$(git -C "$REPO_DIR" config user.name || echo Ralph)"
    git_email="$(git -C "$REPO_DIR" config user.email || echo ralph@localhost)"

    docker run --rm "${tty_flags[@]}" \
        --name "adhdknight-ralph-$$" \
        -v "$REPO_DIR:/work" \
        -v "$HOME_VOLUME:/home/ralph" \
        -v "$DEPLOY_KEY:/run/secrets/deploy_key:ro" \
        -e GIT_AUTHOR_NAME="$git_name" -e GIT_AUTHOR_EMAIL="$git_email" \
        -e GIT_COMMITTER_NAME="$git_name" -e GIT_COMMITTER_EMAIL="$git_email" \
        -e GIT_SSH_COMMAND="ssh -i /run/secrets/deploy_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" \
        -e GIT_CONFIG_COUNT=1 \
        -e GIT_CONFIG_KEY_0="url.$SANDBOX_URL.insteadOf" \
        -e GIT_CONFIG_VALUE_0="$origin_url" \
        -e CLAUDE_MODEL="${CLAUDE_MODEL:-claude-opus-5-5}" \
        "$IMAGE" "$@"
}

case "${1:-}" in
    build) build ;;
    login) run_container claude ;;
    run)   run_container ./scripts/ralph-loop.sh "${2:-40}" ;;
    shell) run_container bash ;;
    *)
        sed -n '3,20p' "$0"
        exit 1
        ;;
esac
