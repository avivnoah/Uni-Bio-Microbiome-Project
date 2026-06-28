"""Reproduce + restyle the partner's exploration on our data, in the deck palette.

Repoints her Windows-path notebooks to data/train, verifies her numbers, and
regenerates her figures (age/BMI/gender/country by group, metadata-only feature
importance, per-group differential abundance & metabolite counts) plus her
random-cell imputation-R2 baseline. Outputs paper/ink/rose figures + a
partner_findings.json consumed by build_html.py / build_deck.py.
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
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import KNNImputer
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import cross_val_score, cross_val_predict, StratifiedKFold, KFold

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "train"
FIG = ROOT / "analysis" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(42)

PAPER, INK, MUT, ACCENT = "#FAF9F6", "#0A0A0A", "#6B6863", "#FF2D55"
sns.set_theme(style="ticks", context="talk")
plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUT, "ytick.color": MUT, "axes.titlecolor": INK,
    "axes.grid": True, "grid.color": "#E4E1DA", "grid.linewidth": .8,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 12, "axes.titlesize": 14, "axes.titleweight": "bold", "legend.frameon": False,
})
CENTER_COLORS = {"Danemark": INK, "France": ACCENT, "Germany": MUT}
GENDER_COLORS = [INK, ACCENT]
out: dict = {}


def clr(frame, pseudo=1e-6):
    x = frame.to_numpy(float) + pseudo
    x = x / x.sum(1, keepdims=True)
    lx = np.log(x)
    return pd.DataFrame(lx - lx.mean(1, keepdims=True), index=frame.index, columns=frame.columns)


# ---- load (repointed from her Windows paths) ----
micro = pd.read_csv(DATA / "microbiome.csv", index_col=0)
metab = pd.read_csv(DATA / "metabolome.csv", index_col=0)
meta = pd.read_csv(DATA / "metadata.csv", index_col=0).loc[micro.index]
metab = metab.loc[micro.index]
G = "PATGROUPFINAL_C"
order = sorted(meta[G].dropna().unique(), key=str)
has_micro = ~micro.isna().all(axis=1)
has_metab = ~metab.isna().all(axis=1)


# ---- A+B: age & BMI by group (confounders) ----
fig, ax = plt.subplots(1, 2, figsize=(15, 5.2))
for a, col, title in [(ax[0], "AGE", "Age by patient group"), (ax[1], "BMI_C", "BMI by patient group")]:
    d = meta[[G, col]].dropna()
    sns.boxplot(data=d, x=G, y=col, order=order, ax=a, color="#D7D3CB",
                linecolor=INK, fliersize=2, medianprops={"color": ACCENT, "linewidth": 2.2})
    a.set_title(title); a.set_xlabel("patient group"); a.set_ylabel(col.replace("_C", ""))
fig.tight_layout(); fig.savefig(FIG / "10_age_bmi_by_group.png", dpi=130); plt.close(fig)

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

# ---- F+G: per-group differential features vs control (group 8) ----
micro_clr = clr(micro[has_micro])
metab_log = np.log1p(metab[has_metab])
mz = pd.DataFrame(StandardScaler().fit_transform(metab_log), index=metab_log.index, columns=metab_log.columns)
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

# ---- H: verify her random-cell imputation-R2 baseline (on metabolome) ----
def masked_r2(X, rate, method):
    Xv = X.to_numpy(float).copy()
    mask = RNG.random(Xv.shape) < rate
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
        # Random-Forest imputation (MICE-style): predict each masked cell from the
        # other metabolites. Light settings + one pass to keep runtime sane.
        rf = RandomForestRegressor(n_estimators=20, max_depth=8, n_jobs=-1, random_state=0)
        imp = IterativeImputer(estimator=rf, max_iter=1, random_state=0).fit_transform(Xm)
    pred = imp[mask]
    ss_res = np.sum((truth - pred) ** 2); ss_tot = np.sum((truth - truth.mean()) ** 2)
    return round(float(1 - ss_res / ss_tot), 3)


# RF imputation is slow at full size; run it on a fixed subsample for speed.
Xme = mz  # standardized log metabolome on complete-metab rows
Xme_rf = Xme.iloc[RNG.choice(len(Xme), size=min(500, len(Xme)), replace=False)]
naive = {}
for rate in (0.1, 0.2, 0.4, 0.6):
    row = {m: masked_r2(Xme, rate, m) for m in ("mean", "median", "knn")}
    row["rf"] = masked_r2(Xme_rf, rate, "rf")
    naive[f"{int(rate*100)}%"] = row
out["partner_naive_imputation_r2"] = naive

# ---- disease state WITH vs WITHOUT imputation (guiding question) ----
# On the 1042 complete subjects: classify disease group (RF, balanced accuracy, 5-fold).
#  without = microbiome only (metabolome treated as unavailable)
#  with    = microbiome + metabolome reconstructed from microbiome (out-of-fold KNN)
#  real    = microbiome + the true metabolome (upper bound)
cc = micro_clr.index.intersection(mz.index)
Xmi_c = pd.DataFrame(StandardScaler().fit_transform(micro_clr.loc[cc]), index=cc)
Xme_c = mz.loc[cc]
y_c = meta.loc[cc, G].astype(str).values
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

(ROOT / "analysis" / "partner_findings.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
print("\nfigures -> 10_age_bmi_by_group, 12_country_by_group, 13_gender_by_group, "
      "14_feature_importance, 15_diff_per_group")
