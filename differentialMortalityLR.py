import pandas as pd
from filterACS import get_dx_cols
import statsmodels.formula.api as sm
import numpy as np



surgical_emergency_codes = {
    "Acute_Appendicits": ["5409", "5400", "5401"],  # Acute appendicitis
    "Acute_Cholecystits": ["5750"],  # Acute cholecystitis
    "Necrotizing_Fasciitis": ["72886"], # Necrotizing fasciitis
    "Perforated_Diverticulitis": ["56210", "56211", "56213"], # Perforated diverticulitis
    "Acute_Perforated_Duodenal_Ulcer": ["5321"],  # Acute perforated duodenal ulcer
}

def do_lr(df, formula_str):
    lr = sm.logit(formula_str, data=df)
    res = lr.fit_regularized(maxiter=1000)

    odds_ratios = np.exp(res.params)
    lower_ci = np.exp(res.conf_int()[0])
    upper_ci = np.exp(res.conf_int()[1])

    print(res.summary())

    res_df = pd.DataFrame(data={"Odds Ratios": odds_ratios, "CI Lower": lower_ci, "CI Upper": upper_ci, "P Value": res.pvalues})
    res_df = res_df.drop(index="Intercept")  # Drop the intercept

    pd.set_option('display.max_columns', 5)
    print(res_df)

    return res_df

if __name__ == "__main__":
    comorbidity = "CM_DM"
    se_df = pd.read_csv("cache/acs.csv", low_memory=False)
    se_df = se_df[se_df["TRAN_OUT"] == 0]
    assert se_df["TRAN_OUT"].sum() == 0

    other_cms = [c for c in se_df.columns if c.startswith("CM_") and c != comorbidity]


    # First do baseline LR to show risk of mortality (controlled for APRDRG_Risk_Mortality) of the chosen comorbidity
    baseline_df = se_df[["DIED", "AGE", "acs_type", comorbidity] + other_cms].dropna()
    # formula_str = f"DIED ~ APRDRG_Risk_Mortality + {comorbidity}"
    formula_str = f"DIED ~ " + " + ".join([comorbidity] + other_cms + ["AGE", "C(acs_type)"])
    res_df = do_lr(baseline_df, formula_str)
    res_df.to_csv(f"results/baseline_lr_{comorbidity}.csv")

    def label_groups(r):
        # first determine if demographics are right
        if r["RACE"] == 1 and r["ZIPINC_QRTL"] == 4 and r["FEMALE"] == 0 and r["PAY1"] == 3 and r[comorbidity] == 1:
            return "HighHealthcareAccess_Comorbidity+"
        elif r["RACE"] == 2 and r["ZIPINC_QRTL"] == 1 and r["FEMALE"] == 0 and (not r["PAY1"] in [1, 3, 6]) and r[comorbidity] == 0:
            return "LowHealthcareAccess_Comorbidity-"
        else:
            return pd.NA

    se_df["Group"] = se_df.apply(label_groups, axis=1)
    access = se_df[se_df["Group"] == "HighHealthcareAccess_Comorbidity+"]
    noaccess = se_df[se_df["Group"] == "LowHealthcareAccess_Comorbidity-"]
    se_df = se_df[["Group", "DIED", "AGE", "acs_type"] + other_cms].dropna()

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

    formula_str = "DIED ~ C(Group, Treatment(reference='HighHealthcareAccess_Comorbidity+')) + " + " + ".join([c for c in other_cms if c not in dropped_cms] + ["AGE", "C(acs_type)"]) 
    print(formula_str)

    res_df = do_lr(se_df, formula_str)
    res_df.to_csv(f"results/adjustedor_{comorbidity}.csv")
