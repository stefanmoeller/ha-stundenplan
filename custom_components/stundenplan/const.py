"""Constants for the Stundenplan integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "stundenplan"
NAME: Final = "Stundenplan"
VERSION: Final = "0.3.0"
DEFAULT_CHILD_NAME: Final = "Fritz"
DEFAULT_SUBJECT_ICON: Final = "mdi:book-open-page-variant"
DEFAULT_LESSON_COUNT: Final = 6
MAX_LESSON_COUNT: Final = 12
MAX_SUBJECT_COUNT: Final = 30

CONF_CHILD_NAME = "child_name"
CONF_LESSON_COUNT = "lesson_count"
CONF_SCHOOL_DAYS = "school_days"
CONF_HOLIDAY_CALENDAR = "holiday_calendar"
CONF_LESSON_TIMES = "lesson_times"
CONF_SUBJECTS = "subjects"
CONF_WEEK_PLAN = "week_plan"

WEEKDAY_KEYS: Final = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAY_NAMES_DE = {
    "mon": "Montag",
    "tue": "Dienstag",
    "wed": "Mittwoch",
    "thu": "Donnerstag",
    "fri": "Freitag",
    "sat": "Samstag",
    "sun": "Sonntag",
}
WEEKDAY_SHORT_DE = {
    "mon": "Mo",
    "tue": "Di",
    "wed": "Mi",
    "thu": "Do",
    "fri": "Fr",
    "sat": "Sa",
    "sun": "So",
}

DEFAULT_LESSON_TIMES = [
    {"start": "08:15", "end": "09:00"},
    {"start": "09:00", "end": "09:45"},
    {"start": "10:15", "end": "11:00"},
    {"start": "11:00", "end": "11:45"},
    {"start": "12:00", "end": "12:45"},
    {"start": "12:50", "end": "13:35"},
]

COLOR_VALUES = {
    "primary": "var(--primary-color)",
    "accent": "var(--accent-color)",
    "red": "#F44336",
    "pink": "#E91E63",
    "purple": "#9C27B0",
    "deep_purple": "#673AB7",
    "indigo": "#3F51B5",
    "blue": "#2196F3",
    "light_blue": "#03A9F4",
    "cyan": "#00BCD4",
    "teal": "#009688",
    "green": "#4CAF50",
    "light_green": "#8BC34A",
    "lime": "#CDDC39",
    "yellow": "#FFEB3B",
    "amber": "#FFC107",
    "orange": "#FF9800",
    "deep_orange": "#FF5722",
    "brown": "#795548",
    "grey": "#9E9E9E",
    "blue_grey": "#607D8B",
    "black": "#000000",
    "white": "#FFFFFF",
}

SUBJECT_COLOR_OPTIONS = [
    {"value": "primary", "label": "Primärfarbe"},
    {"value": "accent", "label": "Akzentfarbe"},
    {"value": "red", "label": "Rot"},
    {"value": "pink", "label": "Rosa"},
    {"value": "purple", "label": "Violett"},
    {"value": "deep_purple", "label": "Dunkelviolett"},
    {"value": "indigo", "label": "Indigo"},
    {"value": "blue", "label": "Blau"},
    {"value": "light_blue", "label": "Hellblau"},
    {"value": "cyan", "label": "Cyan"},
    {"value": "teal", "label": "Türkis"},
    {"value": "green", "label": "Grün"},
    {"value": "light_green", "label": "Hellgrün"},
    {"value": "lime", "label": "Lime"},
    {"value": "yellow", "label": "Gelb"},
    {"value": "amber", "label": "Bernstein"},
    {"value": "orange", "label": "Orange"},
    {"value": "deep_orange", "label": "Tieforange"},
    {"value": "brown", "label": "Braun"},
    {"value": "grey", "label": "Grau"},
    {"value": "blue_grey", "label": "Blaugrau"},
    {"value": "black", "label": "Schwarz"},
    {"value": "white", "label": "Weiß"},
]

DEFAULT_SUBJECTS = [
    {"name": "Mathe", "icon": "mdi:calculator", "color": "blue"},
    {"name": "Deutsch", "icon": "mdi:book-open-page-variant", "color": "pink"},
    {"name": "Englisch", "icon": "mdi:translate", "color": "green"},
    {"name": "Sport", "icon": "mdi:soccer", "color": "orange"},
    {"name": "Religion", "icon": "mdi:church", "color": "purple"},
]
