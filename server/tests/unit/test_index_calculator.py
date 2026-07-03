import pytest
from app.services.index_calculator import compute_daily, _value_effective

DEFAULT_CONFIG = {
    "sleep": {"weight": 15.0, "impact": 1, "parent": None, "scale": True},
    "overall_feeling": {"weight": 13.0, "impact": 1, "parent": None, "scale": True},
    "physical_activity": {"weight": 11.0, "impact": 1, "parent": None, "scale": False},
    "stress_work": {"weight": 13.0, "impact": -1, "parent": None, "scale": False},
    "mindfulness": {"weight": 11.0, "impact": 1, "parent": None, "scale": False},
}


def test_value_effective_scale():
    assert _value_effective(1, 1) == 0.0
    assert _value_effective(1, 3) == 0.5
    assert _value_effective(1, 5) == 1.0


def test_value_effective_binary():
    assert _value_effective(1, None) == 1.0
    assert _value_effective(0, None) == 0.0


def test_scale_element_computes_correctly():
    # sleep scale=4 → e=0.75, overall scale=5 → e=1.0
    # index = 100 * (15*0.75 + 13*1.0) / (15+13) = 100 * 24.25/28 = 86.607
    result = compute_daily(
        values=[
            {"element_key": "sleep", "value_binary": 1, "value_scale": 4},
            {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 5},
        ],
        entity_config=DEFAULT_CONFIG,
        active_keys=["sleep", "overall_feeling"],
    )
    assert result is not None
    assert abs(result.index_value - 86.61) < 0.02


def test_binary_element():
    result = compute_daily(
        values=[{"element_key": "physical_activity", "value_binary": 1, "value_scale": None}],
        entity_config=DEFAULT_CONFIG,
        active_keys=["physical_activity"],
    )
    assert result is not None
    assert abs(result.index_value - 100.0) < 0.01


def test_negative_impact_inverted():
    # stress_work impact=-1, value_binary=1 → effective = 1.0 - 1.0 = 0.0 → index = 0
    result = compute_daily(
        values=[{"element_key": "stress_work", "value_binary": 1, "value_scale": None}],
        entity_config=DEFAULT_CONFIG,
        active_keys=["stress_work"],
    )
    assert result is not None
    assert abs(result.index_value - 0.0) < 0.01


def test_negative_impact_not_done_is_good():
    # stress_work binary=0 → effective = 1.0 - 0.0 = 1.0 → index = 100
    result = compute_daily(
        values=[{"element_key": "stress_work", "value_binary": 0, "value_scale": None}],
        entity_config=DEFAULT_CONFIG,
        active_keys=["stress_work"],
    )
    assert result is not None
    assert abs(result.index_value - 100.0) < 0.01


def test_subnode_c1_algorithm():
    config = {
        "lifestyle": {"weight": 20.0, "impact": None, "parent": None, "scale": False},
        "physical_activity": {"weight": 10.0, "impact": 1, "parent": "lifestyle", "scale": False},
        "mindfulness": {"weight": 10.0, "impact": 1, "parent": "lifestyle", "scale": False},
    }
    # Both active: avg(1.0, 0.0) = 0.5 → contribution = 20 * 0.5 = 10 → index = 50
    result = compute_daily(
        values=[
            {"element_key": "physical_activity", "value_binary": 1},
            {"element_key": "mindfulness", "value_binary": 0},
        ],
        entity_config=config,
        active_keys=["physical_activity", "mindfulness"],
    )
    assert result is not None
    assert abs(result.index_value - 50.0) < 0.01


def test_empty_values_returns_none():
    result = compute_daily(values=[], entity_config=DEFAULT_CONFIG, active_keys=["sleep"])
    assert result is None


def test_all_inactive_returns_none():
    result = compute_daily(
        values=[{"element_key": "sleep", "value_binary": 1, "value_scale": 4}],
        entity_config=DEFAULT_CONFIG,
        active_keys=[],
    )
    assert result is None


def test_all_max_equals_100():
    result = compute_daily(
        values=[
            {"element_key": "sleep", "value_binary": 1, "value_scale": 5},
            {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 5},
            {"element_key": "physical_activity", "value_binary": 1},
            {"element_key": "stress_work", "value_binary": 0},
            {"element_key": "mindfulness", "value_binary": 1},
        ],
        entity_config=DEFAULT_CONFIG,
        active_keys=list(DEFAULT_CONFIG.keys()),
    )
    assert result is not None
    assert abs(result.index_value - 100.0) < 0.01


def test_all_zero_equals_0():
    result = compute_daily(
        values=[
            {"element_key": "sleep", "value_binary": 1, "value_scale": 1},
            {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 1},
            {"element_key": "physical_activity", "value_binary": 0},
            {"element_key": "stress_work", "value_binary": 1},
            {"element_key": "mindfulness", "value_binary": 0},
        ],
        entity_config=DEFAULT_CONFIG,
        active_keys=list(DEFAULT_CONFIG.keys()),
    )
    assert result is not None
    assert abs(result.index_value - 0.0) < 0.01


def test_subnode_weight_not_inflated():
    # 1 element vs 3 elements with same parent weight → same index
    config_1 = {
        "cat": {"weight": 15.0, "impact": None, "parent": None},
        "e1": {"weight": 5.0, "impact": 1, "parent": "cat"},
    }
    config_3 = {
        "cat": {"weight": 15.0, "impact": None, "parent": None},
        "e1": {"weight": 5.0, "impact": 1, "parent": "cat"},
        "e2": {"weight": 5.0, "impact": 1, "parent": "cat"},
        "e3": {"weight": 5.0, "impact": 1, "parent": "cat"},
    }
    r1 = compute_daily(
        values=[{"element_key": "e1", "value_binary": 1}],
        entity_config=config_1,
        active_keys=["e1"],
    )
    r3 = compute_daily(
        values=[
            {"element_key": "e1", "value_binary": 1},
            {"element_key": "e2", "value_binary": 1},
            {"element_key": "e3", "value_binary": 1},
        ],
        entity_config=config_3,
        active_keys=["e1", "e2", "e3"],
    )
    assert r1 is not None and r3 is not None
    assert abs(r1.index_value - r3.index_value) < 0.01
    assert abs(r1.index_value - 100.0) < 0.01
