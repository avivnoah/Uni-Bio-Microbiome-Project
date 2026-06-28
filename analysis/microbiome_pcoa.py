"""Microbiome structure: alpha diversity, Aitchison PCoA, between-group distance.

Figures 04_microbiome_pcoa.png, 03_alpha_diversity.png,
06_between_group_distance.png; key: pcoa_explained. Deterministic (no RNG).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform

from _common import (FIG, INK, ACCENT, MUT, SEQ, GROUP_PAL, group_col,
                     clr, pcoa, shannon, load_data, masks, group_order, save_findings)


def main():
    meta, micro, metab = load_data()
    has_micro, has_metab, complete, micro_only, metab_only = masks(micro, metab)
    micro_clr = clr(micro[has_micro])
    order = group_order(meta)

    findings: dict = {}

    # ---- alpha diversity ----
    shan = pd.Series(shannon(micro[has_micro]), index=micro_clr.index)
    mdf = meta.loc[micro_clr.index].assign(shannon=shan.values)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=mdf, x=group_col, y="shannon", order=order, ax=ax, color="#D7D3CB", linecolor=INK, medianprops={"color": ACCENT, "linewidth": 2})
    ax.set_title("Shannon diversity by disease group"); ax.set_xlabel("PatientGroup")
    fig.tight_layout(); fig.savefig(FIG / "03_alpha_diversity.png", dpi=130); plt.close(fig)

    # ---- PCoA (Aitchison) ----
    aitch = squareform(pdist(micro_clr.to_numpy()))
    coords, expl = pcoa(aitch, 2)
    findings["pcoa_explained"] = [round(float(e), 3) for e in expl]
    pc = pd.DataFrame(coords, columns=["PC1", "PC2"], index=micro_clr.index)
    pc[group_col] = meta.loc[pc.index, group_col].values
    pc["CENTER"] = meta.loc[pc.index, "CENTER_C"].values
    fig, ax = plt.subplots(1, 2, figsize=(16, 6))
    sns.scatterplot(data=pc, x="PC1", y="PC2", hue=group_col, hue_order=order,
                    s=14, ax=ax[0], palette=GROUP_PAL, alpha=0.8)
    ax[0].set_title(f"Microbiome PCoA (Aitchison)  PC1={expl[0]:.1%} PC2={expl[1]:.1%}")
    ax[0].legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    sns.scatterplot(data=pc, x="PC1", y="PC2", hue="CENTER", s=14, ax=ax[1], alpha=0.8,
                    palette=[INK, ACCENT, MUT])
    ax[1].set_title("Same PCoA, coloured by CENTER (confounder)")
    fig.tight_layout(); fig.savefig(FIG / "04_microbiome_pcoa.png", dpi=130); plt.close(fig)

    # single-panel disease-only PCoA for the slide deck (avoids the biased 3-vs-9 colour comparison)
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.scatterplot(data=pc, x="PC1", y="PC2", hue=group_col, hue_order=order,
                    s=16, ax=ax, palette=GROUP_PAL, alpha=0.85)
    ax.set_title(f"Microbiome PCoA (Aitchison)   PC1={expl[0]:.1%}   PC2={expl[1]:.1%}")
    ax.legend(title="disease group", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "04b_microbiome_pcoa_disease.png", dpi=130); plt.close(fig)

    # ---- between-group mean Aitchison distance ----
    groups = order
    avg = np.zeros((len(groups), len(groups)))
    gvals = meta.loc[micro_clr.index, group_col].values
    for i, gi in enumerate(groups):
        for j, gj in enumerate(groups):
            ii = np.where(gvals == gi)[0]; jj = np.where(gvals == gj)[0]
            avg[i, j] = aitch[np.ix_(ii, jj)].mean()
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(pd.DataFrame(avg, index=groups, columns=groups), annot=True,
                fmt=".1f", cmap=SEQ, ax=ax)
    ax.set_title("Mean Aitchison distance between groups")
    fig.tight_layout(); fig.savefig(FIG / "06_between_group_distance.png", dpi=130); plt.close(fig)

    save_findings("microbiome_pcoa", findings)


if __name__ == "__main__":
    main()
