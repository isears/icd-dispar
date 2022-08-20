from icdcodex import icd2vec, hierarchy
import pickle


if __name__ == "__main__":
    print("Building ICD9 embedder...")
    icd9_embedder = icd2vec.Icd2Vec(num_embedding_dimensions=64)
    icd9_embedder.fit(*hierarchy.icd9())

    with open("cache/icd9_embedder.pkl", 'wb') as f:
        pickle.dump(icd9_embedder, f)

    print("Building ICD10 embedder...")
    icd10_embedder = icd2vec.Icd2Vec(num_embedding_dimensions=64)
    icd10_embedder.fit(*hierarchy.icd10cm(version="2019"))

    with open("cache/icd10_embedder.pkl", 'wb') as f:
        pickle.dump(icd10_embedder, f)

    print("Done")
