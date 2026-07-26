import os
import re
import yaml
from fastapi import HTTPException, status

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config", "entities")

_SAFE_APP_ID = re.compile(r"^[a-zA-Z0-9_-]+$")


def _path_for(app_id: str) -> str:
    if not _SAFE_APP_ID.match(app_id):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid app_id")
    return os.path.join(CONFIG_DIR, f"{app_id}.yaml")


def load_entities_raw(app_id: str) -> str:
    """Raw YAML text for the given app_id — this is what the Android client downloads
    and feeds straight into its own EntityConfigLoader (same parser as the bundled asset)."""
    path = _path_for(app_id)
    if not os.path.isfile(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No entities config for app_id '{app_id}'")
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_entities_version(app_id: str) -> str:
    raw = load_entities_raw(app_id)
    data = yaml.safe_load(raw) or {}
    version = (data.get("metadata") or {}).get("version")
    return str(version) if version is not None else "0"
