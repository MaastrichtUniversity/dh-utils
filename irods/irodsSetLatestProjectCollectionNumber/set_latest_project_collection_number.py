import argparse
import ssl
from irods.session import iRODSSession
from irods.meta import iRODSMeta


class AvuSetter:
    def __init__(self, config, args):
        self.config = config
        self.args = args
        self.session = None
        self.already_set = 0
        self.newly_set = 0

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

    def set_avu(self):
        project_dir = self.session.collections.get("/nlmumc/projects")
        projects = project_dir.subcollections
        for project in projects:
            print(f"Processing '{project.name}'")
            has_avu_already_set = self.get_existence_latest_project_collection_number_avu(project)
            if has_avu_already_set:
                print(f"\t AVU latestProjectCollectionNumber already set")
                self.already_set += 1
            else:
                self.set_latest_project_collection_number_avu(project)
                self.newly_set += 1
        self.session.cleanup()

    def set_latest_project_collection_number_avu(self, project):
        latest_project_collection_number_value = self.calculate_latest_project_collection_number(project)
        if self.args.commit:
            print(
                f"\t Setting latestProjectCollectionNumber '{project.name}' to '{latest_project_collection_number_value}'"
            )
            new_meta = iRODSMeta("latestProjectCollectionNumber", str(latest_project_collection_number_value))
            project.metadata[new_meta.name] = new_meta
        else:
            print(
                f"\t -- skipping setting latestProjectCollectionNumber to {latest_project_collection_number_value} for {project.name}. Running in dry mode"
            )

    @staticmethod
    def get_existence_latest_project_collection_number_avu(project):
        metadata = project.metadata
        if "latestProjectCollectionNumber" in metadata:
            return True
        return False

    @staticmethod
    def calculate_latest_project_collection_number(project):
        latest_value = 0
        collections = project.subcollections
        for collection in collections:
            collection_id = collection.name[1:10]
            if int(collection_id) > latest_value:
                latest_value = int(collection_id)
        return latest_value


def main():
    parser = argparse.ArgumentParser(
        description="set the latestProjectCollectionNumber AVU to a correct value for all projects"
    )
    parser.add_argument("-c", "--commit", action="store_true", help="commit to actually set the AVUs")
    args = parser.parse_args()

    host = input("Enter your iRODS host:")
    username = input("Enter your iRODS username:")
    password = input("Enter your IRODS password:")

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

    avu_setter = AvuSetter(config, args)
    avu_setter.init_session()
    avu_setter.set_avu()
    print("-" * 65)

    print(f"\t {avu_setter.already_set} latestProjectCollectionNumber already set")
    print(f"\t {avu_setter.newly_set} latestProjectCollectionNumber {'' if args.commit else 'to be '}set")


if __name__ == "__main__":
    main()
