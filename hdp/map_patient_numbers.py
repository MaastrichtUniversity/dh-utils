#!/usr/bin/env python3

import csv
import glob
import sys
import json
from pathlib import Path
from collections import defaultdict

MAPPING_FILE = "patnr_bsn_mapping.json"


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


def load_bsns(file_path):
    bsns = []

    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')

        for row in reader:
            if len(row) < 2:
                continue

            bsn = normalize(row[1])

            if bsn:
                bsns.append(bsn)

    return bsns


def collect_patnrs(path_pattern):
    patnr_files = defaultdict(set)

    for filename in glob.glob(path_pattern):

        # Skip already processed files
        if filename.endswith("_bsn.csv"):
            continue

        with open(filename, newline='', encoding='utf-8-sig') as f:

            reader = csv.DictReader(f, delimiter=';')
            normalize_fieldnames(reader)

            if not reader.fieldnames:
                continue

            if 'Patnr' not in reader.fieldnames:
                print(f"Skipping {filename}: headers={reader.fieldnames}")
                continue

            seen_in_file = set()

            for row_number, row in enumerate(reader, start=2):

                patnr = normalize(row.get('Patnr'))

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

        with open(input_path, newline='', encoding='utf-8-sig') as infile, \
             open(output_path, 'w', newline='', encoding='utf-8') as outfile:

            reader = csv.DictReader(infile, delimiter=';')
            normalize_fieldnames(reader)

            if not reader.fieldnames:
                continue

            if 'Patnr' not in reader.fieldnames:
                print(f"Skipping {filename}: no Patnr column")
                continue

            # Rename Patnr column to BSN
            new_fieldnames = [
                'BSN' if f == 'Patnr' else f
                for f in reader.fieldnames
            ]

            writer = csv.DictWriter(
                outfile,
                fieldnames=new_fieldnames,
                delimiter=';'
            )

            writer.writeheader()

            for row_number, row in enumerate(reader, start=2):

                original_patnr = row.get('Patnr')
                normalized_patnr = normalize(original_patnr)

                if normalized_patnr:

                    if normalized_patnr in mapping:
                        row['Patnr'] = mapping[normalized_patnr]
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

                    if normalized_key == 'Patnr':
                        output_row['BSN'] = value
                    else:
                        output_row[normalized_key] = value

                writer.writerow(output_row)

        print(f"Written: {output_path}")


def main():

    if len(sys.argv) < 3:
        print("Usage: script.py '<csv_pattern>' <fake_bsns.csv> [--commit]")
        sys.exit(1)

    csv_pattern = sys.argv[1]
    bsn_file = sys.argv[2]
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
