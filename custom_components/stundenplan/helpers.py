from __future__ import annotations

import re
from typing import Any

from homeassistant.util import slugify as ha_slugify

from .const import COLOR_VALUES, CONF_SUBJECTS, DEFAULT_SUBJECT_ICON

_HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def slugify_name(value: str) -> str:
    """Return a stable entity-id compatible slug."""
    slug = ha_slugify(value or "stundenplan")
    return slug or "stundenplan"


def normalize_color(value: str | None) -> str:
    """Normalize configured subject colors to safe CSS values."""
    if not value:
        return COLOR_VALUES["primary"]
    if value in COLOR_VALUES:
        return COLOR_VALUES[value]
    if _HEX_COLOR_PATTERN.match(value):
        return value
    if value.startswith("var("):
        return value
    return COLOR_VALUES["primary"]


def subject_lookup(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Return subject metadata keyed by the configured subject name."""
    result: dict[str, dict[str, str]] = {}
    for subject in data.get(CONF_SUBJECTS, []) or []:
        name = str(subject.get("name", "")).strip()
        if not name:
            continue
        result[name] = {
            "subject": name,
            "icon": subject.get("icon") or DEFAULT_SUBJECT_ICON,
            "color": normalize_color(subject.get("color")),
            "color_key": subject.get("color") or "primary",
        }
    return result
