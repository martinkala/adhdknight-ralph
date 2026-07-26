"""
Port of Android IndexCalculator.computeDailyIndexGrouped().
Algorithm C1: group_avg(active_children) × parent.weight for group nodes;
direct contribution for root trackable nodes without active children.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class DetailItem:
    element_key: str
    value_effective: float
    weight: float
    contribution: float
    impact: int


@dataclass
class ComputeResult:
    index_value: float
    detail: list[DetailItem]
    active_weight_sum: float
    skipped_keys: list[str]


def _value_effective(
    value_binary: int,
    value_scale: int | None,
    scale_min: int | None = None,
    scale_max: int | None = None,
) -> float:
    if value_scale is not None:
        if scale_min is not None and scale_max is not None and scale_max != scale_min:
            return (value_scale - scale_min) / (scale_max - scale_min)
        # Fallback: fixed 1..5 scale assumption (legacy behavior for callers that don't
        # provide per-element bounds).
        return (value_scale - 1) / 4.0
    return float(value_binary)


def compute_daily(
    values: list[dict],
    entity_config: dict[str, dict],
    active_keys: list[str],
) -> ComputeResult | None:
    """
    Compute daily ADHD index.

    values: list of {element_key, value_binary, value_scale}
    entity_config: {key: {weight, impact, parent, scale, ...}}
    active_keys: keys the user has activated

    Returns None if no active keys or no values.
    """
    active_set = set(active_keys)
    if not active_set:
        return None

    value_map: dict[str, float] = {}
    for v in values:
        key = v["element_key"]
        node = entity_config.get(key, {})
        eff = _value_effective(
            v.get("value_binary", 0),
            v.get("value_scale"),
            node.get("scale_min"),
            node.get("scale_max"),
        )
        value_map[key] = eff

    if not value_map:
        return None

    root_nodes = {k: n for k, n in entity_config.items() if n.get("parent") is None}
    detail: list[DetailItem] = []
    total_weight = 0.0
    weighted_sum = 0.0
    skipped: list[str] = []

    for root_key, root_node in root_nodes.items():
        root_weight = float(root_node.get("weight", 0))
        root_impact = root_node.get("impact")  # None = group node

        children = {k: n for k, n in entity_config.items() if n.get("parent") == root_key}
        active_children = {k: n for k, n in children.items() if k in active_set}

        if active_children:
            # C1: group avg of active children × root weight
            child_effs: list[float] = []
            for ck, cn in active_children.items():
                child_impact = cn.get("impact", 1)
                raw = value_map.get(ck, 0.0)
                eff = (1.0 - raw) if child_impact == -1 else raw
                child_effs.append(eff)

            group_avg = sum(child_effs) / len(child_effs)
            contribution = root_weight * group_avg
            total_weight += root_weight
            weighted_sum += contribution
            detail.append(DetailItem(
                element_key=root_key,
                value_effective=group_avg,
                weight=root_weight,
                contribution=contribution,
                impact=root_impact if root_impact is not None else 1,
            ))

        elif root_key in active_set and root_impact is not None:
            # trackable root with no active children → direct contribution
            raw = value_map.get(root_key, 0.0)
            eff = (1.0 - raw) if root_impact == -1 else raw
            contribution = root_weight * eff
            total_weight += root_weight
            weighted_sum += contribution
            detail.append(DetailItem(
                element_key=root_key,
                value_effective=eff,
                weight=root_weight,
                contribution=contribution,
                impact=root_impact,
            ))
        else:
            skipped.append(root_key)

    if total_weight == 0:
        return None

    index_value = round((weighted_sum / total_weight) * 100, 2)
    return ComputeResult(
        index_value=index_value,
        detail=detail,
        active_weight_sum=total_weight,
        skipped_keys=skipped,
    )
