import glob
import pandas as pd

if __name__ == "__main__":
    sum_no_weight = 0
    sum_weight = 0
    for fname in glob.glob("cache/NIS_*.appendicitis.csv"):
        print(fname)

        df = pd.read_csv(fname, usecols=["DISCWT"])
        sum_no_weight += len(df)
        sum_weight += df["DISCWT"].sum()


    print(sum_no_weight)
    print(sum_weight)
