"""Text cleanup and normalization for food entries (constitution D5). Typos are never corrected."""
import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_SEPARATORS = re.compile(r"[,\n]")


def clean_text(s: str) -> str:
    """Trim and collapse any run of whitespace to a single space."""
    return _WHITESPACE.sub(" ", s).strip()


def normalize(s: str) -> str:
    """clean_text, casefold and strip diacritics (NFKD without combining marks) -> text_norm."""
    decomposed = unicodedata.normalize("NFKD", clean_text(s).casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def split_entries(raw: str) -> list[str]:
    """Split one input on commas and newlines into cleaned, non-empty entries."""
    return [part for part in (clean_text(p) for p in _SEPARATORS.split(raw)) if part]
