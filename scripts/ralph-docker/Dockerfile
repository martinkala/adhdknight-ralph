# Isolated environment for the Ralph Wiggum loop.
# The container sees only the repository (bind mount at /work) and its own home volume;
# it never gets the host's ~/.ssh, ~/.claude or other projects.
FROM python:3.14-slim-trixie

ARG UID=1000
ARG GID=1000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git openssh-client ca-certificates curl nodejs npm gettext make \
    && rm -rf /var/lib/apt/lists/*

# Playwright system libraries for Chromium (browser binaries are downloaded later by test-food.sh
# into the ralph home volume)
RUN pip install --no-cache-dir playwright \
    && playwright install-deps chromium \
    && pip uninstall -y playwright \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code && npm cache clean --force

# The container keeps its own venvs (server/.venv-docker, ...) next to the host's .venv,
# because a venv is tied to the interpreter path it was created with
ENV VENV_NAME=.venv-docker

RUN groupadd -g "$GID" ralph && useradd -m -u "$UID" -g "$GID" -s /bin/bash ralph

USER ralph
WORKDIR /work
