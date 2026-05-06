from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    CONF_CHILD_NAME,
    CONF_HOLIDAY_CALENDAR,
    CONF_LESSON_COUNT,
    CONF_LESSON_TIMES,
    CONF_SCHOOL_DAYS,
    CONF_SUBJECTS,
    CONF_WEEK_PLAN,
    DEFAULT_CHILD_NAME,
    DEFAULT_LESSON_COUNT,
    DEFAULT_LESSON_TIMES,
    DEFAULT_SCHOOL_DAYS,
    DEFAULT_SUBJECTS,
    HA_COLOR_HEX,
    HA_COLOR_LABELS,
    DOMAIN,
    WEEKDAY_NAMES,
    WEEKDAY_SHORT_NAMES,
    WEEKDAY_ORDER,
)

SCAN_INTERVAL = timedelta(minutes=5)
_LOGGER = logging.getLogger(__name__)


def _merged_config(entry: ConfigEntry) -> dict[str, Any]:
    data = dict(entry.data)
    data.update(entry.options)
    return _normalize_config(data)


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(config)
    lesson_count = int(normalized.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT) or DEFAULT_LESSON_COUNT)

    lesson_times = list(normalized.get(CONF_LESSON_TIMES) or [])
    while len(lesson_times) < lesson_count:
        if len(lesson_times) < len(DEFAULT_LESSON_TIMES):
            lesson_times.append(dict(DEFAULT_LESSON_TIMES[len(lesson_times)]))
        else:
            lesson_times.append({"start": "", "end": ""})
    normalized[CONF_LESSON_TIMES] = lesson_times[:lesson_count]

    subjects = normalized.get(CONF_SUBJECTS) or DEFAULT_SUBJECTS
    normalized[CONF_SUBJECTS] = subjects

    school_days = normalized.get(CONF_SCHOOL_DAYS) or DEFAULT_SCHOOL_DAYS
    normalized[CONF_SCHOOL_DAYS] = list(school_days)

    week_plan = dict(normalized.get(CONF_WEEK_PLAN) or {})
    for day in normalized[CONF_SCHOOL_DAYS]:
        values = list(week_plan.get(day) or [])
        while len(values) < lesson_count:
            values.append("")
        week_plan[day] = values[:lesson_count]
    normalized[CONF_WEEK_PLAN] = week_plan
    normalized[CONF_LESSON_COUNT] = lesson_count
    return normalized


def _plan_slug(config: dict[str, Any]) -> str:
    name = config.get(CONF_CHILD_NAME, DEFAULT_CHILD_NAME) or DEFAULT_CHILD_NAME
    return slugify(str(name)) or "stundenplan"


def _plan_name(config: dict[str, Any]) -> str:
    name = config.get(CONF_CHILD_NAME, DEFAULT_CHILD_NAME) or DEFAULT_CHILD_NAME
    return str(name).strip() or DEFAULT_CHILD_NAME


def _today_key() -> str:
    return WEEKDAY_ORDER[dt_util.now().weekday()]


def _subject_map(subjects: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(subject.get("name", "")).strip(): subject for subject in subjects if str(subject.get("name", "")).strip()}


def _format_color(color: Any) -> str:
    if isinstance(color, list) and len(color) >= 3:
        return f"rgb({int(color[0])}, {int(color[1])}, {int(color[2])})"
    if isinstance(color, str) and color:
        return HA_COLOR_HEX.get(color, color)
    return "var(--primary-color)"


def _color_label(color: Any) -> str | None:
    if isinstance(color, str):
        return HA_COLOR_LABELS.get(color, color)
    if isinstance(color, list) and len(color) >= 3:
        return f"RGB {int(color[0])}, {int(color[1])}, {int(color[2])}"
    return None


def _lesson_for(config: dict[str, Any], day_key: str, idx: int) -> dict[str, Any] | None:
    lesson_times = config.get(CONF_LESSON_TIMES, DEFAULT_LESSON_TIMES)
    plan = config.get(CONF_WEEK_PLAN, {}).get(day_key, [])
    if idx >= len(plan):
        return None
    subject_name = str(plan[idx] or "").strip()
    if not subject_name:
        return None
    subjects = _subject_map(config.get(CONF_SUBJECTS, []))
    subject = subjects.get(subject_name, {})
    lesson_time = lesson_times[idx] if idx < len(lesson_times) else {"start": None, "end": None}
    return {
        "hour": idx + 1,
        "start": lesson_time.get("start"),
        "end": lesson_time.get("end"),
        "subject": subject_name,
        "icon": subject.get("icon", "mdi:book-open-page-variant"),
        "color": _format_color(subject.get("color")),
        "color_key": subject.get("color"),
        "color_label": _color_label(subject.get("color")),
    }


def _build_lessons(config: dict[str, Any], day_key: str) -> list[dict[str, Any]]:
    lesson_count = int(config.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT))
    lessons: list[dict[str, Any]] = []
    for idx in range(lesson_count):
        lesson = _lesson_for(config, day_key, idx)
        if lesson:
            lessons.append(lesson)
    return lessons


def _build_grid(config: dict[str, Any], day_key: str) -> list[dict[str, Any] | None]:
    lesson_count = int(config.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT))
    return [_lesson_for(config, day_key, idx) for idx in range(lesson_count)]


def _school_end(config: dict[str, Any], day_key: str) -> str | None:
    lesson_times = config.get(CONF_LESSON_TIMES, DEFAULT_LESSON_TIMES)
    plan = config.get(CONF_WEEK_PLAN, {}).get(day_key, [])
    last_index: int | None = None
    for idx, subject_name in enumerate(plan):
        if str(subject_name or "").strip():
            last_index = idx
    if last_index is None or last_index >= len(lesson_times):
        return None
    return lesson_times[last_index].get("end")


def _calendar_free_reason(hass: HomeAssistant, calendar_entity: str | None) -> str | None:
    if not calendar_entity:
        return None
    state = hass.states.get(calendar_entity)
    if not state or state.state != "on":
        return None
    return state.attributes.get("message") or state.attributes.get("friendly_name") or "schulfrei"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = DataUpdateCoordinator(
        hass,
        logger=_LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_interval=SCAN_INTERVAL,
    )
    async_add_entities([
        StundenplanSensor(coordinator, hass, entry),
    ], update_before_add=True)


class StundenplanBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.hass = hass
        self.entry = entry
        self._config = _merged_config(entry)
        plan_name = _plan_name(self._config)
        self._plan_slug = _plan_slug(self._config)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Stundenplan {plan_name}",
            "manufacturer": "Custom Integration",
            "model": "Stundenplan v1",
        }

    async def async_update(self) -> None:
        self._config = _merged_config(self.entry)
        self._plan_slug = _plan_slug(self._config)


class StundenplanSensor(StundenplanBaseSensor):
    def __init__(self, coordinator: DataUpdateCoordinator, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(coordinator, hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_schedule"
        self._attr_name = None
        self._attr_icon = "mdi:timetable"
        self._attr_suggested_object_id = f"stundenplan_{self._plan_slug}"

    @property
    def native_value(self) -> str:
        self._config = _merged_config(self.entry)
        reason = _calendar_free_reason(self.hass, self._config.get(CONF_HOLIDAY_CALENDAR))
        if reason:
            return f"Schulfrei: {reason}"
        day_key = _today_key()
        if day_key not in self._config.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS):
            return "Kein Unterricht"
        end = _school_end(self._config, day_key)
        return f"Schulende {end}" if end else "Kein Unterricht"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        self._config = _merged_config(self.entry)
        day_key = _today_key()
        reason = _calendar_free_reason(self.hass, self._config.get(CONF_HOLIDAY_CALENDAR))
        is_school_day = day_key in self._config.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS)
        is_free_day = bool(reason)
        today_lessons = [] if is_free_day or not is_school_day else _build_lessons(self._config, day_key)
        attrs = {
            "name": self._config.get(CONF_CHILD_NAME, DEFAULT_CHILD_NAME),
            "date": date.today().isoformat(),
            "weekday": day_key,
            "weekday_name": WEEKDAY_NAMES.get(day_key, day_key),
            "weekday_short_name": WEEKDAY_SHORT_NAMES.get(day_key, day_key),
            "is_school_day": is_school_day,
            "is_free_day": is_free_day,
            "free_reason": reason,
            "holiday_calendar": self._config.get(CONF_HOLIDAY_CALENDAR),
            "school_end": None if is_free_day or not is_school_day else _school_end(self._config, day_key),
            "lessons": today_lessons,
        }
        attrs.update(_week_attributes(self._config))
        return attrs


def _week_attributes(config: dict[str, Any]) -> dict[str, Any]:
    subjects = config.get(CONF_SUBJECTS, [])
    subject_map = _subject_map(subjects)
    normalized_subjects = {
        name: {
            "name": subject.get("name"),
            "icon": subject.get("icon", "mdi:book-open-page-variant"),
            "color": _format_color(subject.get("color")),
            "color_key": subject.get("color"),
            "color_label": _color_label(subject.get("color")),
        }
        for name, subject in subject_map.items()
    }
    days = {}
    for day_key in config.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS):
        days[day_key] = {
            "name": WEEKDAY_NAMES.get(day_key, day_key),
            "short_name": WEEKDAY_SHORT_NAMES.get(day_key, day_key),
            "lessons": _build_lessons(config, day_key),
            "lesson_grid": _build_grid(config, day_key),
            "school_end": _school_end(config, day_key),
        }
    return {
        "lesson_count": config.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT),
        "lesson_times": config.get(CONF_LESSON_TIMES, DEFAULT_LESSON_TIMES),
        "school_days": config.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS),
        "weekday_names": WEEKDAY_NAMES,
        "weekday_short_names": WEEKDAY_SHORT_NAMES,
        "subjects": normalized_subjects,
        "week_plan": config.get(CONF_WEEK_PLAN, {}),
        "days": days,
    }
