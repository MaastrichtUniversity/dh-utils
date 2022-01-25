import json
import os
import xml.etree.cElementTree as ET

from irods import exception
from irods.exception import CollectionDoesNotExist, NoResultFound
from irods.models import Collection as iRODSCollection
from irodsrulewrapper.rule import RuleManager

from metadata_xml_to_json import Conversion

from jsonschema import validate


def read_metadata_xml(session, xml_path):
    try:
        with session.data_objects.open(xml_path, "r") as f:
            metadata_xml = ET.fromstring(f.read())
    except (exception.DataObjectDoesNotExist, exception.SYS_FILE_DESC_OUT_OF_RANGE):
        metadata_xml = ""
        print(f"Error: {xml_path} not found")

    return metadata_xml


def get_avu_metadata(rule_manager, coll, users, project_id):
    query = rule_manager.session.query(iRODSCollection).filter(iRODSCollection.id == coll.id)
    try:
        result = query.one()
    except NoResultFound:
        raise CollectionDoesNotExist()
    ctime = result[iRODSCollection.create_time]

    try:
        pid = coll.metadata.get_one("PID").value
    except KeyError:
        pid = ""
        print(f"Error: PID missing for {coll.path}/")
        # TODO request PID if missing

    try:
        creator = coll.metadata.get_one("creator").value
    except KeyError:
        creator = ""
        print(f"Error: creator missing for {coll.path}/")

    try:
        display_name = users[creator].display_name
        split = display_name.split(" ")
        first_name = split[0]
        last_name = " ".join(split[1:])
        creator_username = users[creator].user_name
    except KeyError:
        first_name = ""
        last_name = ""
        creator_username = ""
        print(f"Error: user info missing for {creator}/")

    ret = {
        "PID": f"https://hdl.handle.net/{pid}.1",
        "creatorGivenName": first_name,
        "creatorFamilyName": last_name,
        "creator_username": creator_username,
        "submissionDate": f"{ctime.year}-{ctime.month}-{ctime.day}",
        "ctime": f"{ctime.year}-{ctime.month}-{ctime.day}T{ctime.hour}:{ctime.minute}:{ctime.second}",
        "contributors": get_contributors(rule_manager, project_id)
    }
    return ret


def update_collection_metadata(rule_manager, project_id, collection_id, schema_version):
    destination_collection = f"/nlmumc/projects/{project_id}/{collection_id}"

    rule_manager.set_collection_avu(destination_collection, "latest_version_number", "1")
    rule_manager.set_collection_size(project_id, collection_id, "false", "false")
    rule_manager.set_collection_avu(destination_collection, "schemaName", "DataHub_extended_schema")
    rule_manager.set_collection_avu(destination_collection, "schemaVersion", schema_version)


def register_pids(rule_manager, project_id, collection_id):
    destination_collection = f"/nlmumc/projects/{project_id}/{collection_id}"

    # Requesting a PID via epicPID for version 0 (root version)
    handle_pids = rule_manager.get_versioned_pids(project_id, collection_id, "")
    if not handle_pids:
        print("Retrieving multiple PID's failed for {}, leaving blank".format(destination_collection))
    elif handle_pids.collection["handle"] == "":
        print("Retrieving PID for root collection failed for {}, leaving blank".format(destination_collection))
    elif handle_pids.schema["handle"] == "":
        print("Retrieving PID for root collection schema failed for {}, leaving blank".format(destination_collection))
    elif handle_pids.instance["handle"] == "":
        print("Retrieving PID for root collection instance failed for {}, leaving blank".format(destination_collection))

    # Requesting PID's for Project Collection version 1 (includes instance and schema)
    handle_pids_version = rule_manager.get_versioned_pids(project_id, collection_id, "1")
    if not handle_pids_version:
        print("Retrieving multiple PID's failed for {} version 1, leaving blank".format(destination_collection))


def replace_collection_metadata(rule_manager, project_id, collection_id, pid, instance_object, schema_object):
    destination_collection = f"/nlmumc/projects/{project_id}/{collection_id}"
    instance_path = f"{destination_collection}/instance.json"
    instance_tmp = 'instance_tmp.json'
    schema_path = f"{destination_collection}/schema.json"
    schema_tmp = 'schema_tmp.json'
    version = 1

    # Update @id of instance.json and schema.json
    schema_url = f"{pid}schema.{version}"
    instance_object["@id"] = f"{pid}instance.{version}"
    instance_object["schema:isBasedOn"] = schema_url
    schema_object["@id"] = schema_url

    # Replace instance.json and schema.json in collection root
    with open(instance_tmp, 'w') as instance_outfile:
        json.dump(instance_object, instance_outfile)
    with open(schema_tmp, 'w') as schema_outfile:
        json.dump(schema_object, schema_outfile)

    try:
        rule_manager.session.data_objects.put(instance_tmp, instance_path)
        rule_manager.session.data_objects.put(schema_tmp, schema_path)

        os.remove(instance_tmp)
        os.remove(schema_tmp)
    except (exception.DataObjectDoesNotExist, exception.SYS_FILE_DESC_OUT_OF_RANGE):
        print(f"Error: during put operation")

    # Check if .metadata_versions

    # Create a copy of instance.json and schema.json in .metadata_versions
    # Create metadata_versions and copy schema and instance from root to that folder as version 1
    rule_manager.create_ingest_metadata_versions(project_id, collection_id)


def convert_collection_metadata(rule_manager, json_instance_template, users):
    session = rule_manager.session

    # https://raw.githubusercontent.com/MaastrichtUniversity/dh-mdr/release/customizable_metadata/core/static/assets/schemas/DataHub_general_schema.json?token=GHSAT0AAAAAABQNGBMEBRROAKZVV4K6ZBFUYPX6BOQ
    with open("DataHub_extended_schema.json", encoding='utf-8') as schema_file:
        json_schema = json.load(schema_file)
    schema_version = json_schema["pav:version"]

    projects_root = session.collections.get("/nlmumc/projects")
    for project in projects_root.subcollections:
        project_id = project.name
        for collection in project.subcollections:
            collection_id = collection.name
            print(f"Processing {project_id}/{collection_id}")

            # Add check if instance/schema already exist

            if collection_id != "C000000001" or project_id != "P000000014":
                continue

            rule_manager.open_project_collection(project_id, collection_id, session.username, "own")

            xml_path = f"/nlmumc/projects/{project_id}/{collection_id}/metadata.xml"
            metadata_xml = read_metadata_xml(session, xml_path)
            if metadata_xml == "":
                print(f"Error: Skip conversion for {xml_path}")
                rule_manager.close_project_collection(project_id, collection_id)
                continue

            avu = get_avu_metadata(rule_manager, collection, users, project_id)
            json_instance = Conversion(metadata_xml, json_instance_template, avu).get_instance()

            validate(instance=json_instance, schema=json_schema)
            # TODO affiliation mapping

            # print(json.dumps(json_instance, ensure_ascii=False, indent=4))

            register_pids(rule_manager, project_id, collection_id)
            update_collection_metadata(rule_manager, project_id, collection_id, schema_version)
            replace_collection_metadata(rule_manager, project_id, collection_id, avu["PID"], json_instance, json_schema)
            rule_manager.close_project_collection(project_id, collection_id)


def get_users_info(rule_manager):
    ret = {}
    result = rule_manager.get_users("false")
    for user in result.users:
        email = rule_manager.get_username_attribute_value(user.user_name, "email")
        ret[email.value] = user

    return ret


def get_contributors(rule_manager, project_id):
    result = rule_manager.get_project_contributors_metadata(project_id)
    return {
        "data manager": {
            "contributorFullName": result.data_steward.display_name,
            "contributorFamilyName": result.data_steward.family_name,
            "contributorType": {
                "rdfs:label": "data manager",
                "@id": "http://purl.org/zonmw/generic/10077"
            },
            "contributorGivenName": result.data_steward.given_name,
            "contributorEmail": result.data_steward.email,
        },
        "project manager": {
            "contributorFullName": result.principal_investigator.display_name,
            "contributorFamilyName": result.principal_investigator.family_name,
            "contributorType": {
                "rdfs:label": "project manager",
                "@id": "http://purl.org/zonmw/generic/10082"
            },
            "contributorGivenName": result.principal_investigator.given_name,
            "contributorEmail": result.principal_investigator.email,
        }
    }


def main():
    # host = input("Enter your iRODS host:")
    # username = input("Enter your iRODS username:")
    # password = input("Enter your IRODS password:")
    host = "irods.dh.local"
    username = "rods"
    password = "irods"

    # force-flag
    # dry-mode
    # commit

    config = {
        "IRODS_HOST": host,
        "IRODS_USER": username,
        "IRODS_PASS": password,
        "IRODS_CLIENT_SERVER_POLICY": "CS_NEG_REQUIRE"
    }
    rule_manager = RuleManager(admin_mode=True, config=config)
    users = get_users_info(rule_manager)

    with open("instance_template_min.json", encoding='utf-8') as instance_file:
        json_instance_template = json.load(instance_file)

    convert_collection_metadata(rule_manager, json_instance_template, users)
    rule_manager.session.cleanup()


if __name__ == "__main__":
    main()
