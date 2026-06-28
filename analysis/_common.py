"""Shared setup for the per-topic MetaCardis analysis scripts.

Ported verbatim from the (now retired) eda.py / partner_eda.py monoliths: the
ROOT/DATA/FIG paths, data loading + the missing-modality masks, the CLR / PCoA /
PERMANOVA / Mantel / Shannon helpers, the editorial matplotlib theme + palette
constants, and a save_findings() helper that writes analysis/findings/<topic>.json.

Fidelity note: eda.py consumed a SINGLE np.random.default_rng(0) across three
blocks in this order -- (1) the PCoA/PERMANOVA subsample choice, (2) the two
PERMANOVA permutation loops (group then center), (3) the naive baseline. Splitting
those blocks into separate scripts would change the RNG draw sequence and the
resulting numbers. rng_after_permanova() rebuilds a fresh default_rng(0) and
advances it through draws (1) and (2) so the naive-baseline script reproduces the
original draws byte-for-byte. country_permanova.py reproduces (1)+(2) directly
from a fresh default_rng(0); microbiome_pcoa.py uses no RNG (deterministic).
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
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial.distance import pdist, squareform
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "train"
FIG = ROOT / "analysis" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
FINDINGS_DIR = ROOT / "analysis" / "findings"

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
SEQ = LinearSegmentedColormap.from_list("paper_rose", [PAPER, "#F4B7C2", ACCENT, "#8E1330"])
DIV = LinearSegmentedColormap.from_list("ink_rose", [INK, "#7C7A74", PAPER, "#F4A6B6", ACCENT])

# partner-deck palettes (from partner_eda.py)
CENTER_COLORS = {"Danemark": INK, "France": ACCENT, "Germany": MUT}
GENDER_COLORS = [INK, ACCENT]

group_col = "PATGROUPFINAL_C"
G = group_col


# --------------------------------------------------------------------------- #
# helpers (ported verbatim)
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


def permanova(dist: np.ndarray, labels: np.ndarray, rng, n_perm: int = 199):
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
        perm = rng.permutation(labels)
        ss_wp = within(perm)
        f = ((ss_total - ss_wp) / (a - 1)) / (ss_wp / (n - a))
        if f >= f_obs:
            count += 1
    return float(f_obs), count / (n_perm + 1)


def mantel(d1: np.ndarray, d2: np.ndarray, rng, n_perm: int = 199):
    iu = np.triu_indices_from(d1, k=1)
    v1, v2 = d1[iu], d2[iu]
    r_obs = spearmanr(v1, v2).correlation
    n = d1.shape[0]
    count = 1
    for _ in range(n_perm):
        p = rng.permutation(n)
        if abs(spearmanr(d1[np.ix_(p, p)][iu], v2).correlation) >= abs(r_obs):
            count += 1
    return float(r_obs), count / (n_perm + 1)


def shannon(frame):
    p = frame.to_numpy(dtype=float)
    p = p / p.sum(axis=1, keepdims=True)
    return -(np.where(p > 0, p * np.log(p), 0)).sum(axis=1)


# --------------------------------------------------------------------------- #
# data loading + missing-modality structure (ported verbatim from eda.py)
# --------------------------------------------------------------------------- #
def load_data():
    """Return (meta, micro, metab) aligned by micro.index, exactly as eda.py."""
    meta = pd.read_csv(DATA / "metadata.csv", index_col=0)
    micro = pd.read_csv(DATA / "microbiome.csv", index_col=0)
    metab = pd.read_csv(DATA / "metabolome.csv", index_col=0)
    meta, metab = meta.loc[micro.index], metab.loc[micro.index]
    return meta, micro, metab


def masks(micro, metab):
    has_micro = ~micro.isna().all(axis=1)
    has_metab = ~metab.isna().all(axis=1)
    complete = has_micro & has_metab
    micro_only = has_micro & ~has_metab
    metab_only = ~has_micro & has_metab
    return has_micro, has_metab, complete, micro_only, metab_only


def group_order(meta):
    return sorted(meta[group_col].dropna().unique(), key=str)


# --------------------------------------------------------------------------- #
# RNG fidelity replay
# --------------------------------------------------------------------------- #
def rng_after_permanova(meta, micro_clr):
    """Fresh default_rng(0) advanced through the exact draws eda.py made before
    the naive baseline: the subsample choice + the two PERMANOVA permutation
    loops (group then center). Returns the rng positioned for the naive block."""
    rng = np.random.default_rng(0)
    sub = rng.choice(len(micro_clr), size=min(700, len(micro_clr)), replace=False)
    labg = meta.loc[micro_clr.index, group_col].values[sub]
    labc = meta.loc[micro_clr.index, "CENTER_C"].values[sub]
    for _ in range(199):
        rng.permutation(labg)
    for _ in range(199):
        rng.permutation(labc)
    return rng


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #
def save_findings(topic: str, d: dict) -> None:
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    (FINDINGS_DIR / f"{topic}.json").write_text(json.dumps(d, indent=2, default=str))
    print(f"[{topic}] ->", FINDINGS_DIR / f"{topic}.json")
    print(json.dumps(d, indent=2, default=str))
