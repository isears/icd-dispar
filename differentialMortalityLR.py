import pandas as pd
from filterACS import get_dx_cols
from filterParallel import DX_CODES
import statsmodels.formula.api as sm
import numpy as np


def do_lr(df, formula_str):
    lr = sm.logit(formula_str, data=df)
    res = lr.fit_regularized(maxiter=1000)

    odds_ratios = np.exp(res.params)
    lower_ci = np.exp(res.conf_int()[0])
    upper_ci = np.exp(res.conf_int()[1])

    #print(res.summary())

    res_df = pd.DataFrame(data={"Odds Ratios": odds_ratios, "CI Lower": lower_ci, "CI Upper": upper_ci, "P Value": res.pvalues})
    res_df = res_df.drop(index="Intercept")  # Drop the intercept

    pd.set_option('display.max_columns', 5)
    print(res_df)

    return res_df

if __name__ == "__main__":
    comorbidity = "CM_DM"
    se_df = pd.read_csv("cache/acs.csv", low_memory=False)
    #se_df = se_df[(se_df["ORPROC"] == 1)]

    other_cms = [c for c in se_df.columns if c.startswith("CM_") and c != comorbidity]

    # Labeling utility functions
    def label_groups_comorbid(r):
        if r["ZIPINC_QRTL"] == 4 and r["PAY1"] == 3 and r[comorbidity] == 1:
            return "HighHealthcareAccess_Comorbidity+"
        elif r["ZIPINC_QRTL"] == 1 and (not r["PAY1"] in [1, 3, 6]) and r[comorbidity] == 0:
            return "LowHealthcareAccess_Comorbidity-"
        else:
            return pd.NA

    def get_highaccess(r):
        return r["ZIPINC_QRTL"] == 4 and r["PAY1"] == 3

    def label_groups(r):
        if r["ZIPINC_QRTL"] == 4 and r["PAY1"] == 3:
            return "HighHealthcareAccess"
        elif r["ZIPINC_QRTL"] == 1 and (not r["PAY1"] in [1, 3, 6]):
            return "LowHealthcareAccess"
        else:
            return pd.NA

    # Do LR to find adjusted odds ratios for high access vs low access
    access_df = se_df
    access_df["access_group"] = se_df.apply(label_groups, axis=1)
    access_df = access_df[["postoperative_infection", "access_group", "AGE", "FEMALE", "ZIPINC_QRTL", "PAY1", comorbidity] + other_cms].dropna()
    formula_str = f"postoperative_infection ~ C(access_group, Treatment(reference='HighHealthcareAccess')) + " + " + ".join([comorbidity] + other_cms + ["AGE", "FEMALE"])
    res_df = do_lr(access_df, formula_str)


    # Do baseline LR to show risk of mortality (controlled for APRDRG_Risk_Mortality) of the chosen comorbidity
    high_access_df = se_df[["postoperative_infection", "AGE", "FEMALE", "ZIPINC_QRTL", "PAY1", comorbidity] + other_cms].dropna()
    high_access_df = high_access_df[high_access_df.apply(get_highaccess, axis=1)]

    formula_str = f"postoperative_infection ~ " + " + ".join([comorbidity] + other_cms + ["AGE", "FEMALE"])
    res_df = do_lr(high_access_df, formula_str)
    res_df.to_csv(f"results/highaccess_lr_{comorbidity}.csv")

    se_df["Group"] = se_df.apply(label_groups_comorbid, axis=1)
    access = se_df[se_df["Group"] == "HighHealthcareAccess_Comorbidity+"]
    noaccess = se_df[se_df["Group"] == "LowHealthcareAccess_Comorbidity-"]
    se_df = se_df[["Group", "postoperative_infection", "AGE"] + other_cms].dropna()

    # Remove low-prevalence CMs
    dropped_cms = list()
    for cm in other_cms:
        if access[cm].sum() == 0:
            print(f"Dropping {cm} for not being present in access group")
            se_df = se_df.drop(columns=[cm])
            dropped_cms.append(cm)
        elif noaccess[cm].sum() == 0:
            print(f"Dropping {cm} for not being present in access group")
            se_df = se_df.drop(columns=[cm])
            dropped_cms.append(cm)

    formula_str = "postoperative_infection ~ C(Group, Treatment(reference='HighHealthcareAccess_Comorbidity+')) + " + " + ".join([c for c in other_cms if c not in dropped_cms] + ["AGE"]) 
    print(formula_str)

    res_df = do_lr(se_df, formula_str)
    res_df.to_csv(f"results/adjustedor_{comorbidity}.csv")
