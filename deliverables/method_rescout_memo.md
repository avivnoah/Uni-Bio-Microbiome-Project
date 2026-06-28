# Decision Memo: Missing-Modality Distance Matrix, Method Selection

**To:** Academic staff
**Re:** Which candidate(s) to feature alongside Augmented-GW and miss-SNF
**Bottom line:** Add exactly one new featured method, CM-Harmonic, framed as the global-geometry-preserving placement method. Everything else is a lateral move or capped by the cross-modal ceiling.

---

## 1) Ranked shortlist of survivors (fatals dropped)

Dropped as fatal: LMDS-Complete (isotonic calibration is a monotone map, zero rank signal under Spearman) and Metric-Fusion Completion (conditional-expectation fill is rank-equivalent to dropping the missing term; rho of squared distances near 0.02).

**1. CM-Harmonic (avg 5.3, no fatal)** -- our pick.
Pitch: Treat the 1042 complete patients' true 2-PC coordinates as fixed boundary values and let them diffuse across a fused micro+metab similarity graph, so each single-omics patient inherits coordinates from whoever it is genuinely close to. One global Laplacian solve, no iterative training.
Best edge over GW/miss-SNF: It anchors directly on the grader's own target coordinates (the true 2-PC positions) instead of matching abstract within-modality geometry, and the partial patients densify the graph that supports placement. GW matches geometry blind to the target; harmonic extension is pointed straight at it.
Biggest risk: Maximum-principle shrinkage. Harmonic extension pulls every placed point toward the graph interior, compressing the radial PC1/PC2 coordinate of exactly the 696 patients that score. If the smoothing collapses them toward a modality-conditional mean, no monotone transform recovers the ranks.

**2. GFA-BLUP (avg 5.3, no fatal)** -- lateral.
Pitch: Fit Group Factor Analysis (shared plus per-modality private factors), infer a single-omics patient's shared and present-private scores, then krige the absent private factors instead of zeroing them.
Best edge over GW/miss-SNF: A principled shared/private decomposition that cleanly separates what is recoverable (shared) from what is not (private), which is honest about the ceiling.
Biggest risk: The kriging step is self-defeating. Private factors are by construction orthogonal to the shared block, so their conditional mean given shared scores is approximately zero at the 0.382 ceiling. The novelty collapses to MOFA+ with extra steps.

**3. UFGW-Anchor (avg 4.7, no fatal)** -- lateral, dominated.
Pitch: Place each single-omics patient by an unbalanced, fused Gromov-Wasserstein coupling between its within-modality cost-to-anchors and the anchors' true 2-PC geometry, then barycentric-project into 2-PC space.
Best edge over GW/miss-SNF: Projects into the exact target 2-PC space and adds an unbalanced marginal to handle differing cloud masses, a modest cleanup of the incumbent GW.
Biggest risk: The target is exactly linear for complete patients, so optimal single-omics placement is the closed-form frozen-PCA projection. GW cost-matching plus barycentric averaging is a noisier route to that same point with a contraction-to-centroid term, so on the metric it is mathematically dominated by mean-impute. It is a slightly nicer GW, not a better-than-GW.

**4. Procrustes-Diffusion (avg 4.3, no fatal)** -- weakest survivor.
Pitch: Build per-modality diffusion-map embeddings, learn one rigid Procrustes rotation on the 1042 shared anchors, push single-omics patients through it.
Best edge over GW/miss-SNF: Diffusion maps preserve global geometry (admissible here, unlike UMAP/t-SNE), and rigid alignment cannot warp, so it is geometrically conservative.
Biggest risk: A near-isometry between the micro and metab manifolds almost certainly does not exist at coupling rho below 0.25. The single rigid rotation has large anchor residual, mis-registering precisely the 696 contributed patients. Its geometric purity is also its ceiling: rigid cannot fix real cross-manifold distortion.

**5. EDM-Complete (avg 4.0, no fatal)** -- keep on bench.
Pitch: Seed the anchor block with true 2-PC squared distances, observe within-modality distances, complete the n-by-n distance matrix under a hard low-rank PSD constraint.
Best edge over GW/miss-SNF: Operates natively in distance space, which is what the grader consumes, and gives a single clean low-rank object.
Biggest risk: PC2 is roughly 99% metab-driven, so a micro-only patient's metab-loaded axis is under-determined; the completion fills it by a near-zero-R-squared cross-modal regression. Block-structured (not random) missingness also breaks low-rank-completion identifiability. The "immune to the ceiling" premise is false.

---

## 2) Verdict vs incumbents: ADD one, do not replace

**Keep both incumbents. Add CM-Harmonic as the third featured method. Replace nothing.**

Justification from the scores: no survivor scored a decisive win (top avg is 5.3, and even that one carries a real interior-shrinkage risk). Nothing earns the right to evict a working incumbent. But CM-Harmonic and GFA-BLUP tie for the top, and CM-Harmonic is the only candidate whose single best edge is genuinely orthogonal to what GW and miss-SNF already do: it anchors on the target coordinates themselves rather than on within-modality geometry. That is additive, so it belongs in the featured set, not as a replacement.

**What the corrected insight unlocks.** The earlier framing assumed linear methods were the ceiling. The corrected insight is that we are constrained only to global-geometry-preserving methods, not to linear ones, so global-preserving nonlinear methods (diffusion maps, kernel PCA, classical MDS, harmonic extension) are admissible and can in principle beat the linear target. This unlocks exactly one idea that genuinely beats GW/miss-SNF rather than tying them: **CM-Harmonic**, because harmonic extension on a fused diffusion graph is a nonlinear, global-preserving placement that points at the true 2-PC coordinates. GW and miss-SNF do not use the target coordinates at all; they reconstruct geometry and hope it aligns. That is the one real lever the corrected insight opens.

By contrast, the methods this insight does **not** rescue are the lateral moves: UFGW-Anchor (a tidier GW, dominated by linear projection on the linear-target patients), GFA-BLUP (a linear latent model whose novel step zeros out), and Procrustes-Diffusion (uses a global-preserving embedding but throws it away through a rigid alignment that the weak coupling makes ill-posed). Being allowed to go nonlinear does not help any method whose limiting factor is cross-modal predictability rather than embedding geometry.

---

## 3) Honest caveat: which "novel" ideas are capped by the cross-modal ceiling

These cannot beat naive mean-impute in the missing regime, because their novel mechanism reduces to recovering the absent modality from the present one, which is capped at max taxon-metabolite rho = 0.382 (R-squared roughly 0.017 on the load-bearing axis):

- **GFA-BLUP's kriging:** E[private_absent | shared] is approximately 0 by construction. Collapses to MOFA+ / centroid-zeroing.
- **UFGW-Anchor's barycentric placement:** weights come only from present-modality similarity, so it is a present-modality regression of the joint coordinate, bounded by the same ceiling and mean-reverting on the absent-loaded axis.
- **EDM-Complete's "ceiling-immune" claim:** false. A single-modality patient's joint position depends on the absent modality, which is exactly as unpredictable in distance space as in feature space.
- **Both fatals (LMDS, Metric-Fusion):** already dead, and for the same root reason dressed as a monotone distance map that Spearman ignores.

The uncomfortable truth: for the 696 single-modality patients, the metab-loaded coordinate axis is close to information-theoretically unrecoverable from the other modality. No method evades this. CM-Harmonic survives the caveat only partially, because it does not try to predict the absent modality from the present one; it places patients by graph proximity to the labelled completes, so its ceiling is set by how well the fused graph's neighborhoods agree with the true 2-PC neighborhoods, which is a different and possibly higher bound than 0.382. That distinction is its whole case, and it must be demonstrated, not assumed.

---

## 4) Recommendation for slide deck and M2 implementation

**Slide deck framing (creativity band, 96-100):**
- Lead with the corrected axis: the real problem is not linear-vs-nonlinear, it is global-vs-local structure preservation. State plainly that UMAP/t-SNE are inadmissible and explain why (they distort global geometry that Mantel-Spearman scores). This single reframing is the rigor signal that graders reward.
- Position the featured trio as one coherent story: GW (optimal-transport placement), miss-SNF (network fusion), and the new CM-Harmonic (target-anchored harmonic placement on a fused global-preserving graph). Three different mathematical traditions, one task.
- Show the cross-modal ceiling (rho = 0.382) as the honest boundary, and explain that CM-Harmonic's pitch is to route around it via graph proximity to labelled anchors rather than through it via imputation.

**What to actually implement and test by M2:**
1. **Build and benchmark CM-Harmonic end to end.** Fused micro+metab kNN graph, true 2-PC coordinates as Dirichlet boundary on the 1042 completes, single Laplacian solve for the 696. This is the M2 deliverable.
2. **Run the two make-or-break diagnostics before trusting any placement** (cheap, do them first):
   - Measure PC1/PC2 loading mass on each modality (confirm the suspected ~99% metab-driven PC2). This tells you how badly each single-omics group is under-determined.
   - Measure Spearman between fused-graph neighborhood structure and true 2-PC neighborhood structure on held-out completes. This is CM-Harmonic's actual ceiling; if it is not comfortably above 0.382, the method has no edge.
3. **Quantify and mitigate interior shrinkage.** Compare the radial spread (distance-to-centroid distribution) of placed 696 vs the completes. If compressed, test a radial-rescaling or a small anchor-weighted correction, and report it as an ablation.
4. **Mandatory ablations** so it does not read as a rebrand of Zhu-2003 label propagation: CM-Harmonic vs plain miss-SNF vs a diffusion-map baseline vs mean-impute, all on Mantel-Spearman, restricted to the 696 single-modality patients. The contribution lives or dies on this table.
5. **Gate:** if CM-Harmonic does not beat PLS-to-frozen-PCA and mean-impute on the 696-patient subset, do not feature it; fall back to GW + miss-SNF and report the ceiling as the honest negative result (still creativity-band material).

Files: no code reviewed or written for this memo; all inputs were the supplied tournament results and project context. Deliverables above map to the M2 (2026-09-10) milestone.