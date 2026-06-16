# Milestone 1 — findings & talking points

MetaCardis multi-omic distance pipeline. Group: (add names).

## 0. The task, restated precisely (this reframes everything)

The deliverable is **not** disease classification. It is an **n×n sample–sample distance
matrix** from combined microbiome + metabolome that stays faithful **when an entire
modality is missing** for some samples. The grader builds ground truth by:
`standard-scale every feature → PCA → Euclidean distance in the first 2 PCs`, and scores
our matrix with a **Mantel test**. So the target geometry is **linear and low-dimensional**.

**Consequence we build the whole pipeline around:** with both modalities present the target
is trivially recomputable (just run their pipeline). **The entire scientific problem lives in
the missing-modality regime** — recovering where a one-modality sample sits in the *joint*
PCA geometry.

## 1. Data exploration — key challenges

- **The missing modality is REAL in the data, not hypothetical.** Of 1738 subjects:
  **1042 have both omics, 348 microbiome-only, 348 metabolome-only** (the two missing
  sets are disjoint). ~40% of subjects are missing a whole modality. This *is* the project.
- **Microbiome** = 170 species, **relative abundance** (rows sum to 1, compositional, ~2%
  zeros) → we CLR-transform ourselves. (The brief's "CLR-transformed" wording is wrong vs
  the actual file.) **Metabolome** = 104 serum metabolites, heavy-tailed positive
  (0.01–582) → log1p + standardize.
- **Class imbalance**: T2D (group 3) n=528 … chronic-heart-failure (group 7) n=18, across 9
  groups (1, 2a, 2b, 3, 4, 5, 6, 7, 8=control).
- **CENTER is the dominant axis and a confounder.** PERMANOVA on Aitchison distances:
  **CENTER F=8.84 > disease-group F=3.72** (both p≈0.005). The country of recruitment
  structures the microbiome more than disease does.
- **Metadata missingness is MNAR by country**: Denmark has **100%** missing
  GENDER/BMI/AGE (privacy law), France ~2%, Germany 0% — separate from omics missingness.
- Microbiome PCoA (Aitchison): PC1 24.6%, PC2 13.7%. 107/170 species are
  Bonferroni-significant T2D-vs-control (Mann–Whitney on CLR).
- **Cross-omics coupling is weak**: max |Spearman| taxa↔metabolite = **0.382**. This caps
  what any cross-modal imputation can recover.

## 2. Naïve baseline (mandatory) — and a surprising, important result

Drop the metabolome for a fraction of the 1042 complete samples, impute it, recompute the
distance matrix, Mantel vs the full-data ground truth:

| metabolome dropped | mean-impute | KNN-impute | PLS cross-modal |
|---|---|---|---|
| 10% | **0.957** | 0.956 | 0.955 |
| 30% | **0.888** | 0.876 | 0.872 |
| 50% | **0.773** | 0.760 | 0.768 |

**Mean imputation ties or beats KNN and PLS at every level.** Why this is not a bug but a
deep fact: (a) the target is *linear PCA of standardized features*, so a mean-imputed
(→ post-standardization ≈ zero) block simply stops contributing to the PCs — i.e. the
distance falls back to the present modality's contribution, which is the correct linear thing
to do; (b) cross-modal signal (r≤0.38) is too weak for regression to add more than it costs
in noise. **The bar to beat at 50% missing is ~0.77, and a trivial method already clears it.**

Disease-state prediction (RF, 5-fold balanced accuracy, 9 classes, chance≈0.11):
both omics **0.26** vs microbiome-only **0.19** — the second modality helps, confirming there
*is* complementary signal worth recovering, just weak and metabolite-specific.

**Takeaway for the pipeline:** beating the baseline requires exploiting the *predictable
subset* of cross-modal structure and the *metabolome-only* direction better than a global
linear regressor — not brute-force imputation.

## 3. The inspiring methods (cutting-edge, 2025) and our adaptation

### ① Augmented / Fused Gromov–Wasserstein optimal transport (cross-field: math/vision)
*Source: SCOT+ (Baker et al., Bioinformatics Advances 2025); GW = Mémoli; FGW = Vayer 2020.*
GW compares samples living in **incomparable spaces** using only **within-modality
pairwise geometry** — no shared features required. A microbiome-only sample is coupled to
the complete samples' microbiome geometry, then **barycentric-projected onto the joint-PCA
anchor** to get a position. *Honest caveat we surface ourselves:* plain GW is
isometry-invariant (rotation/reflection ambiguity), so we use **Augmented GW**, whose
feature-supervision term breaks the ambiguity. We gate it on **beating mean/PLS** in the
missing-modality regime. Cross-field origin + 2025 software + empty application slot for bulk
microbiome+metabolome = the originality headline.

### ② miss-SNF — Similarity Network Fusion for completely-missing sources
*Source: miss-SNF (Bioinformatics 2025), extending SNF (Wang, Nature Methods 2014).*
Builds one sample-similarity network per modality and fuses them by cross-diffusion. It is the
**first SNF variant designed for whole-modality missingness**: a sample lacking a source is
reconstructed through its shared neighbors. **Output is literally a fused n×n similarity →
distance** — our exact deliverable. Never applied to microbiome+metabolome → novel use.

### Sound backbone / comparators
- **Coupled factorization (ACMTF-R, PLOS ONE 2026)**: shared sample-latent estimable from
  either modality via a missingness-masked fit; compute distances from the **common
  (cross-modally shared) components only** → commits only to what's recoverable, matches the
  linear target. The recsys "cold-start" framing.
- Baseline ladder: **mean / KNN / RF / PLS→frozen-PCA**.

## 4. Proposed pipeline & evaluation plan

1. **Preprocess**: CLR(microbiome) + log1p/standardize(metabolome); train-only scaler & PCA;
   keep CENTER as a covariate (regress out only if it helps Mantel — it may not, since the
   grader's own ground truth contains the center effect).
2. **Core model**: shared-latent distance robust to missing modality (AGW-OT and/or miss-SNF),
   benchmarked head-to-head against the baseline ladder.
3. **Evaluate**: Mantel r vs PCA-2PC ground truth, swept over missing-% (10/30/50; both
   directions: drop metabolome AND drop microbiome). **Subject-grouped CV** (distance pairs
   are non-iid); scaler/PCA fit on train only.
4. **Stretch / M2–M3**: uncertainty-aware distances (multiple imputation → distribution over
   distance matrices) to be honest about the cross-modal ceiling.

## Figures (in analysis/figures/)
01 overview · 02 missing-by-center · 03 alpha-diversity · 04 microbiome-PCoA ·
06 between-group distance · 07 differential abundance · 08 metabolome trends ·
09 cross-omics correlation
