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
    parser.add_argument("-p", "--project", default=None, action='store',
                        required=False, type=str,
                        help="iRODS project ID. If none is given, will default to P000000001.")
    parser.add_argument("-c", "--collection", default=None, action='store',
                        required=False, type=str,
                        help="iRODS collection ID. If none is given, will default to C000000001.")
    parser.add_argument("-f", "--source_file", default=None, action='store',
                        required=True, type=str, help="Local path to source file.")
    parser.add_argument("-n", "--name", default=None, action='store',
                        required=True, type=str, help="Name of file, how it should be stored in iRODS.")
    parser.add_argument("-d", "--dest", default=None, action='store',
                        required=True, type=str, help="Destination path to locally store file from iRODS.")


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
    valid = {"yes": True, "y": True, "no": False, "n": False}
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


# Slightly modified, based on "check_irods_resources_availability.py" Nagios check
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
        elif resource.status == None:
            log.warning(f"Resource '{resource.name}' seems available! (undefined status)")
        else:
            log.warning(f"Resource '{resource.name}' has status '{resource.status}'")


def check_path(session, project_id, collection_id):
    project = f"/nlmumc/projects/{project_id}"
    projectCollection = f"/nlmumc/projects/{project_id}/{collection_id}"
    if not session.collections.exists(project):
        log.error(f"The project {project_id} does not exist. Make sure it exists before proceeding!")
        log.error(f"Exiting...")
        sys.exit(0)
    elif not session.collections.exists(projectCollection):
        log.error(f"The collection {collection_id} does not exist. Make sure it exists before proceeding!")
        log.error(f"Exiting...")
        sys.exit(0)


def check_file(session, project_id, collection_id, name):
    filePath = f"/nlmumc/projects/{project_id}/{collection_id}/{name}"
    if session.data_objects.exists(filePath):
        yesNo = query_yes_no(f"The filename '{name}' already exists at the chosen path, do you want to overwrite the file?")
        if yesNo == False:
            log.info(f"Exiting... Please retry using a different filename.")
            sys.exit(0)


def put_file(session, project_id, collection_id, name, source_file):
    path = f"/nlmumc/projects/{project_id}/{collection_id}/{name}"
    log.info(f"Putting file: '{name}' from project: '{project_id}', collection: '{collection_id}'")
    try:
        session.data_objects.put(source_file, path)
        log.info(f"Put operation successful!")
    except (
            exception.DataObjectDoesNotExist,
            exception.SYS_FILE_DESC_OUT_OF_RANGE,
            KeyError,
    ):
        log.error(f"Error: during put operation. Exiting...")
        sys.exit(0)


def get_file(session, project_id, collection_id, name, dest):
    path = f"/nlmumc/projects/{project_id}/{collection_id}/{name}"
    log.info(f"Getting file: '{name}' from project: '{project_id}', collection: '{collection_id}'")
    log.info(f"Destination: '{dest}'")
    try:
        session.data_objects.get(path, dest)
        log.info(f"Get operation successful!")
    except (
            exception.OVERWRITE_WITHOUT_FORCE_FLAG,
            KeyError,
    ):
        log.error(f"Get operation failed! Make sure the filename does not exist at the destination.")
        return 1


def remove_file(session, project_id, collection_id, name):
    path = f"/nlmumc/projects/{project_id}/{collection_id}/{name}"
    log.info(f"Removing file: '{name}' from project: '{project_id}', collection: '{collection_id}'")
    try:
        session.data_objects.get(path).unlink(force = True)
        log.info(f"Removal successful!")
    except (
            exception.DataObjectDoesNotExist,
            KeyError,
    ):
        log.error(f"Error: during remove operation. Exiting...")
        sys.exit(0)


def main():
    args = parse_args()
    with irods_session(args.env_file) as session:
        log.info("START: checking resource availability...")
        check_resources(session, args.exclusions)
        log.info("START: putting, getting and removing file...")
        if args.project is None:
            args.project = "P000000001"
            log.warning("No project given, defaulting to project: P000000001")
        if args.collection is None:
            args.collection = "C000000001"
            log.warning("No collection given, defaulting to collection: C000000001")
        check_path(session, args.project, args.collection)
        check_file(session, args.project, args.collection, args.name)
        put_file(session, args.project, args.collection, args.name, args.source_file)
        if get_file(session, args.project, args.collection, args.name, args.dest) == 1:
            remove_file(session, args.project, args.collection, args.name)
        else:
            remove_file(session, args.project, args.collection, args.name)

if __name__ == "__main__":
    try:
        log = setup_custom_logger(__name__, logging.INFO)
        sys.exit(not main())
    except KeyboardInterrupt:
        sys.exit(2)
