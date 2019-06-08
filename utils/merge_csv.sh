#!/usr/local/bin/sh

CSV_PATH="$1"
OUTPUT_PATH="$2"

# Ignore header row in files
for file in $CSV_PATH*; do
    if [ -f "$file" ]; then
        tail -q -n +2 "$file" | cut -f 1- -d "|" >> "$OUTPUT_PATH"merged.csv
    fi
done
