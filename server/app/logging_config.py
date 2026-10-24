import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
API_LOG_FILE = LOG_DIR / "api.log"

_configured = False


def configure_api_logging() -> None:
    """Routes all API-side logging — request logs (`adhd.request`) and monitoring
    check/escalation warnings (`adhd.monitoring`) — to a dedicated `logs/api.log`
    (FR-017-FR-019), separate from the Django web console's `logs/web.log`.

    Called from both `app/main.py` (the running API process) and
    `scripts/run_monitoring_checks.py` (the standalone systemd-timer script, T036),
    since the latter never imports `app.main`."""
    global _configured
    if _configured:
        return
    _configured = True

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(API_LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    adhd_logger = logging.getLogger("adhd")
    adhd_logger.setLevel(logging.INFO)
    adhd_logger.addHandler(handler)
    adhd_logger.propagate = False
