import pandas as pd
import subprocess

INPUT_DIR = "/tmp/LSRESULTS/"

def merge_csv_files():
    subprocess.call(["../utils/merge_csv.sh", "INPUT_DIR"])

def transform():
    df = pd.read_csv(INPUT_DIR + "merged.csv" , sep="|")
    df['AC_Code'] = df['AC_Code'].astype(str).str.zfill(2)
    df['OSN'] = df['OSN'].astype(str).str.zfill(2)
    df["Candidate_ID"] = df['State_Code'] + '_' + df['AC_Code'].astype(str)+ '_' + df['OSN'].astype(str)
    df["Constituency_ID"] = df['State_Code'] + '_' + df['AC_Code']

    # Rank the candidates by Total Votes, Within a constituency
    df['AC_Rank'] = df.groupby(['State','AC_Code'])['Total of Votes'].rank(ascending=False)
    df.sort_values(['State','AC_Code','AC_Rank'], inplace=True)

    # Calculate Difference of votes between positions
    df['Vote_Diff']= df.groupby(['State','AC_Code'])['Total of Votes'].diff(-1)

    # Find Constituency Type
    df['Constituency'], df['Constituency_Type'] = df['Constituency'].str.split('\(', 1).str
    df['Constituency_Type'] = df['Constituency_Type'].fillna("GEN")
    df['Constituency_Type'] = df['Constituency_Type'].str.replace("\)", "")

    return df


if __name__ == "__main__":
    merge_csv_files()
    out_df = transform()
    out_df.to_csv(INPUT_DIR + "ls_results_2019.csv")