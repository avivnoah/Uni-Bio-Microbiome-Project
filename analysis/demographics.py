"""Demographics by patient group: age & BMI, gender composition.

Figures 10_age_bmi_by_group.png, 13_gender_by_group.png; no JSON keys.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from _common import FIG, INK, ACCENT, GENDER_COLORS, G, load_data, group_order, save_findings


def main():
    meta, micro, metab = load_data()
    order = group_order(meta)

    # ---- A+B: age & BMI by group (confounders) ----
    fig, ax = plt.subplots(1, 2, figsize=(15, 5.2))
    for a, col, title in [(ax[0], "AGE", "Age by patient group"), (ax[1], "BMI_C", "BMI by patient group")]:
        d = meta[[G, col]].dropna()
        sns.boxplot(data=d, x=G, y=col, order=order, ax=a, color="#D7D3CB",
                    linecolor=INK, fliersize=2, medianprops={"color": ACCENT, "linewidth": 2.2})
        a.set_title(title); a.set_xlabel("patient group"); a.set_ylabel(col.replace("_C", ""))
    fig.tight_layout(); fig.savefig(FIG / "10_age_bmi_by_group.png", dpi=130); plt.close(fig)

    # ---- D: gender composition by group ----
    gt = pd.crosstab(meta[G], meta["GENDER"]).reindex(order)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    bottom = np.zeros(len(gt))
    for j, col in enumerate(gt.columns):
        lab = {0.0: "male", 1.0: "female"}.get(col, str(col))
        ax.bar(gt.index.astype(str), gt[col], bottom=bottom, label=lab,
               color=GENDER_COLORS[j % 2], width=.72)
        bottom += gt[col].values
    ax.set_title("Patient group composition by gender")
    ax.set_xlabel("patient group"); ax.set_ylabel("samples"); ax.legend(title="gender")
    fig.tight_layout(); fig.savefig(FIG / "13_gender_by_group.png", dpi=130); plt.close(fig)

    save_findings("demographics", {})


if __name__ == "__main__":
    main()
