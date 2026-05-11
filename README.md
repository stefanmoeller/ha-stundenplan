# Stundenplan

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
[![Validate](https://github.com/stefanmoeller/ha-stundenplan/actions/workflows/validate.yml/badge.svg)](https://github.com/stefanmoeller/ha-stundenplan/actions/workflows/validate.yml)

`Stundenplan` ist eine Home-Assistant-Integration fuer Schulstundenplaene.  
Ab Version `0.2.0` enthaelt das Projekt **kein eigenes Lovelace-Frontend mehr**.  
Die Darstellung erfolgt ueber Standardkarten mit Sensor-Zustand und -Attributen.

## Features

- UI-basierte Konfiguration in Home Assistant
- ein Sensor pro Stundenplan
- Schultage, Stundenzeiten, Faecher und Wochenplan konfigurierbar
- optionaler Ferien-/Feiertagskalender
- strukturierte Sensor-Attribute fuer Dashboards, Templates und Automationen
- deutsch/englische Uebersetzungen fuer den Integrationsdialog

## Voraussetzungen

- Home Assistant `2024.6.0` oder neuer
- optional: Kalender-Entitaet fuer schulfreie Tage

## Installation (HACS)

1. HACS -> `Custom repositories`
2. Repository hinzufuegen:

   ```text
   https://github.com/stefanmoeller/ha-stundenplan
   ```

3. Kategorie `Integration` waehlen
4. `Stundenplan` installieren
5. Home Assistant neu starten
6. Integration unter `Einstellungen > Geraete & Dienste` hinzufuegen

## Konfiguration

Der Assistent fuehrt durch:

1. Name, max. Stundenzahl, Schultage, optionaler Ferienkalender
2. Beginn/Ende je Stunde
3. Anzahl Faecher
4. Name/Icon/Farbe pro Fach
5. Fach je Stunde und Wochentag

## Sensor-Attribute

| Attribut | Beschreibung |
| --- | --- |
| `child_name` | Name des Stundenplans |
| `weekday`, `weekday_name`, `weekday_short` | aktueller Wochentag |
| `date` | Datum im ISO-Format |
| `is_school_day` | aktueller Tag ist Schultag |
| `is_free_day` | Ferienkalender ist aktiv |
| `free_reason` | Grund aus Kalender |
| `school_end` | Ende der letzten Stunde am aktuellen Tag |
| `lessons` | Stunden am aktuellen Tag |
| `lesson_times` | alle konfigurierten Stundenzeiten |
| `lesson_count` | Anzahl Unterrichtsstunden |
| `school_days` | konfigurierte Schultage |
| `subjects` | konfigurierte Faecher |
| `days` | kompletter Wochenplan |
| `day_subjects` | Faecher je Tag als Mapping (`mon`..`sun`) |
| `day_school_end` | Schulende je Tag als Mapping (`mon`..`sun`) |
| `monday_subjects` ... `sunday_subjects` | flache Faecherliste pro Wochentag |
| `monday_school_end` ... `sunday_school_end` | flaches Schulende pro Wochentag |

---

## Dashboard Beispiele (DE)

### 1) Today (aktueller Tag)

```yaml
type: markdown
title: Stundenplan heute
content: >-
  {% set e = 'sensor.stundenplan_fritz' %}
  **{{ state_attr(e, 'weekday_name') or 'Heute' }}**

  {% if state_attr(e, 'is_free_day') %}
  Schulfrei{% if state_attr(e, 'free_reason') %}: {{ state_attr(e, 'free_reason') }}{% endif %}
  {% elif not state_attr(e, 'is_school_day') %}
  Kein Schultag
  {% elif (state_attr(e, 'lessons') or []) | count == 0 %}
  Keine Stunden
  {% else %}
  Schulende: {{ state_attr(e, 'school_end') or '-' }}

  {% for l in state_attr(e, 'lessons') or [] %}
  - {{ l.start or '--:--' }}-{{ l.end or '--:--' }} | {{ l.subject }}
  {% endfor %}
  {% endif %}
```

### 2) Wochen-Tabelle

```yaml
type: markdown
title: Wochenplan (Tabelle)
content: >-
  {% set e = 'sensor.stundenplan_fritz' %}
  {% set days = state_attr(e, 'days') or {} %}
  {% set school_days = state_attr(e, 'school_days') or [] %}

  | Tag | Stunden | Schulende |
  | --- | --- | --- |
  {% for d in school_days %}
  {% set row = days.get(d, {}) %}
  | {{ row.name or d }} | {{ (row.lessons or []) | map(attribute='subject') | join(', ') or '-' }} | {{ row.school_end or '-' }} |
  {% endfor %}
```

### 3) Wochen-Karten (Grid)

```yaml
type: grid
columns: 2
square: false
cards:
  - type: entity
    entity: sensor.stundenplan_fritz
    name: Status
  - type: entities
    title: Heute
    entities:
      - type: attribute
        entity: sensor.stundenplan_fritz
        attribute: weekday_name
        name: Wochentag
      - type: attribute
        entity: sensor.stundenplan_fritz
        attribute: school_end
        name: Schulende
      - type: attribute
        entity: sensor.stundenplan_fritz
        attribute: free_reason
        name: Grund schulfrei
```

---

## Dashboard Examples (EN)

### 1) Today

```yaml
type: markdown
title: School schedule today
content: >-
  {% set e = 'sensor.stundenplan_fritz' %}
  **{{ state_attr(e, 'weekday_name') or 'Today' }}**

  {% if state_attr(e, 'is_free_day') %}
  No school{% if state_attr(e, 'free_reason') %}: {{ state_attr(e, 'free_reason') }}{% endif %}
  {% elif not state_attr(e, 'is_school_day') %}
  Not a school day
  {% elif (state_attr(e, 'lessons') or []) | count == 0 %}
  No lessons
  {% else %}
  School end: {{ state_attr(e, 'school_end') or '-' }}

  {% for l in state_attr(e, 'lessons') or [] %}
  - {{ l.start or '--:--' }}-{{ l.end or '--:--' }} | {{ l.subject }}
  {% endfor %}
  {% endif %}
```

### 2) Week Table

```yaml
type: markdown
title: Weekly schedule (table)
content: >-
  {% set e = 'sensor.stundenplan_fritz' %}
  {% set days = state_attr(e, 'days') or {} %}
  {% set school_days = state_attr(e, 'school_days') or [] %}

  | Day | Lessons | School end |
  | --- | --- | --- |
  {% for d in school_days %}
  {% set row = days.get(d, {}) %}
  | {{ row.name or d }} | {{ (row.lessons or []) | map(attribute='subject') | join(', ') or '-' }} | {{ row.school_end or '-' }} |
  {% endfor %}
```

### 3) Week Cards (Grid)

```yaml
type: grid
columns: 2
square: false
cards:
  - type: entity
    entity: sensor.stundenplan_fritz
    name: Status
  - type: entities
    title: Today
    entities:
      - type: attribute
        entity: sensor.stundenplan_fritz
        attribute: weekday_name
        name: Weekday
      - type: attribute
        entity: sensor.stundenplan_fritz
        attribute: school_end
        name: School end
      - type: attribute
        entity: sensor.stundenplan_fritz
        attribute: free_reason
        name: Free-day reason
```

## Support

Issues und Feature-Wuensche bitte ueber GitHub melden:
https://github.com/stefanmoeller/ha-stundenplan/issues
