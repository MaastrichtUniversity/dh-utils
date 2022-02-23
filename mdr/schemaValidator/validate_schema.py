import argparse
import json


class SchemaValidator:
    ERROR_COUNT = 0
    WARNING_COUNT = 0

    def __init__(self, args):
        self.file = args.file

    def validate(self):
        schema = self.open_and_parse()
        if schema:
            pass

    def open_and_parse(self):
        schema = None
        try:
            schema = json.loads(self.file.read())
        except ValueError as e:
            self.ERROR_COUNT += 1
            print(f"ERROR: error encountered while parsing the schema as json: '{e}'")
        return schema


def main():
    parser = argparse.ArgumentParser(description="validate schema description")
    parser.add_argument("file", type=argparse.FileType("r"), help="Path to the schema to validate")
    args = parser.parse_args()

    if not args.file.name.endswith(".json"):
        exit(f"Invalid file path provided. Should be a '.json' file")

    validator = SchemaValidator(args)
    validator.validate()
    print("Summary:")
    print(f"\t {validator.ERROR_COUNT} error(s) encountered")
    print(f"\t {validator.WARNING_COUNT} warning(s) encountered")


if __name__ == "__main__":
    main()
