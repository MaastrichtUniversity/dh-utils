## How to run

This script expects to be run as `irods`. Meaning, it expects to find a
`~/.irods/irods_environment.json` file containing all necessary information to
"log into" iRODS. An alternative `irods_environment.json` path can be provided
via the `-e|--env-file` argument.

## How to test

You can run this script in our development/test iRODS container. For example,
you could do something like:
(*If* you are not volume mapping dh-utils on irods, which is commented out in
docker-dev/docker-compose-irods. It's easiest to uncomment it)
```
./rit.sh up -d irods
$ docker cp ./irodsHousekeeping.py corpus_irods_1:/var/lib/irods/
./rit.sh exec irods
root@irods# apt-get install python3-pip
root@irods# su - irods
irods@irods$ pip3 install python-irodsclient
irods@irods$ python3 irodsHousekeeping.py
```

Or volume map the `dh-utils` repo in `docker-compose-irods.yml`, but in `/opt/`
or somewhere like that, **not** in `/var/lib/irods/`, as
[setup_irods.py](https://github.com/irods/irods/blob/4.2.6/scripts/setup_irods.py#L232)
will try to change permissions of that file and you will have to change it back
outside the container. And if you do readonly for the mount, setup_irods.py
will crash and irods won't start.

If volume-mapping dh-utils:
```
irods@irods$ cd /opt/dh-utils/irods/irodsHousekeeping
irods@irods$ python3 irodsHousekeeping.py
```

Or also use vs-code and attach to a live container after volume mapping.

#### More quick tests..

You can (poorly) test `missing_replicated_non_sql()` by doing, for example:
```
$ itrim -N 1 -V --dryrun /nlmumc/projects/P000000014/C000000001/src/filehere
```
(After having ingested that file, etc.)
That `itrim` should leave only one replica of that file (take out `--dryrun`), and
running `missing_replicated_non_sql` function/script now should report it as a warning.

:construction: TODO: Better / easier set up and testing process for dh-utils/irods! :construction:


## Quick recap on iRODS terminology

There are 4 different types of **_iRODS objects_**:
* **_data objects_**
* **_collections_**
* **_resources_**
* **_users_**

Any directory (in the UNIX sense) in iRODS, is a **_collection_** to iRODS.

We (DataHub) have **_projects_** (e.g. `P000000001`), and **_project collections_**
(e.g. `C000000001`). Note that both **_projects_**, and **_project collections_** are
actually "directories", therefore to iRODS they are both **_collections_**.

Keep in mind that all **_data objects_** are **_iRODS objects_** but not all **_iRODS
objects_** are **_data objects_**. :)

And to rub a bit of salt into the wound, we sometimes use the word
"**_collection_**" when we mean "**_project collection_**".

About **_resources_**, there are two types:
* **Storage resources**: These are pointers to the real deal: physical storage
  devices, like S3, unix file system, etc..
* **Coordinating resources**: These are more "virtual" resources. Multiple
  "real" (storage) resources can live under one of these. There are subtypes to
  this, such as:
    * Replication
    * Round robin
    * Passthru
    * etc...?

This script looks for _coordinating resources_ of type `replication` to find
the _storage resources_ under which replicas of _data objects_ live. We do this
because we might want to ensure that there are at least 2 copies, for instance.

## non-sql vs sql

The current code includes two families of functions. Unfortunately
python-irodsclient does not provide a "not exist" statement for Queries, so
([as suggested by iRODS
developers](https://github.com/irods/irods/issues/2437)), you can use direct
SQL queries to accomplish this via `SpecificQuery`. However, these SQL queries
go **unchecked**, and we might not feel comfortable running them. If a DROP
were to snuck in there, calamity :/
Therefore a non-sql versions (potentially slower, or faster!) are provided as
well as a drop-in-place replacement.

### iRODS SQL internals

iCAT uses (or seems to use!) these tables (among others):
* `r_data_main`: **_data objects_**
* `r_coll_main`: **_collections_**
* `r_resc_main`: **_resources_**
* `r_user_main`: **_users_**
* `r_meta_main`: metadata (AVUs)
* `r_objt_metamap`: for associating **_iRODS objects_** (**_data objects_**, **_collections_**, etc) to metadata (AVUs)

## Notes
There is a 'DataObject.replica_status', which mayyybe it's always 1 when the
object is replicated? Probably not? Since I'm not sure and couldn't find
documentation, won't use.
OR, does maybe iRODS keep track of replicas some other way?

# TODO:
* Test performance of SQL vs non-SQL with bigger / actual data
* If SQL somehow faster than non-SQL, write `missing_replicated_sql`?
* Some refactoring
* Documentation
* Ended up removing code to do "Not In resource list". Just didn't seem worth it. But maybe I'm wrong?
* Output should be more uniform? Parseable?
* Check users that have: pendingSramInvite & pendingDeletionProcedure ?
* Check projects that have ingest gone wrong AVU?
