import pandas as pd
import glob
import re
from icdcodex import icd2vec, hierarchy
import numpy as np
import pickle
from sklearn.decomposition import PCA
import seaborn as sns
import matplotlib.pyplot as plt

EMBEDDING_DIMS=64
OUTCOME_COLS=["RACE", "HOSP_REGION", "ZIPINC_QRTL"]

def get_dx_cols(all_cols):
    icd9_cols = [col for col in all_cols if re.search("^DX[0-9]{1,2}$", col)]
    icd10_cols = [col for col in all_cols if re.search("^I10_DX[0-9]{1,2}$", col)]

    return icd9_cols + icd10_cols


def handle_single_chunk(chunk, dx_cols, embedder, icd10):
    # Fixup ICD columns for ingestion into icdcodex
    if icd10:

        def fix_icd10(code):
            if len(code) > 3:
                ret = f"{code[0:3]}.{code[3:]}"
            else:
                ret = code

            return ret

        chunk[dx_cols] = chunk[dx_cols].applymap(fix_icd10)

    colnames = [f"centroid_{idx}" for idx in range(0, EMBEDDING_DIMS)]

    def get_embeddings(row):
        all_embeddings = list()
        for code in [c for c in row[dx_cols].to_list() if c]:
            try:
                all_embeddings.append(embedder.to_vec([code]))
            except KeyError as e:
                print(f"[-] Warning: key error for {code}")

        if len(all_embeddings) > 0:
            data = np.mean(np.stack(all_embeddings, axis=0), axis=0)
            return pd.Series(data=np.squeeze(data), index=colnames)
        else:
            print(f"[-] Warning: empty row: {row.name}")
            return pd.Series(data=[np.na for _ in range(0, EMBEDDING_DIMS)], index=colnames)

    chunk[colnames] = chunk.apply(get_embeddings, axis=1)
    chunk = chunk.drop(columns=dx_cols)

    return chunk[colnames + OUTCOME_COLS]

def handle_single_file(fname):
    print(f"[*] Processing {fname}")
    df = pd.DataFrame()


    # In theory columns will remain consistent within a file, even if they change between files
    cols = next(pd.read_stata(fname, chunksize=1)).columns
    dx_cols = get_dx_cols(cols)
    embedder = icd2vec.Icd2Vec(num_embedding_dimensions=EMBEDDING_DIMS)

    if "10" in dx_cols[0]:  # ICD10 case
        print(f"[*] Detected IC10")
        icd10 = True
        with open("cache/icd10_embedder.pkl", 'rb') as f:
            embedder = pickle.load(f)

    else:
        print(f"[*] Detected ICD9")
        icd10 = False
        with open("cache/icd9_embedder.pkl", 'rb') as f:
            embedder = pickle.load(f)

    print(f"[+] Embedder fit")    

    for chunk in pd.read_stata(
        fname, chunksize=10**5, columns=OUTCOME_COLS + dx_cols
    ):
        
        df = pd.concat([df,handle_single_chunk(chunk, dx_cols, embedder, icd10)])

    # Monitor memory usage
    df.info()

    return df


if __name__ == "__main__":
    # df = pd.DataFrame()

    # for fname in glob.glob("./data/*.dta"):
    #     df = df.append(handle_single_file(fname))
        
    # df.to_csv("vectorized.csv", index=False)    

    out_df = handle_single_file("cache/testdata.dta")

    print(out_df)

    pca = PCA(n_components=2)
    pca_res = pca.fit_transform(out_df[[c for c in out_df if c.startswith("centroid")]].values)

    out_df = pd.concat([out_df[OUTCOME_COLS], pd.DataFrame(data=pca_res, columns=["x", "y"])], axis=1)

    sns.set_theme()
    ax = sns.scatterplot(x="x", y="y", hue="HOSP_REGION", data=out_df)

    plt.savefig("pca_region.png")
