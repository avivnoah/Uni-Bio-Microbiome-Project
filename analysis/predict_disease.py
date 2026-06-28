"""Disease prediction: metadata-only feature importance + omics CV accuracy,
plus the age/shannon confounder check.

Figure 14_feature_importance.png; keys: metadata_feature_importance,
metadata_only_cv_balacc, disease_pred_balacc, confounders.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold

from _common import (FIG, INK, ACCENT, G, group_col, clr, shannon,
                     load_data, masks, save_findings)


def main():
    meta, micro, metab = load_data()
    has_micro, has_metab, complete, micro_only, metab_only = masks(micro, metab)
    micro_clr = clr(micro[has_micro])
    metab_log = np.log1p(metab[has_metab])
    mz = pd.DataFrame(StandardScaler().fit_transform(metab_log),
                      index=metab_log.index, columns=metab_log.columns)

    out: dict = {}

    # ---- E: metadata-only disease-prediction feature importance ----
    md = meta.dropna(subset=["BMI_C", "AGE", "GENDER"]).copy()
    Xmd = pd.get_dummies(md[["BMI_C", "AGE", "GENDER", "CENTER_C"]], columns=["CENTER_C"])
    ymd = md[G].astype(str)
    rf = RandomForestClassifier(n_estimators=400, random_state=0, n_jobs=-1).fit(Xmd, ymd)
    imp = pd.Series(rf.feature_importances_, index=Xmd.columns).sort_values(ascending=False).head(6)
    out["metadata_feature_importance"] = {k: round(float(v), 3) for k, v in imp.items()}
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(imp.index[::-1], imp.values[::-1], color=[ACCENT if i == len(imp) - 1 else INK
            for i in range(len(imp))][::-1])
    ax.set_title("Metadata-only disease prediction: feature importance")
    ax.set_xlabel("importance")
    fig.tight_layout(); fig.savefig(FIG / "14_feature_importance.png", dpi=130); plt.close(fig)
    out["metadata_only_cv_balacc"] = round(float(cross_val_score(
        RandomForestClassifier(300, random_state=0, n_jobs=-1), Xmd, ymd,
        cv=StratifiedKFold(5, shuffle=True, random_state=0), scoring="balanced_accuracy").mean()), 3)

    # ---- confounders: age vs shannon ----
    shan = pd.Series(shannon(micro[has_micro]), index=micro_clr.index)
    have_age = meta.loc[micro_clr.index, "AGE"].notna().values
    out["confounders"] = {
        "age_vs_shannon_spearman": round(float(spearmanr(
            meta.loc[micro_clr.index, "AGE"].values[have_age], shan.values[have_age]).correlation), 3),
    }

    # ---- disease prediction: both omics (complete) vs microbiome-only (all micro rows) ----
    cc_idx = micro_clr.index.intersection(mz.index)
    Xmi = pd.DataFrame(StandardScaler().fit_transform(micro_clr.loc[cc_idx]),
                       index=cc_idx, columns=micro_clr.columns)
    Xme = mz.loc[cc_idx]
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1)
    y_c = meta.loc[cc_idx, group_col].astype(str).values
    acc_both = cross_val_score(rf, np.hstack([Xmi.values, Xme.values]), y_c,
                               cv=cv, scoring="balanced_accuracy").mean()
    mi_all = pd.DataFrame(StandardScaler().fit_transform(micro_clr),
                          index=micro_clr.index, columns=micro_clr.columns)
    y_m = meta.loc[mi_all.index, group_col].astype(str).values
    acc_micro = cross_val_score(rf, mi_all.values, y_m, cv=cv,
                                scoring="balanced_accuracy").mean()
    out["disease_pred_balacc"] = {
        "both_omics_complete": round(float(acc_both), 3),
        "microbiome_only_all": round(float(acc_micro), 3),
    }

    save_findings("predict_disease", out)


if __name__ == "__main__":
    main()
