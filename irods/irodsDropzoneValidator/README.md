# iRODSDropzoneValidator
A tool to perform checksum validation of a dropZone against a projectCollection.

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
usage: irodsDropzoneValidator.py [-h] [-s DIR] [-d COLLECTION] [-q] [-v] [-c] [-p PARALLEL]

optional arguments:
  -h, --help                          show this help message and exit
  -s DIR, --source DIR                Source directory to check (default: None)
  -d COLLECTION, --target COLLECTION  Target iRODS collection to validate against (default: None)
  -q, --quiet                         Hide progress and only show errors (default: False)
  -v, --verbose                       Be extra verbose (default: False)
  -c, --continue                      Continue on validation error (default: False)
  -p PARALLEL, --parallel PARALLEL    Number of parallel processes running checksum (default: 1)
``` 
 