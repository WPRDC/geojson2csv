# geojson2csv
This is a simple Python script for extracting a CSV version of a GeoJSON file. Specifically, for each feature, it extracts whatever the "properties" field contains, as well as the latitude and longitude associated with the feature. It uses Shapely to convert each feature's geometry to the corresponding Well-Known Text format, which it adds to the CSV file in the "wkt" field. At present, it assumes that the entire GeoJSON file is a single Feature Collection.

This script uses the [henu/bigjson](https://github.com/henu/bigjson) library to handle JSON files that are bigger than the available RAM.
