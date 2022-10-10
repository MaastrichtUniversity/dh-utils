import os
import sys
import logging
import argparse
from irods.session import iRODSSession
from irods.resource import iRODSResource
from irods.models import Resource
from irods import exception


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=100),
    )
    # parser.add_argument("-H", "--host", default=None, action='store', required=False, type=str)
    parser.add_argument("-e", "--env-file", default=None, action='store',
                        required=False, type=str, help="Path to irods environment file containing connection settings.")
    parser.add_argument("-x", "--exclusions", nargs="+", default="bundleResc, demoResc, rootResc", action='store',
                        required=False, type=str, help="Resources to exclude in resource availability check.")
    parser.add_argument("-f", "--source_file", default=None, action='store',
                        required=False, type=str, help="Local path to source file.")
    parser.add_argument("-n", "--name", default=None, action='store',
                        required=False, type=str, help="Name of file, how it should be stored in iRODS.")
    parser.add_argument("-d", "--dest", default=None, action='store',
                        required=False, type=str, help="Destination path to locally store file from iRODS.")
    parser.add_argument("-o", "--overwrite", required=False, action='store_true', help="Overwrite files if they exist.")
    parser.add_argument("-a", "--archive-file", required=False, action='store_true', help="Archive file to tape.")

    return parser.parse_args()


# https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": "yes", "y": "yes", "no": "no", "n": "no"}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer: '%s'" % default)

    while True:
        log.info(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            log.error(f"Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


# Skeleton (logging, irods_session) based on: irodsDropzoneValidator.py
def setup_custom_logger(name, log_level):
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)7s - %(module)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(log_level)
    log.addHandler(handler)

    return log


def irods_session(env_file=None):
    default_env_file = "~/.irods/irods_environment.json"
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
        log.error(f"No \"{default_env_file}\" found. Use iinit to make one.")
        return None

    return session


# Returns all 'replication' resources available.
def get_resources(session):
    repl_coor_rescs = session.query(Resource).filter(Resource.type == 'replication')
    repl_coor_rescs_names = [repl_resc[Resource.name] for repl_resc in repl_coor_rescs]
    log.info(f"Found Replication resource(s): {repl_coor_rescs_names}")

    return repl_coor_rescs_names


# Slightly modified, based on "check_irods_resources_availability.py" Nagios check.
# Checks all resources.
def check_resources(session, exclusions):
    resources = [iRODSResource(session.resources, query_result) for query_result in session.query(Resource).all()]
    for resource in resources:
        if exclusions and resource.name in exclusions:
            log.info(f"Resource '{resource.name}' excluded from check.")
            continue

        if resource.status == "down":
            log.error(f"Resource '{resource.name}' has status DOWN in iRODS")
        elif resource.status == "up":
            log.info(f"Resource '{resource.name}' seems available! (status: up)")
        elif resource.status is None:
            log.warning(f"Resource '{resource.name}' seems available! (undefined status)")
        else:
            log.warning(f"Resource '{resource.name}' has status '{resource.status}'")


# Make sure path exists, in this case the home folder of the user.
def check_path(session):
    path = f"/nlmumc/home/{session.username}"
    if not session.collections.exists(path):
        log.error(f"The path {path}/ does not exist. Make sure it exists before proceeding!")
        log.error(f"Exiting...")
        sys.exit(1)


# Check if file(name) already exist and ask if it is okay to overwrite it.
# If overwrite flag is passed it will overwrite if file(name) already exists.
def check_file(session, resources, name, overwrite):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    for resource in resources:
        if session.data_objects.exists(str(file_path+"_"+resource)) and overwrite is False:
            yes_no = query_yes_no(f"The filename '{name}_{resource}' already exists at {path}/, resource {resource}. Do you want to overwrite the file?")
            if yes_no == "no":
                log.info(f"Exiting... Please retry using a different filename.")
                sys.exit(1)
        elif session.data_objects.exists(str(file_path+"_"+resource)) and overwrite is True:
            log.info(f"Overwrite flag passed. Will overwrite file '{name}_{resource}' at '{path}/'")


# Put operation of file to all available 'replication' resources.
def put_file(session, resources, name, source_file):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    try:
        for resource in resources:
            log.info(f"Putting file '{name}_{resource}' to '{path}/', resource '{resource}'")
            session.data_objects.put(source_file, str(file_path+"_"+resource), destRescName=resource)
            log.info(f"Put operation to '{resource}' successful!")
    except (
            exception.DataObjectDoesNotExist,
            exception.SYS_FILE_DESC_OUT_OF_RANGE,
            exception.UNIX_FILE_CREATE_ERR,
            KeyError
    ):
        log.error(f"Error: during put operation. Exiting...")
        sys.exit(1)


# Archival of file to tape by replicating the file with destination resource 'arcRescSURF01'.
def archive_file(session, resources, name, archive_file):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    if archive_file is True:
        try:
            for resource in resources:
                log.info(f"Archiving file '{name}_{resource}' from '{path}/' to 'arcRescSURF01'")
                session.data_objects.replicate(str(file_path+"_"+resource), resource="arcRescSURF01")
                log.info(f"Archival to 'arcRescSURF01' successful!")
        except(
                exception.DataObjectDoesNotExist,
                KeyError
        ):
            log.error(f"Error during archive operation. Exiting...")
            sys.exit(1)


# Get operation of file
def get_file(session, resources, name, dest):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    try:
        for resource in resources:
            log.info(f"Getting file '{name}_{resource}' from '{path}/', resource '{resource}")
            log.info(f"Destination: '{dest}'")
            session.data_objects.get(str(file_path+"_"+resource), dest)
            log.info(f"Get operation successful!")
    except (
            exception.OVERWRITE_WITHOUT_FORCE_FLAG,
            KeyError,
    ):
        log.error(f"Get operation failed! Make sure the filename does not exist at the destination.")
        return 1


# Removal of all files based on filename, with unlink. This also removes all replicates.
def remove_file(session, resources, name):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    try:
        for resource in resources:
            log.info(f"Removing file '{name}_{resource}' from '{path}/', resource '{resource}'")
            session.data_objects.get(str(file_path+"_"+resource)).unlink(force=True)
            log.info(f"Removal from resource: '{resource}' successful!")
    except (
            exception.DataObjectDoesNotExist,
            KeyError
    ):
        log.error(f"Error: during remove operation. Exiting...")
        sys.exit(1)


def main():
    args = parse_args()
    print(args)
    with irods_session(args.env_file) as session:
        log.info("START: checking resource availability...")
        check_resources(session, args.exclusions)
        print()

        resources = get_resources(session)
        print()

        log.info("START: putting, getting and removing file...")
        check_path(session)
        check_file(session, resources, args.name, args.overwrite)
        put_file(session, resources, args.name, args.source_file)
        archive_file(session, resources, args.name, args.archive_file)
        if get_file(session, resources, args.name, args.dest) == 1:
            remove_file(session, resources, args.name)
        else:
            remove_file(session, resources, args.name)


if __name__ == "__main__":
    try:
        log = setup_custom_logger("irodsDeploymentTests", logging.INFO)
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
