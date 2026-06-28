# Cross-Field Pipeline Hunt (v2) — ranked field

- 6 · CM-Harmonic / SheafFit — learned-restriction-map harmonic extension onto the grader's true 2-PC boundary (topology-sheaf (generalizing incumbent I3 CM-Harmonic))
- 4.8 · ProMA — Product-Manifold Additive (Fisher-Pythagoras) distance with missingness-renormalization (info-geometry)
- 4.8 · DLB — Diffusion-Landscape Bath: anchored heat-kernel geometry with NO cross-modal edges (statphys-diffusion)
- 4 · GlueSB — gluing two entropic bridges through complete patients (disjoint micro-only x metab-only pairs) (ot-schrodinger)
- 3.5 · ASFE — Anchor-State Fidelity Embedding: partial-trace quantum fidelity to a frozen anchor panel (quantum-tensor)
- 4 FATAL · CoKrige-2PC — Co-Kriging / GP-BLUP onto the grader's 2-PC target field (anisotropic per-PC, with kriging variance) (geophysics-inverse)
- 3.8 FATAL · OGKP — Observability-Gated Koopman/state placement: reconstruct only the observable shared-state directions, gate the metric (control-koopman)

---

# DECISION MEMO: One Non-Linear Winner + Replacement Verdict

## 1. THE PICK

**CM-Harmonic-Aniso** — anchored harmonic graph extension onto the grader's own true 2-PC boundary, with held-out-fit per-axis affine calibration, asymmetric per-axis borrowing, and a fail-closed gate stack (sheaf machinery demoted to an optional ablation, not shipped).

Pitch: This is the only family in the field that anchors directly on the grader's OWN target geometry — it pins the 1042 complete patients at their true first-two-PC coordinates and then lets the 696 single-modality patients find their place by harmonic diffusion across a fused similarity graph, the way a hiker with no GPS fixes their position by triangulating off known summits they can see rather than by guessing their own altitude. It is genuinely non-linear (a sparse Laplacian solve, not a projection), global-geometry-preserving (admissible under Mantel/Spearman, unlike UMAP/t-SNE), and it refuses to pay the imputation tax: it never reconstructs the absent modality, it routes patients by proximity to landmarks the grader itself defined. The honest novelty a Nobel-caliber reviewer respects is not the harmonic solve (classical) but the discipline around it: it is the only method that turns the grading rubric's ground truth into a Dirichlet boundary condition and then proves, per-axis, exactly where the cross-modal ceiling — not the method — is binding.

## 2. WHY IT WINS

Its single decisive edge over I1/I2/I3 in their raw form: **it anchors on the grader's exact target coordinates as a hard boundary condition, so the 1042x1042 complete block is correct by construction and every single-modality patient is placed in the grader's true PC1/PC2 frame rather than in a blind, self-reconstructed embedding.** Fused-GW (I1) recovers geometry up to a rotation/reflection it must then guess; miss-SNF (I2) fuses similarity networks in an arbitrary spectral frame with no tie to the target axes; raw CM-Harmonic (I3) has the right anchor but silently compresses the scored 696 via harmonic interior-shrinkage and never corrects it. CM-Harmonic-Aniso keeps the anchor and adds the only shrinkage fix the math permits.

Why it is not capped by the 0.382 ceiling: that ceiling is the max single-taxon-to-single-metabolite Spearman, and it only binds on the **cross-axis** component (a microbiome-only patient's PC2, which is ~99% metabolite-driven). The bulk of the method's value lives on the **same-axis** component — PC1 for micro-only, PC2 for metab-only — which it recovers by graph proximity to grader-anchored completes WITHIN the present modality, never crossing the modal gap. That same-axis placement is not a cross-modal prediction, so the 0.382 number does not apply to it. The honest concession is built into the method, not hidden: where the cross-axis component IS ceiling-bound, the asymmetric borrow falls back to global-mean (provably equal to mean-impute, never worse). It routes AROUND the ceiling on the component that carries most of the signal and refuses to underperform mean-impute on the component where the ceiling is real.

## 3. HOW IT WORKS, simply

Student-presentable: Imagine plotting all 1738 patients on the grader's 2-D map. We already know exactly where the 1042 complete patients go, because the grader's formula needs both omics and they have both — pin them down as fixed landmarks. Now build a friendship graph: connect patients who are similar in microbiome, and separately connect patients who are similar in metabolome, then overlay the two. A single-modality patient simply does not draw any friendship edges in the modality it is missing — absence is absence-of-edge, we never invent fake data for it. To place the 696 unknowns, we apply one rule: each unknown patient sits at the weighted average position of its graph neighbors (a single sparse linear solve over the whole graph at once). That is harmonic extension — the unknowns relax into the smoothest configuration consistent with the fixed landmarks.

Two honest corrections finish the job. First, harmonic averaging pulls everyone slightly toward the center (shrinkage), and on a rank metric the only thing that actually distorts distance ranks is the PC1-to-PC2 balance, so we fit a tiny two-number axis-balance correction on a held-out set of completes that we deliberately un-pinned and re-placed — the only set that has actually felt the shrinkage. Second, for the absent axis (e.g. a micro-only patient's metabolite-driven PC2), we borrow it from present-modality neighbors with a learned shrink-to-mean weight, and if a gate shows that borrow beats nothing, we use it; if it fails, we fall back to the global mean (provably no worse than mean-impute).

## 4. HONEST LIMITS

Where the ceiling still bites: the cross-axis component is irreducibly cross-modal. Recovering a micro-only patient's metabolite-driven PC2 IS multivariate micro-to-metab prediction wearing a graph costume, bounded by cross-omics rank correlation (single-feature rho=0.382, EDA cross-omics rho<0.25). PLS-to-frozen-PCA is the optimal LINEAR extractor of that same signal, so the margin over PLS on the cross-axis component may be thin or zero. The affine calibration de-shrinks magnitudes but provably cannot raise the rank ceiling.

What could make it fail: (a) M3 transfer structurally requires each unseen cohort to contain enough complete patients to form a Dirichlet boundary — a boundary-poor cohort degrades silently with no pre-submission signal; mitigation is to report the per-cohort fused-neighborhood-vs-true-2PC number as a transfer-confidence diagnostic and fall back to PLS when it fails. (b) Calibration overfit on few-DOF, non-iid distance pairs; mitigated by subject-grouped folds and ratio-only regularization, and must be ablated against identity calibration. (c) Scope-creep temptation to re-add the demoted sheaf layer under deadline pressure — explicitly fenced behind a residual-justified ablation.

Realistic Mantel claim (do NOT overclaim): pooled-n Mantel will look high for ALL anchored methods because the 1042x1042 block dominates and is correct by construction — pooled is NOT the discriminating number. The defensible claim lives on the 696 single-modality subset: MATCH or modestly beat PLS-to-frozen-PCA on the same-axis component, clearly beat mean/KNN/RF-impute on the same-axis component, and be statistically indistinguishable from PLS on the cross-axis component. This is a creativity-and-rigor story (anchoring on the grader's own target + an honest per-axis ceiling decomposition), explicitly NOT a "we beat the baseline by X Spearman points" story.

## 5. REPLACEMENT VERDICT

**Drop I2 (miss-SNF). Keep I1 (Augmented/Fused-GW) and I3 — where I3 is upgraded in place to CM-Harmonic-Aniso.**

Rationale: CM-Harmonic-Aniso is the hardened evolution OF I3, so it does not "replace" I3 so much as become it — the featured anchored slot is filled by the upgraded form. That leaves one slot to cut among I1 and I2. Cut miss-SNF, for three evidence-backed reasons:

1. **Redundant mechanism, weaker anchor.** miss-SNF fuses per-modality similarity networks in an arbitrary spectral frame with no tie to the grader's target axes. CM-Harmonic-Aniso does strictly more: it builds the same fused per-modality graph (CLR-micro + log-metab kNN affinities, absence = absence-of-edge) but then pins it to the grader's TRUE 2-PC coordinates. SNF is the un-anchored special case of the anchored method we are keeping — having both is presenting the same fusion idea twice, once without the decisive anchor.
2. **No principled M3 transfer rule.** SNF's fused-network spectral embedding is per-dataset and has no clean fit-on-train/apply-to-cohort rule; CM-Harmonic-Aniso and Fused-GW both have explicit transfer stories (refit boundary per cohort onto the cohort's own PCA frame; barycentric projection onto a joint anchor, respectively).
3. **Lowest distinct contribution.** Keep Fused-GW because it is the genuinely DIFFERENT idea in the deck — optimal-transport coupling with an augmented term that breaks GW's rotation/reflection ambiguity is a mechanistically distinct route (transport, not diffusion) and gives the deck breadth: one transport method, one harmonic-extension method, plus the baseline ladder. SNF adds neither a distinct mechanism nor a transfer story nor an anchor the kept pair lacks.

Net featured deck: **Fused-GW (I1, transport) + CM-Harmonic-Aniso (upgraded I3, anchored harmonic) + baseline ladder (mean/KNN/RF-impute, PLS-to-frozen-PCA)**. ProMA-H and DLB-Anchored stay as ablation rows (the safe frozen-loadings floor, and the soft-kernel operator-agnosticism check), not featured slots.

## 6. SLIDE-READY CONTENT

**Eyebrow:** Missing-modality patient placement, routed around the cross-modal ceiling

**Headline:** CM-Harmonic-Aniso — placing patients on the grader's own map by triangulation, not imputation

**Bullets:**
- Pins the 1042 complete patients at their TRUE first-two-PC coordinates as a Dirichlet boundary; the only method anchored on the grader's own target geometry, so the complete block is correct by construction.
- Places the 696 single-modality patients by one sparse harmonic Laplacian solve on a fused micro+metab kNN graph where a missing modality is absence-of-edge, never an imputed value — routing AROUND the 0.382 ceiling via proximity, not THROUGH it via reconstruction.
- Held-out-fit per-axis affine calibration corrects harmonic interior-shrinkage on the PC1:PC2 balance ratio (the only thing that moves cross-axis distance RANKS under Spearman); low-DOF and ratio-only by design to resist overfit.
- Honest per-axis decomposition: strong same-axis recovery (beats all imputation baselines), cross-axis falls back to global-mean = mean-impute, provably never worse on any axis; transfer-confidence diagnostic gates an automatic fallback to PLS on boundary-poor M3 cohorts.

**M2 implementation gate (one line):** Ship only if, on subject-grouped held-out completes, PER-AXIS Spearman of fused-neighborhood placement exceeds BOTH 0.382 AND the PLS-to-frozen-PCA per-axis correlation for each masked modality, AND the affine calibration improves held-out 696-subset Mantel over identity — else fall back to global-mean PC2 (mean-impute) on the failing axis and to PLS on any failing cohort.