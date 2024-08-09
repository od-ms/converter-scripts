# Refill Stationen


Das Skript nutzt die API der OpenFairDB, um die Standorte der Refill-Stationen in Münster auszulesen. Dann legt es eine GeoJSON und eine CSV Datei mit der Liste der Standorte an.

## Ausführen
```bash
# Hole Daten von der OpenFairDb
# und erzeuge die CSV- und GeoJSON-Dateien
python3 create-csv-and-geojson.py
```

## Optional: Rohdaten auslesen

Um die JSON-Rohdaten der OpenFairDB mit einigen zusätzlichen Informationen, wie z.B. Nutzerbewertungen einer Location, in eine JSON-Datei für eigene Analysen zwischenzuspeichern, kann man folgenen Bash-Befehl verwenden:

```bash
wget 'https://api.ofdb.io/v0/search?bbox=51.927648559470114%2C7.52391815185547%2C51.98900306873843%2C7.678413391113282&text=refill%20refill-station%20refill-trinkbrunnen%20refill-sticker%20trinkwasser%20leitungswasser&categories=2cd00bebec0c48ba9db761da48678134%2C77b3c33a92554bcf8e8c2c86cedd6f6f' -O refill_stationen.json
```
