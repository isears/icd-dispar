import pandas as pd
import re
import numpy as np
from scipy.stats import fisher_exact


def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols


surgical_emergency_codes = [
    "5409", "5400", "5401",  # Acute appendicitis
    "5750",  # Acute cholecystitis
    "72886", # Necrotizing fasciitis
    "56210", "56211", "56213", # Perforated diverticulitis
    "5321",  # Acute perforated duodenal ulcer
]

Years = range(2003, 2015)

if __name__ == "__main__":
    df = pd.DataFrame()

    for year in Years:
        print(f"Processing data for year: {year}")
        for chunk in pd.read_stata(f"data/NIS_{year}_Full.dta", chunksize=10000):
            chunk = chunk[chunk[get_dx_cols(chunk.columns)].isin(surgical_emergency_codes).any("columns")]
            chunk = chunk[chunk["TRAN_OUT"] == 0]

            df = df.append(chunk)

        df.info()

    df.to_csv("cache/acs.csv", index=False)

   