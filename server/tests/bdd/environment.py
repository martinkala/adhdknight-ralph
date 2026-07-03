import os
import yaml

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name: str) -> dict:
    path = os.path.join(FIXTURES_DIR, f"{name}.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def before_all(context):
    from app.services.index_calculator import compute_daily
    context.compute_daily = compute_daily
    context.load_fixture = load_fixture
    # Pre-register all context attributes at the highest scope
    context.result = None
    context.fixture = None
    context.entity_config = {}
    context.values = []
    context.active_keys = []
    context.configs = []
    context.all_values = []
    context.all_active_keys = []
    context.range_days = []
    context.range_entity_config = {}
    context.range_results = []
    context.results = []
    context.group_weight = 0.0


