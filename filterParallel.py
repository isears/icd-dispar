import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import glob
import re
import os
from timeit import default_timer as timer


pd.options.mode.chained_assignment = None

# https://www.icd10data.com/ICD10CM/Codes/K00-K95/K35-K38/K35-#K35.2
DX_CODES = {
    "acute_appendicitis": ["5409", "5400", "5401"],  # Acute appendicitis
    "acute_cholecystitis": ["5750"],  # Acute cholecystitis
    "necrotizing_fasciitis": ["72886"], # Necrotizing fasciitis
    "perforated_diverticulitis": ["56210", "56211", "56213"], # Perforated diverticulitis
    "acute_perforated_duodenal_ulcer": ["5321"],  # Acute perforated duodenal ulcer
}

def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols

def process_chunk(chunk):
        print(f"Spawned chunk worker {os.getpid()}")
        start = timer()
        dx_columns = get_dx_cols(chunk.columns)
        # Initial filtering
        chunk = chunk[chunk["TRAN_OUT"] == 0]

        saved_parts = list()
        for dx_category, codes in DX_CODES.items():
            dx_only = chunk[chunk[dx_columns].isin(codes).any("columns")]
            dx_only["acs_type"] = dx_category

            saved_parts.append(dx_only)


        end = timer()
        print(f"Chunk workder {os.getpid()} finished in {end - start}")
        return pd.concat(saved_parts)

def process_single_file(fname):
    print(f"[*] Processing {fname}")
    df  = pd.DataFrame()

    columns = next(pd.read_stata(fname, chunksize=1)).columns
    dx_columns = get_dx_cols(columns)
    used_columns = dx_columns
    used_columns += [c for c in columns if c.startswith("CM_")]
    used_columns += ["DIED", "TRAN_OUT", "TRAN_IN", "AGE", "APRDRG_Risk_Mortality", "APRDRG_Severity", "FEMALE", "ZIPINC_QRTL", "PAY1", "RACE", "HOSP_REGION"]
    print(f"[{fname}] Using columns:")
    print(used_columns)

    with ProcessPoolExecutor(max_workers=len(os.sched_getaffinity(0))) as exe:
        chunk_generator = pd.read_stata(fname, chunksize=1000000, columns=used_columns)
        results = exe.map(process_chunk, chunk_generator)

    
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

    results = list()
    for fname in files_to_process:
        results.append(process_single_file(fname))
    
    df = pd.concat(results)
    df.info()
    df.to_csv("cache/acs.csv", index=False)