import os
import sys
import logging
import argparse
import time
import re
import hashlib
import base64
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
                        required=False, type=str, help="Resources to exclude in resource availability check."
                                                       "This does not exclude these resources for put/get operations!")
    parser.add_argument("-f", "--source_file", default=None, action='store',
                        required=True, type=str, help="Local path to source file.")
    parser.add_argument("-n", "--name", default=None, action='store',
                        required=True, type=str, help="Name of file, how it should be stored in iRODS.")
    parser.add_argument("-o", "--overwrite", required=False, action='store_true', help="Overwrite files if they exist.")

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


_LEVEL_COLORS = {
    logging.DEBUG: "\033[2m",    # dim
    logging.WARNING: "\033[33m", # yellow
    logging.ERROR: "\033[31m",   # red
}
_RESET = "\033[0m"


class ColorFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        color = _LEVEL_COLORS.get(record.levelno, "")
        return f"{color}{msg}{_RESET}" if color else msg


# Skeleton (logging, irods_session) based on: irodsDropzoneValidator.py
def setup_custom_logger(name, log_level):
    formatter = ColorFormatter(fmt="%(asctime)s - %(levelname)7s - %(module)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(log_level)
    log.addHandler(handler)
    log.propagate = False  # Prevent duplicate output via the root logger

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
    log.info(f"Found replication resource(s): {repl_coor_rescs_names}")

    return repl_coor_rescs_names


# Returns all 'passthru' resources available.
def get_passthru_resources(session):
    passthru_rescs = session.query(Resource).filter(Resource.type == 'passthru')
    passthru_rescs_names = [resc[Resource.name] for resc in passthru_rescs]
    log.info(f"Found passthru resource(s): {passthru_rescs_names}")

    return passthru_rescs_names


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
            yes_no = query_yes_no(f"The filename '{name}_{resource}' already exists at {path}/, resource {resource}. "
                                  f"Do you want to overwrite the file?")
            if yes_no == "no":
                log.info(f"Exiting... Please retry using a different filename.")
                sys.exit(1)
        elif session.data_objects.exists(str(file_path+"_"+resource)) and overwrite is True:
            log.info(f"Overwrite flag passed. Will overwrite file '{name}_{resource}' at '{path}/'")


# Put operation of file to all available resources. Returns a list of (operation, resource, success, message).
def put_file(session, resources, name, source_file):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    results = []
    for resource in resources:
        try:
            log.info(f"Putting '{name}_{resource}' to '{path}/' on resource '{resource}'")
            session.data_objects.put(source_file, str(file_path + "_" + resource), destRescName=resource)
            log.info(f"Put to '{resource}' successful!")
            results.append(("put", resource, True, ""))
        except (
                exception.DataObjectDoesNotExist,
                exception.SYS_FILE_DESC_OUT_OF_RANGE,
                exception.UNIX_FILE_CREATE_ERR,
                KeyError
        ) as e:
            log.error(f"Put to '{resource}' failed: {e}")
            results.append(("put", resource, False, str(e)))
    return results


# Cross-replication of files between replication resources (round-robin).
# Returns a list of (operation, target, success, message).
def replicate_file(session, resources, name):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    results = []
    for k in range(len(resources)):
        src = resources[k]
        dst = resources[(k + 1) % len(resources)]
        try:
            session.data_objects.replicate(str(file_path + "_" + src), resource=dst)
            log.info(f"Replication of '{name}_{src}' to '{dst}' successful!")
            results.append(("replicate", f"{src} -> {dst}", True, ""))
        except (
                exception.DataObjectDoesNotExist,
                KeyError
        ) as e:
            log.error(f"Replication of '{name}_{src}' to '{dst}' failed: {e}")
            results.append(("replicate", f"{src} -> {dst}", False, str(e)))
    return results


# Get operation of file, including checksum verification.
# Returns a list of (operation, resource, success, message).
def get_file(session, resources, name):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    dest = "./"
    time_stamp = int(time.time())
    log.info("Get operation started. Files will be placed in the current directory.")
    results = []
    for resource in resources:
        local_path = dest + name + "_" + resource + "_" + str(time_stamp)
        try:
            log.info(f"Getting '{name}_{resource}' from '{path}/' on resource '{resource}'")
            session.data_objects.get(file_path + "_" + resource, local_path)
            log.info(f"Get from '{resource}' successful!")
            results.append(("get", resource, True, ""))
        except (
                exception.OVERWRITE_WITHOUT_FORCE_FLAG,
                KeyError,
        ) as e:
            log.error(f"Get from '{resource}' failed: {e}")
            results.append(("get", resource, False, str(e)))
            continue

        try:
            log.info(f"Verifying checksum for '{name}_{resource}'...")
            # Retrieve checksum from iRODS and strip the 'sha2:' prefix
            chksum = session.data_objects.chksum(str(file_path + "_" + resource))
            chksum_stripped = re.sub('sha2:', '', chksum)

            # Read the local file in 64 KB chunks and compute its SHA-256
            # Equivalent to: sha256sum file | xxd -r -p | base64
            sha2 = hashlib.sha256()
            BUF_SIZE = 65536
            with open(local_path, 'rb') as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    sha2.update(data)
            b64chksum = re.sub('[b\']', '', str(base64.b64encode(sha2.digest())))

            if chksum_stripped == b64chksum:
                log.info(f"Checksum for '{name}_{resource}' matches!")
                results.append(("checksum", resource, True, ""))
            else:
                log.error(f"Checksum mismatch for '{name}_{resource}': iRODS={chksum_stripped}, local={b64chksum}")
                results.append(("checksum", resource, False, f"iRODS={chksum_stripped}, local={b64chksum}"))
        except Exception as e:
            log.error(f"Checksum verification for '{resource}' failed: {e}")
            results.append(("checksum", resource, False, str(e)))
    return results


# Removal of all files based on filename, with unlink. This also removes all replicates.
# Returns a list of (operation, resource, success, message).
def remove_file(session, resources, name):
    path = f"/nlmumc/home/{session.username}"
    file_path = f"{path}/{name}"
    results = []
    for resource in resources:
        try:
            log.info(f"Removing '{name}_{resource}' from '{path}/' on resource '{resource}'")
            session.data_objects.get(str(file_path + "_" + resource)).unlink(force=True)
            log.info(f"Removal from '{resource}' successful!")
            results.append(("remove", resource, True, ""))
        except (
                exception.DataObjectDoesNotExist,
                KeyError
        ) as e:
            log.error(f"Removal from '{resource}' failed: {e}")
            results.append(("remove", resource, False, str(e)))
    return results


def print_summary(results):
    _GREEN = "\033[32m"
    _RED = "\033[31m"
    log.info("=" * 60)
    log.info(" SUMMARY")
    log.info("=" * 60)
    for operation, target, success, message in results:
        status = f"{_GREEN}[OK    ]{_RESET}" if success else f"{_RED}[FAILED]{_RESET}"
        line = f"  {status}  {operation:<12} {target}"
        if not success and message:
            line += f"  |  {message}"
        log.info(line)
    log.info("-" * 60)
    total = len(results)
    ok = sum(1 for _, _, s, _ in results if s)
    if ok == total:
        log.info(f"  {_GREEN}{ok}/{total} operations completed successfully.{_RESET}")
    else:
        log.info(f"  {_RED}{ok}/{total} operations completed successfully. {total - ok} failed.{_RESET}")
    log.info("=" * 60)


def run_stage(all_results, stage_results):
    """Extend all_results with stage_results. Returns False if any step failed."""
    all_results.extend(stage_results)
    return all(s for _, _, s, _ in stage_results)


def main():
    args = parse_args()
    all_results = []
    with irods_session(args.env_file) as session:
        log.info("START: checking resource availability...")
        check_resources(session, args.exclusions)
        print()
        resources = get_resources(session)
        passthru_resources = get_passthru_resources(session)
        print()
        check_path(session)

        if resources:
            log.info("START: testing replication resources (put, replicate, get, remove)...")
            check_file(session, resources, args.name, args.overwrite)
            if not run_stage(all_results, put_file(session, resources, args.name, args.source_file)):
                print_summary(all_results)
                sys.exit(1)
            if not run_stage(all_results, replicate_file(session, resources, args.name)):
                print_summary(all_results)
                sys.exit(1)
            if not run_stage(all_results, get_file(session, resources, args.name)):
                print_summary(all_results)
                sys.exit(1)
            if not run_stage(all_results, remove_file(session, resources, args.name)):
                print_summary(all_results)
                sys.exit(1)
        else:
            log.warning("No replication resources found, skipping replication tests.")

        print()
        if passthru_resources:
            log.info("START: testing passthru resources (put, get, remove)...")
            check_file(session, passthru_resources, args.name, args.overwrite)
            if not run_stage(all_results, put_file(session, passthru_resources, args.name, args.source_file)):
                print_summary(all_results)
                sys.exit(1)
            if not run_stage(all_results, get_file(session, passthru_resources, args.name)):
                print_summary(all_results)
                sys.exit(1)
            if not run_stage(all_results, remove_file(session, passthru_resources, args.name)):
                print_summary(all_results)
                sys.exit(1)
        else:
            log.info("No passthru resources found, skipping passthru tests.")

        print()
        print_summary(all_results)


if __name__ == "__main__":
    try:
        log = setup_custom_logger("irodsDeploymentTests", logging.INFO)
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
