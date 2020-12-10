# Background
_metadataUpdater_ can be used to update metadata in iRODS in a retrospective way. 
It starts with the wrapper script `irodsUpdater.sh` which calls the actual worker 
scripts `metadata_xml_migrate.py` to update metadata.xml files and 
`avu_migrate.sh` to update AVUs.

# Instructions

## Adding new migrations

1. Create new directory in `migrations/` with the version to migrate to
1. Add one or both of the following scripts (`metadata_xml_migrate.py` and/or `avu_migrate.sh`) 
in the `migrations/` directory.
1. Update the version variable in `localTesting.sh` and `irodsUpdater.sh` to new version

## Local testing of migrations (dry-run)

1. Create new directory in testing with version to migrate to
1. Add *.xml files tot test on to this directory
1. Run `./diff.sh -p | colordiff` to review changes

## Remote testing of migrations (on iRODS) (dry-run)

1. Get a working rodsadmin connection through iinit to iRODS server of choice
1. Run `./irodsUpdater.sh` to execute updater
1. Run `./diff.sh -p | colordiff` to review changes

## Execute mode (commit the changes to iRODS)

1. Get a working rodsadmin connection through iinit to iRODS server of choice
1. Run `./irodsUpdater.sh --commit` to execute updater in commit mode
1. Run `./diff.sh -p | colordiff` to review changes

## TODO

* TODO: Ability to continue from a previous run, or to skip broken files
* TODO: Ability to run validation XSD on results
* TODO: We should place metadata.xml version information somewhere, as iRODS metadata or in the XML itself
