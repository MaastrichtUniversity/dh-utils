# schemaValidator

* **Name:** schemaValidator
* **Description**: Validate if the input schema is following the DataHub schema rules
* **Developer:** Dean Linssen, DataHub Maastricht University
* **License:** ?
* **Depends on:** cedar-parsing-utils

## How to install the dependencies
```
sudo apt-get install python3-virtualenv
python3 -m virtualenv --python=python3 venv3
source ./venv3/bin/activate

pip install -e git+https://github.com/MaastrichtUniversity/cedar-parsing-utils.git@develop#egg=cedar-parsing-utils

# To exit the venv
# deactivate
```

# Usage
```
source ./venv3/bin/activate

python3 validate_schema.py [path to the schema file]

optional arguments:
  -h, --help            show this help message and exit
```
