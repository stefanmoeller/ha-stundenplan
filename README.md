# Stundenplan

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
[![Validate](https://github.com/stefanmoeller/ha-stundenplan/actions/workflows/validate.yml/badge.svg)](https://github.com/stefanmoeller/ha-stundenplan/actions/workflows/validate.yml)

**Stundenplan** ist eine Home-Assistant-Integration für Schulstundenpläne. Sie erstellt pro konfiguriertem Stundenplan eine Sensor-Entität und liefert eine Lovelace Custom Card für die Tages- oder Wochenansicht mit.

## Funktionen

- Konfiguration vollständig über die Home-Assistant-Oberfläche
- ein Sensor pro Stundenplan
- frei konfigurierbare Unterrichtszeiten
- auswählbare Schultage
- optionaler Ferien- oder Feiertagskalender
- Schulfächer mit Name, Icon und Farbe
- Wochenplan mit bis zu 12 Unterrichtsstunden pro Tag
- Lovelace Custom Card mit den Modi `today`, `table` und `cards`
- deutsche und englische Übersetzungen
- vorbereitet für HACS als Custom Repository

## Voraussetzungen

- Home Assistant `2024.6.0` oder neuer
- HACS, falls die Installation über den Home Assistant Community Store erfolgen soll
- optional: eine Kalender-Entität für Ferien, Feiertage oder schulfreie Tage

## Installation über HACS

1. Öffne HACS in Home Assistant.
2. Wähle **Custom repositories**.
3. Füge dieses Repository hinzu:

   ```text
   https://github.com/stefanmoeller/ha-stundenplan
   ```

4. Wähle als Kategorie **Integration**.
5. Installiere **Stundenplan**.
6. Starte Home Assistant neu.
7. Füge die Integration unter **Einstellungen > Geräte & Dienste > Integration hinzufügen > Stundenplan** hinzu.

Die Lovelace Card wird mit der Integration ausgeliefert. Lege in Home Assistant unter **Einstellungen > Dashboards > Ressourcen** eine Ressource an:

```yaml
url: /stundenplan/school-schedule-card.js
type: module
```

## Manuelle Installation

1. Kopiere `custom_components/stundenplan` nach `/config/custom_components/stundenplan`.
2. Starte Home Assistant neu.
3. Füge die Integration unter **Einstellungen > Geräte & Dienste > Integration hinzufügen > Stundenplan** hinzu.
4. Füge die Lovelace-Ressource hinzu:

   ```yaml
   url: /stundenplan/school-schedule-card.js
   type: module
   ```

Für bestehende Dashboards kann die klassische `/local`-Variante weiter genutzt werden. Kopiere dafür `www/school-schedule-card.js` nach `/config/www/school-schedule-card.js` und verwende:

```yaml
url: /local/school-schedule-card.js
type: module
```

## Konfiguration

Der Einrichtungsdialog führt durch alle notwendigen Schritte:

1. Name des Stundenplans, Anzahl der Unterrichtsstunden, Schultage und optionaler Ferienkalender
2. Beginn und Ende jeder Unterrichtsstunde
3. Anzahl der Schulfächer
4. Name, Icon und Farbe pro Fach
5. Fächerbelegung pro Schultag

Die Konfiguration kann später über **Einstellungen > Geräte & Dienste > Stundenplan > Konfigurieren** angepasst werden.

## Lovelace Card

### Tagesansicht

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: today
title: Stundenplan
```

### Wochenansicht als Tabelle

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: table
title: Stundenplan
```

### Wochenansicht als Karten

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: cards
title: Stundenplan
```

### Ohne Kartentitel

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: today
show_title: false
```

### Navigation beim Antippen

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: today
tap_action:
  action: navigate
  navigation_path: /lovelace/stundenplan
```

## Card-Optionen

| Option | Typ | Standard | Beschreibung |
| --- | --- | --- | --- |
| `entity` | string | erforderlich | Sensor-Entität der Integration |
| `mode` | string | `today` | `today`, `table`, `cards` oder `card` |
| `title` | string | `Stundenplan` | Titel der Lovelace Card |
| `show_title` | boolean | `true` | blendet den Titel ein oder aus |
| `tap_action` | object | optional | unterstützt `navigate` mit `navigation_path` |

## Sensor-Attribute

Die Sensor-Entität liefert neben dem aktuellen Status strukturierte Attribute für Dashboards, Templates und Automationen.

| Attribut | Beschreibung |
| --- | --- |
| `child_name` | Name des Stundenplans |
| `weekday`, `weekday_name`, `weekday_short` | aktueller Wochentag |
| `date` | aktuelles Datum im ISO-Format |
| `is_school_day` | ob der aktuelle Tag ein konfigurierter Schultag ist |
| `is_free_day` | ob der Ferienkalender aktuell aktiv ist |
| `free_reason` | Meldung oder Name des aktiven Kalendereintrags |
| `school_end` | Ende der letzten Unterrichtsstunde des Tages |
| `lessons` | Unterrichtsstunden des aktuellen Tages |
| `lesson_times` | konfigurierte Unterrichtszeiten |
| `lesson_count` | Anzahl der Unterrichtsstunden |
| `school_days` | konfigurierte Schultage |
| `subjects` | konfigurierte Fächer mit Icon und Farbe |
| `days` | vollständiger Wochenplan |

## HACS-Veröffentlichung

Das Repository ist als HACS Custom Repository vorbereitet:

- `custom_components/stundenplan/manifest.json` enthält die erforderlichen Metadaten.
- `hacs.json` liegt im Repository-Root.
- Alle zur Integration gehörenden Laufzeitdateien liegen unter `custom_components/stundenplan/`.
- Die Lovelace Card wird über `/stundenplan/school-schedule-card.js` aus dem Integrationspaket ausgeliefert.
- `.github/workflows/validate.yml` prüft das Repository mit HACS und Hassfest.

Für eine Aufnahme in die Standard-Repositories von HACS sind zusätzlich ein öffentliches GitHub-Repository, aktivierte Issues, passende Topics, ein Release, bestandene Validierungs-Workflows und ein passender Eintrag in `home-assistant/brands` erforderlich.

## Entwicklung

Nach Änderungen sollten mindestens diese Prüfungen laufen:

```bash
python -m compileall custom_components/stundenplan
python -m json.tool custom_components/stundenplan/manifest.json
python -m json.tool hacs.json
```

Auf GitHub übernehmen HACS Action und Hassfest die repositorynahen Validierungen.

## Support

Fehler und Vorschläge bitte über die GitHub Issues melden. Bitte dabei Home-Assistant-Version, Integrationsversion, relevante Logs und eine kurze Reproduktion angeben.
