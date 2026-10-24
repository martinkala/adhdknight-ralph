# Contract: Monitoring Status (operator-facing)

The spec requires warnings to be "surfaced" (FR-008, FR-010, FR-012) but doesn't mandate a specific channel. This contract defines the minimal read surface needed so an operator can see current state; the actual alert delivery mechanism (log line, email, etc.) is an implementation choice for `/speckit-tasks`.

## `GET /internal/monitoring/status` (FastAPI, operator-authenticated)

Returns the most recent check results and any unresolved warnings.

**Response 200**:
```json
{
  "last_web_console_check": { "checked_at": "2026-08-04T12:00:00Z", "success": true, "error_detail": null, "consecutive_failures": 0 },
  "last_api_check": { "checked_at": "2026-08-04T12:00:00Z", "success": false, "error_detail": "connection refused", "consecutive_failures": 2 },
  "last_integrity_snapshot": { "captured_at": "2026-08-04T12:00:00Z", "total_user_count": 42 },
  "recent_warnings": [
    { "raised_at": "2026-08-04T11:00:00Z", "metric": "user_data_growth", "user_id": "...", "previous_value": 10, "current_value": 500, "threshold": 100 }
  ]
}
```

`consecutive_failures` (FR-008a) is derived at query time per `data-model.md`'s `MonitoringCheckResult` escalation note, not a stored field. A value `>= N` (configured threshold, default 2) means the escalation warning is currently active for that target.

**Auth**: Restricted to an operator/admin credential — MUST NOT be reachable by regular users, since it exposes per-user data-volume figures.

## Internal check triggers (not public HTTP contracts)

- Synthetic login checks (FR-005, FR-006) and integrity snapshot capture (FR-009, FR-011) are triggered by a scheduled job (systemd timer per research.md §2), not by an inbound HTTP request from a client. They call existing login endpoints (web console login form, API `/auth` login) exactly as a real user would, then write results via the internal service layer — no new public contract beyond the status read above.
