"""Config flow for the Stundenplan integration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    DEFAULT_SUBJECT_ICON,
    DEFAULT_SUBJECTS,
    DOMAIN,
    MAX_LESSON_COUNT,
    MAX_SUBJECT_COUNT,
    NAME,
    SUBJECT_COLOR_OPTIONS,
    WEEKDAY_KEYS,
    WEEKDAY_NAMES_DE,
)

CONF_SUBJECT_COUNT = "subject_count"
CONF_COLOR = "color"


def _default_subject() -> dict[str, str]:
    """Return a blank subject entry."""
    return {"name": "", "icon": DEFAULT_SUBJECT_ICON, "color": "primary"}


def _default_data() -> dict[str, Any]:
    """Return the default schedule configuration."""
    lesson_count = DEFAULT_LESSON_COUNT
    school_days = WEEKDAY_KEYS[:5]

    return {
        CONF_CHILD_NAME: DEFAULT_CHILD_NAME,
        CONF_LESSON_COUNT: lesson_count,
        CONF_SCHOOL_DAYS: school_days,
        CONF_HOLIDAY_CALENDAR: None,
        CONF_LESSON_TIMES: DEFAULT_LESSON_TIMES[:lesson_count],
        CONF_SUBJECTS: list(DEFAULT_SUBJECTS),
        CONF_WEEK_PLAN: {day: [""] * lesson_count for day in school_days},
    }


def _as_list(value: Any) -> list[Any]:
    """Normalize Home Assistant selector values to lists."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _coerce_lesson_count(value: Any) -> int:
    """Return a positive lesson count."""
    try:
        lesson_count = int(value)
    except (TypeError, ValueError):
        return DEFAULT_LESSON_COUNT
    return max(1, lesson_count)


def _normalize_lesson_times(value: Any, lesson_count: int) -> list[dict[str, str]]:
    """Return exactly one start/end pair for each lesson."""
    lesson_times = _as_list(value)
    normalized: list[dict[str, str]] = []

    for index in range(lesson_count):
        default = (
            DEFAULT_LESSON_TIMES[index]
            if index < len(DEFAULT_LESSON_TIMES)
            else {"start": "08:00", "end": "08:45"}
        )
        current = lesson_times[index] if index < len(lesson_times) else {}
        current = current if isinstance(current, Mapping) else {}
        normalized.append(
            {
                "start": str(current.get("start") or default["start"]),
                "end": str(current.get("end") or default["end"]),
            }
        )

    return normalized


def _normalize_subjects(value: Any) -> list[dict[str, str]]:
    """Return subject dictionaries suitable for config-entry storage."""
    subjects: list[dict[str, str]] = []

    for subject in _as_list(value):
        if not isinstance(subject, Mapping):
            continue
        subjects.append(
            {
                "name": str(subject.get("name") or "").strip(),
                "icon": str(subject.get("icon") or DEFAULT_SUBJECT_ICON),
                "color": str(subject.get("color") or "primary"),
            }
        )

    return subjects or list(DEFAULT_SUBJECTS)


def _normalize_week_plan(
    value: Any,
    school_days: Sequence[str],
    lesson_count: int,
) -> dict[str, list[str]]:
    """Return a week plan with the right number of lesson slots per day."""
    raw_week_plan = value if isinstance(value, Mapping) else {}
    week_plan: dict[str, list[str]] = {}

    for day, lessons in raw_week_plan.items():
        week_plan[str(day)] = [str(lesson or "") for lesson in _as_list(lessons)]

    for day in school_days:
        lessons = week_plan.get(day, [])
        lessons += [""] * max(0, lesson_count - len(lessons))
        week_plan[day] = lessons[:lesson_count]

    return week_plan


def _merge_defaults(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Merge stored config-entry data with defaults and normalize shapes."""
    result = _default_data()
    if data:
        result.update(dict(data))

    lesson_count = _coerce_lesson_count(result.get(CONF_LESSON_COUNT))
    school_days = [str(day) for day in _as_list(result.get(CONF_SCHOOL_DAYS))]

    result[CONF_LESSON_COUNT] = lesson_count
    result[CONF_SCHOOL_DAYS] = school_days
    result[CONF_LESSON_TIMES] = _normalize_lesson_times(
        result.get(CONF_LESSON_TIMES),
        lesson_count,
    )
    result[CONF_SUBJECTS] = _normalize_subjects(result.get(CONF_SUBJECTS))
    result[CONF_WEEK_PLAN] = _normalize_week_plan(
        result.get(CONF_WEEK_PLAN),
        school_days,
        lesson_count,
    )

    return result


def _calendar_selector() -> selector.EntitySelector:
    """Return an entity selector for holiday calendars."""
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain="calendar", multiple=False)
    )


def _school_day_options() -> list[dict[str, str]]:
    """Return weekday options in calendar order."""
    return [{"value": key, "label": WEEKDAY_NAMES_DE[key]} for key in WEEKDAY_KEYS]


def _color_selector() -> selector.SelectSelector:
    """Return the configured subject color selector."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=SUBJECT_COLOR_OPTIONS,
            mode=selector.SelectSelectorMode.DROPDOWN,
            sort=False,
            custom_value=False,
        )
    )


def _subject_options(subjects: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Return subject names for weekday lesson selection."""
    names = sorted(
        {
            str(subject.get("name", "")).strip()
            for subject in subjects
            if str(subject.get("name", "")).strip()
        },
        key=str.casefold,
    )
    return [{"value": "", "label": "-"}] + [
        {"value": name, "label": name} for name in names
    ]


def _lesson_time_field(index: int, suffix: str) -> str:
    """Return a lesson-time schema key."""
    return f"lesson_{index + 1}_{suffix}"


def _lesson_field(index: int) -> str:
    """Return a lesson schema key."""
    return f"lesson_{index + 1}"


class _StundenplanFlowMixin:
    """Shared implementation for config and options flows."""

    _data: dict[str, Any]
    _day_index: int
    _subject_index: int

    def _initialize_flow(self, data: Mapping[str, Any] | None = None) -> None:
        self._data = _merge_defaults(data)
        self._subject_index = 0
        self._day_index = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Collect general schedule settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            self._data[CONF_LESSON_COUNT] = _coerce_lesson_count(
                user_input.get(CONF_LESSON_COUNT)
            )
            self._data[CONF_SCHOOL_DAYS] = [
                str(day) for day in _as_list(user_input.get(CONF_SCHOOL_DAYS))
            ]

            if not self._data[CONF_SCHOOL_DAYS]:
                errors[CONF_SCHOOL_DAYS] = "required"
            else:
                await self._async_prepare_unique_id()
                return await self.async_step_lesson_times()

        return self.async_show_form(
            step_id="user",
            data_schema=self._user_schema(),
            errors=errors,
        )

    async def async_step_lesson_times(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Collect lesson start and end times."""
        self._data = _merge_defaults(self._data)
        lesson_count = int(self._data[CONF_LESSON_COUNT])

        if user_input is not None:
            self._data[CONF_LESSON_TIMES] = [
                {
                    "start": user_input[_lesson_time_field(index, "start")],
                    "end": user_input[_lesson_time_field(index, "end")],
                }
                for index in range(lesson_count)
            ]
            return await self.async_step_subject_count()

        return self.async_show_form(
            step_id="lesson_times",
            data_schema=self._lesson_times_schema(),
        )

    async def async_step_subject_count(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Collect how many subjects should be configured."""
        if user_input is not None:
            subject_count = int(user_input[CONF_SUBJECT_COUNT])
            subjects = list(self._data.get(CONF_SUBJECTS) or [])

            while len(subjects) < subject_count:
                subjects.append(_default_subject())

            self._data[CONF_SUBJECTS] = subjects[:subject_count]
            self._subject_index = 0
            return await self.async_step_subject()

        return self.async_show_form(
            step_id="subject_count",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SUBJECT_COUNT,
                        default=len(self._data.get(CONF_SUBJECTS) or DEFAULT_SUBJECTS),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=MAX_SUBJECT_COUNT,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    )
                }
            ),
        )

    async def async_step_subject(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Collect one subject at a time."""
        subjects = list(self._data.get(CONF_SUBJECTS) or [])
        subject_count = len(subjects)

        if self._subject_index >= subject_count:
            self._day_index = 0
            return await self.async_step_day_plan()

        if user_input is not None:
            subjects[self._subject_index] = {
                "name": str(user_input[CONF_NAME]).strip(),
                "icon": user_input.get(CONF_ICON) or DEFAULT_SUBJECT_ICON,
                "color": user_input.get(CONF_COLOR) or "primary",
            }
            self._data[CONF_SUBJECTS] = subjects
            self._subject_index += 1
            return await self.async_step_subject()

        current = subjects[self._subject_index]
        return self.async_show_form(
            step_id="subject",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=current.get("name", ""),
                    ): str,
                    vol.Required(
                        CONF_ICON,
                        default=current.get("icon", DEFAULT_SUBJECT_ICON),
                    ): selector.IconSelector(),
                    vol.Required(
                        CONF_COLOR,
                        default=current.get("color", "primary"),
                    ): _color_selector(),
                }
            ),
            description_placeholders={
                "current": str(self._subject_index + 1),
                "total": str(subject_count),
            },
        )

    async def async_step_day_plan(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Collect lesson subjects for each configured weekday."""
        self._data = _merge_defaults(self._data)
        school_days: list[str] = self._data[CONF_SCHOOL_DAYS]
        lesson_count = int(self._data[CONF_LESSON_COUNT])

        if self._day_index >= len(school_days):
            return self._create_entry()

        day = school_days[self._day_index]
        week_plan = dict(self._data.get(CONF_WEEK_PLAN) or {})

        if user_input is not None:
            week_plan[day] = [
                user_input.get(_lesson_field(index), "")
                for index in range(lesson_count)
            ]
            self._data[CONF_WEEK_PLAN] = week_plan
            self._day_index += 1
            return await self.async_step_day_plan()

        current = list(week_plan.get(day) or [])
        current += [""] * max(0, lesson_count - len(current))
        subject_options = _subject_options(self._data.get(CONF_SUBJECTS) or [])

        fields = {}
        for index in range(lesson_count):
            fields[
                vol.Optional(
                    _lesson_field(index),
                    default=current[index] if index < len(current) else "",
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=subject_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    sort=False,
                    custom_value=False,
                )
            )

        return self.async_show_form(
            step_id="day_plan",
            data_schema=vol.Schema(fields),
            description_placeholders={"day": WEEKDAY_NAMES_DE.get(day, day)},
        )

    async def _async_prepare_unique_id(self) -> None:
        """Prepare uniqueness checks for config flows."""

    def _create_entry(self):
        """Create the final flow entry."""
        raise NotImplementedError

    def _user_schema(self) -> vol.Schema:
        """Return the general settings schema."""
        return vol.Schema(
            {
                vol.Required(
                    CONF_CHILD_NAME,
                    default=self._data.get(CONF_CHILD_NAME, ""),
                ): str,
                vol.Required(
                    CONF_LESSON_COUNT,
                    default=self._data.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=MAX_LESSON_COUNT,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_SCHOOL_DAYS,
                    default=self._data.get(CONF_SCHOOL_DAYS, WEEKDAY_KEYS[:5]),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=_school_day_options(),
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_HOLIDAY_CALENDAR,
                    default=self._data.get(CONF_HOLIDAY_CALENDAR),
                ): _calendar_selector(),
            }
        )

    def _lesson_times_schema(self) -> vol.Schema:
        """Return the lesson-time schema."""
        lesson_count = int(self._data[CONF_LESSON_COUNT])
        fields = {}

        for index in range(lesson_count):
            current = self._data[CONF_LESSON_TIMES][index]
            fields[
                vol.Required(
                    _lesson_time_field(index, "start"),
                    default=current.get("start", ""),
                )
            ] = selector.TimeSelector()
            fields[
                vol.Required(
                    _lesson_time_field(index, "end"),
                    default=current.get("end", ""),
                )
            ] = selector.TimeSelector()

        return vol.Schema(fields)


class StundenplanConfigFlow(
    _StundenplanFlowMixin,
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle the config flow for Stundenplan."""

    VERSION = 1

    def __init__(self) -> None:
        self._initialize_flow()

    async def _async_prepare_unique_id(self) -> None:
        child_name = str(self._data.get(CONF_CHILD_NAME) or "").strip().casefold()
        await self.async_set_unique_id(f"{DOMAIN}_{child_name}")
        self._abort_if_unique_id_configured()

    def _create_entry(self):
        return self.async_create_entry(
            title=f"{NAME} {self._data[CONF_CHILD_NAME]}",
            data=self._data,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "StundenplanOptionsFlow":
        return StundenplanOptionsFlow(config_entry)


class StundenplanOptionsFlow(
    _StundenplanFlowMixin,
    config_entries.OptionsFlow,
):
    """Handle options for an existing Stundenplan entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        merged = dict(config_entry.data or {})
        merged.update(dict(config_entry.options or {}))
        self._config_entry = config_entry
        self._initialize_flow(merged)

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Start the options flow."""
        return await self.async_step_user(user_input)

    def _create_entry(self):
        return self.async_create_entry(title="", data=self._data)
