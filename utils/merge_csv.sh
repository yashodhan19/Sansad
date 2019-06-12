#!/usr/local/bin/sh

CSV_PATH="$1"

# Ignore header row in files
for file in $CSV_PATH*; do
    if [ -f "$file" ]; then
        tail -q -n +2 "$file" | cut -f 1- -d "|" >> merged.csv
    fi
done
