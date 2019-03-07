# irodsMigrateCollection

* **Name:** irodsMigrateCollection
* **Description**: Migrates a collection from one resource to another including checksum verification
* **Developer:** Roger Niesten, DataHub Maastricht University
* **License:** ?
* **Depends on:** 
  * iRODS icommands
  * DataHub irods-ruleset
  * iRODS version 4.1.12 (not compatible with iRODS 4.2.x)

## Syntax

    ./irodsMigrateCollection.sh [options] -C collection [-R targetresource]
        
    mandatory:
      -P --PROJECT=project  the project to be migrated
      -R --RESOURCE=target  the target resource (overwrites default target resource in script)

    optional:
      -C --COLLECTION=coll  the collection to be migrated
    
    options:
      -v --verbose=level    verbose output (Debug, Info, Warning, Error)
      -d --display-logs     display logs to console 
      -y                    don't ask for confirmation
      -l --logfile=logfile  path to logfile base name (overwriting default). Example: /tmp/mylogfile

## Usage
1. Get a working _rodsadmin_ connection through `iinit` from an iRODS server of choice. 
    1. **NOTE!** that the _openProjectCollection.r_ and _closeProjectCollection.r_ rules need to be present on this 
    server in _/rules/projectCollection/_

1. **[DRY-RUN]** Test the script and review the output with 

    `./irodsMigrateCollection.sh -P P000000001 -C C000000001 -R replRescAZM01 -v DBG -d` 

1. **[COMMIT]** Execute the changes with

    `./irodsMigrateCollection.sh -P P000000001 -C C000000001 -R replRescAZM01 -v DBG -d -y --commit` 

## Logfile
By default, the logfile will be created in the current working dir. It has a name like `irodsMigrateCollection_<PROJECT><COLLECTION>_<DATE>-<TIMESTAMP>.log`.
If the logfile cannot be created in this default folder (or the override folder from the `--logfile` option), the script will notify you and write output only to stdout.