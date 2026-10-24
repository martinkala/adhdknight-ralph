"""Display helpers of the Food diary templates."""
from decimal import Decimal

from django import template
from django.utils import formats

register = template.Library()


def _number(value) -> str:
    """0.5 -> "0,5" (localized decimal separator), 2.0 -> "2"; no trailing zeros."""
    text = f"{Decimal(str(value)).normalize():f}"
    return text.replace(".", formats.get_format("DECIMAL_SEPARATOR"))


@register.filter
def qty(item) -> str:
    """Quantity chip label of an entry or quantity option: "2×", "0,5 l", "200 g"; "" without a quantity."""
    if item.get("quantity") is None:
        return ""
    unit = item.get("unit")
    return f"{_number(item['quantity'])} {unit}" if unit else f"{_number(item['quantity'])}×"


@register.filter
def number(value) -> str:
    return "" if value is None else _number(value)


@register.filter
def bp_raw(bp) -> str:
    """Blood pressure as the quick-entry string for editing: "130/85 72 07:30"."""
    parts = [f"{bp['systolic']}/{bp['diastolic']}"]
    if bp.get("pulse"):
        parts.append(str(bp["pulse"]))
    if bp.get("measured_at"):
        parts.append(bp["measured_at"])
    return " ".join(parts)
