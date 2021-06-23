import bigjson
import os, sys, csv, re
from shapely.geometry import shape

# For a GeoJSON file that starts like this:
#{"type":"FeatureCollection",
# "features":
#       [{"geometry": {"type": "Point", "coordinates": [-79.81167781195305, 40.5421828403599]},
#         "type": "Feature", 
#         "id": 0,
#         "properties": {"STATUS": "ACTIVE", "ADDRESS_ID": 1, "EDIT_DATE": "2013-06-13", "PARENT_ID": 0, "MUNICIPALI": "HARMAR", "STATE": "PA", "COUNTY": "ALLEGHENY", "SOURCE": "GDR", "FULL_ADDRE": "118 ORR AVE", "ADDR_NUM": "118", "POINT_Y": 447055.300166, "STREET_ID": 17808, "FEATURE_KE": 1, "ADDRESS_TY": 0, "POINT_X": 1395563.70007, "ST_TYPE": "AVE", "ST_NAME": "ORR", "ZIP_CODE": "15024"}
#         },
#         {"geometry": {"type": "Point", "coordinates": [-79.80979744004718, 40.542211378710846]}, "type": "Feature", "id": 1, "properties": {"STATUS": "ACTIVE", "ADDRESS_ID": 2, "EDIT_DATE": "2013-06-13", "PARENT_ID": 0, "MUNICIPALI": "HARMAR", "STATE": "PA", "COUNTY": "ALLEGHENY", "SOURCE": "GDR", "FULL_ADDRE": "121 WILSON AVE", "ADDR_NUM": "121", "POINT_Y": 447053.500053, "STREET_ID": 26070, "FEATURE_KE": 2, "ADDRESS_TY": 0, "POINT_X": 1396086.40006, "ST_TYPE": "AVE", "ST_NAME": "WILSON", "ZIP_CODE": "15024"...
#

# We want to convert it to something like this:
# FEATURE_KE,ADDRESS_ID,PARENT_ID,STREET_ID,ADDRESS_TY,STATUS,ADDR_NUM_P,ADDR_NUM,ADDR_NUM_S,ST_PREMODI,ST_PREFIX,ST_PRETYPE,ST_NAME,ST_TYPE,ST_POSTMOD,UNIT_TYPE,UNIT,FLOOR,MUNICIPALI,COUNTY,STATE,ZIP_CODE,COMMENT,EDIT_DATE,EDIT_USER,SOURCE,EXP_FLAG,FULL_ADDRE,ST_SUFFIX,POINT_X,POINT_Y,LAT,LNG
#1,1,0,17808,0,ACTIVE, ,118, , , , ,ORR,AVE, , , , ,HARMAR,ALLEGHENY,PA,15024, ,2013-06-13 00:00:00, ,GDR, ,118 ORR AVE, ,1395563.70007,447055.300166,447055.3000382334,1395563.6999376416
#...

# For this to work on a humongous GeoJSON file, the file will have to be loaded and parsed in chunks. We use the marvelous bigjson library to achieve the lazy loading and parsing.

def write_or_append_to_csv(filename, list_of_dicts, keys=None):
    if not os.path.isfile(filename):
        with open(filename, 'w') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, extrasaction='ignore', lineterminator='\n')
            dict_writer.writeheader()
            dict_writer.writerows(list_of_dicts)
    with open(filename, 'a') as output_file:
        dict_writer = csv.DictWriter(output_file, keys, extrasaction='ignore', lineterminator='\n')
        #dict_writer.writeheader()
        dict_writer.writerows(list_of_dicts)

def detect_keys(list_of_dicts):
    keys = set()
    for row in list_of_dicts:
        keys = set(row.keys()) | keys
    keys = sorted(list(keys)) # Sort them alphabetically, in the absence of any better idea.
    # [One other option would be to extract the field names from the schema and send that
    # list as the third argument to write_to_csv.]
    print(f'Extracted keys: {keys}')
    return keys

def convert_geometry_to_wkt(geometry):
    """Return the well-known text representation of
    the geometry from the GeoJSON element."""
    g_shape = shape(geometry)
    return g_shape.wkt

def convert_geojson_row_to_dict(row):
    d = dict(row['properties'])
    geometry = row['geometry']
    if geometry['type'] == 'Point':
        d['LNG'], d['LAT'] = geometry['coordinates']
    d['wkt'] = convert_geometry_to_wkt(geometry)
    return d

def handle_big_json_file(filepath):
    if filepath[-8:].lower() == '.geojson':
        output_filepath = re.sub('.geojson$', '.csv', filepath, flags=re.IGNORECASE)
    else:
        output_filepath = 'output.csv'

    with open(filepath, 'rb') as f:
        j = bigjson.load(f)
        features = j['features']
        csv_rows = []
        count = 0

        # Pre-detect keys to avoid ignoring keys that may not be
        # be in the first batch of features. This significantly increases
        # the processing time, but something like this is necessary to
        # handle cases where the very last GeoJSON feature adds a
        # previously unseen key.
        keys = set()
        for feature in features:
            keys = set(feature['properties'].keys()) | keys
        keys = list(keys)
        keys = sorted(list(keys)) # Sort them alphabetically, in the absence of any better idea.
        # [One other option would be to extract the field names from the schema and send that
        # list as the third argument to write_to_csv.]
        print(f'Extracted keys: {keys}')

        for feature in features:
            csv_row = convert_geojson_row_to_dict(feature.to_python())
            csv_rows.append(csv_row)
            if len(csv_rows) == 1000:
                count += len(csv_rows)
                write_or_append_to_csv(output_filepath, csv_rows, keys)
                csv_rows = []
                print(f"{count} rows have been written.")

if len(sys.argv) == 1:
    print("Please specify the filename or filepath of the GeoJSON file to be converted to a CSV file.")
else:
    if len(sys.argv) > 2:
        print("Only the first filename/path is going to be converted to CSV.")
    filepath = sys.argv[1]
    handle_big_json_file(filepath)
