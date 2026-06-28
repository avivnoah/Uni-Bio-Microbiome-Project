"""Differential abundance: per-group counts (partner) + T2D-vs-control taxa +
metabolome group trends.

Figures 15_diff_per_group.png, 07_diff_abundance.png, 08_metabolome_trends.png;
keys: diff_species_per_group, diff_metab_per_group, da_n_sig_bonferroni.
Deterministic (no RNG).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests
from sklearn.preprocessing import StandardScaler

from _common import (FIG, INK, ACCENT, DIV, G, group_col, clr,
                     load_data, masks, group_order, save_findings)


def main():
    meta, micro, metab = load_data()
    has_micro, has_metab, complete, micro_only, metab_only = masks(micro, metab)
    micro_clr = clr(micro[has_micro])
    metab_log = np.log1p(metab[has_metab])
    mz = pd.DataFrame(StandardScaler().fit_transform(metab_log),
                      index=metab_log.index, columns=metab_log.columns)
    order = group_order(meta)

    out: dict = {}

    # ---- F+G: per-group differential features vs control (group 8) ----
    gv_mic = meta.loc[micro_clr.index, G]
    gv_met = meta.loc[mz.index, G]

    def n_sig(tab, groupvec, g, ctrl="8"):
        case = tab[groupvec.values == g]; con = tab[groupvec.values == ctrl]
        if len(case) < 5:
            return 0
        ps = [mannwhitneyu(case[c], con[c], alternative="two-sided").pvalue for c in tab.columns]
        return int((multipletests(ps, method="fdr_bh")[1] < 0.05).sum())

    cases = [g for g in order if g != "8"]
    sig_sp = {g: n_sig(micro_clr, gv_mic, g) for g in cases}
    sig_mb = {g: n_sig(mz, gv_met, g) for g in cases}
    out["diff_species_per_group"] = sig_sp
    out["diff_metab_per_group"] = sig_mb
    fig, ax = plt.subplots(1, 2, figsize=(15, 5.2))
    ax[0].bar(list(sig_sp), list(sig_sp.values()), color=INK, width=.7)
    ax[0].set_title("Differential species vs control (FDR<0.05)")
    ax[0].set_xlabel("disease group"); ax[0].set_ylabel("# significant species")
    ax[1].bar(list(sig_mb), list(sig_mb.values()), color=ACCENT, width=.7)
    ax[1].set_title("Differential metabolites vs control (FDR<0.05)")
    ax[1].set_xlabel("disease group"); ax[1].set_ylabel("# significant metabolites")
    fig.tight_layout(); fig.savefig(FIG / "15_diff_per_group.png", dpi=130); plt.close(fig)

    # ---- differential abundance: T2D (3) vs control (8) ----
    gv = meta.loc[micro_clr.index, group_col]
    ci, co = micro_clr[gv.values == "3"], micro_clr[gv.values == "8"]
    rows = []
    for sp in micro_clr.columns:
        p = mannwhitneyu(ci[sp], co[sp], alternative="two-sided").pvalue
        rows.append((sp, ci[sp].mean() - co[sp].mean(), p))
    da = pd.DataFrame(rows, columns=["species", "clr_diff", "p"]).set_index("species")
    da["p_adj"] = (da["p"] * len(da)).clip(upper=1.0)
    out["da_n_sig_bonferroni"] = int((da["p_adj"] < 0.05).sum())
    top = pd.concat([da.nlargest(8, "clr_diff"), da.nsmallest(8, "clr_diff")])
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh([s[:34] for s in top.index], top["clr_diff"],
            color=[ACCENT if v > 0 else INK for v in top["clr_diff"]])
    ax.set_title("Top differential taxa: T2D (3) vs control (8)")
    ax.set_xlabel("Δ mean CLR (T2D − control)")
    fig.tight_layout(); fig.savefig(FIG / "07_diff_abundance.png", dpi=130); plt.close(fig)

    # ---- metabolome trends by disease group ----
    mz_grp = meta.loc[mz.index, group_col]
    mean_by_grp = mz.groupby(mz_grp.values).mean()
    var_top = mean_by_grp.var().nlargest(25).index
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(mean_by_grp[var_top].T, cmap=DIV, center=0, ax=ax,
                cbar_kws={"label": "mean z-score"})
    ax.set_title("Most group-variable metabolites (z) by disease group")
    fig.tight_layout(); fig.savefig(FIG / "08_metabolome_trends.png", dpi=130); plt.close(fig)

    save_findings("differential_abundance", out)


if __name__ == "__main__":
    main()
