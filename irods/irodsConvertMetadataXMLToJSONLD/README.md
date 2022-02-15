# irodsConvertMetadataXMLToJSONLD

* **Name:** irodsConvertMetadataXMLToJSONLD
* **Description**: Convert local or existing metadata.xml to json-ld based on the DataHub_extended_schema
* **Developer:** Jonathan Mélius, DataHub Maastricht University
* **License:** ?
* **Depends on:** irods-rule-wrapper

## How to install the dependencies
```
sudo apt-get install python3-virtualenv
python3 -m virtualenv --python=python3 venv3
source ./venv3/bin/activate

pip install jsonschema
pip install pytz
pip install -e git+https://github.com/MaastrichtUniversity/irods-rule-wrapper.git@release/customizable_metadata#egg=irods-rule-wrapper

# To exit the venv
# deactivate
```

# Before usage
1. Edit the `update_existing_collections.py` file and change the token inside the `schema_url` variable. Example 
    ```
    schema_url = "https://raw.githubusercontent.com/MaastrichtUniversity/dh-mdr/release/customizable_metadata/core/static/assets/schemas/DataHub_extended_schema.json?token=YOUR_TOKEN_HERE"
    ```
1. Make necessary changes to the `assets/creators_info_mapping.json` file. This file is for users for which the creator info cannot be retrieved from iCAT.

# Usage
```
source ./venv3/bin/activate

# To convert local metadata.xml
python3 metadata_xml_to_json.py [path to the config file] [output instance json path]
python3 metadata_xml_to_json.py config.json instance.json

# To update existing metadata.xml inside project collections
python3 update_existing_collections.py [-h] [-f] [-c] [-w] [-v]
                                      [-p PROJECT_COLLECTION_PATH]

update_existing_collections description

optional arguments:
  -h, --help            show this help message and exit
  -f, --force-flag      Overwrite existing metadata files
  -c, --commit          Commit to upload the converted file
  -w, --wipe            Wipes .metadata_versions before conversion. Asks for confirmation before doing it.
  -v, --verbose         Print the converted instance.json
  -p PROJECT_COLLECTION_PATH, --project-collection-path PROJECT_COLLECTION_PATH
                        The absolute path of the project collection to convert
```
