import pandas as pd
import re
import numpy as np
import statsmodels.api as sm


def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols

"""
Cross tab format:

            Disease     No Disease
Exposure
No Exposure
"""
def make_crosstab(exposure_group: pd.DataFrame, control_group: pd.DataFrame) -> np.ndarray:
    crosstab = np.zeros((2,2))
    crosstab[0,0] = len(exposure_group[exposure_group["DIED"] == 1])
    crosstab[0,1] = len(exposure_group[exposure_group["DIED"] == 0])
    crosstab[1,0] = len(control_group[control_group["DIED"] == 1])
    crosstab[1,1] = len(control_group[control_group["DIED"] == 0])
    
    return crosstab

def odds_ci(cross_tab, odds_ratio: float, confidence=0.95) -> tuple:
    z_confidence = 1.96  # TODO: fix magic number
    root = np.sqrt(sum([1 / x for x in cross_tab.values.flatten()]))
    base = np.log(odds_ratio)
    ci = (np.exp(base - z_confidence * root), np.exp(base + z_confidence * root))
    return ci


surgical_emergency_codes = [
    "5409", "5400", "5401",  # Acute appendicitis
    "5750",  # Acute cholecystitis
    "72886", # Necrotizing fasciitis
    "56210", "56211", "56213", # Perforated diverticulitis
    "5321",  # Acute perforated duodenal ulcer
]

if __name__ == "__main__":
    morbidity = "CM_DM"
    se_df = pd.read_csv("cache/acs.csv", low_memory=False)
    #se_df = se_df[se_df["TRAN_IN"] == 0]
    se_df = se_df[se_df["TRAN_OUT"] == 0]

    """
    Access group:
    - White
    - Male
    - High income quartile (4)
    - Private insurance
    """
    def filter_access(r):
        # first determine if demographics are right
        demo_filter = r["RACE"] == 1 and r["ZIPINC_QRTL"] == 4 and r["FEMALE"] == 0 and r["PAY1"] == 3

        if demo_filter:
            # Dropping other CMs leaves 0 cases!
            # cm_columns = [c for c in r.index if c.startswith("CM_") and c != morbidity]

            # # only CM is DM
            # return r[cm_columns].sum() == 0 and r[morbidity] ==1
            return r[morbidity] == 1
        else:
            return False

    access_group = se_df[se_df.apply(filter_access, axis=1)]

    """
    No access group:
    - Black
    - Male
    - Low income quartile (1)
    - Non-private / Non-medicare insurance
    """
    def filter_no_access(r):
        demo_filter = r["RACE"] == 2 and r["ZIPINC_QRTL"] == 1 and r["FEMALE"] == 0 and (not r["PAY1"] in [1, 3, 6])

        if demo_filter:
            return r[morbidity] == 0
        else:
            return False


    print("Odds for access vs no-access group:")
    no_access_group = se_df[se_df.apply(filter_no_access, axis=1)]

    mortality_access = len(access_group[access_group["DIED"] == 1])
    lived_access = len(access_group[access_group["DIED"] == 0])

    mortality_no_access = len(no_access_group[no_access_group["DIED"] == 1])
    lived_no_access = len(no_access_group[no_access_group["DIED"] == 0])

    crosstab = sm.stats.Table2x2(np.array([[mortality_access, lived_access], [mortality_no_access, lived_no_access]]))

    print(crosstab)

    print(f"Odds: {crosstab.oddsratio}")
    print(f"P value: {crosstab.oddsratio_pvalue()}")
    print(f"Confidence interval: {crosstab.oddsratio_confint()}")


    print("Odds for entire dataset")
    mortality_dm = len(se_df[(se_df[morbidity] == 1) & (se_df["DIED"] == 1)])
    lived_dm = len(se_df[(se_df[morbidity] == 1) & (se_df["DIED"] == 0)])

    mortality_no_dm = len(se_df[(se_df[morbidity] == 0) & (se_df["DIED"] == 1)])
    lived_no_dm = len(se_df[(se_df[morbidity] == 0) & (se_df["DIED"] == 0)])

    crosstab = sm.stats.Table2x2(np.array([[mortality_dm, lived_dm], [mortality_no_dm, lived_no_dm]]))
    print(crosstab)

    print(f"Odds: {crosstab.oddsratio}")
    print(f"P value: {crosstab.oddsratio_pvalue()}")
    print(f"Confidence interval: {crosstab.oddsratio_confint()}")




