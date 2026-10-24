"""Blood pressure quick-entry parser and weight validation (constitution D4)."""
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

SYSTOLIC_RANGE = (60, 260)
DIASTOLIC_RANGE = (30, 160)
PULSE_RANGE = (30, 220)
WEIGHT_RANGE = (Decimal(20), Decimal(300))

# "130/85", "130/85 72", "130/85 72 7:30", "130/85 7:30" — the time is recognized by ":".
_BLOOD_PRESSURE = re.compile(
    r"^(?P<sys>\d{1,3})\s*/\s*(?P<dia>\d{1,3})(?:\s+(?P<pulse>\d{1,3}))?(?:\s+(?P<time>\d{1,2}:\d{2}))?$"
)
_TIME = re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{2})$")


class MeasurementError(ValueError):
    """ValueError whose message is a machine-readable error code (bp_format, bp_range, ...)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def normalize_time(raw: str) -> str:
    """'7:30' -> '07:30'. Raises MeasurementError('time_format') for anything else."""
    match = _TIME.match(raw.strip())
    if not match or int(match["h"]) > 23 or int(match["m"]) > 59:
        raise MeasurementError("time_format")
    return f"{int(match['h']):02d}:{match['m']}"


def _in_range(value: int | None, bounds: tuple[int, int]) -> bool:
    return value is None or bounds[0] <= value <= bounds[1]


def validate_blood_pressure(systolic: int, diastolic: int, pulse: int | None = None) -> None:
    if not (
        _in_range(systolic, SYSTOLIC_RANGE)
        and _in_range(diastolic, DIASTOLIC_RANGE)
        and _in_range(pulse, PULSE_RANGE)
        and systolic > diastolic
    ):
        raise MeasurementError("bp_range")


def parse_blood_pressure(raw: str) -> dict:
    """Returns {systolic, diastolic, pulse, measured_at}; raises MeasurementError bp_format / bp_range."""
    match = _BLOOD_PRESSURE.match(" ".join(raw.split()))
    if not match:
        raise MeasurementError("bp_format")
    try:
        measured_at = normalize_time(match["time"]) if match["time"] else None
    except MeasurementError:
        raise MeasurementError("bp_format") from None
    systolic, diastolic = int(match["sys"]), int(match["dia"])
    pulse = int(match["pulse"]) if match["pulse"] else None
    validate_blood_pressure(systolic, diastolic, pulse)
    return {"systolic": systolic, "diastolic": diastolic, "pulse": pulse, "measured_at": measured_at}


def validate_weight(kg: float | Decimal | str) -> Decimal:
    """Rounds to one decimal place (half up) and checks 20–300 kg, else MeasurementError('weight_range')."""
    try:
        value = Decimal(str(kg).replace(",", ".")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise MeasurementError("weight_range") from None
    if not WEIGHT_RANGE[0] <= value <= WEIGHT_RANGE[1]:
        raise MeasurementError("weight_range")
    return value
