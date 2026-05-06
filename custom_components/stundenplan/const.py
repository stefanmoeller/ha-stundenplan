DOMAIN = "stundenplan"

CONF_CHILD_NAME = "child_name"
CONF_LESSON_COUNT = "lesson_count"
CONF_SCHOOL_DAYS = "school_days"
CONF_HOLIDAY_CALENDAR = "holiday_calendar"
CONF_LESSON_TIMES = "lesson_times"
CONF_SUBJECTS = "subjects"
CONF_WEEK_PLAN = "week_plan"

DEFAULT_CHILD_NAME = "Fritz"
DEFAULT_LESSON_COUNT = 6
DEFAULT_SCHOOL_DAYS = ["mon", "tue", "wed", "thu", "fri"]

WEEKDAY_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WEEKDAY_NAMES = {
    "mon": "Montag",
    "tue": "Dienstag",
    "wed": "Mittwoch",
    "thu": "Donnerstag",
    "fri": "Freitag",
    "sat": "Samstag",
    "sun": "Sonntag",
}
WEEKDAY_SHORT_NAMES = {
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

HA_COLOR_OPTIONS = [
    {"value": "red", "label": "Rot", "hex": "#F44336", "rgb": [244, 67, 54]},
    {"value": "pink", "label": "Pink", "hex": "#E91E63", "rgb": [233, 30, 99]},
    {"value": "purple", "label": "Lila", "hex": "#9C27B0", "rgb": [156, 39, 176]},
    {"value": "deep-purple", "label": "Dunkellila", "hex": "#673AB7", "rgb": [103, 58, 183]},
    {"value": "indigo", "label": "Indigo", "hex": "#3F51B5", "rgb": [63, 81, 181]},
    {"value": "blue", "label": "Blau", "hex": "#2196F3", "rgb": [33, 150, 243]},
    {"value": "light-blue", "label": "Hellblau", "hex": "#03A9F4", "rgb": [3, 169, 244]},
    {"value": "cyan", "label": "Cyan", "hex": "#00BCD4", "rgb": [0, 188, 212]},
    {"value": "teal", "label": "Türkis", "hex": "#009688", "rgb": [0, 150, 136]},
    {"value": "green", "label": "Grün", "hex": "#4CAF50", "rgb": [76, 175, 80]},
    {"value": "light-green", "label": "Hellgrün", "hex": "#8BC34A", "rgb": [139, 195, 74]},
    {"value": "lime", "label": "Limette", "hex": "#CDDC39", "rgb": [205, 220, 57]},
    {"value": "yellow", "label": "Gelb", "hex": "#FFEB3B", "rgb": [255, 235, 59]},
    {"value": "amber", "label": "Bernstein", "hex": "#FFC107", "rgb": [255, 193, 7]},
    {"value": "orange", "label": "Orange", "hex": "#FF9800", "rgb": [255, 152, 0]},
    {"value": "deep-orange", "label": "Tieforange", "hex": "#FF5722", "rgb": [255, 87, 34]},
    {"value": "brown", "label": "Braun", "hex": "#795548", "rgb": [121, 85, 72]},
    {"value": "light-grey", "label": "Hellgrau", "hex": "#BDBDBD", "rgb": [189, 189, 189]},
    {"value": "grey", "label": "Grau", "hex": "#9E9E9E", "rgb": [158, 158, 158]},
    {"value": "dark-grey", "label": "Dunkelgrau", "hex": "#616161", "rgb": [97, 97, 97]},
    {"value": "blue-grey", "label": "Blaugrau", "hex": "#607D8B", "rgb": [96, 125, 139]},
]
HA_COLOR_HEX = {item["value"]: item["hex"] for item in HA_COLOR_OPTIONS}
HA_COLOR_LABELS = {item["value"]: item["label"] for item in HA_COLOR_OPTIONS}
HA_COLOR_RGB = {item["value"]: item["rgb"] for item in HA_COLOR_OPTIONS}

DEFAULT_SUBJECTS = [
    {"name": "Mathe", "icon": "mdi:calculator", "color": "blue"},
    {"name": "Deutsch", "icon": "mdi:book-open-page-variant", "color": "pink"},
    {"name": "Englisch", "icon": "mdi:translate", "color": "green"},
    {"name": "Sport", "icon": "mdi:soccer", "color": "orange"},
    {"name": "Religion", "icon": "mdi:church", "color": "purple"},
]
