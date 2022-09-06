import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import re
import os
from timeit import default_timer as timer


pd.options.mode.chained_assignment = None

# https://www.icd10data.com/ICD10CM/Codes/K00-K95/K35-K38/K35-#K35.2
DX_CODES = {
    # "acute_appendicitis": ["5409", "5400", "5401"],  # Acute appendicitis
    # "acute_cholecystitis": ["5750"],  # Acute cholecystitis
    "perforated_diverticulitis": ["56213"], # Perforated diverticulitis
    "nonperforated_diverticulitis": ["56211"]
    # "acute_perforated_duodenal_ulcer": ["5321"],  # Acute perforated duodenal ulcer
    #"postoperative_infection": ["9985", "99851", "99859"]

}

def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols

def get_proc_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^PR[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_PR[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols

def process_chunk(chunk):
        dx_columns = get_dx_cols(chunk.columns)
        codes_of_interest = sum([val for _, val in DX_CODES.items()], [])

        chunk = chunk[chunk[dx_columns].isin(codes_of_interest).any("columns")]
        chunk = chunk[chunk["TRAN_OUT"] == 0]
        return chunk

def process_single_file(fname):
    print(f"[*] Processing {fname}")
    df  = pd.DataFrame()

    columns = next(pd.read_stata(fname, chunksize=1)).columns
    dx_columns = get_dx_cols(columns)
    proc_columns = get_proc_cols(columns)
    used_columns = list()
    used_columns = dx_columns
    used_columns += proc_columns
    used_columns += [c for c in columns if c.startswith("CM_")]
    used_columns += ["AGE", "APRDRG_Risk_Mortality", "APRDRG_Severity", "FEMALE", "ZIPINC_QRTL", "PAY1", "HOSP_REGION", "DIED", "RACE", "LOS", "TRAN_OUT"]
    print(f"[{fname}] Using columns:")
    print(used_columns)

    results = list()
    for chunk in pd.read_stata(fname, chunksize=1000000, columns=used_columns):
        results.append(process_chunk(chunk))

    
    df = pd.concat(results)

    print(f"[+] Finished processing: {fname}")

    return df

if __name__ == "__main__":
    files_to_process = [f"data/NIS_{idx}_Full.dta" for idx in range(2010, 2015)]
    print("Files:")
    print(files_to_process)

    print("Codes:")
    print(DX_CODES)

    print("-"*10)

    with ProcessPoolExecutor(max_workers=len(os.sched_getaffinity(0))) as exe:
        results = exe.map(process_single_file, files_to_process)
    
    df = pd.concat(results)
    df.info()
    df.to_csv("cache/acs.csv", index=False)