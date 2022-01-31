import json
import os
import xml.etree.cElementTree as ET
import urllib.request
import argparse

from irods import exception
from irods.exception import CollectionDoesNotExist, NoResultFound
from irods.models import Collection as iRODSCollection
from irodsrulewrapper.rule import RuleManager
from irodsrulewrapper.utils import check_project_collection_path_format, convert_to_current_timezone
from jsonschema import validate

from metadata_xml_to_json import Conversion


class UpdateExistingCollections:
    ERROR_COUNT = 0
    WARNING_COUNT = 0
    COLLECTION_DONE_COUNT = 0
    COLLECTION_COUNT = 0

    def __init__(self, rule_manager, json_instance_template, json_schema, args):
        self.rule_manager = rule_manager
        self.json_instance_template = json_instance_template
        self.json_schema = json_schema

        self.users = self.get_users_info()
        self.session = rule_manager.session
        self.schema_version = json_schema["pav:version"]
        self.original_pid_requested = False

        self.force_flag = args.force_flag
        self.commit = args.commit
        self.project_collection_path = args.project_collection_path
        self.verbose = args.verbose

    def read_metadata_xml(self, xml_path):
        try:
            with self.session.data_objects.open(xml_path, "r") as f:
                metadata_xml = ET.fromstring(f.read())
        except (exception.DataObjectDoesNotExist, exception.SYS_FILE_DESC_OUT_OF_RANGE):
            metadata_xml = ""
            print(f"\t\t Error: {xml_path} not found")
            self.ERROR_COUNT += 1

        return metadata_xml

    def get_avu_metadata(self, collection_object, project_id):
        query = self.rule_manager.session.query(iRODSCollection).filter(iRODSCollection.id == collection_object.id)
        try:
            result = query.one()
        except NoResultFound:
            raise CollectionDoesNotExist()
        ctime = result[iRODSCollection.create_time]

        try:
            pid = collection_object.metadata.get_one("PID").value
        except KeyError:
            print(f"\t\t Warning: PID missing for {collection_object.path}/")
            pid = ""
            self.WARNING_COUNT += 1
            if self.commit:
                pid = self.register_original_pids(project_id, collection_object.name)
                self.rule_manager.set_collection_avu(collection_object.path, "PID", pid)
                print(f"\t\t Set avu PID({pid}) for {collection_object.path}")
                self.original_pid_requested = True

        try:
            creator = collection_object.metadata.get_one("creator").value
        except KeyError:
            creator = ""
            print(f"\t\t Warning: creator missing for {collection_object.path}/")
            self.WARNING_COUNT += 1

        try:
            display_name = self.users[creator].display_name
            split = display_name.split(" ")
            first_name = split[0]
            last_name = " ".join(split[1:])
            creator_username = self.users[creator].user_name
        except KeyError:
            first_name = ""
            last_name = ""
            creator_username = ""
            print(f"\t\t Warning: user info missing for {creator}")
            self.WARNING_COUNT += 1

        ret = {
            "affiliation_mapping_file": "assets/affiliation_mapping.json",
            "base_PID": f"https://hdl.handle.net/{pid}",
            "version_PID": f"https://hdl.handle.net/{pid}.1",
            "creatorGivenName": first_name,
            "creatorFamilyName": last_name,
            "creator_username": creator_username,
            "submissionDate": convert_to_current_timezone(ctime, "%Y-%m-%d"),
            "ctime": convert_to_current_timezone(ctime, "%Y-%m-%dT%H:%M:%S"),
            "contributors": self.get_contributors(project_id),
        }
        return ret

    def update_collection_avu(self, project_id, collection_id):
        destination_collection = f"/nlmumc/projects/{project_id}/{collection_id}"

        self.rule_manager.set_collection_avu(destination_collection, "latest_version_number", "1")
        self.rule_manager.set_collection_size(project_id, collection_id, "false", "false")
        self.rule_manager.set_collection_avu(destination_collection, "schemaName", "DataHub_extended_schema")
        self.rule_manager.set_collection_avu(destination_collection, "schemaVersion", self.schema_version)

    def register_pids(self, project_id, collection_id):
        if not self.original_pid_requested:
            self.register_original_pids(project_id, collection_id)
        self.register_version_pids(project_id, collection_id)

    def register_original_pids(self, project_id, collection_id):
        # Requesting a PID via epicPID for version 0 (root version)
        handle_pids = self.rule_manager.get_versioned_pids(project_id, collection_id, "")
        if not handle_pids:
            print(f"\t\t Warning: Retrieving multiple PID's failed for {project_id}/{collection_id}, leaving blank")
            self.WARNING_COUNT += 1
        elif handle_pids.collection["handle"] == "":
            print(
                f"\t\t Warning: Retrieving PID for root collection failed for {project_id}/{collection_id},"
                f" leaving blank"
            )
            self.WARNING_COUNT += 1
        elif handle_pids.schema["handle"] == "":
            print(
                f"\t\t Warning: Retrieving PID for root collection schema failed for {project_id}/{collection_id},"
                f" leaving blank"
            )
            self.WARNING_COUNT += 1
        elif handle_pids.instance["handle"] == "":
            print(
                f"\t\t Warning: Retrieving PID for root collection instance failed for {project_id}/{collection_id},"
                f" leaving blank"
            )
            self.WARNING_COUNT += 1

        return handle_pids.collection["handle"]

    def register_version_pids(self, project_id, collection_id):
        # Requesting PID's for Project Collection version 1 (includes instance and schema)
        handle_pids_version = self.rule_manager.get_versioned_pids(project_id, collection_id, "1")
        if not handle_pids_version:
            print(
                f"\t\t Warning: Retrieving multiple PID's failed for {project_id}/{collection_id} version 1,"
                f" leaving blank"
            )
            self.WARNING_COUNT += 1

    def replace_collection_metadata(self, project_id, collection_id, pid, instance_object):
        destination_collection = f"/nlmumc/projects/{project_id}/{collection_id}"
        instance_path = f"{destination_collection}/instance.json"
        instance_tmp = "instance_tmp.json"
        schema_path = f"{destination_collection}/schema.json"
        schema_tmp = "schema_tmp.json"
        version = 1

        # Update @id of instance.json and schema.json
        schema_url = f"{pid}schema.{version}"
        instance_object["@id"] = f"{pid}instance.{version}"
        instance_object["schema:isBasedOn"] = schema_url
        self.json_schema["@id"] = schema_url

        # Replace instance.json and schema.json in collection root
        with open(instance_tmp, "w") as instance_outfile:
            json.dump(instance_object, instance_outfile)
        with open(schema_tmp, "w") as schema_outfile:
            json.dump(self.json_schema, schema_outfile)

        status = 0
        status += self.upload_file(instance_tmp, instance_path)
        status += self.upload_file(schema_tmp, schema_path)

        # Create a copy of instance.json and schema.json in .metadata_versions
        # Create metadata_versions and copy schema and instance from root to that folder as version 1
        version_folder_path = destination_collection + "/.metadata_versions"
        version_schema_path = version_folder_path + "/schema.1.json"
        version_instance_path = version_folder_path + "/instance.1.json"
        if not self.session.collections.exists(version_folder_path):
            self.session.collections.create(version_folder_path)
        status += self.upload_file(instance_tmp, version_instance_path)
        status += self.upload_file(schema_tmp, version_schema_path)

        os.remove(instance_tmp)
        os.remove(schema_tmp)
        return status

    def upload_file(self, source_file, destination_path):
        if not self.force_flag and self.rule_manager.session.data_objects.exists(destination_path):
            print(f"\t\t Error: {destination_path} already exists")

            return 1

        try:
            self.rule_manager.session.data_objects.put(source_file, destination_path)
        except (
            exception.DataObjectDoesNotExist,
            exception.SYS_FILE_DESC_OUT_OF_RANGE,
            KeyError,
        ):
            print(f"\t\t Error: during put operation")
            self.ERROR_COUNT += 1

        return 0

    def convert_all_collections(self):
        projects_root = self.session.collections.get("/nlmumc/projects")
        for project in projects_root.subcollections:
            print(f"* Looping over project {project.name}")
            for collection in project.subcollections:
                self.convert_collection_metadata(project.name, collection.name, collection)

    def convert_collection_metadata(self, project_id, collection_id, collection_object):
        print(f"\t- Processing {project_id}/{collection_id}")
        self.COLLECTION_COUNT += 1
        session = self.rule_manager.session

        instance_path = f"{collection_object.path}/instance.json"
        schema_path = f"{collection_object.path}/schema.json"

        if not self.force_flag and self.rule_manager.session.data_objects.exists(instance_path):
            print(f"\t\t Error: File {instance_path} already exist")
            print(f"\t\t Error: Skip conversion for {collection_object.path}")
            self.ERROR_COUNT += 1
            return
        if not self.force_flag and self.rule_manager.session.data_objects.exists(schema_path):
            print(f"\t\t Error: File {schema_path} already exist")
            print(f"\t\t Error: Skip conversion for {collection_object.path}")
            self.ERROR_COUNT += 1
            return

        xml_path = f"/nlmumc/projects/{project_id}/{collection_id}/metadata.xml"
        metadata_xml = self.read_metadata_xml(xml_path)
        if metadata_xml == "":
            print(f"\t\t Error: Skip conversion for {xml_path}")
            return

        avu = self.get_avu_metadata(collection_object, project_id)
        json_instance = Conversion(metadata_xml, self.json_instance_template, avu).get_instance()

        validate(instance=json_instance, schema=self.json_schema)

        if self.commit:
            self.rule_manager.open_project_collection(project_id, collection_id, session.username, "own")
            self.register_pids(project_id, collection_id)
            self.update_collection_avu(project_id, collection_id)
            status = self.replace_collection_metadata(project_id, collection_id, avu["base_PID"], json_instance)
            self.rule_manager.close_project_collection(project_id, collection_id)
            if status == 0:
                print("\t\t Upload done")
            else:
                print("\t\t Upload uncompleted")

        if self.verbose:
            print(json.dumps(json_instance, ensure_ascii=False, indent=4))

        print("\t\t Conversion done")
        self.COLLECTION_DONE_COUNT += 1

    def get_contributors(self, project_id):
        result = self.rule_manager.get_project_contributors_metadata(project_id)
        return {
            "data manager": {
                "contributorFullName": result.data_steward.display_name,
                "contributorFamilyName": result.data_steward.family_name,
                "contributorType": {
                    "rdfs:label": "data manager",
                    "@id": "http://purl.org/zonmw/generic/10077",
                },
                "contributorGivenName": result.data_steward.given_name,
                "contributorEmail": result.data_steward.email,
            },
            "project manager": {
                "contributorFullName": result.principal_investigator.display_name,
                "contributorFamilyName": result.principal_investigator.family_name,
                "contributorType": {
                    "rdfs:label": "project manager",
                    "@id": "http://purl.org/zonmw/generic/10082",
                },
                "contributorGivenName": result.principal_investigator.given_name,
                "contributorEmail": result.principal_investigator.email,
            },
        }

    def get_users_info(self):
        ret = {}
        result = self.rule_manager.get_users("false")
        for user in result.users:
            email = self.rule_manager.get_username_attribute_value(user.user_name, "email", "false")
            ret[email.value] = user

        return ret


def main():
    host = input("Enter your iRODS host:")
    username = input("Enter your iRODS username:")
    password = input("Enter your IRODS password:")

    parser = argparse.ArgumentParser(description="update_existing_collections description")
    parser.add_argument("-f", "--force-flag", action="store_true", help="Overwrite existing metadata files")
    parser.add_argument("-c", "--commit", action="store_true", help="Commit to upload the converted file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print the converted instance.json")
    parser.add_argument(
        "-p", "--project-collection-path", type=str, help="The absolute path of the project collection to convert"
    )
    args = parser.parse_args()

    if args.project_collection_path and not check_project_collection_path_format(args.project_collection_path):
        exit(f"Wrong project collection path {args.project_collection_path}")

    config = {
        "IRODS_HOST": host,
        "IRODS_USER": username,
        "IRODS_PASS": password,
        "IRODS_CLIENT_SERVER_POLICY": "CS_NEG_REQUIRE",
    }
    rule_manager = RuleManager(admin_mode=True, config=config)

    with open("assets/instance_template_min.json", encoding="utf-8") as instance_file:
        json_instance_template = json.load(instance_file)

    schema_url = "https://raw.githubusercontent.com/MaastrichtUniversity/dh-mdr/release/customizable_metadata/core/static/assets/schemas/DataHub_extended_schema.json?token=GHSAT0AAAAAABQNGBMFCMVM2BPHP4EEM65QYQA6BLA"
    with urllib.request.urlopen(schema_url) as url:
        json_schema = json.loads(url.read().decode())

    converter = UpdateExistingCollections(rule_manager, json_instance_template, json_schema, args)

    if args.project_collection_path:
        split = args.project_collection_path.split("/")
        project_id = split[3]
        collection_id = split[4]
        collection_object = rule_manager.session.collections.get(args.project_collection_path)
        converter.convert_collection_metadata(project_id, collection_id, collection_object)
    else:
        converter.convert_all_collections()

    rule_manager.session.cleanup()

    print("Summary:")
    print(f"\t {converter.COLLECTION_DONE_COUNT}/{converter.COLLECTION_COUNT} collection(s) converted")
    print(f"\t {converter.ERROR_COUNT} error(s) encountered")
    print(f"\t {converter.WARNING_COUNT} warning(s) encountered")


if __name__ == "__main__":
    main()
