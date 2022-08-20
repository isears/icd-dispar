import re
import pandas as pd
from filterParallel import DX_CODES


def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols


if __name__ == "__main__":
    aids_codes = ["B20", "42", "042", "V08"]

    df = pd.read_csv("cache/bla.csv")

    dx_cols = get_dx_cols(df.columns)

    df['AIDS'] = df[dx_cols].isin(aids_codes).any("columns")

    aids_count = len(df[df["AIDS"]])
    all_count = len(df)

    print("UnWeighted statistics:")
    print(f"AIDS: {aids_count}")
    print(f"All: {all_count}")
    print(f"{aids_count / all_count * 100} %")


    weighted_aids = df[df["AIDS"]]["DISCWT"].sum()
    weighted_all = df[~df["AIDS"]]["DISCWT"].sum()

    print("Weighted statistics:")
    print(f"AIDS: {weighted_aids}")
    print(f"All: {weighted_all}")
    print(f"{weighted_aids / weighted_all * 100} %")

    code_df = pd.DataFrame()
    for code in DX_CODES:
        code_count = len(df[(df == code).any("columns")])

        code_df = code_df.append({"Code": code, "Raw Count": code_count, "Percent": (code_count / all_count) * 100}, ignore_index=True)


    print(code_df)
    code_df.to_csv("counts_by_code.csv", index=False)
    print(code_df.Percent.sum())
