import pandas as pd
import re
import statsmodels.formula.api as sm
import numpy as np
import icd10

OUTCOME_COLS=["RACE", "HOSP_REGION", "ZIPINC_QRTL"]


def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols


if __name__ == "__main__":
    df = pd.read_stata("cache/testdata.dta")
    dx_cols = get_dx_cols(df.columns)

    # Could also be a sum() agg, there are some cases of double assignment
    dx_dummies = pd.get_dummies(df[dx_cols], prefix='', prefix_sep='').groupby(level=0, axis=1).max()
    dx_dummies = dx_dummies.drop(columns=['', 'incn'])

    # Drop columns with less than 1%
    dx_dummies = dx_dummies.loc[:, dx_dummies.sum() > (len(dx_dummies) * 0.01)]

    lr_df = pd.DataFrame()
    lr_df["LOWINCOME"] = (df["ZIPINC_QRTL"] == 1.0).astype(int)
    lr_df = pd.concat([lr_df, dx_dummies], axis=1)

    formula_str = f"LOWINCOME ~ " + " + ".join([f"{col}" for col in dx_dummies.columns])

    print(f"Formula string: {formula_str}")
    lr = sm.logit(formula_str, data=lr_df)
    res = lr.fit_regularized()

    odds_ratios = np.exp(res.params)
    lower_ci = np.exp(res.conf_int()[0])
    upper_ci = np.exp(res.conf_int()[1])

    table_out = pd.DataFrame(
        data={
            "Odds Ratios": odds_ratios,
            "Lower CI": lower_ci,
            "Upper CI": upper_ci,
            "P Value": res.pvalues,
        },
        index=res.params.index,
    )

    table_out = table_out.iloc[1:,:]  # Remove intercept
    table_out = table_out.sort_values(by="P Value", ascending=True)
    table_out["Code Description"] = table_out.index.map(lambda x: icd10.find(x).description)
    print(table_out)

    table_out.to_csv("./lowincome_icd_codes.csv")

    print("Done")

    