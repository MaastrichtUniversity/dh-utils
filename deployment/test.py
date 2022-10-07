import os
import sys
import logging
import argparse
from irods.session import iRODSSession
from irods.resource import iRODSResource
from irods.meta import iRODSMeta
from irods.models import Resource


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=100),
    )
    # parser.add_argument("-H", "--host", default=None, action='store', required=False, type=str)
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


def get_resources(session):
    resources = [iRODSResource(session.resources, query_result) for query_result in session.query(Resource).all()]

    return resources

def checking(session, path):
    object = session.collections.get(path)

    return object.metadata.get_one('resource')


def main():
    args = parse_args()
    with irods_session(args.env_file) as session:
        obj = get_resources(session)
        print(obj)
        obj2 = checking(session, "/nlmumc/projects/P000000010/")
        print(obj2)


if __name__ == "__main__":
    try:
        log = setup_custom_logger(__name__, logging.INFO)
        sys.exit(not main())
    except KeyboardInterrupt:
        sys.exit(2)
