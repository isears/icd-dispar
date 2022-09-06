import pandas as pd
import re

pd.options.mode.chained_assignment = None  # default='warn'


def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols

def get_proc_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^PR[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_PR[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols


def general_stats(has_dm: pd.DataFrame, no_dm: pd.DataFrame):
    df_out = pd.DataFrame(columns=["Diabetes", "No Diabetes"])
    df_out.loc["Total (n)"] = [len(has_dm), len(no_dm)]
    df_out.loc["AGE (mean)"] = [has_dm.AGE.mean(), no_dm.AGE.mean()]
    df_out.loc["FEMALE (%)"] = [len(has_dm[has_dm["FEMALE"] == 1]) / len(has_dm) * 100, len(no_dm[no_dm["FEMALE"] == 1]) / len(no_dm) * 100]
    df_out.loc["ZIPINC_QRTL (mean)"] = [has_dm["ZIPINC_QRTL"].mean(), no_dm["ZIPINC_QRTL"].mean()]
    df_out.loc["DIED (%)"] = [len(has_dm[has_dm["DIED"] == 1]) / len(has_dm) * 100, len(no_dm[no_dm["DIED"] == 1]) / len(no_dm) * 100]
    df_out.loc["LOS (mean)"] = [has_dm["LOS"].mean(), no_dm["LOS"].mean()]
    df_out = pd.concat([df_out, pd.DataFrame({"Diabetes": has_dm["RACE"].value_counts(normalize=True) * 100, "No Diabetes": no_dm["RACE"].value_counts(normalize=True) * 100})])
    df_out = df_out.rename(index={1.0: "RACE: White", 2.0: "RACE: Black", 3.0: "RACE: Hispanic", 4.0: "RACE: Asian or Pacific Islander", 5.0: "RACE: Native American", 6.0: "RACE: Other"})

    return df_out


if __name__ == "__main__":
    base_df = pd.read_csv("cache/acs.csv", low_memory=False)
    dx_cols = get_dx_cols(base_df.columns)
    proc_cols = get_proc_cols(base_df.columns)

    # All types of diverticulitis
    print("Analyzing all diverticulitis cases...")

    has_dm = base_df[base_df["CM_DM"] == 1]
    no_dm = base_df[base_df["CM_DM"] == 0]

    table1 = general_stats(has_dm, no_dm)
    table1.loc["Presented w/Perforation (%)"] = [len(has_dm[has_dm[dx_cols].isin(["56213"]).any("columns")]) / len(has_dm) * 100, len(no_dm[no_dm[dx_cols].isin(["56213"]).any("columns")]) / len(no_dm) * 100]

    print(table1)
    table1.to_csv("diverticulitis/diverticulitis_all_types.csv")

    # Perforated diverticulitis subset
    print("Analyzing perforated diverticulitis subset...")
    perf_df = base_df[base_df[dx_cols].isin(["56213"]).any("columns")]
    has_dm = perf_df[perf_df["CM_DM"] == 1]
    no_dm = perf_df[perf_df["CM_DM"] == 0]
    table2 = general_stats(has_dm, no_dm)

    def has_ir_percent(df: pd.DataFrame):
        return len(df[df[proc_cols].isin(["5491"]).any("columns")]) / len(df) * 100

    table2.loc["Had IR procedure (%)"] = [has_ir_percent(has_dm), has_ir_percent(no_dm)]

    operation_codes = ["5411", "5412", "5419", "4581", "4582", "4583", "4541", "4542", "4543", "4549", "4552"]
    def has_op_percent(df: pd.DataFrame):
        return len(df[df[proc_cols].isin(operation_codes).any("columns")]) / len(df) * 100

    table2.loc["Had operation (%)"] = [has_op_percent(has_dm), has_op_percent(no_dm)]

    print(table2)
    table2.to_csv("diverticulitis/diverticulitis_perforated.csv")

    # Perforated diverticulitis with IR subset
    print("Analyzing perforated diverticulitis with IR subset...")
    pd_and_ir_df = perf_df[perf_df[proc_cols].isin(["5491"]).any("columns")]
    def count_ir_procs(row):
        return (row[proc_cols] == "5491").sum()
    pd_and_ir_df["IR Count"] = pd_and_ir_df.apply(count_ir_procs, axis=1)
    has_dm = pd_and_ir_df[pd_and_ir_df["CM_DM"] == 1]
    no_dm = pd_and_ir_df[pd_and_ir_df["CM_DM"] == 0]

    table3 = general_stats(has_dm, no_dm)
    table3.loc["Had operation (%)"] = [has_op_percent(has_dm), has_op_percent(no_dm)]
    table3.loc["Multiple IR (%)"] = [len(has_dm[has_dm["IR Count"] > 1]) / len(has_dm) * 100, len(no_dm[no_dm["IR Count"] > 1]) / len(no_dm) * 100]

    print(table3)
    table3.to_csv("diverticulitis/diverticulitis_perforated_ir.csv")

