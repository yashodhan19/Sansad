import glob
import os
import sys

INPUT_DIR = sys.argv[0]

out_filename = "combined_seizure_reports.csv"
if os.path.exists(out_filename):
    os.remove(out_filename)

read_files = glob.glob("INPUT_DIR/*.csv")
with open(out_filename, "w") as outfile:
    for filename in read_files:
        with open(filename) as infile:
            for line in infile:
                outfile.write('{},{}\n'.format(line.strip(), os.path.basename(filename)))