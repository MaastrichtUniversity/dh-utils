import argparse
import subprocess


def set_avu_to_mounted_dropzones(commit, attribute, value):
    run_iquest = "iquest \"%s\" \"SELECT COLL_NAME WHERE COLL_PARENT_NAME = '/nlmumc/ingest/zones'\""
    dropzones = subprocess.check_output(run_iquest, shell=True).strip()

    for dropzone in dropzones.splitlines():
        print (dropzone)
        if commit:
            run_set_imeta = "imeta set -C {} {} {}".format(dropzone, attribute, value)
            subprocess.check_call(run_set_imeta, shell=True)
            print ("\t--updated")
        else:
            run_ls_imeta = "imeta ls -C {} {}".format(dropzone, attribute)
            ils = subprocess.check_output(run_ls_imeta, shell=True).strip()
            print (ils)


def main():
    parser = argparse.ArgumentParser(description="Set the attribute value to all (mounted) drop-zones")
    parser.add_argument("-a", "--attribute", type=str, help="The attribute to set", required=True)
    parser.add_argument("-v", "--value", type=str, help="The value to set", required=True)
    parser.add_argument("-m", "--mounted", action="store_true", help="Only sets the AVU for mounted drop-zones")
    parser.add_argument("-c", "--commit", action="store_true", help="Commit to the AVU changes")
    args = parser.parse_args()

    if args.commit:
        print ("Running in COMMIT mode")
    else:
        print ("Running in DRY-RUN")

    # TODO add set_avu_to_direct_dropzone * set_avu_to_alldropzones
    if args.mounted:
        set_avu_to_mounted_dropzones(args.commit, args.attribute, args.value)


if __name__ == "__main__":
    main()
