from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
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
    DOMAIN,
    HA_COLOR_RGB,
    WEEKDAY_NAMES,
    WEEKDAY_ORDER,
)


def _calendar_options(hass) -> list[dict[str, str]]:
    options = [{"value": "", "label": "Kein Kalender"}]
    for entity_id in sorted(hass.states.async_entity_ids("calendar")):
        state = hass.states.get(entity_id)
        label = state.name if state and state.name else entity_id
        options.append({"value": entity_id, "label": f"{label} ({entity_id})"})
    return options


def _color_to_rgb(value: Any) -> list[int]:
    if isinstance(value, list) and len(value) >= 3:
        return [int(value[0]), int(value[1]), int(value[2])]
    if isinstance(value, str) and value in HA_COLOR_RGB:
        return HA_COLOR_RGB[value]
    return HA_COLOR_RGB["blue-grey"]


def _normalize_color_value(value: Any) -> list[int]:
    return _color_to_rgb(value)


def _normalize_subjects(subjects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for subject in subjects:
        name = str(subject.get("name", "")).strip()
        key = name.casefold()
        if not name or key in seen:
            continue
        seen.add(key)
        cleaned.append(
            {
                "name": name,
                "icon": str(subject.get("icon", "mdi:book-open-page-variant")).strip() or "mdi:book-open-page-variant",
                "color": _normalize_color_value(subject.get("color", HA_COLOR_RGB["blue-grey"])),
            }
        )
    return sorted(cleaned, key=lambda item: item["name"].casefold())


def _subject_select_options(subjects: list[dict[str, Any]]) -> list[dict[str, str]]:
    options = [{"value": "", "label": "Keine Stunde / frei"}]
    for subject in sorted(subjects, key=lambda item: str(item.get("name", "")).casefold()):
        name = str(subject.get("name", "")).strip()
        if name:
            options.append({"value": name, "label": name})
    return options


def _base_data(entry: config_entries.ConfigEntry | None = None) -> dict[str, Any]:
    if entry is None:
        return {}
    data = dict(entry.data)
    data.update(entry.options)
    return data


def _entry_title(data: dict[str, Any]) -> str:
    name = str(data.get(CONF_CHILD_NAME, DEFAULT_CHILD_NAME)).strip() or DEFAULT_CHILD_NAME
    return f"Stundenplan {name}"


def _entry_unique_id(data: dict[str, Any]) -> str:
    name = str(data.get(CONF_CHILD_NAME, DEFAULT_CHILD_NAME)).strip() or DEFAULT_CHILD_NAME
    return f"stundenplan_{slugify(name) or 'default'}"


class StundenplanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._current_day_index = 0
        self._current_subject_index = 0
        self._subjects_buffer: list[dict[str, Any]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data.update(user_input)
            if not self._data.get(CONF_CHILD_NAME):
                self._data[CONF_CHILD_NAME] = DEFAULT_CHILD_NAME
            return await self.async_step_lesson_times()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CHILD_NAME, default=DEFAULT_CHILD_NAME): selector.TextSelector(),
                    vol.Required(CONF_LESSON_COUNT, default=DEFAULT_LESSON_COUNT): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=12, step=1, mode=selector.NumberSelectorMode.BOX)
                    ),
                    vol.Required(CONF_SCHOOL_DAYS, default=DEFAULT_SCHOOL_DAYS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[{"value": d, "label": WEEKDAY_NAMES[d]} for d in WEEKDAY_ORDER],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Optional(CONF_HOLIDAY_CALENDAR, default=""): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=_calendar_options(self.hass), mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                }
            ),
        )

    async def async_step_lesson_times(self, user_input: dict[str, Any] | None = None):
        lesson_count = int(self._data.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT))
        if user_input is not None:
            self._data[CONF_LESSON_TIMES] = [
                {"start": user_input[f"lesson_{i}_start"], "end": user_input[f"lesson_{i}_end"]}
                for i in range(1, lesson_count + 1)
            ]
            return await self.async_step_subject_count()

        fields = {}
        for i in range(1, lesson_count + 1):
            default_time = DEFAULT_LESSON_TIMES[i - 1] if i <= len(DEFAULT_LESSON_TIMES) else {"start": "08:00", "end": "08:45"}
            fields[vol.Required(f"lesson_{i}_start", default=default_time["start"])] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TIME)
            )
            fields[vol.Required(f"lesson_{i}_end", default=default_time["end"])] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TIME)
            )
        return self.async_show_form(step_id="lesson_times", data_schema=vol.Schema(fields))

    async def async_step_subject_count(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data["subject_count"] = int(user_input["subject_count"])
            return await self.async_step_subjects()

        return self.async_show_form(
            step_id="subject_count",
            data_schema=vol.Schema(
                {
                    vol.Required("subject_count", default=len(DEFAULT_SUBJECTS)): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=30, step=1, mode=selector.NumberSelectorMode.BOX)
                    )
                }
            ),
        )

    async def async_step_subjects(self, user_input: dict[str, Any] | None = None):
        self._current_subject_index = 0
        self._subjects_buffer = []
        return await self.async_step_subject_detail()

    async def async_step_subject_detail(self, user_input: dict[str, Any] | None = None):
        subject_count = int(self._data.get("subject_count", len(DEFAULT_SUBJECTS)))
        idx = self._current_subject_index

        if user_input is not None:
            self._subjects_buffer.append(
                {
                    "name": user_input.get("subject_name", ""),
                    "icon": user_input.get("subject_icon", "mdi:book-open-page-variant"),
                    "color": _normalize_color_value(user_input.get("subject_color", HA_COLOR_RGB["blue-grey"])),
                }
            )
            self._current_subject_index += 1
            if self._current_subject_index >= subject_count:
                self._data[CONF_SUBJECTS] = _normalize_subjects(self._subjects_buffer)
                self._data.pop("subject_count", None)
                self._current_day_index = 0
                self._data[CONF_WEEK_PLAN] = {}
                return await self._next_day_step()
            return await self.async_step_subject_detail()

        default = DEFAULT_SUBJECTS[idx] if idx < len(DEFAULT_SUBJECTS) else {"name": "", "icon": "mdi:book-open-page-variant", "color": "blue-grey"}
        return self.async_show_form(
            step_id="subject_detail",
            data_schema=vol.Schema(
                {
                    vol.Required("subject_name", default=default.get("name", "")): selector.TextSelector(),
                    vol.Required("subject_icon", default=default.get("icon", "mdi:book-open-page-variant")): selector.IconSelector(),
                    vol.Required("subject_color", default=_color_to_rgb(default.get("color", "blue-grey"))): selector.ColorRGBSelector(),
                }
            ),
            description_placeholders={"number": str(idx + 1), "total": str(subject_count)},
        )

    async def _next_day_step(self):
        school_days = list(self._data.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS))
        if self._current_day_index >= len(school_days):
            await self.async_set_unique_id(_entry_unique_id(self._data))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=_entry_title(self._data), data=self._data)
        return await self.async_step_weekday(None, day=school_days[self._current_day_index])

    async def async_step_weekday(self, user_input: dict[str, Any] | None = None, day: str | None = None):
        school_days = list(self._data.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS))
        if day is None:
            day = school_days[self._current_day_index]
        lesson_count = int(self._data.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT))

        if user_input is not None:
            self._data[CONF_WEEK_PLAN][day] = [user_input.get(f"lesson_{i}_subject", "") for i in range(1, lesson_count + 1)]
            self._current_day_index += 1
            return await self._next_day_step()

        options = _subject_select_options(self._data.get(CONF_SUBJECTS, []))
        fields = {}
        for i in range(1, lesson_count + 1):
            fields[vol.Optional(f"lesson_{i}_subject", default="")] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
            )
        return self.async_show_form(
            step_id="weekday",
            data_schema=vol.Schema(fields),
            description_placeholders={"day": WEEKDAY_NAMES.get(day, day)},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return StundenplanOptionsFlow(config_entry)


class StundenplanOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._data: dict[str, Any] = _base_data(config_entry)
        self._current_day_index = 0
        self._current_subject_index = 0
        self._subjects_buffer: list[dict[str, Any]] = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_lesson_times()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CHILD_NAME, default=self._data.get(CONF_CHILD_NAME, DEFAULT_CHILD_NAME)): selector.TextSelector(),
                    vol.Required(CONF_LESSON_COUNT, default=int(self._data.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT))): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=12, step=1, mode=selector.NumberSelectorMode.BOX)
                    ),
                    vol.Required(CONF_SCHOOL_DAYS, default=self._data.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS)): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[{"value": d, "label": WEEKDAY_NAMES[d]} for d in WEEKDAY_ORDER],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Optional(CONF_HOLIDAY_CALENDAR, default=self._data.get(CONF_HOLIDAY_CALENDAR, "")): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=_calendar_options(self.hass), mode=selector.SelectSelectorMode.DROPDOWN)
                    ),
                }
            ),
        )

    async def async_step_lesson_times(self, user_input: dict[str, Any] | None = None):
        lesson_count = int(self._data.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT))
        existing = self._data.get(CONF_LESSON_TIMES, DEFAULT_LESSON_TIMES)
        if user_input is not None:
            self._data[CONF_LESSON_TIMES] = [
                {"start": user_input[f"lesson_{i}_start"], "end": user_input[f"lesson_{i}_end"]}
                for i in range(1, lesson_count + 1)
            ]
            return await self.async_step_subject_count()

        fields = {}
        for i in range(1, lesson_count + 1):
            default_time = existing[i - 1] if i <= len(existing) else {"start": "08:00", "end": "08:45"}
            fields[vol.Required(f"lesson_{i}_start", default=default_time["start"])] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TIME)
            )
            fields[vol.Required(f"lesson_{i}_end", default=default_time["end"])] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TIME)
            )
        return self.async_show_form(step_id="lesson_times", data_schema=vol.Schema(fields))

    async def async_step_subject_count(self, user_input: dict[str, Any] | None = None):
        subjects = self._data.get(CONF_SUBJECTS, DEFAULT_SUBJECTS)
        if user_input is not None:
            self._data["subject_count"] = int(user_input["subject_count"])
            return await self.async_step_subjects()
        return self.async_show_form(
            step_id="subject_count",
            data_schema=vol.Schema(
                {
                    vol.Required("subject_count", default=len(subjects)): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=30, step=1, mode=selector.NumberSelectorMode.BOX)
                    )
                }
            ),
        )

    async def async_step_subjects(self, user_input: dict[str, Any] | None = None):
        self._current_subject_index = 0
        self._subjects_buffer = []
        return await self.async_step_subject_detail()

    async def async_step_subject_detail(self, user_input: dict[str, Any] | None = None):
        subject_count = int(self._data.get("subject_count", len(self._data.get(CONF_SUBJECTS, DEFAULT_SUBJECTS))))
        existing = self._data.get(CONF_SUBJECTS, DEFAULT_SUBJECTS)
        idx = self._current_subject_index

        if user_input is not None:
            self._subjects_buffer.append(
                {
                    "name": user_input.get("subject_name", ""),
                    "icon": user_input.get("subject_icon", "mdi:book-open-page-variant"),
                    "color": _normalize_color_value(user_input.get("subject_color", HA_COLOR_RGB["blue-grey"])),
                }
            )
            self._current_subject_index += 1
            if self._current_subject_index >= subject_count:
                self._data[CONF_SUBJECTS] = _normalize_subjects(self._subjects_buffer)
                self._data.pop("subject_count", None)
                self._current_day_index = 0
                self._data[CONF_WEEK_PLAN] = {}
                return await self._next_day_step()
            return await self.async_step_subject_detail()

        default = existing[idx] if idx < len(existing) else {"name": "", "icon": "mdi:book-open-page-variant", "color": "blue-grey"}
        return self.async_show_form(
            step_id="subject_detail",
            data_schema=vol.Schema(
                {
                    vol.Required("subject_name", default=default.get("name", "")): selector.TextSelector(),
                    vol.Required("subject_icon", default=default.get("icon", "mdi:book-open-page-variant")): selector.IconSelector(),
                    vol.Required("subject_color", default=_color_to_rgb(default.get("color", "blue-grey"))): selector.ColorRGBSelector(),
                }
            ),
            description_placeholders={"number": str(idx + 1), "total": str(subject_count)},
        )

    async def _next_day_step(self):
        school_days = list(self._data.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS))
        if self._current_day_index >= len(school_days):
            self.hass.config_entries.async_update_entry(self._config_entry, title=_entry_title(self._data))
            return self.async_create_entry(title="", data=self._data)
        return await self.async_step_weekday(None, day=school_days[self._current_day_index])

    async def async_step_weekday(self, user_input: dict[str, Any] | None = None, day: str | None = None):
        school_days = list(self._data.get(CONF_SCHOOL_DAYS, DEFAULT_SCHOOL_DAYS))
        if day is None:
            day = school_days[self._current_day_index]
        lesson_count = int(self._data.get(CONF_LESSON_COUNT, DEFAULT_LESSON_COUNT))
        old_plan = self._config_entry.options.get(CONF_WEEK_PLAN, self._config_entry.data.get(CONF_WEEK_PLAN, {}))

        if user_input is not None:
            self._data[CONF_WEEK_PLAN][day] = [user_input.get(f"lesson_{i}_subject", "") for i in range(1, lesson_count + 1)]
            self._current_day_index += 1
            return await self._next_day_step()

        options = _subject_select_options(self._data.get(CONF_SUBJECTS, []))
        existing_day = old_plan.get(day, [])
        fields = {}
        for i in range(1, lesson_count + 1):
            default = existing_day[i - 1] if i <= len(existing_day) else ""
            fields[vol.Optional(f"lesson_{i}_subject", default=default)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
            )
        return self.async_show_form(
            step_id="weekday",
            data_schema=vol.Schema(fields),
            description_placeholders={"day": WEEKDAY_NAMES.get(day, day)},
        )
