#!/usr/bin/env python3
import csv
import glob
import sys
import json
from pathlib import Path
from collections import defaultdict

MAPPING_FILE = "patnr_bsn_mapping.json"

def load_bsns(file_path):
    bsns = []
    with open(file_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) < 2:
                continue
            bsn = row[1].strip()
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
            if not reader.fieldnames:
                continue
            fieldnames = [h.strip() for h in reader.fieldnames]
            if 'Patnr' not in fieldnames:
                print(f"Skipping {filename}: headers={fieldnames}")
                continue
            seen_in_file = set()
            for row in reader:
                value = row.get('Patnr')
                if value:
                    seen_in_file.add(value.strip())
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
            if not reader.fieldnames:
                continue
            fieldnames = [h.strip() for h in reader.fieldnames]
            if 'Patnr' not in fieldnames:
                print(f"Skipping {filename}: no Patnr column")
                continue

            # Rename Patnr column to BSN
            new_fieldnames = ['BSN' if f == 'Patnr' else f for f in fieldnames]

            writer = csv.DictWriter(outfile, fieldnames=new_fieldnames, delimiter=';')
            writer.writeheader()

            for row in reader:
                patnr = row.get('Patnr')
                if patnr and patnr in mapping:
                    row['Patnr'] = mapping[patnr]
                writer.writerow({('BSN' if k=='Patnr' else k): v for k,v in row.items()})

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
    except FileNotFoundError:
        mapping = {}

    # Load all fake BSNs
    bsns = load_bsns(bsn_file)
    used_bsns = set(mapping.values())
    unused_bsns = [b for b in bsns if b not in used_bsns]

    # Collect all Patnr
    patnrs, patnr_files = collect_patnrs(csv_pattern)

    # Determine new Patnr not yet in mapping
    new_patnrs = [p for p in patnrs if p not in mapping]
    if len(unused_bsns) < len(new_patnrs):
        raise ValueError(f"Not enough unused BSNs for {len(new_patnrs)} new Patnr values")

    # Assign BSNs to new Patnr
    for i, patnr in enumerate(new_patnrs):
        mapping[patnr] = unused_bsns[i]

    if not commit:
        print("DRY RUN (no files will be written)")
        print("Patnr;BSN;FileCount")
        for p in patnrs:
            count = len(patnr_files[p])
            print(f"{p};{mapping[p]};{count}")
    else:
        # Save mapping
        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        print(f"Mapping saved to {MAPPING_FILE}")

        # Write mapped files with renamed header
        write_mapped_files(csv_pattern, mapping)

if __name__ == "__main__":
    main()
