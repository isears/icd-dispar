import pandas as pd
import re
import numpy as np
import glob


def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols

def get_dx_cols2(all_cols):
    icd9_cols = [col for col in all_cols if col.startswith("DX")]
    icd10_cols = [col for col in all_cols if col.startswith("I10_DX")]

    assert len(icd9_cols + icd10_cols) > 0
    return icd9_cols + icd10_cols

appendicitis_codes = [
    "K35", "K3521", "K3531", "K358", "5400"
]

if __name__ == "__main__":
    df = pd.DataFrame()

    for fname in glob.glob("data/*.dta"):
        print(f"Processing file: {fname}")
        pop_count = 0
        appendicitis_count = 0
        for chunk in pd.read_stata(fname, chunksize=1000000):
            appendicitis_only = chunk[chunk[get_dx_cols2(chunk.columns)].isin(appendicitis_codes).any("columns")]
            pop_count += len(chunk)
            appendicitis_count += len(appendicitis_only)

            df = pd.concat([df, appendicitis_only])

        
        print(f"Total appendicitis this year: {appendicitis_count}")
        print(f"Proportion of hospital stays: {appendicitis_count / pop_count}")
        print(f"Total stay count: {pop_count}")

    df.to_csv("cache/appendicitis.csv", index=False)

   