#!/usr/bin/env python3
# Skeleton based on: irodsDropzoneValidator.py

import os
import sys
import logging
import argparse
from collections import defaultdict
from irods.session import iRODSSession
from irods.models import Collection, CollectionMeta, User, UserMeta
from irods.column import Criterion
from irods.query import SpecificQuery
from irods.exception import CAT_SQL_ERR, CAT_NO_ROWS_FOUND


# SQL LIKE patterns for project collections, collections, and users.
PROJ_COLLS_PATH_LIKE = '/nlmumc/projects/P_________/C_________'
PROJS_PATH_LIKE = '/nlmumc/projects/P_________'
USERS_NOT_LIKE = 'service-%'

# TODO: is this the correct list?
# List of attribute names that we expect every project to have
PROJS_AVU_LIST = [
    'authorizationPeriodEndDate',
    'dataSteward',
    'disableArchive',
    'enableArchive',
    'enableContributorEditMetadata',
    'enableDropzoneSharing',
    'ingestResource',
    'resource',
    'responsibleCostCenter',
    'storageQuotaGb'
]

# TODO: is this the correct list?
# List of attributes names (AVUs) that we expect every project collection to have
PROJ_COLLS_AVU_LIST = [
    'creator',
    'PID',
    'title',
    'numFiles'
]

# TODO: is this the correct list?
# List of attributes name (AVUs) that we expect for every user
USERS_AVU_LIST = [
    'displayName',
    'email',
    'pendingSramInvite',
    'voPersonExternalID',
    'voPersonExternalAffiliation',
    'eduPersonUniqueID',
    'pendingDeletionProcedure'
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=100),
    )
    #parser.add_argument("-H", "--host", default=None, action='store', required=False, type=str)
    parser.add_argument("-e", "--env-file", default=None, action='store',
                        required=False, type=str, help="Path to irods environment file containing connection settings.")

    return parser.parse_args()


def setup_custom_logger(name, log_level):
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)7s - %(module)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(log_level)
    log.addHandler(handler)

    return log


def irods_session(env_file=None):
    default_env_file="~/.irods/irods_environment.json"
    # arg provided >> env var 'IRODS_ENVIRONEMNT_FILE' >> default_env_file
    if not env_file:
        try:
            env_file = os.environ["IRODS_ENVIRONMENT_FILE"]
        except KeyError:
            env_file = os.path.expanduser(default_env_file)
    try:
        # Build iRODS connection
        session = iRODSSession(irods_env_file=env_file)
    except FileNotFoundError:
        log.error(f"No \"{default_env_file}\"` found. Use iinit to make one.")
        return None

    return session


def missing_avu_sql(session, avu_name, irods_obj_type, obj_name_like=None, not_like=False):
    # depending on the iRODS object type, different tables/columns will be queried,
    # written out for the sake of explicitness
    if irods_obj_type == 'Collection':
        obj_table = 'r_coll_main'
        obj_column_name =  'coll_name'
        obj_column_id = 'coll_id'
        obj_model_name = Collection.name
    elif irods_obj_type == 'User':
        obj_table = 'r_user_main'
        obj_column_name =  'user_name'
        obj_column_id = 'user_id'
        obj_model_name = User.name
    else:
        raise Exception("iRODS object type not supported.")

    objs_found = list()
    # We begin to hackily construct our SQL query
    # See: https://github.com/irods/irods/issues/2437
    #      And ./README.md
    sql_name_constraint_and = ''
    if obj_name_like:
        sql_name_constraint_and = f"o1.{obj_column_name} {'not like' if not_like else 'like'} '{obj_name_like}' AND"
    sql_only_user_type_and = ''
    if irods_obj_type == 'User':
        # We are not interested in groups nor admins (?)
        # See: https://github.com/irods/python-irodsclient#listing-users-and-groups--calculating-group-membership
        sql_only_user_type_and = "o1.user_type_name = 'rodsuser' AND"
    sql = f"""
    SELECT {obj_column_name}
    FROM {obj_table} as o1
    WHERE {sql_name_constraint_and} {sql_only_user_type_and}
    NOT EXISTS (
        SELECT 1
        FROM {obj_table} as o2
        JOIN r_objt_metamap ON o2.{obj_column_id} = r_objt_metamap.object_id
        JOIN r_meta_main ON r_meta_main.meta_id = r_objt_metamap.meta_id
        WHERE r_meta_main.meta_attr_name = '{avu_name}'
        AND o1.{obj_column_id} = o2.{obj_column_id}
    );
    """
    log.debug("SQL QUERY:")
    log.debug(sql)
    # FIXME: concurrency! Will crash
    alias = f'sql_missing_avu_{irods_obj_type}_{avu_name}'
    columns = [obj_model_name]
    query = SpecificQuery(session, sql, alias, columns)

    query.register()
    try:
        objs_found = [result[obj_model_name] for result in query]
    except CAT_NO_ROWS_FOUND:
        objs_found = None
    finally:
        # If SQL query goes wrong, we should un-register the query.
        # This should be equivalent (?) to `iadmin rsq $alias` (where $alias is: f'sql_missing_avu_{irods_obj_type}_{avu_name}')
        query.remove()

    return objs_found


def missing_avu_non_sql(session, avu_name, irods_obj_type, obj_name_like=None, not_like=False):
    # depending on the iRODS object type, different tables/columns will be queried,
    # written out for the sake of explicitness
    if irods_obj_type == 'Collection':
        obj_model = Collection
        obj_model_meta =  CollectionMeta
    elif irods_obj_type == 'User':
        obj_model = User
        obj_model_meta = UserMeta
    else:
        raise Exception("iRODS object type not supported.")

    objs = session.query(obj_model, obj_model_meta)

    if obj_name_like:
        objs = objs.filter(Criterion(f"{'not like' if not_like else 'like'}", obj_model.name, obj_name_like))

    if irods_obj_type == 'User':
        objs = objs.filter(User.type == 'rodsuser')

    # this can probably be done more elegantly...
    objs_dict = defaultdict(int)

    for obj in objs:
        if (obj_model_meta.name, avu_name) in obj.items():
            objs_dict[obj[obj_model.name]] += 1
        else:
            objs_dict[obj[obj_model.name]] += 0

    return [k for k, v in objs_dict.items() if v == 0]


def main():
    args = parse_args()

    with irods_session(args.env_file) as session:
        # TODO .. you could refactor this a bit to avoid some duplication, but just testing for now..
        log.debug("Checking missing AVUs for projects..")
        for avu_name in PROJS_AVU_LIST:
            log.debug("Checking AVU {avu_name}..")
            #projs_missing_avu = missing_avu_non_sql(session, avu_name, 'Collection', PROJS_PATH_LIKE)
            projs_missing_avu = missing_avu_sql(session, avu_name, 'Collection', PROJS_PATH_LIKE)
            if projs_missing_avu:
                for proj in projs_missing_avu:
                    log.warn(f"Project {proj} is missing AVU \"{avu_name}\"")
            else:
                log.info(f"No project seems to be missing AVU \"{avu_name}\"")

        log.debug("Checking missing AVUs for project collections..")
        for avu_name in PROJ_COLLS_AVU_LIST:
            log.debug("Checking AVU {avu_name}..")
            #colls_missing_avu = missing_avu_non_sql(session, avu_name, 'Collection', PROJ_COLLS_PATH_LIKE)
            colls_missing_avu = missing_avu_sql(session, avu_name, 'Collection', PROJ_COLLS_PATH_LIKE)
            if colls_missing_avu:
                for coll in colls_missing_avu:
                    log.warn(f"Collection {coll} is missing AVU \"{avu_name}\"")
            else:
                log.info(f"No project collection seems to be missing AVU \"{avu_name}\"")

        log.debug("Checking missing AVUS for users..")
        for avu_name in USERS_AVU_LIST:
            log.debug("Checking AVU {avu_name}..")
            #users_missing_avu = missing_avu_non_sql(session, avu_name, 'User', USERS_NOT_LIKE, not_like=True)
            users_missing_avu = missing_avu_sql(session, avu_name, 'User', USERS_NOT_LIKE, not_like=True)
            if users_missing_avu:
                for user in users_missing_avu:
                    log.warn(f"User {user} is missing AVU \"{avu_name}\"")
            else:
                log.info(f"No user seems to be missing AVU \"{avu_name}\"")


if __name__ == "__main__":
    try:
        log = setup_custom_logger("irodsHousekeeping", logging.INFO)
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
