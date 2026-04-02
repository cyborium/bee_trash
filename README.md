# BEE Abfuhrkalender

Müllabfuhrkalender für die Stadt Emden

Nie wieder den Müllkalender suchen: BEE Abfuhrkalender bringt alle Abholtermine der 17 Emder Stadtbezirke direkt in Home Assistant. Sensoren, Kalender und Binary Sensor pro Abfallart - bereit für Automationen und Dashboards.

> **Disclaimer**
> This is an unofficial, private open-source project and is not affiliated
> with, endorsed by, or in any way connected to BEE Emden
> (Bau- und Entsorgungsbetrieb Emden).
> BEE Emden is not responsible for this integration and provides no support for it.
> All trademarks and company names are the property of their respective owners.

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cyborium&repository=bee_trash&category=integration)

## Installation

### HACS (empfohlen)

1. HACS öffnen → Integrationen → Rechts oben auf die drei Punkte → Benutzerdefinierte Repositories
2. Repository-URL eingeben: `https://github.com/cyborium/bee_trash`
3. Kategorie: Integration
4. Integration installieren und Home Assistant neustarten

### Manuell

1. Den Ordner `custom_components/bee_trash/` nach `<config>/custom_components/bee_trash/` kopieren
2. Home Assistant neustarten

## Einrichtung

1. Einstellungen → Geräte & Dienste → Integration hinzufügen → **BEE Abfuhrkalender** suchen
2. Im Konfigurationsdialog den gewünschten **Bezirk** auswählen
3. Fertig

## Was du bekommst

Pro Bezirk werden automatisch 9 Entitäten erstellt (3 Abfallarten × 3 Plattformen):

| Plattform | Pro Abfallart | Beispiel |
|-----------|---------------|----------|
| Sensor | Nächstes Abholdatum als Datum | `sensor.restabfall_nachste_abholung` |
| Binary Sensor | `true` wenn morgen Abholung | `binary_sensor.restabfall_abholung_morgen` |
| Kalender | Alle Abholdaten als Ereignisse | `calendar.restabfall` |

## Mindestanforderungen

- Home Assistant ≥ 2024.1.0
- HACS (für die empfohlene Installationsmethode)

## Unterstützte Abfallarten

- Restabfall
- Papier
- Gelber Sack

## Unterstützte Bezirke

Alle 17 Stadtbezirke von Emden: Altstadt, Larrelt, Constantia, Port Arthur / Transvaal, Hafen, Barenburg / Harsweg, Twixlum / Wybelsum / Logumer Vorwerk / Knock, Conrebbersweg, Wolthusen, AOK-Viertel / Großfaldern, Kleinfaldern / Herrentor, Friesland / Borssum / Hilmarsum, Amtsgerichtsviertel und Ringstraße / Am Tonnenhof, Jarssum / Widdelswehr, Petkum Uphusen / Tholenswehr / Marienwehr, Kulturviertel (nördlich/südlich Früchteburger Weg).

## Datenquelle

Die Abfuhrdaten werden aus den offiziellen ICS-Kalenderfeeds der BEE Emden bezogen. Die Abfrage erfolgt alle 12 Stunden zusätzlich zu einer täglichen Aktualisierung um 7 Uhr.

## Bekannte Einschränkungen

- **Nur ICS-Datenquelle:** Es gibt aktuell keinen PDF-Fallback, falls die ICS-Feeds nicht verfügbar sind.
- **Drei Abfallarten:** Restabfall, Papier und Gelber Sack. Bioabfall wird derzeit nicht unterstützt.
- **Nur Emden:** Die Integration ist spezifisch für die 17 Stadtbezirke von Emden und funktioniert nicht für andere Städte.
- **Ein Bezirk pro Einrichtung:** Für mehrere Bezirke muss die Integration mehrfach hinzugefügt werden.
- **Veraltete Daten in der Diagnose-Ansicht:** Die Geräte-Seite in Home Assistant kann in der Diagnose-Sektion veraltete Abholdaten anzeigen (z. B. Monate zurückliegend). **Dies betrifft nur die Diagnose-Ansicht.** Die tatsächlichen Entitätszustände sind korrekt und können unter **Entwicklungswerkzeuge → Zustände** eingesehen werden. Das ist die maßgebliche Datenquelle für Automationen, Dashboards und alle anderen Auslesungen. Die Ursache liegt vermutlich in der Home Assistant-Frontend-Darstellung von `SensorDeviceClass.DATE`-Entitäten auf der Geräte-Seite. Es handelt sich um ein kosmetisches Anzeige-Problem — die Integration liefert korrekte Daten. Es gibt aktuell keine bestätigte Umgehungslösung.

## Fehlerbehebung

**Keine Daten in den Sensoren:**
1. Prüfe die Home Assistant-Protokolle (`Einstellungen` → `System` → `Protokolle`) nach Einträgen von `bee_trash`.
2. Stelle sicher, dass der gewählte Bezirk korrekt ist.
3. Entferne die Integration und füge sie erneut hinzu.

**Falsche Abholdaten:**
- Die Daten stammen direkt von BEE Emden. Prüfe zunächst den [BEE-Abfuhrkalender](https://www.bee-emden.de/abfall/entsorgungssystem/abfuhrkalender/) auf Aktualität.
- Öffne ein [Issue](https://github.com/cyborium/bee_trash/issues) mit dem betroffenen Bezirk und dem erwarteten vs. angezeigten Datum.

**Integration wird nicht gefunden:**
- Stelle sicher, dass Home Assistant nach der Installation neu gestartet wurde.
- Bei manueller Installation: Prüfe, dass der Ordner `custom_components/bee_trash/` die Datei `manifest.json` enthält.

## Credits & Acknowledgements

This integration is based on [aha_trash](https://github.com/soundstorm/aha_trash)
by [soundstorm](https://github.com/soundstorm), licensed under the
[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html).

The original implementation provided the foundation for the Home Assistant
integration structure, config flow, and entity setup.
It was adapted and extended for the waste collection schedule of
BEE Emden (Bau- und Entsorgungsbetrieb Emden).

This project is also released under the GNU General Public License v3.0.
