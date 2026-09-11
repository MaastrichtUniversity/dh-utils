#!/usr/bin/env python3

import csv
import glob
import sys
import json
from io import StringIO
from pathlib import Path
from collections import defaultdict

MAPPING_FILE = "patnr_bsn_mapping.json"
BSN_LENGTH = 9
CSV_ENCODINGS = ('utf-8-sig', 'cp1252', 'latin-1')


def normalize(value):
    """
    Normalize CSV values so visually identical Patnr values
    become truly identical keys.

    Handles:
    - None
    - leading/trailing whitespace
    - BOM characters
    - non-breaking spaces
    - zero-width spaces
    """
    if value is None:
        return None

    return (
        str(value)
        .replace('\ufeff', '')   # BOM
        .replace('\u200b', '')   # zero-width space
        .replace('\u00a0', ' ')  # non-breaking space
        .strip()
    )


def normalize_fieldnames(reader):
    """
    Normalize DictReader fieldnames in-place.
    """
    if reader.fieldnames:
        reader.fieldnames = [normalize(h) for h in reader.fieldnames]


def get_patnr_fieldname(fieldnames):
    """
    Return the first supported patient number column name.
    """
    if not fieldnames:
        return None

    for candidate in ('Patnr', 'PAT_ID'):
        if candidate in fieldnames:
            return candidate

    return None


def read_csv_text(file_path):
    for encoding in CSV_ENCODINGS:
        try:
            with open(file_path, newline='', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Unable to decode CSV file: {file_path}")


def load_bsns(file_path):
    rows = list(csv.reader(StringIO(read_csv_text(file_path), newline=''),
                           delimiter=';'))

    bsns = []
    for line_number, row in enumerate(rows, start=1):
        if len(row) < 2:
            continue

        bsn = normalize(row[1])
        if not bsn:
            continue

        if not (bsn.isascii() and bsn.isdigit() and len(bsn) == BSN_LENGTH):
            raise ValueError(
                f"Invalid BSN in {file_path} line {line_number}: {bsn!r}. "
                "Expected a semicolon-delimited fake BSN file with a "
                "nine-digit BSN in column 2."
            )

        bsns.append(bsn)

    if not bsns:
        raise ValueError(f"No BSNs found in {file_path}")

    return bsns


def collect_patnrs(path_pattern):
    patnr_files = defaultdict(set)

    for filename in glob.glob(path_pattern):

        # Skip already processed files
        if filename.endswith("_bsn.csv"):
            continue

        with StringIO(read_csv_text(filename), newline='') as file:
            reader = csv.DictReader(file, delimiter=';')
            normalize_fieldnames(reader)

            if not reader.fieldnames:
                continue

            patnr_fieldname = get_patnr_fieldname(reader.fieldnames)

            if not patnr_fieldname:
                print(f"Skipping {filename}: headers={reader.fieldnames}")
                continue

            seen_in_file = set()

            for row_number, row in enumerate(reader, start=2):

                patnr = normalize(row.get(patnr_fieldname))

                if patnr:
                    seen_in_file.add(patnr)

            for patnr in seen_in_file:
                patnr_files[patnr].add(filename)

    sorted_patnrs = sorted(patnr_files.keys())

    return sorted_patnrs, patnr_files


def write_mapped_files(path_pattern, mapping):

    for filename in glob.glob(path_pattern):

        if filename.endswith("_bsn.csv"):
            continue

        input_path = Path(filename)
        output_path = input_path.with_name(input_path.stem + "_bsn.csv")

        with (
            StringIO(read_csv_text(input_path), newline='') as infile,
            open(output_path, 'w', newline='', encoding='utf-8') as outfile,
        ):

            reader = csv.DictReader(infile, delimiter=';')
            normalize_fieldnames(reader)

            if not reader.fieldnames:
                continue

            patnr_fieldname = get_patnr_fieldname(reader.fieldnames)

            if not patnr_fieldname:
                print(f"Skipping {filename}: no Patnr/PAT_ID column")
                continue

            # Rename Patnr column to BSN
            new_fieldnames = [
                'BSN' if f in ('Patnr', 'PAT_ID') else f
                for f in reader.fieldnames
            ]

            writer = csv.DictWriter(
                outfile,
                fieldnames=new_fieldnames,
                delimiter=';'
            )

            writer.writeheader()

            for row_number, row in enumerate(reader, start=2):

                original_patnr = row.get(patnr_fieldname)
                normalized_patnr = normalize(original_patnr)

                if normalized_patnr:

                    if normalized_patnr in mapping:
                        row[patnr_fieldname] = mapping[normalized_patnr]
                    else:
                        print(
                            f"WARNING: No mapping found in {filename} "
                            f"line {row_number}: "
                            f"{repr(original_patnr)} "
                            f"(normalized={repr(normalized_patnr)})"
                        )

                # Write row with renamed header
                output_row = {}

                for key, value in row.items():
                    normalized_key = normalize(key)

                    if normalized_key == patnr_fieldname:
                        output_row['BSN'] = value
                    else:
                        output_row[normalized_key] = value

                writer.writerow(output_row)

        print(f"Written: {output_path}")


def main():

    arguments = [argument for argument in sys.argv[1:] if argument != "--commit"]

    if len(arguments) != 2:
        print("Usage: script.py '<csv_pattern>' <fake_bsns.csv> [--commit]")
        print("Quote <csv_pattern> so the shell does not expand it.")
        sys.exit(1)

    csv_pattern, bsn_file = arguments
    commit = "--commit" in sys.argv

    # Load existing mapping
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        # Normalize loaded mapping keys/values
        mapping = {
            normalize(k): normalize(v)
            for k, v in mapping.items()
        }

    except FileNotFoundError:
        mapping = {}

    # Load all fake BSNs
    bsns = load_bsns(bsn_file)

    used_bsns = set(mapping.values())

    unused_bsns = [
        b for b in bsns
        if b not in used_bsns
    ]

    # Collect all Patnr values
    patnrs, patnr_files = collect_patnrs(csv_pattern)

    # Determine new Patnr values not yet mapped
    new_patnrs = [
        p for p in patnrs
        if p not in mapping
    ]

    if len(unused_bsns) < len(new_patnrs):
        raise ValueError(
            f"Not enough unused BSNs for "
            f"{len(new_patnrs)} new Patnr values"
        )

    # Assign BSNs to new Patnr values
    for i, patnr in enumerate(new_patnrs):
        mapping[patnr] = unused_bsns[i]

    if not commit:

        print("DRY RUN (no files will be written)")
        print("Patnr;BSN;FileCount")

        for patnr in patnrs:
            count = len(patnr_files[patnr])

            print(f"{patnr};{mapping[patnr]};{count}")

    else:

        # Save mapping
        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(
                mapping,
                f,
                indent=2,
                ensure_ascii=False
            )

        print(f"Mapping saved to {MAPPING_FILE}")

        # Write mapped files
        write_mapped_files(csv_pattern, mapping)


if __name__ == "__main__":
    main()
