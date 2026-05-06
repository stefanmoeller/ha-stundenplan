# Stundenplan

Einfacher Stundenplan fuer Home Assistant: Konfiguration und Karten.

- Autor: @stefanmoeller
- Repository: https://github.com/stefanmoeller/ha-stundenplan
- Domain: `stundenplan`
- Version: `0.1.0`
- Icon: `mdi:timetable`

## Funktionen

- UI-basierte Konfiguration ueber den Home-Assistant-Config-Flow
- Eine Entity pro Stundenplan, z. B. `sensor.stundenplan_fritz`
- Multi-Instanz-faehig: mehrere Stundenplaene erzeugen unterschiedliche Entity-IDs
- Stundenzeiten global pro Stundenplan
- Schultage konfigurierbar
- Ferienkalender optional
- Faecher mit Name, Icon und Farbe
- Wochenplan je Wochentag
- Lovelace-Karte mit den Modi `today`, `table` und `cards`
- Theme-faehige Darstellung
- Uebersetzungen vorbereitet: Deutsch und Englisch

## Installation

1. ZIP entpacken.
2. Ordner kopieren:
   - `custom_components/stundenplan` nach `/config/custom_components/stundenplan`
   - `www/school-schedule-card.js` nach `/config/www/school-schedule-card.js`
3. Home Assistant komplett neu starten.
4. Integration hinzufuegen:
   - Einstellungen -> Geraete & Dienste -> Integration hinzufuegen -> Stundenplan
5. Lovelace-Ressource hinzufuegen:
   - URL: `/local/school-schedule-card.js`
   - Typ: `JavaScript-Modul`
6. Browsercache leeren.

## Karten

### Heute

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: today
title: Schule heute
```

### Ohne Titel

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: today
show_title: false
```

### Wochenplan als Tabelle

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: table
title: Stundenplan
```

### Wochenplan als Karten

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: cards
title: Stundenplan
```

### Navigation

```yaml
type: custom:school-schedule-card
entity: sensor.stundenplan_fritz
mode: today
tap_action:
  action: navigate
  navigation_path: /lovelace/stundenplan
```

## Hinweise zur Farbauswahl

Die Faecher nutzen den Home-Assistant-Color-RGB-Selector. Dadurch wird die gewaehlt Farbe in der Konfiguration sichtbar. Die Karte rendert die Farbe als echten farbigen Icon-Kreis.

Eine native Home-Assistant-Auswahlliste mit farbigen Swatches pro Listeneintrag ist im Standard-Config-Flow nicht frei gestaltbar. Deshalb nutzt diese Version den sichtbaren Farbpicker statt einer reinen Namensliste.

## Geplant

- Visueller Lovelace-Karteneditor ab Version 0.2.0
- Verbesserte Mehrsprachigkeit
- Optional Matrix-Editor fuer den Wochenplan
