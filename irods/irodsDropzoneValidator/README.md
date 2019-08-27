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
  -t COLLECTION, --target COLLECTION  Target iRODS collection to validate against (default: None)
  -q, --quiet                         Hide progress and only show errors (default: False)
  -v, --verbose                       Be extra verbose (default: False)
  -c, --continue                      Continue on validation error (default: False)
  -p n, --parallel n                  Number of parallel processes running checksum (default: 1)
``` 
 
 ## TODOs
 
 * Build a minimal check, where just file existence and perhaps file size is checked
 * Update progress bar during checksum byte reading for more accurate progress
 * Calculate also the iRODS checksum when missing
 * Build a resume option, to resume a failed run (cache checksum results?)