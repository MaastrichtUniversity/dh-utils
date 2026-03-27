#!/bin/bash

file="$1"

# Read header (first line)
header=$(head -n 1 "$file")

# Extract 2nd column name
col2=$(echo "$header" | cut -d';' -f2)

# Only proceed if it matches
if [[ "$col2" == "VERANTW_MEDEW" ]]; then
    tmp=$(mktemp)

    cut -d';' -f1,3- "$file" > "$tmp" && mv "$tmp" "$file"
    echo "Column removed."
else
    echo "Second column is not VERANTW_MEDEW. No changes made."
fi
