"""Sensor platform for the Stundenplan integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from . import entry_config
from .const import (
    CONF_CHILD_NAME,
    CONF_HOLIDAY_CALENDAR,
    CONF_LESSON_COUNT,
    CONF_LESSON_TIMES,
    CONF_SCHOOL_DAYS,
    CONF_WEEK_PLAN,
    DEFAULT_SUBJECT_ICON,
    DOMAIN,
    NAME,
    VERSION,
    WEEKDAY_KEYS,
    WEEKDAY_NAMES_DE,
    WEEKDAY_SHORT_DE,
)
from .helpers import slugify_name, subject_lookup

SCAN_INTERVAL = timedelta(minutes=15)
DEFAULT_SCHOOL_DAYS = WEEKDAY_KEYS[:5]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Stundenplan sensor entity."""
    entity = StundenplanSensor(hass, entry)
    async_add_entities([entity], True)

    def _midnight_update(now) -> None:
        entity.async_schedule_update_ha_state(True)

    entry.async_on_unload(
        async_track_time_change(
            hass,
            _midnight_update,
            hour=0,
            minute=0,
            second=5,
        )
    )


class StundenplanSensor(SensorEntity):
    """Expose the configured school schedule as one sensor entity."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:timetable"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        child_name = entry_config(entry).get(CONF_CHILD_NAME) or NAME
        self._slug = slugify_name(child_name)

        self._attr_name = f"{NAME} {child_name}"
        self._attr_unique_id = f"{entry.entry_id}_schedule"
        self.entity_id = f"sensor.stundenplan_{self._slug}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for Home Assistant's device registry."""
        child_name = entry_config(self.entry).get(CONF_CHILD_NAME) or NAME
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": f"{NAME} {child_name}",
            "manufacturer": "@stefanmoeller",
            "model": NAME,
            "sw_version": VERSION,
            "configuration_url": "https://github.com/stefanmoeller/ha-stundenplan",
        }

    @property
    def native_value(self) -> str:
        """Return the current sensor state."""
        attrs = self.extra_state_attributes or {}
        if attrs.get("is_free_day"):
            return "Schulfrei"
        return attrs.get("weekday_name") or NAME

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes consumed by the Lovelace card."""
        return build_schedule_attributes(self.hass, entry_config(self.entry))


def _calendar_status(
    hass: HomeAssistant,
    calendar_entity: str | None,
) -> tuple[bool, str | None]:
    """Return whether the configured holiday calendar is active today."""
    if not calendar_entity:
        return False, None

    calendar_state = hass.states.get(calendar_entity)
    if not calendar_state or calendar_state.state != "on":
        return False, None

    return True, (
        calendar_state.attributes.get("message")
        or calendar_state.attributes.get("friendly_name")
    )


def _empty_day(day: str) -> dict[str, Any]:
    """Return an empty day structure with stable keys."""
    return {
        "key": day,
        "name": WEEKDAY_NAMES_DE.get(day, day),
        "short_name": WEEKDAY_SHORT_DE.get(day, day),
        "school_end": None,
        "lessons": [],
        "lesson_grid": [],
    }


def _lesson_time(lesson_times: list[dict[str, Any]], index: int) -> dict[str, Any]:
    """Return a lesson-time entry for the given index."""
    if index < len(lesson_times):
        return lesson_times[index]
    return {}


def build_schedule_attributes(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Build the schedule attributes for the current day and full week."""
    now = dt_util.now()
    today = now.date()
    weekday_key = WEEKDAY_KEYS[today.weekday()]

    school_days = data.get(CONF_SCHOOL_DAYS) or DEFAULT_SCHOOL_DAYS
    lesson_times = data.get(CONF_LESSON_TIMES) or []
    lesson_count = int(data.get(CONF_LESSON_COUNT) or len(lesson_times) or 0)
    week_plan = data.get(CONF_WEEK_PLAN) or {}
    subjects = subject_lookup(data)

    calendar_entity = data.get(CONF_HOLIDAY_CALENDAR)
    is_free_day, free_reason = _calendar_status(hass, calendar_entity)

    days: dict[str, Any] = {}
    for day in school_days:
        raw_lessons = list((week_plan.get(day) or [])[:lesson_count])
        raw_lessons += [""] * max(0, lesson_count - len(raw_lessons))

        lesson_grid = []
        lessons = []
        for index, subject_name in enumerate(raw_lessons):
            subject_name = str(subject_name or "").strip()
            if not subject_name:
                lesson_grid.append(None)
                continue

            lesson = dict(
                subjects.get(
                    subject_name,
                    {
                        "subject": subject_name,
                        "icon": DEFAULT_SUBJECT_ICON,
                        "color": "var(--primary-color)",
                        "color_key": "primary",
                    },
                )
            )
            lesson["hour"] = index + 1

            current_time = _lesson_time(lesson_times, index)
            if current_time:
                lesson["start"] = current_time.get("start")
                lesson["end"] = current_time.get("end")

            lesson_grid.append(lesson)
            lessons.append(lesson)

        school_end = None
        for index in range(min(len(raw_lessons), len(lesson_times)) - 1, -1, -1):
            if raw_lessons[index]:
                school_end = lesson_times[index].get("end")
                break

        days[day] = {
            "key": day,
            "name": WEEKDAY_NAMES_DE.get(day, day),
            "short_name": WEEKDAY_SHORT_DE.get(day, day),
            "school_end": school_end,
            "lessons": lessons,
            "lesson_grid": lesson_grid,
        }

    today_data = days.get(weekday_key, _empty_day(weekday_key))

    return {
        "child_name": data.get(CONF_CHILD_NAME),
        "weekday": weekday_key,
        "weekday_name": today_data.get("name"),
        "weekday_short": today_data.get("short_name"),
        "date": today.isoformat(),
        "is_school_day": weekday_key in school_days,
        "is_free_day": is_free_day,
        "free_reason": free_reason,
        "school_end": today_data.get("school_end"),
        "lessons": []
        if is_free_day or weekday_key not in school_days
        else today_data.get("lessons", []),
        "lesson_times": lesson_times,
        "lesson_count": lesson_count,
        "school_days": school_days,
        "holiday_calendar": calendar_entity,
        "weekday_names": WEEKDAY_NAMES_DE,
        "weekday_short_names": WEEKDAY_SHORT_DE,
        "subjects": subjects,
        "days": days,
    }
