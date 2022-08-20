import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import glob
import re

# https://www.icd10data.com/ICD10CM/Codes/K00-K95/K35-K38/K35-#K35.2
DX_CODES = [
    "K35", "K352", "K3521", "K3520", "K353", "K3530", "K3532", "K3533", "K3531", "K358", "K3580", "K3589", "K35890", "K35891", "5400", "5401", "5409", "540"
]

def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols


def has_appendicitis(row):
    for c in DX_CODES:
        if row.str.startswith(c).any():
            return True

    return False


def process_single_file(fname):
    print(f"[*] Processing {fname}")
    df  = pd.DataFrame()

    columns = next(pd.read_stata(fname, chunksize=1)).columns
    dx_cols = get_dx_cols(columns)
    dx_cols += ["DISCWT"]
    print(f"[{fname}] Using columns:")
    print(dx_cols)

    total_admissions = 0
    total_appendicits = 0

    for chunk in pd.read_stata(fname, chunksize=100000, columns=dx_cols):
        total_admissions += len(chunk)
        chunk = chunk[chunk.isin(DX_CODES).any("columns")]

        total_appendicits += len(chunk)

        df = pd.concat([df, chunk])


    print(f"[{fname}] Total admissions: {total_admissions}")
    print(f"[{fname}] Total appendicitis: {total_appendicits}")

    print(f"[+] Finished processing: {fname}")

    df.to_csv(f"cache/{fname.split('/')[-1]}.appendicitis.csv", index=False)
    return df



if __name__ == "__main__":
    files_to_process = list(glob.glob("data/*.dta"))
    #files_to_process = ["data/NIS_2016_Full.dta"]
    print("Files:")
    print(files_to_process)

    print("Codes:")
    print(DX_CODES)

    print("-"*10)

    with ProcessPoolExecutor(max_workers=30) as exe:        
        results = exe.map(process_single_file,files_to_process)
    
    df = pd.concat(results)
    df.info()
    df.to_csv("cache/bla.csv", index=False)