# iRODSingestvalidator
A tool for DevOps to verify if a dropzone has been ingested properly.
You need the pre-ingest-document (located inside the HNAS iRODS container in /var/log/irods-pre-ingest/) 
and an active iinit connection with access to the destination collection

Run it in a screen on large collections. The error output will be printed into a file `/tmp/errors_file`

## Configuration
The iRODS user environment file `~/.irods/irods_environment.json` is being used to 
configure the iRODS connection. Prepare your environment using `iinit`.

## Running

```bash
usage: python3 irodsIngestValidator.py [-h] [-f FILE]

optional arguments:
  -h, --help                          show this help message and exit
  -f FILE, --file FILE                The path to the pre-ingest-document (default: None)
``` 
 
 ## TODOs
 
 * Properly print the errors into a user-defined output file