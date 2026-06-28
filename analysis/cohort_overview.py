"""Cohort overview: modality structure, group counts, metadata missingness.

Figure 01_overview.png; keys: modality_structure, group_counts,
metadata_missing_pct, omics_missing_by_center.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from _common import (FIG, INK, MUT, ACCENT, group_col, load_data, masks,
                     group_order, save_findings)


def main():
    meta, micro, metab = load_data()
    has_micro, has_metab, complete, micro_only, metab_only = masks(micro, metab)

    findings: dict = {}
    findings["modality_structure"] = {
        "n_total": int(len(micro)),
        "complete_both": int(complete.sum()),
        "microbiome_only": int(micro_only.sum()),
        "metabolome_only": int(metab_only.sum()),
    }
    findings["group_counts"] = meta[group_col].value_counts().sort_index().to_dict()
    findings["metadata_missing_pct"] = meta.isna().mean().mul(100).round(1).to_dict()
    findings["omics_missing_by_center"] = pd.crosstab(
        meta["CENTER_C"], np.where(micro_only, "micro_only",
            np.where(metab_only, "metab_only", "complete"))).to_dict()

    # ---- Fig 1: modality structure + metadata missingness ----
    fig, ax = plt.subplots(1, 3, figsize=(20, 5))
    order = group_order(meta)
    sns.countplot(data=meta, x=group_col, order=order, ax=ax[0], color=INK)
    ax[0].set_title("Disease-group distribution"); ax[0].set_xlabel("PatientGroup")
    struct = pd.Series(findings["modality_structure"]).drop("n_total")
    ax[1].bar(["both", "micro\nonly", "metab\nonly"], struct.values,
              color=[INK, MUT, ACCENT])
    ax[1].set_title("Omics availability (~40% miss a modality)"); ax[1].set_ylabel("samples")
    miss = meta.isna().mean().mul(100).sort_values(ascending=False)
    sns.barplot(x=miss.values, y=miss.index, ax=ax[2], color=MUT)
    ax[2].set_title("Metadata missing (%)"); ax[2].set_xlabel("% missing")
    fig.tight_layout(); fig.savefig(FIG / "01_overview.png", dpi=130); plt.close(fig)

    save_findings("cohort_overview", findings)


if __name__ == "__main__":
    main()
