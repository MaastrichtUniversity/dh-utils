# iRODSDropzoneValidator
A tool to perform checksum validation of a dropzone against a projectCollection.

## Installation
Use virtualenv to install dependencies
```bash
python3 -m venv datahub 
source datahub/bin/activate
pip install -r requirements.txt
```

## Configuration
The iRODS user environment file `~/.irods/irods_environment.json` is being used to 
configure the iRODS connection. Prepare your environment using `iinit`.

## Running

```bash
./irodsDropzoneValidator.py --help
usage: irodsDropzoneValidator.py [-h] [-s DIR] [-d COLLECTION] [-q] [-v] [-c]

optional arguments:
  -h, --help            show this help message and exit
  -s DIR, --source DIR  Source directory to check
  -d COLLECTION, --target COLLECTION
                        Target iRODS collection to validate against
  -q, --quiet           Hide progress and only show errors
  -v, --verbose         Be extra verbose
  -c, --continue        Continue on validation error
``` 
 