
# Anleitung zum Aktualisieren der PV-Anlagen-der-Stadt-Münster-Datei

Die wird vom Skript "split_datafile.py" benötigt

```bash
# Erzeuge die python Datei aus dem Juypter Notebook
jupyter nbconvert --to python generate_pv_anlagen.ipynb

# Schreibe die Datei `pv_anlagen_stadt_muenster.csv`
python3 generate_pv_anlagen.py

```