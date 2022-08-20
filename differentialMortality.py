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

if __name__ == "__main__":
    se_df = pd.read_csv("cache/acs.csv", low_memory=False)
    #se_df = se_df[se_df["TRAN_IN"] == 0]
    #se_df = se_df[se_df["TRAN_OUT"] == 0]

    """
    Access group:
    - White
    - Male
    - High income quartile (4)
    - Private insurance
    """
    def filter_access(r):
        return r["RACE"] == 1 and r["ZIPINC_QRTL"] == 4 and r["PAY1"] == 3 and r["CM_CHRNLUNG"] == 1

    access_group = se_df[se_df.apply(filter_access, axis=1)]

    """
    No access group:
    - Black
    - Male
    - Low income quartile (1)
    - Non-private / Non-medicare insurance
    """
    def filter_no_access(r):
        return r["RACE"] == 2 and r["ZIPINC_QRTL"] == 1 and (not r["PAY1"] in [1, 3, 6]) and r["CM_CHRNLUNG"] == 0


    no_access_group = se_df[se_df.apply(filter_no_access, axis=1)]

    mortality_access = len(access_group[access_group["DIED"] == 1])
    lived_access = len(access_group[access_group["DIED"] == 0])

    mortality_no_access = len(no_access_group[no_access_group["DIED"] == 1])
    lived_no_access = len(no_access_group[no_access_group["DIED"] == 0])

    crosstab = np.array([[mortality_access, lived_access], [mortality_no_access, lived_no_access]])

    print(crosstab)

    odds, pval = fisher_exact(crosstab)
    print(f"Odds: {odds}")
    print(f"P value: {pval}")

    mortality_dm = len(se_df[(se_df["CM_CHRNLUNG"] == 1) & (se_df["DIED"] == 1)])
    lived_dm = len(se_df[(se_df["CM_CHRNLUNG"] == 1) & (se_df["DIED"] == 0)])

    mortality_no_dm = len(se_df[(se_df["CM_CHRNLUNG"] == 0) & (se_df["DIED"] == 1)])
    lived_no_dm = len(se_df[(se_df["CM_CHRNLUNG"] == 0) & (se_df["DIED"] == 0)])

    crosstab = np.array([[mortality_no_dm, lived_no_dm], [mortality_dm, lived_dm]])

    print(crosstab)

    odds, pval = fisher_exact(crosstab)
    print(f"Odds: {odds}")
    print(f"P value: {pval}")



