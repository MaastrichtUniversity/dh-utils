import argparse
import ssl
import json

from irods.session import iRODSSession
from irods.meta import iRODSMeta


class Converter:
    def __init__(self, config, args):
        self.config = config
        self.args = args
        self.session = None
        self.dictionary = {}
        self.errors = 0
        self.skipped_azm = 0
        self.converted = 0

    def init_session(self):
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None)
        ssl_settings = {
            "irods_client_server_negotiation": "request_server_negotiation",
            "irods_encryption_algorithm": "AES-256-CBC",
            "irods_encryption_key_size": 32,
            "irods_encryption_num_hash_rounds": 16,
            "irods_encryption_salt_size": 8,
            "ssl_context": ssl_context,
        }

        irods_session_settings = {
            "host": self.config["IRODS_HOST"],
            "user": self.config["IRODS_USER"],
            "password": self.config["IRODS_PASS"],
            "port": 1247,
            "zone": "nlmumc",
            "irods_client_server_policy": self.config["IRODS_CLIENT_SERVER_POLICY"],
            **ssl_settings,
        }

        self.session = iRODSSession(**irods_session_settings)

    def convert_budget_numbers(self):
        self.load_json()
        project_dir = self.session.collections.get("/nlmumc/projects")
        projects = project_dir.subcollections
        for project in projects:
            print(f"Processing '{project.path}'")
            old_budget_number = self.get_budget_number(project)
            print(f"\t Old budget number '{old_budget_number}'")
            new_budget_number = self.convert_budget_number(old_budget_number)
            if new_budget_number:
                self.converted += 1
                self.set_new_budget_number(project, new_budget_number)

        self.session.cleanup()

    def load_json(self):
        try:
            self.dictionary = json.load(self.args.dictionary)
        except ValueError:
            print("Error encountered while parsing JSON -- exiting")
            exit(1)

    @staticmethod
    def get_budget_number(project):
        metadata = project.metadata
        return metadata["responsibleCostCenter"].value

    def convert_budget_number(self, old_budget_number):
        if "AZM" in old_budget_number:
            print(f"\t Old budget number is AZM number -- skipping")
            self.skipped_azm += 1
            return
        elif "UM" in old_budget_number:
            old_budget_number_stripped = old_budget_number.replace("UM-", "")
            if old_budget_number_stripped not in self.dictionary:
                print(f"\t ERROR: Old budget number does not have a new budget number")
                self.errors += 1
                return
            else:
                new_budget_number = self.dictionary[old_budget_number_stripped]
                new_number_with_prefix = f"UM-{new_budget_number['new_number']}"
                print(f"\t New budget number found! '{new_number_with_prefix}'. Department: '{new_budget_number['description_new']}'")
                return new_number_with_prefix
        else:
            print("\t ERROR: Budget number does not conform to old standard")
            self.errors += 1

    def set_new_budget_number(self, project, new_budget_number):
        if self.args.commit:
            print(f"\t Setting new budget number for '{project.path}' to '{new_budget_number}'")
            new_meta = iRODSMeta('responsibleCostCenter', str(new_budget_number))
            project.metadata[new_meta.name] = new_meta
        else:
            print(f"\t -- skipping setting new budget number. Running in dry mode")


def main():
    parser = argparse.ArgumentParser(description="Convert budget numbers in iRODS")
    parser.add_argument("-c", "--commit", action="store_true", help="commit to actually modify the budget number")
    parser.add_argument("dictionary", type=argparse.FileType("r"), help="Path to the dictionary for the conversion")
    args = parser.parse_args()

    host = input("Enter your iRODS host:")
    username = input("Enter your iRODS username:")
    password = input("Enter your IRODS password:")

    if not args.dictionary.name.endswith(".json"):
        exit(f"Invalid file path provided. Should be a '.json' file")

    config = {
        "IRODS_HOST": host,
        "IRODS_USER": username,
        "IRODS_PASS": password,
        "IRODS_CLIENT_SERVER_POLICY": "CS_NEG_REQUIRE",
    }

    if args.commit:
        print("Starting conversion in commit mode")
    else:
        print("Starting conversion in dry mode")

    converter = Converter(config, args)
    converter.init_session()
    converter.convert_budget_numbers()
    print("-" * 65)

    if converter.errors:
        print("Conversion result: NOT OK - errors found")
        print(f"\t {converter.errors} error(s) encountered")
    else:
        print("Conversion OK!")

    print(f"\t {converter.skipped_azm} azM numbers skipped")
    print(f"\t {converter.converted} budget numbers {'' if args.commit else 'to be '}converted")


if __name__ == "__main__":
    main()
