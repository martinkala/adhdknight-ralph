"""food-003 FR-5: blood pressure quick entry and weight validation."""
from decimal import Decimal

import pytest

from app.services.food_measurements import MeasurementError, parse_blood_pressure, validate_weight


def test_bp_systolic_diastolic_only():
    assert parse_blood_pressure("130/85") == {"systolic": 130, "diastolic": 85, "pulse": None, "measured_at": None}


def test_bp_with_pulse_and_time():
    assert parse_blood_pressure("130/85 72 7:30") == {
        "systolic": 130, "diastolic": 85, "pulse": 72, "measured_at": "07:30",
    }


def test_bp_with_time_without_pulse():
    assert parse_blood_pressure("130/85 7:30") == {
        "systolic": 130, "diastolic": 85, "pulse": None, "measured_at": "07:30",
    }


def test_bp_with_pulse():
    assert parse_blood_pressure(" 130 / 85  72 ")["pulse"] == 72


@pytest.mark.parametrize("raw", ["145/02", "85/130", "130/85 10", "300/85"])
def test_bp_range(raw):
    with pytest.raises(ValueError) as exc:
        parse_blood_pressure(raw)
    assert str(exc.value) == "bp_range" and exc.value.code == "bp_range"


@pytest.mark.parametrize("raw", ["abc", "", "130", "130/85 72 25:00", "130/85 72 7:30 x"])
def test_bp_format(raw):
    with pytest.raises(MeasurementError) as exc:
        parse_blood_pressure(raw)
    assert exc.value.code == "bp_format"


def test_weight_rounded_to_one_decimal():
    assert validate_weight(80.64) == Decimal("80.6")
    assert validate_weight("80,65") == Decimal("80.7")


@pytest.mark.parametrize("kg", [10, 300.1, "abc"])
def test_weight_range(kg):
    with pytest.raises(ValueError, match="weight_range"):
        validate_weight(kg)
