#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import json
import subprocess

COUNT = 0
TOTAL = 0
ERRORS = 0

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40, width=100),
    )

    parser.add_argument('-f', '--file', help='JSON input file', type=argparse.FileType('r'))
    settings = parser.parse_args()

    if not settings.file:
        parser.print_usage()
        return sys.exit(1)

    return settings


def setup_custom_logger(name, log_level):
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)7s - %(module)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(log_level)
    log.addHandler(handler)

    return log

def get_full_path(path, item):
    if item["type"] == "file":
        destination_path = f"{path}/{item['name']}"
        verify_contents(destination_path, item["name"])
    if item["type"] == "directory":
        new_path = f"{path}/{item['name']}"
        for child in item["children"]:
            get_full_path(new_path, child)

def verify_contents(destination_full_path, file_name):
    write_progress()
    run_ils = f"ils -l \"{destination_full_path}\""
    try:
        output = subprocess.check_output(run_ils.encode('utf-8'), shell=True).decode("utf-8")
        total_number_of_occurrences = output.count(file_name)
        # An ingest always goes to a replicated resource, except if files have already been moved to tape
        if total_number_of_occurrences < 2 and "arcRescSURF01" not in output:
            add_to_errors(destination_full_path, "Item is not replicated properly")
    except subprocess.CalledProcessError as e:
        add_to_errors(destination_full_path, str(e))

def add_to_errors(destination_full_path, error_message):
    global ERRORS
    ERRORS += 1
    with open("/tmp/errors_file","a+") as f:
        f.write(f"Error occurred for {destination_full_path} \n")
        f.write(f"{error_message} \n")

def write_progress():
    global COUNT
    COUNT += 1
    percentage = (COUNT / TOTAL) * 100
    print(f"{COUNT} / {TOTAL} ({round(percentage, 2)}%)", end='\r')

def main():
    config = parse_arguments()
    contents = json.load(config.file)

    with open("/tmp/errors_file","a+") as f:
        f.write(f"Starting validation of {contents['type']} ingest {contents['token']} by {contents['creator']}\n")
        f.write("------------------------\n")

    global TOTAL
    TOTAL = contents["file_count"]

    for item in contents["file_folder_structure"]["children"]:
        base_path = f"/nlmumc/projects/{contents['project']}/{contents['collection']}"
        get_full_path(base_path, item)
    
    print(f"Finished validating {contents['type']} ingest {contents['token']} by {contents['creator']}")
    print("Results:")
    print("------------------------")
    print(f"Total: {TOTAL}")
    print(f"Successful: {TOTAL - ERRORS}")
    print(f"Errors: {ERRORS} ({round(((COUNT / TOTAL) * 100), 2)})%")

    with open("/tmp/errors_file","a+") as f:
        f.write(f"Finished validation of {contents['type']} ingest {contents['token']} by {contents['creator']}\n")
        f.write("------------------------\n")

    return 0


if __name__ == "__main__":
    try:
        logger = setup_custom_logger("irodsIngestValidator", logging.INFO)
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
