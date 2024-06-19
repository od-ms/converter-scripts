# Anleitung Tischtennisplatten

Dieses Verzeichnis enthält ein Skript, das Exportdateien aus verschiedenen Fachanwendungen kombiniert, um daraus eine Datei mit den (ungefähren) Geokoordinaten aller öffentlichen Tischtennisplatten im Stadtgebiet von Münster zu erstellen.

Das Skript kombiniert die Liste der Tischtennisplatten, die keine Geokoordinaten enthält, mit den Standorten der Spielplätze und den Standorten der Schulen, die beide mit Geokoordinaten vorliegen. Dadurch entsteht eine **angenäherte** Liste mit allen Tischtennisplatten-Standorten.

## Vorbereitung
1. `Tischtennisplatten2024.csv` -> Die Tischtennisplatten-Datendatei vom Grünflächenamt (ohne Geokoordinaten)
2. `Schulen.csv` -> Open Data Liste aller Schulstandorte in Münster (mit Geokoordinaten-Punkte)
3. `Spielplaetze_2022.csv` -> Open Data Liste aller Spielplätze in Münster (mit Geokoordinaten-Polygone)

## Ausführung

Python Skript per Shell ausführen:
```bash
python3 combine_datasets.py

   ... es folgt eine lange Log-Ausgabe ..

# ...
#<2024-06-19 14:37:23,478 INFO> 278 Found xxx
#<2024-06-19 14:37:23,479 INFO> 279 Found yyy
#<2024-06-19 14:37:23,479 WARNING> Filtered 19 Datasets because not Tischtennisplatte: [...]
#<2024-06-19 14:37:23,479 INFO> GEOJSON_DATA: Got 260 Datasets
#<2024-06-19 14:37:23,479 INFO> Writing GeoJSON...
#<2024-06-19 14:37:23,480 INFO> FeatureCollection size: 260
#<2024-06-19 14:37:23,480 INFO> Writing file 'tischtennisplatten_muenster.geojson'
```

**Ergebnis:**\
Die zwei Datendateien `tischtennisplatten_muenster.[csv|geojson]` sollten erzeugt worden sein.
