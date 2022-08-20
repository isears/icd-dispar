import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import glob
import re

DX_CODES = ["K35", "K3521", "K3531", "K358", "5400"]


def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols


def process_single_file(fname):
    df = pd.DataFrame()

    columns = next(pd.read_stata(fname, chunksize=10)).columns
    dx_cols = get_dx_cols(columns)
    print(f"[{fname}] Using columns:")
    print(dx_cols)

    count = 0

    for chunk in pd.read_stata(fname, chunksize=10000, columns=["AGE"]):
        # chunk = chunk[chunk[get_dx_cols(chunk.columns)].isin(DX_CODES).any("columns")]
        count += len(chunk)

    print(f"{fname} count: {count}")


if __name__ == "__main__":
    files_to_process = list(glob.glob("data/*.dta"))
    print("Files:")
    print(files_to_process)

    print("Codes:")
    print(DX_CODES)

    print("-" * 10)

    for fname in files_to_process:
        process_single_file(fname)
