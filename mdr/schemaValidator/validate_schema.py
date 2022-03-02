import argparse

from schema_parser import SchemaParser


def main():
    parser = argparse.ArgumentParser(description="validate schema description")
    parser.add_argument("file", type=argparse.FileType("r"), help="Path to the schema to validate")
    args = parser.parse_args()

    if not args.file.name.endswith(".json"):
        exit(f"Invalid file path provided. Should be a '.json' file")

    validator = SchemaParser(args)
    validator.validate()
    print("-" * 65)
    if not validator.utils.ERROR_COUNT:
        if validator.utils.WARNING_COUNT:
            print("Validation result: OK with warnings. No errors found.")
            print(f"\t {validator.utils.WARNING_COUNT} warning(s) encountered")
        else:
            print("Validation result: OK. No errors found.")
            print(f"\t {validator.utils.WARNING_COUNT} warning(s) encountered")
    else:
        print("Validation result: NOT OK - errors found")
        print(f"\t {validator.utils.ERROR_COUNT} error(s) encountered")
        print(f"\t {validator.utils.WARNING_COUNT} warning(s) encountered")


if __name__ == "__main__":
    main()
