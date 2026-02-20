# Aktualisierung der Klimadashboard-Datei: 

`./update-all.sh`


## Anleitung zum Aktualisieren der PV-Anlagen-der-Stadt-Münster-Datei

Die Datei `pv_anlagen_stadt_muenster.csv` wird vom Skript "split_datafile.py" benötigt, damit in der Klimadashboard-Datendatei aktuelle Solardaten auftauchen. 

Wenn man das Jupyter Notebook aktualisiert hat, kann man die Update-Datei folgendermaßen neu generieren: 

```bash
# Erzeuge die python Datei aus dem Juypter Notebook
jupyter nbconvert --to python generate_pv_anlagen.ipynb

# Schreibe die Datei `pv_anlagen_stadt_muenster.csv`
python3 generate_pv_anlagen.py

```
