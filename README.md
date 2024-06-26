# Open Data Münster Skript Repo
Skripte zum Konvertieren von Dateien. Diese Skripte werden derzeit 1x im Jahr manuell ausgeführt.

--------------

## Elektroauto Ladesäulen

[Siehe Unterverzeichnis `ladesaeulen/`](ladesaeulen)

--------------

## Tischtennisplatten Standorte

[Siehe Unterverzeichnis `tischtennisplatten/`](tischtennisplatten)

--------------

## AWM Container Standorte

### Vorbereitung
Die Container Standort-JSON-Dateien müssen manuell über die AWM-Webseite heruntergeladen werden, und ins Verzeichnis `data/` abgelegt werden. Anleitung dazu: Siehe Kommentare in der Sourcecode-Datei.

### Ausführung
```
python3 awm-container2023.py
```

--------------

## Kalender politische Gremiensitzungen

Liest die Gremientermine aus der OParl Schnittstelle des Ratsinformationssystems der Stadt Münster aus und schreibt sie in eine `ical`-Datei.

Läuft relativ lange, da die Sitzungstermine Seitenweise zurückgegeben werden, und auch ur-alte Termine drin sind, die automatisch rausgefiltert werden.

### Vorbereitung

Die Variable `CONFIG_EXPORT_YEAR` muss im Sourcecode auf das aktuelle Jahr gesetzt werden.

### Ausführung

```bash
# Virtuelles Environment mit dem Namen "venv" initialisieren falls noch kein venv-Unterverzeichnis da ist:
python3 -m venv venv

# venv fürs aktuelle Projekt aktivieren
source venv/bin/activate

python3 oparl_generate_gremienkalender_ical.py
```

--------------

## Stadtwerke ÖPNV POIs

Liest die verschiedenen POIs ein (Barrierefreie Haltestellen, Park&Ride, Bike&Ride, ...) und speichert sie als GeoJSON und als CSV.

[Siehe Unterverzeichnis `stadtwerke/`](stadtwerke)

--------------

## Klimadashboard

Die Datendatei wird 1x im Monat per Cronjob neu generiert und eingecheckt.
Auf folgender Url werden die Metadaten der aktuellen Datei zurückgeliefert: https://opendata.stadt-muenster.de/api/3/action/resource_show?id=klimadashboard

[Skript siehe Unterverzeichnis `klimadashboard/`](klimadashboard)

Schritte zum Ausführen:
* Inputdatei abglegen als `05515000_csv_klimarelevante_daten.csv`
* Skript starten `python3 split_datafile.py`
* Aktuelle Datei im Repository einchecken `git add klimadata.csv;git commit ...;git push;`