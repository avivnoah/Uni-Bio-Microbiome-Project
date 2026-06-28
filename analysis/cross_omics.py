"""Cross-omics Spearman correlation on the complete subjects.

Figure 09_cross_omics_corr.png; keys: n_complete_for_corr,
max_abs_taxa_metab_corr. Deterministic (no RNG).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
from sklearn.preprocessing import StandardScaler

from _common import FIG, DIV, clr, load_data, masks, save_findings


def main():
    meta, micro, metab = load_data()
    has_micro, has_metab, complete, micro_only, metab_only = masks(micro, metab)
    micro_clr = clr(micro[has_micro])
    metab_log = np.log1p(metab[has_metab])
    mz = pd.DataFrame(StandardScaler().fit_transform(metab_log),
                      index=metab_log.index, columns=metab_log.columns)

    findings: dict = {}

    cidx = micro_clr.index.intersection(mz.index)
    mv = micro_clr.loc[cidx, micro_clr.var().nlargest(30).index]
    bv = mz.loc[cidx, mz.var().nlargest(30).index]
    cc = np.array([[spearmanr(mv[a], bv[b]).correlation for b in bv.columns] for a in mv.columns])
    findings["n_complete_for_corr"] = int(len(cidx))
    findings["max_abs_taxa_metab_corr"] = round(float(np.nanmax(np.abs(cc))), 3)
    fig, ax = plt.subplots(figsize=(12, 9))
    sns.heatmap(pd.DataFrame(cc, index=mv.columns, columns=bv.columns),
                cmap=DIV, center=0, vmin=-0.6, vmax=0.6, ax=ax, xticklabels=False)
    ax.set_title("Spearman: top-variance taxa (rows) vs metabolites (cols)")
    fig.tight_layout(); fig.savefig(FIG / "09_cross_omics_corr.png", dpi=130); plt.close(fig)

    save_findings("cross_omics", findings)


if __name__ == "__main__":
    main()
