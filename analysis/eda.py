"""
MetaCardis Milestone-1 exploration + naive baseline.

Key data fact (discovered in exploration): the training tables are aligned by
SampleID but the omics VALUES are missing for ~40% of subjects -- 348 subjects
have microbiome only, 348 have metabolome only, 1042 have both. The whole-
modality missingness the project targets is therefore ALREADY PRESENT in the
training data, not something we have to invent.

Pipeline target (from the instructions): an n x n sample-sample DISTANCE matrix
from combined microbiome + metabolome that stays faithful when an entire
modality is absent. The grader builds ground truth by standard-scaling every
feature -> PCA -> Euclidean distance in the first two PCs, scored with a Mantel
test. The naive baseline below is framed against THAT target.

Self-contained: CLR, PCoA, PERMANOVA, Mantel implemented here; only the standard
scientific stack is required.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr, mannwhitneyu
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import KNNImputer
from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "train"
FIG = ROOT / "analysis" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(0)

# ---- editorial palette so figures match the slide deck (paper / ink / rose) ----
PAPER, INK, MUT, ACCENT = "#FAF9F6", "#0A0A0A", "#6B6863", "#FF2D55"
sns.set_theme(style="ticks", context="talk")
plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUT, "ytick.color": MUT, "axes.titlecolor": INK,
    "axes.grid": True, "grid.color": "#E4E1DA", "grid.linewidth": .8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 12, "axes.titlesize": 13, "axes.titleweight": "bold",
    "legend.frameon": False,
})
# muted categorical palette for the 9 disease groups (informational, not the accent)
GROUP_PAL = ["#0A0A0A", "#6B6863", "#B23A48", "#FF2D55", "#C58A3B",
             "#3F6C6A", "#8A8D9B", "#7D4F9E", "#A8A29A"]
from matplotlib.colors import LinearSegmentedColormap
SEQ = LinearSegmentedColormap.from_list("paper_rose", [PAPER, "#F4B7C2", ACCENT, "#8E1330"])
DIV = LinearSegmentedColormap.from_list("ink_rose", [INK, "#7C7A74", PAPER, "#F4A6B6", ACCENT])
findings: dict = {}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def clr(frame: pd.DataFrame, pseudo: float = 1e-6) -> pd.DataFrame:
    x = frame.to_numpy(dtype=float) + pseudo
    x = x / x.sum(axis=1, keepdims=True)
    log_x = np.log(x)
    return pd.DataFrame(log_x - log_x.mean(axis=1, keepdims=True),
                        index=frame.index, columns=frame.columns)


def pcoa(dist: np.ndarray, k: int = 2):
    n = dist.shape[0]
    d2 = dist ** 2
    j = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * j @ d2 @ j
    vals, vecs = np.linalg.eigh(b)
    order = np.argsort(vals)[::-1]
    vals, vecs = vals[order], vecs[:, order]
    coords = vecs[:, :k] * np.sqrt(np.maximum(vals[:k], 0))
    explained = np.maximum(vals, 0) / np.maximum(np.maximum(vals, 0).sum(), 1e-12)
    return coords, explained[:k]


def permanova(dist: np.ndarray, labels: np.ndarray, n_perm: int = 199):
    labels = np.asarray(labels)
    n = dist.shape[0]
    d2 = dist ** 2
    ss_total = d2.sum() / (2 * n)
    groups = np.unique(labels)
    a = len(groups)

    def within(lbl):
        ss = 0.0
        for g in groups:
            idx = np.where(lbl == g)[0]
            ss += d2[np.ix_(idx, idx)].sum() / (2 * len(idx))
        return ss

    ss_w = within(labels)
    f_obs = ((ss_total - ss_w) / (a - 1)) / (ss_w / (n - a))
    count = 1
    for _ in range(n_perm):
        perm = RNG.permutation(labels)
        ss_wp = within(perm)
        f = ((ss_total - ss_wp) / (a - 1)) / (ss_wp / (n - a))
        if f >= f_obs:
            count += 1
    return float(f_obs), count / (n_perm + 1)


def mantel(d1: np.ndarray, d2: np.ndarray, n_perm: int = 199):
    iu = np.triu_indices_from(d1, k=1)
    v1, v2 = d1[iu], d2[iu]
    r_obs = spearmanr(v1, v2).correlation
    n = d1.shape[0]
    count = 1
    for _ in range(n_perm):
        p = RNG.permutation(n)
        if abs(spearmanr(d1[np.ix_(p, p)][iu], v2).correlation) >= abs(r_obs):
            count += 1
    return float(r_obs), count / (n_perm + 1)


# --------------------------------------------------------------------------- #
# load + identify the real missing-modality structure
# --------------------------------------------------------------------------- #
meta = pd.read_csv(DATA / "metadata.csv", index_col=0)
micro = pd.read_csv(DATA / "microbiome.csv", index_col=0)
metab = pd.read_csv(DATA / "metabolome.csv", index_col=0)
meta, metab = meta.loc[micro.index], metab.loc[micro.index]

has_micro = ~micro.isna().all(axis=1)
has_metab = ~metab.isna().all(axis=1)
complete = has_micro & has_metab
micro_only = has_micro & ~has_metab
metab_only = ~has_micro & has_metab
group_col = "PATGROUPFINAL_C"

findings["modality_structure"] = {
    "n_total": int(len(micro)),
    "complete_both": int(complete.sum()),
    "microbiome_only": int(micro_only.sum()),
    "metabolome_only": int(metab_only.sum()),
}
findings["group_counts"] = meta[group_col].value_counts().sort_index().to_dict()
findings["metadata_missing_pct"] = meta.isna().mean().mul(100).round(1).to_dict()
findings["metadata_missing_by_center"] = (
    meta.assign(m=meta["BMI_C"].isna()).groupby("CENTER_C")["m"].mean().round(3).to_dict())
findings["omics_missing_by_center"] = pd.crosstab(
    meta["CENTER_C"], np.where(micro_only, "micro_only",
        np.where(metab_only, "metab_only", "complete"))).to_dict()

# transforms on available rows only
micro_clr = clr(micro[has_micro])
metab_log = np.log1p(metab[has_metab])


# --------------------------------------------------------------------------- #
# Fig 1: modality structure + metadata missingness
# --------------------------------------------------------------------------- #
fig, ax = plt.subplots(1, 3, figsize=(20, 5))
order = sorted(meta[group_col].dropna().unique(), key=str)
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

# Fig 2: metadata missingness is MNAR by center (Denmark)
miss_center = (meta.assign(c=meta["CENTER_C"])
               .groupby("c")[["GENDER", "BMI_C", "AGE"]].apply(lambda d: d.isna().mean()))
fig, ax = plt.subplots(figsize=(7, 4))
sns.heatmap(miss_center, annot=True, fmt=".2f", cmap=SEQ, vmin=0, vmax=1, ax=ax)
ax.set_title("Metadata missing fraction by CENTER (MNAR)")
fig.tight_layout(); fig.savefig(FIG / "02_missing_by_center.png", dpi=130); plt.close(fig)


# --------------------------------------------------------------------------- #
# microbiome: diversity, PCoA, PERMANOVA, between-group distance
# --------------------------------------------------------------------------- #
def shannon(frame):
    p = frame.to_numpy(dtype=float); p = p / p.sum(axis=1, keepdims=True)
    return -(np.where(p > 0, p * np.log(p), 0)).sum(axis=1)

shan = pd.Series(shannon(micro[has_micro]), index=micro_clr.index)
mdf = meta.loc[micro_clr.index].assign(shannon=shan.values)
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=mdf, x=group_col, y="shannon", order=order, ax=ax, color="#D7D3CB", linecolor=INK, medianprops={"color": ACCENT, "linewidth": 2})
ax.set_title("Shannon diversity by disease group"); ax.set_xlabel("PatientGroup")
fig.tight_layout(); fig.savefig(FIG / "03_alpha_diversity.png", dpi=130); plt.close(fig)

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

sub = RNG.choice(len(micro_clr), size=min(700, len(micro_clr)), replace=False)
labg = meta.loc[micro_clr.index, group_col].values[sub]
labc = meta.loc[micro_clr.index, "CENTER_C"].values[sub]
f_g, p_g = permanova(aitch[np.ix_(sub, sub)], labg, 199)
f_c, p_c = permanova(aitch[np.ix_(sub, sub)], labc, 199)
findings["permanova_group"] = {"F": round(f_g, 2), "p": p_g}
findings["permanova_center"] = {"F": round(f_c, 2), "p": p_c}

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


# --------------------------------------------------------------------------- #
# differential abundance: T2D (3) vs control (8)
# --------------------------------------------------------------------------- #
gv = meta.loc[micro_clr.index, group_col]
ci, co = micro_clr[gv.values == "3"], micro_clr[gv.values == "8"]
rows = []
for sp in micro_clr.columns:
    p = mannwhitneyu(ci[sp], co[sp], alternative="two-sided").pvalue
    rows.append((sp, ci[sp].mean() - co[sp].mean(), p))
da = pd.DataFrame(rows, columns=["species", "clr_diff", "p"]).set_index("species")
da["p_adj"] = (da["p"] * len(da)).clip(upper=1.0)
findings["da_n_sig_bonferroni"] = int((da["p_adj"] < 0.05).sum())
top = pd.concat([da.nlargest(8, "clr_diff"), da.nsmallest(8, "clr_diff")])
fig, ax = plt.subplots(figsize=(9, 7))
ax.barh([s[:34] for s in top.index], top["clr_diff"],
        color=[ACCENT if v > 0 else INK for v in top["clr_diff"]])
ax.set_title("Top differential taxa: T2D (3) vs control (8)")
ax.set_xlabel("Δ mean CLR (T2D − control)")
fig.tight_layout(); fig.savefig(FIG / "07_diff_abundance.png", dpi=130); plt.close(fig)


# --------------------------------------------------------------------------- #
# metabolome trends by disease group
# --------------------------------------------------------------------------- #
mz = pd.DataFrame(StandardScaler().fit_transform(metab_log),
                  index=metab_log.index, columns=metab_log.columns)
mz_grp = meta.loc[mz.index, group_col]
mean_by_grp = mz.groupby(mz_grp.values).mean()
var_top = mean_by_grp.var().nlargest(25).index
fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(mean_by_grp[var_top].T, cmap=DIV, center=0, ax=ax,
            cbar_kws={"label": "mean z-score"})
ax.set_title("Most group-variable metabolites (z) by disease group")
fig.tight_layout(); fig.savefig(FIG / "08_metabolome_trends.png", dpi=130); plt.close(fig)


# --------------------------------------------------------------------------- #
# cross-omics correlation (complete samples only)
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# confounders
# --------------------------------------------------------------------------- #
have_age = meta.loc[micro_clr.index, "AGE"].notna().values
findings["confounders"] = {
    "age_vs_shannon_spearman": round(float(spearmanr(
        meta.loc[micro_clr.index, "AGE"].values[have_age], shan.values[have_age]).correlation), 3),
}


# --------------------------------------------------------------------------- #
# NAIVE BASELINE -- controlled dropout on the 1042 complete samples.
# Ground truth = standardize all features -> PCA -> Euclidean in 2 PCs.
# Then drop a modality for a fraction, impute, recompute distances, Mantel.
# Compared imputers: column-mean, KNN (using the present modality), and a
# linear cross-modal regressor (PLS) -- the honest competitor.
# --------------------------------------------------------------------------- #
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

    # (a) column mean of observed metabolome
    me_mean = Xme.values.copy(); me_mean[miss] = Xme.values[obs].mean(0)
    # (b) KNN using microbiome side as the bridge
    stk = Xme.values.copy(); stk[miss] = np.nan
    me_knn = KNNImputer(n_neighbors=10).fit_transform(
        np.hstack([Xmi.values, stk]))[:, Xmi.shape[1]:]
    # (c) PLS cross-modal regression microbiome -> metabolome (honest competitor)
    pls = PLSRegression(n_components=15).fit(Xmi.values[obs], Xme.values[obs])
    me_pls = Xme.values.copy(); me_pls[miss] = pls.predict(Xmi.values[miss])

    for name, me in (("mean", me_mean), ("knn", me_knn), ("pls", me_pls)):
        pcs = PCA(2, random_state=0).fit_transform(
            StandardScaler().fit_transform(np.hstack([Xmi.values, me])))
        r, p = mantel(gt, squareform(pdist(pcs)), 199)
        res[name] = {"mantel_r": round(r, 3), "p": p}
    baseline[f"drop_metab_{int(frac*100)}pct"] = res
findings["naive_distance_baseline"] = baseline

# disease prediction: both omics (complete) vs microbiome-only (all micro rows)
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
findings["disease_pred_balacc"] = {
    "both_omics_complete": round(float(acc_both), 3),
    "microbiome_only_all": round(float(acc_micro), 3),
}

(ROOT / "analysis" / "findings.json").write_text(json.dumps(findings, indent=2, default=str))
print(json.dumps(findings, indent=2, default=str))
print("\nFigures ->", FIG)
