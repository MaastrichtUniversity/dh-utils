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
        self.enable_archive_set = 0

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

    def set_avus(self):
        project_dir = self.session.collections.get("/nlmumc/projects")
        projects = project_dir.subcollections
        for project in projects:
            print(f"Processing '{project.name}'")
            has_avu_already_set = self.get_existence_enable_unarchive_avu(project)
            if has_avu_already_set:
                print(f"\t AVU enableUnarchive already set")
                self.already_set += 1
                self.get_enable_archive_avu(project)
            else:
                enable_archive_value = self.get_enable_archive_avu(project)
                value_to_set = enable_archive_value if enable_archive_value else "false"
                self.set_enable_unarchive(project, value_to_set)
                self.newly_set += 1
        self.session.cleanup()

    @staticmethod
    def get_existence_enable_unarchive_avu(project):
        metadata = project.metadata
        if "enableUnarchive" in metadata:
            return True
        return False

    def get_enable_archive_avu(self, project):
        metadata = project.metadata
        if "enableArchive" in metadata:
            return metadata["enableArchive"].value
        print(f"\t WARNING: enableArchive not set for project '{project.name}', using default 'false'")
        self.set_enable_archive(project)
        self.enable_archive_set += 1

    def set_enable_unarchive(self, project, value):
        if self.args.commit:
            print(f"\t Setting enableUnarchive '{project.name}' to '{value}'")
            new_meta = iRODSMeta("enableUnarchive", str(value))
            project.metadata[new_meta.name] = new_meta
        else:
            print(f"\t -- skipping setting enableUnarchive. Running in dry mode")

    def set_enable_archive(self, project):
        if self.args.commit:
            print(f"\t Also setting enableArchive '{project.name}' to 'false'")
            new_meta = iRODSMeta("enableArchive", "false")
            project.metadata[new_meta.name] = new_meta
        else:
            print(f"\t -- skipping setting enableArchive. Running in dry mode")


def main():
    parser = argparse.ArgumentParser(description="Set the EnableUnarchive AVU to a default value for all projects")
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
    avu_setter.set_avus()
    print("-" * 65)

    print(f"\t {avu_setter.already_set} enableUnarchive already set")
    print(f"\t {avu_setter.newly_set} enableUnarchive {'' if args.commit else 'to be '}set")
    print(f"\t {avu_setter.enable_archive_set} enableArchive {'' if args.commit else 'to be '}set")


if __name__ == "__main__":
    main()
