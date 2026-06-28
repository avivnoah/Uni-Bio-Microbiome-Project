"""Naive baselines: controlled-dropout distance Mantel (ours), partner's
random-cell imputation-R2, and disease-state WITH vs WITHOUT imputation.

No figure; keys: naive_distance_baseline, disease_with_without,
partner_naive_imputation_r2.

Fidelity:
- naive_distance_baseline replays the eda.py RNG (default_rng(0)) past the
  subsample + the two PERMANOVA loops (see _common.rng_after_permanova) so the
  RNG.choice masks and Mantel permutations match the original byte-for-byte.
- partner_naive_imputation_r2 uses a fresh default_rng(42) in partner_eda.py's
  exact draw order (the Xme_rf subsample first, then the masked_r2 loops).
- disease_with_without is deterministic (fixed-seed CV).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import KNNImputer
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import (cross_val_score, cross_val_predict,
                                     StratifiedKFold, KFold)

from _common import (group_col, clr, mantel, load_data, masks,
                     rng_after_permanova, save_findings)


def main():
    meta, micro, metab = load_data()
    has_micro, has_metab, complete, micro_only, metab_only = masks(micro, metab)
    micro_clr = clr(micro[has_micro])
    metab_log = np.log1p(metab[has_metab])
    mz = pd.DataFrame(StandardScaler().fit_transform(metab_log),
                      index=metab_log.index, columns=metab_log.columns)

    out: dict = {}

    # ----------------------------------------------------------------------- #
    # NAIVE DISTANCE BASELINE (ours) -- controlled dropout on 1042 complete.
    # ----------------------------------------------------------------------- #
    RNG = rng_after_permanova(meta, micro_clr)
    cc_idx = micro_clr.index.intersection(mz.index)             # 1042 complete
    Xmi = pd.DataFrame(StandardScaler().fit_transform(micro_clr.loc[cc_idx]),
                       index=cc_idx, columns=micro_clr.columns)
    Xme = mz.loc[cc_idx]
    gt_pcs = PCA(2, random_state=0).fit_transform(
        StandardScaler().fit_transform(np.hstack([Xmi.values, Xme.values])))
    gt = squareform(pdist(gt_pcs))

    n = len(cc_idx)
    baseline = {}
    for frac in (0.1, 0.3, 0.5):
        miss = RNG.choice(n, int(frac * n), replace=False)
        obs = np.ones(n, bool); obs[miss] = False
        res = {}

        me_mean = Xme.values.copy(); me_mean[miss] = Xme.values[obs].mean(0)
        me_median = Xme.values.copy(); me_median[miss] = np.median(Xme.values[obs], axis=0)
        stk = Xme.values.copy(); stk[miss] = np.nan
        me_knn = KNNImputer(n_neighbors=10).fit_transform(
            np.hstack([Xmi.values, stk]))[:, Xmi.shape[1]:]
        rfreg = RandomForestRegressor(n_estimators=60, max_depth=12, n_jobs=-1, random_state=0)
        rfreg.fit(Xmi.values[obs], Xme.values[obs])
        me_rf = Xme.values.copy(); me_rf[miss] = rfreg.predict(Xmi.values[miss])

        for name, me in (("mean", me_mean), ("median", me_median), ("knn", me_knn), ("rf", me_rf)):
            pcs = PCA(2, random_state=0).fit_transform(
                StandardScaler().fit_transform(np.hstack([Xmi.values, me])))
            r, p = mantel(gt, squareform(pdist(pcs)), RNG, 199)
            res[name] = {"mantel_r": round(r, 3), "p": p}
        baseline[f"drop_metab_{int(frac*100)}pct"] = res
    out["naive_distance_baseline"] = baseline

    # ----------------------------------------------------------------------- #
    # PARTNER: random-cell imputation-R2 baseline (fresh default_rng(42)).
    # ----------------------------------------------------------------------- #
    PRNG = np.random.default_rng(42)

    def masked_r2(X, rate, method):
        Xv = X.to_numpy(float).copy()
        mask = PRNG.random(Xv.shape) < rate
        truth = Xv[mask].copy()
        Xm = Xv.copy(); Xm[mask] = np.nan
        if method == "mean":
            fill = np.nanmean(Xm, axis=0)
            imp = np.where(np.isnan(Xm), fill[None, :], Xm)
        elif method == "median":
            fill = np.nanmedian(Xm, axis=0)
            imp = np.where(np.isnan(Xm), fill[None, :], Xm)
        elif method == "knn":
            imp = KNNImputer(n_neighbors=10).fit_transform(Xm)
        elif method == "rf":
            rf = RandomForestRegressor(n_estimators=20, max_depth=8, n_jobs=-1, random_state=0)
            imp = IterativeImputer(estimator=rf, max_iter=1, random_state=0).fit_transform(Xm)
        pred = imp[mask]
        ss_res = np.sum((truth - pred) ** 2); ss_tot = np.sum((truth - truth.mean()) ** 2)
        return round(float(1 - ss_res / ss_tot), 3)

    # NOTE: partner_eda.py drew the Xme_rf subsample BEFORE the masked_r2 loop.
    Xme_p = mz  # standardized log metabolome on complete-metab rows
    Xme_rf = Xme_p.iloc[PRNG.choice(len(Xme_p), size=min(500, len(Xme_p)), replace=False)]
    naive = {}
    for rate in (0.1, 0.2, 0.4, 0.6):
        row = {m: masked_r2(Xme_p, rate, m) for m in ("mean", "median", "knn")}
        row["rf"] = masked_r2(Xme_rf, rate, "rf")
        naive[f"{int(rate*100)}%"] = row
    out["partner_naive_imputation_r2"] = naive

    # ----------------------------------------------------------------------- #
    # disease state WITH vs WITHOUT imputation (partner, deterministic CV).
    # ----------------------------------------------------------------------- #
    cc = micro_clr.index.intersection(mz.index)
    Xmi_c = pd.DataFrame(StandardScaler().fit_transform(micro_clr.loc[cc]), index=cc)
    Xme_c = mz.loc[cc]
    y_c = meta.loc[cc, group_col].astype(str).values
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    clf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1)
    oof_metab = cross_val_predict(KNeighborsRegressor(n_neighbors=10), Xmi_c.values, Xme_c.values,
                                  cv=KFold(5, shuffle=True, random_state=0))
    ba = lambda Xf: round(float(cross_val_score(clf, Xf, y_c, cv=cv, scoring="balanced_accuracy").mean()), 3)
    out["disease_with_without"] = {
        "without_imputation_microbiome_only": ba(Xmi_c.values),
        "with_imputation_micro_plus_recovered_metab": ba(np.hstack([Xmi_c.values, oof_metab])),
        "real_both_omics_upper_bound": ba(np.hstack([Xmi_c.values, Xme_c.values])),
    }

    save_findings("naive_baseline", out)


if __name__ == "__main__":
    main()
