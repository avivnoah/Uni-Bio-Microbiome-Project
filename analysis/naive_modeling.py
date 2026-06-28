"""
Naive-modeling benchmark for Milestone 1 — self-contained, for Inbal to read /
compare against her own naive_modeling.ipynb.

What the project brief asks (Final Project Instructions, "Project description"):
  "...some omics MODALITIES may be missing for certain samples ... impute the
   missing data (KNN, Random Forest, mean/median) and THEN COMPUTE DISTANCES."

So the missingness is WHOLE-MODALITY (a subject has no metabolome at all, or no
microbiome at all — in our data: 1042 both, 348 microbiome-only, 348 metabolome-only),
and the benchmark must end in distances (the grader scores an n x n distance
matrix with a Mantel test).

This script does exactly two things the brief lists:
  (1) drop a whole modality for a fraction of complete subjects, recover it with
      mean / median / KNN / Random Forest (cross-modal), recompute the distance
      matrix, and score it with a Mantel test vs the full-data truth;
  (2) "predict disease state with vs without imputation" (Random Forest, balanced
      accuracy).

KEY DIFFERENCE vs the original notebook approach:
  - original masked RANDOM SCATTERED CELLS and imputed WITHIN one modality
    (microbiome->microbiome), scoring value-R2. That measures sporadic-gap filling,
    not the project's whole-modality missingness, and it never computes distances.
  - here we drop a WHOLE modality and recover it CROSS-MODALLY (from the modality
    the subject still has), then evaluate via distances (Mantel) + disease accuracy.

Run:  python analysis/naive_modeling.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_val_score, cross_val_predict, StratifiedKFold, KFold
from sklearn.neighbors import KNeighborsRegressor

# --- point this at your train folder (Inbal: change to your Windows path) ---
DATA = Path(__file__).resolve().parent.parent / "data" / "train"
RNG = np.random.default_rng(0)
GROUP = "PATGROUPFINAL_C"


def clr(frame: pd.DataFrame, pseudo: float = 1e-6) -> pd.DataFrame:
    """Centered log-ratio: the compositional fix for relative-abundance data."""
    x = frame.to_numpy(float) + pseudo
    x = x / x.sum(1, keepdims=True)
    lx = np.log(x)
    return pd.DataFrame(lx - lx.mean(1, keepdims=True), index=frame.index, columns=frame.columns)


def mantel(d1: np.ndarray, d2: np.ndarray, n_perm: int = 199):
    """Mantel test: Spearman correlation between two distance matrices (+ perm p)."""
    iu = np.triu_indices_from(d1, k=1)
    r = spearmanr(d1[iu], d2[iu]).correlation
    cnt = 1
    for _ in range(n_perm):
        p = RNG.permutation(d1.shape[0])
        if abs(spearmanr(d1[np.ix_(p, p)][iu], d2[iu]).correlation) >= abs(r):
            cnt += 1
    return round(float(r), 3), round(cnt / (n_perm + 1), 3)


# --------------------------------------------------------------------------- #
# load + transform (microbiome -> CLR, metabolome -> log + standardize)
# --------------------------------------------------------------------------- #
micro = pd.read_csv(DATA / "microbiome.csv", index_col=0)
metab = pd.read_csv(DATA / "metabolome.csv", index_col=0).loc[micro.index]
meta = pd.read_csv(DATA / "metadata.csv", index_col=0).loc[micro.index]

has_micro = ~micro.isna().all(axis=1)
has_metab = ~metab.isna().all(axis=1)
complete = micro.index[has_micro & has_metab]            # 1042 subjects with both
print(f"subjects: {len(micro)} total | {len(complete)} complete | "
      f"{int((has_micro & ~has_metab).sum())} micro-only | "
      f"{int((~has_micro & has_metab).sum())} metab-only\n")

micro_clr = clr(micro.loc[complete])
metab_log = np.log1p(metab.loc[complete])
Xmi = pd.DataFrame(StandardScaler().fit_transform(micro_clr), index=complete)
Xme = pd.DataFrame(StandardScaler().fit_transform(metab_log), index=complete)

# ground-truth distances = grader's recipe on the full (both-modality) data
gt_pcs = PCA(2, random_state=0).fit_transform(
    StandardScaler().fit_transform(np.hstack([Xmi.values, Xme.values])))
gt = squareform(pdist(gt_pcs))


# --------------------------------------------------------------------------- #
# (1) drop a WHOLE modality -> recover -> recompute distances -> Mantel
# --------------------------------------------------------------------------- #
def recover_then_distance(frac: float):
    n = len(complete)
    miss = RNG.choice(n, int(frac * n), replace=False)
    obs = np.ones(n, bool); obs[miss] = False
    out = {}
    # four naive recoveries of the dropped metabolome block
    me = {}
    me["mean"] = Xme.values.copy(); me["mean"][miss] = Xme.values[obs].mean(0)
    me["median"] = Xme.values.copy(); me["median"][miss] = np.median(Xme.values[obs], axis=0)
    stk = Xme.values.copy(); stk[miss] = np.nan                      # KNN via microbiome side
    me["knn"] = KNNImputer(n_neighbors=10).fit_transform(
        np.hstack([Xmi.values, stk]))[:, Xmi.shape[1]:]
    rf = RandomForestRegressor(n_estimators=60, max_depth=12, n_jobs=-1, random_state=0)
    rf.fit(Xmi.values[obs], Xme.values[obs])                        # RF: micro -> metab
    me["rf"] = Xme.values.copy(); me["rf"][miss] = rf.predict(Xmi.values[miss])
    for name, filled in me.items():
        pcs = PCA(2, random_state=0).fit_transform(
            StandardScaler().fit_transform(np.hstack([Xmi.values, filled])))
        out[name] = mantel(gt, squareform(pdist(pcs)))[0]
    return out


print("(1) whole-modality recovery -> distance Mantel (higher = closer to truth)")
print(f"{'dropped':>8} | {'mean':>6} {'median':>6} {'knn':>6} {'rf':>6}")
for frac in (0.1, 0.3, 0.5):
    r = recover_then_distance(frac)
    print(f"{int(frac*100):>7}% | {r['mean']:>6} {r['median']:>6} {r['knn']:>6} {r['rf']:>6}")


# --------------------------------------------------------------------------- #
# (2) predict disease state WITH vs WITHOUT imputation (balanced accuracy)
# --------------------------------------------------------------------------- #
y = meta.loc[complete, GROUP].astype(str).values
clf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1)
skf = StratifiedKFold(5, shuffle=True, random_state=0)
ba = lambda Xf: round(float(cross_val_score(clf, Xf, y, cv=skf, scoring="balanced_accuracy").mean()), 3)
# "with imputation" = metabolome reconstructed from microbiome out-of-fold (KNN)
oof_metab = cross_val_predict(KNeighborsRegressor(10), Xmi.values, Xme.values,
                              cv=KFold(5, shuffle=True, random_state=0))

print("\n(2) disease prediction (RF, balanced accuracy; chance ~ 0.11)")
print(f"  without imputation (microbiome only)        : {ba(Xmi.values)}")
print(f"  with imputation (micro + recovered metab)   : {ba(np.hstack([Xmi.values, oof_metab]))}")
print(f"  real both omics (upper bound)               : {ba(np.hstack([Xmi.values, Xme.values]))}")
