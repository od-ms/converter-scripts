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

