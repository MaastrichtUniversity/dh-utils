#!/usr/bin/env python3
import argparse
import base64
import binascii
import hashlib
import logging
import os
import signal
import sys
from multiprocessing import Pool
from tqdm import tqdm
from irods.exception import *
from irods.session import iRODSSession


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=100)
    )

    parser.add_argument("-s", "--source", metavar='DIR', required=True, help="Source directory to check")
    parser.add_argument("-t", "--target", metavar='COLLECTION', required=True,
                        help="Target iRODS collection to validate against")
    parser.add_argument("-q", "--quiet", action='store_true', help="Hide progress and only show errors")
    parser.add_argument("-v", "--verbose", action='store_true', help="Be extra verbose")
    parser.add_argument("-c", "--continue", action='store_true', help="Continue on validation error")
    parser.add_argument("-p", "--parallel", metavar='n', type=int, help="Number of parallel processes running checksum",
                        default=1)

    settings = parser.parse_args()

    return settings


def setup_custom_logger(name, log_level):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)7s - %(module)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(log_level)
    log.addHandler(handler)

    return log


def checksum_calculator(config, p):
    # Ignore the interrupt signal. Let parent handle that.
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    os_path = os.path.join(config.source, p)

    logger.debug("Calculating checksum for %s" % p)

    # Calculate checksum
    sha256_hash = hashlib.sha256()
    size = 0
    with open(os_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
            size += len(byte_block)

        checksum = sha256_hash.hexdigest()

    return p, size, checksum


def irods_session(config):
    # iRODS config
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
        env_file = os.path.expanduser('~/.irods/irods_environment.json')

    try:
        # Build iRODS connection
        session = iRODSSession(irods_env_file=env_file)
    except FileNotFoundError:
        logger.error("No `~/.irods/irods_environment.json` found. Use iinit to make one.")
        return None

    try:
        session.collections.get(config.target)
    except NetworkException:
        logger.error("Error connecting to iRODS. Check ~/.irods/irods_environment.json and iinit.")
        return None
    except CollectionDoesNotExist:
        logger.error("Target collection `%s` does not exist" % config.target)
        return None

    return session


def irods_hash_to_sha256(h):
    irods_hash = h.split('sha2:')[1]
    base_hash = base64.b64decode(irods_hash)
    return binascii.hexlify(base_hash).decode("utf-8")


def main():
    config = parse_arguments()

    # Change requested log level
    if config.quiet:
        logger.setLevel(logging.ERROR)
    if config.verbose:
        logger.setLevel(logging.DEBUG)

    # iRODS connection
    session = irods_session(config)
    if session is None:
        return 1

    # Multiprocessing pool and result list
    pool = Pool(processes=config.parallel)
    results = list()

    logger.info("Making inventory of source directory '%s'" % config.source)

    # Setup file progress
    progress_bar = tqdm(unit="files", unit_scale=True, disable=config.quiet)

    # Fill input queue with the source directory
    total_bytes = 0
    for root, dirs, files in os.walk(config.source, topdown=False):
        for name in files:
            os_path = os.path.join(root, name)
            rel_path = os.path.relpath(os_path, config.source)

            results.append(pool.apply_async(checksum_calculator, args=(config, rel_path)))
            progress_bar.update(1)

            # Byte size
            stat = os.stat(os_path)
            total_bytes += stat.st_size

    # Finish inventory
    progress_bar.close()
    logger.info("Validating %d files and %d bytes in source directory." % (len(results), total_bytes))

    # Setup progress
    progress_bar = tqdm(unit="bytes", unit_scale=True, total=total_bytes, disable=config.quiet)

    # Loop through results and check with iRODS
    try:
        for result in results:
            # Wait for result worker to finish
            p, size, checksum = result.get()

            # Update progress bar
            progress_bar.update(size)

            # Get iRODS object
            total_p = os.path.join(config.target, p)
            try:
                o = session.data_objects.get(total_p)
            except (CollectionDoesNotExist, DataObjectDoesNotExist):
                logger.error("File `%s` does not exist in target collection" % p)

                if not getattr(config, 'continue'):
                    return 1
                else:
                    continue

            # Check whether iRODS has a checksum stored
            if o.checksum is None:
                logger.error("File `%s` does not have a checksum stored in iRODS" % p)

                if not getattr(config, 'continue'):
                    return 1
                else:
                    continue

            # Convert checksum
            irods_hash_decode = irods_hash_to_sha256(o.checksum)

            # Check checksum
            if irods_hash_decode != checksum:
                logger.error("File `%s` does not match checksum" % p)

                if not getattr(config, 'continue'):
                    return 1
                else:
                    continue

    except KeyboardInterrupt:
        # The finally block is executed always, but the KeyboardInterrupt needs to be reraised to be handled by parent
        raise KeyboardInterrupt
    finally:
        # Terminate worker and progress bar
        pool.terminate()
        pool.join()
        progress_bar.close()
        session.cleanup()

    logger.info("Finished validation")


if __name__ == "__main__":
    try:
        logger = setup_custom_logger("irodsDropzoneValidator", logging.INFO)
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
