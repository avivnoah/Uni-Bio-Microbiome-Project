"""Country composition + PERMANOVA (group / center) + metadata missingness map.

Figures 12_country_by_group.png, 02_missing_by_center.png; keys:
permanova_group, permanova_center, metadata_missing_by_center.

Fidelity: uses a fresh default_rng(0) and draws the subsample BEFORE the two
PERMANOVA loops (group then center), matching eda.py's RNG consumption order.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform

from _common import (FIG, INK, ACCENT, MUT, SEQ, CENTER_COLORS, G, group_col,
                     clr, permanova, load_data, masks, group_order, save_findings)


def main():
    meta, micro, metab = load_data()
    has_micro, has_metab, complete, micro_only, metab_only = masks(micro, metab)
    micro_clr = clr(micro[has_micro])
    order = group_order(meta)

    findings: dict = {}
    findings["metadata_missing_by_center"] = (
        meta.assign(m=meta["BMI_C"].isna()).groupby("CENTER_C")["m"].mean().round(3).to_dict())

    # ---- C: country composition by group ----
    ct = pd.crosstab(meta[G], meta["CENTER_C"]).reindex(order)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    bottom = np.zeros(len(ct))
    for c in ["Danemark", "France", "Germany"]:
        if c in ct:
            ax.bar(ct.index.astype(str), ct[c], bottom=bottom, label=c,
                   color=CENTER_COLORS[c], width=.72)
            bottom += ct[c].values
    ax.set_title("Patient group composition by recruitment center")
    ax.set_xlabel("patient group"); ax.set_ylabel("samples"); ax.legend(title="center")
    fig.tight_layout(); fig.savefig(FIG / "12_country_by_group.png", dpi=130); plt.close(fig)

    # ---- Fig 2: metadata missingness is MNAR by center (Denmark) ----
    miss_center = (meta.assign(c=meta["CENTER_C"])
                   .groupby("c")[["GENDER", "BMI_C", "AGE"]].apply(lambda d: d.isna().mean()))
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.heatmap(miss_center, annot=True, fmt=".2f", cmap=SEQ, vmin=0, vmax=1, ax=ax)
    ax.set_title("Metadata missing fraction by CENTER (MNAR)")
    fig.tight_layout(); fig.savefig(FIG / "02_missing_by_center.png", dpi=130); plt.close(fig)

    # ---- PERMANOVA on subsample (group, then center) ----
    aitch = squareform(pdist(micro_clr.to_numpy()))
    rng = np.random.default_rng(0)
    sub = rng.choice(len(micro_clr), size=min(700, len(micro_clr)), replace=False)
    labg = meta.loc[micro_clr.index, group_col].values[sub]
    labc = meta.loc[micro_clr.index, "CENTER_C"].values[sub]
    f_g, p_g = permanova(aitch[np.ix_(sub, sub)], labg, rng, 199)
    f_c, p_c = permanova(aitch[np.ix_(sub, sub)], labc, rng, 199)
    findings["permanova_group"] = {"F": round(f_g, 2), "p": p_g}
    findings["permanova_center"] = {"F": round(f_c, 2), "p": p_c}

    save_findings("country_permanova", findings)


if __name__ == "__main__":
    main()
