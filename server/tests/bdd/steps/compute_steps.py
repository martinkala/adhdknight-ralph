from behave import given, when, then
from app.services.index_calculator import compute_daily

DEFAULT_CONFIG = {
    "sleep": {"weight": 15.0, "impact": 1, "parent": None, "scale": True},
    "overall_feeling": {"weight": 13.0, "impact": 1, "parent": None, "scale": True},
    "physical_activity": {"weight": 11.0, "impact": 1, "parent": None, "scale": False},
    "stress_work": {"weight": 13.0, "impact": -1, "parent": None, "scale": False},
    "mindfulness": {"weight": 11.0, "impact": 1, "parent": None, "scale": False},
}


@given('the fixture "{name}"')
def step_load_fixture(context, name):
    context.fixture = context.load_fixture(name)


@given("a single day with all elements at maximum")
def step_all_max(context):
    context.values = [
        {"element_key": "sleep", "value_binary": 1, "value_scale": 5},
        {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 5},
        {"element_key": "physical_activity", "value_binary": 1},
        {"element_key": "stress_work", "value_binary": 0},
        {"element_key": "mindfulness", "value_binary": 1},
    ]
    context.entity_config = DEFAULT_CONFIG
    context.active_keys = list(DEFAULT_CONFIG.keys())


@given("a single day with all elements at minimum")
def step_all_min(context):
    context.values = [
        {"element_key": "sleep", "value_binary": 1, "value_scale": 1},
        {"element_key": "overall_feeling", "value_binary": 1, "value_scale": 1},
        {"element_key": "physical_activity", "value_binary": 0},
        {"element_key": "stress_work", "value_binary": 1},
        {"element_key": "mindfulness", "value_binary": 0},
    ]
    context.entity_config = DEFAULT_CONFIG
    context.active_keys = list(DEFAULT_CONFIG.keys())


@given('a single element "{key}" with impact {impact:d} and binary value {val:d}')
def step_single_element(context, key, impact, val):
    context.entity_config = {key: {"weight": 10.0, "impact": impact, "parent": None, "scale": False}}
    context.values = [{"element_key": key, "value_binary": val}]
    context.active_keys = [key]


@given('a group node "{group}" with weight {weight:f} and two active children both done')
def step_group_both_done(context, group, weight):
    context.entity_config = {
        group: {"weight": weight, "impact": None, "parent": None},
        "child_a": {"weight": weight / 2, "impact": 1, "parent": group},
        "child_b": {"weight": weight / 2, "impact": 1, "parent": group},
    }
    context.values = [
        {"element_key": "child_a", "value_binary": 1},
        {"element_key": "child_b", "value_binary": 1},
    ]
    context.active_keys = ["child_a", "child_b"]
    context.group_weight = weight


@given('a group node "{group}" with weight {weight:f} and one of two children done')
def step_group_one_done(context, group, weight):
    context.entity_config = {
        group: {"weight": weight, "impact": None, "parent": None},
        "child_a": {"weight": weight / 2, "impact": 1, "parent": group},
        "child_b": {"weight": weight / 2, "impact": 1, "parent": group},
    }
    context.values = [
        {"element_key": "child_a", "value_binary": 1},
        {"element_key": "child_b", "value_binary": 0},
    ]
    context.active_keys = ["child_a", "child_b"]


@given("a parent node with {n:d} child all done")
def step_parent_1_child(context, n):
    config = {"cat": {"weight": 15.0, "impact": None, "parent": None}}
    values = []
    keys = []
    for i in range(n):
        key = f"e{i+1}"
        config[key] = {"weight": 5.0, "impact": 1, "parent": "cat"}
        values.append({"element_key": key, "value_binary": 1})
        keys.append(key)
    context.configs.append(config)
    context.all_values.append(values)
    context.all_active_keys.append(keys)


@given("a parent node with {n:d} children all done")
def step_parent_n_children(context, n):
    step_parent_1_child(context, n)


@given("no values are provided")
def step_no_values(context):
    context.values = []
    context.entity_config = DEFAULT_CONFIG
    context.active_keys = list(DEFAULT_CONFIG.keys())


@given("values exist but no active keys are specified")
def step_no_active_keys(context):
    context.values = [{"element_key": "sleep", "value_binary": 1}]
    context.entity_config = DEFAULT_CONFIG
    context.active_keys = []


@given("one element is filled out of three active")
def step_one_of_three(context):
    context.values = [{"element_key": "sleep", "value_binary": 1, "value_scale": 5}]
    context.entity_config = DEFAULT_CONFIG
    context.active_keys = ["sleep", "physical_activity", "mindfulness"]


@given("a 3-day range with no values on any day")
def step_empty_range(context):
    context.range_days = [
        {"date": f"2026-06-{28+i}", "values": [], "active_keys": ["sleep"]}
        for i in range(3)
    ]
    context.range_entity_config = DEFAULT_CONFIG


@when('I compute the daily index for day "{date}"')
def step_compute_from_fixture(context, date):
    fixture = context.fixture
    config = {k: v for k, v in fixture["entity_config"].items()}
    day = next((d for d in fixture["days"] if d["date"] == date), None)
    assert day is not None, f"Day {date} not found in fixture"
    context.result = compute_daily(day["values"], config, day["active_keys"])


@when("I compute the daily index")
def step_compute(context):
    context.result = compute_daily(
        getattr(context, "values", []),
        getattr(context, "entity_config", DEFAULT_CONFIG),
        getattr(context, "active_keys", []),
    )


@when("I compute both configurations")
def step_compute_both(context):
    context.results = [
        compute_daily(context.all_values[i], context.configs[i], context.all_active_keys[i])
        for i in range(len(context.configs))
    ]


@when("I compute the range")
def step_compute_range(context):
    context.range_results = []
    for day in context.range_days:
        r = compute_daily(day["values"], context.range_entity_config, day["active_keys"])
        context.range_results.append((day["date"], r))


@then("the index value is approximately {expected:f} with tolerance {tol:f}")
def step_assert_index(context, expected, tol):
    assert context.result is not None, f"Expected index ~{expected} but got None"
    assert abs(context.result.index_value - expected) < tol, (
        f"Expected {expected} ± {tol}, got {context.result.index_value}"
    )


@then("the result is null without error")
def step_result_null(context):
    assert context.result is None, f"Expected None but got {context.result}"


@then("the index value is not null")
def step_index_not_null(context):
    assert context.result is not None


@then("the index is between 0 and 100")
def step_index_range(context):
    assert 0 <= context.result.index_value <= 100


@then("both produce the same index value")
def step_both_same(context):
    r0, r1 = context.results[0], context.results[1]
    assert r0 is not None and r1 is not None
    assert abs(r0.index_value - r1.index_value) < 0.01, (
        f"Expected same index, got {r0.index_value} vs {r1.index_value}"
    )


@then("all results have status {status}")
def step_all_status(context, status):
    status = status.strip('"')
    for date, result in context.range_results:
        assert result is None, f"Expected None for {date} but got {result}"


@then("all index values are null")
def step_all_null(context):
    for date, result in context.range_results:
        assert result is None


@then("the active weight sum equals {expected:f}")
def step_weight_sum(context, expected):
    assert context.result is not None
    assert abs(context.result.active_weight_sum - expected) < 0.01


@then("the fixture has {n:d} days")
def step_fixture_days(context, n):
    assert len(context.fixture["days"]) == n


@then("{n:d} days have no data")
def step_fixture_empty_days(context, n):
    empty = sum(1 for d in context.fixture["days"] if not d.get("values"))
    assert empty == n, f"Expected {n} empty days, found {empty}"
