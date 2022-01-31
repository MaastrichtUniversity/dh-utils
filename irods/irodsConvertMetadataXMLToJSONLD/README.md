# irodsConvertMetadataXMLToJSONLD

* **Name:** irodsConvertMetadataXMLToJSONLD
* **Description**: Convert local or existing metadata.xml to json-ld based on the DataHub_extended_schema
* **Developer:** Jonathan Mélius, DataHub Maastricht University
* **License:** ?
* **Depends on:** irods-rule-wrapper

## How to install the dependencies
```
sudo apt-get install python3-virtualenv
virtualenv --python=python3 venv3
source ./venv3/bin/activate

pip install jsonschema
pip install pytz
pip install -e git+https://github.com/MaastrichtUniversity/irods-rule-wrapper.git@release/customizable_metadata#egg=irods-rule-wrapper

# To exit the venv
# deactivate
```

# Usage
```
source ./venv3/bin/activate

# To convert local metadata.xml
python3 metadata_xml_to_json.py [path to the config file] [output instance json path]
python3 metadata_xml_to_json.py config.json instance.json

# To update existing metadata.xml inside project collections
python3 update_existing_collections.py [-h] [-f] [-c] [-v]
                                      [-p PROJECT_COLLECTION_PATH]

update_existing_collections description

optional arguments:
  -h, --help            show this help message and exit
  -f, --force-flag      Overwrite existing metadata files
  -c, --commit          Commit to upload the converted file
  -v, --verbose         Print the converted instance.json
  -p PROJECT_COLLECTION_PATH, --project-collection-path PROJECT_COLLECTION_PATH
                        The absolute path of the project collection to convert
```
