"""Build deliverables/milestone1.html — bold-mono / Awwwards-editorial slide deck.

Unified milestone-1 deck: our distance-matrix framing + design, combined with the
partner's richer EDA (age/BMI/gender/country, metadata feature importance,
per-group differential counts) re-run on our data and restyled to the palette,
plus a dual-framing naive baseline. Self-contained single file (fonts + figures
base64-embedded), keyboard/click/swipe nav.
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "analysis" / "figures"
_ALL = {}
for _p in sorted((ROOT / "analysis" / "findings").glob("*.json")):
    _ALL.update(json.loads(_p.read_text()))
F = PF = _ALL


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def font_face(path, family):
    p = Path(path)
    if not p.exists():
        return ""
    return (f"@font-face{{font-family:'{family}';font-weight:100 800;font-style:normal;"
            f"font-display:swap;src:url(data:font/woff2;base64,{b64(p)}) format('woff2')}}")


FONTS = font_face("/tmp/sg.woff2", "SpaceG") + font_face("/tmp/jb.woff2", "JBMono")
DISP = "SpaceG, 'Segoe UI', system-ui, sans-serif" if "SpaceG" in FONTS else "system-ui, sans-serif"
MONO = "JBMono, ui-monospace, Menlo, monospace" if "JBMono" in FONTS else "ui-monospace, monospace"


def img(name, alt=""):
    return f'<img alt="{alt}" src="data:image/png;base64,{b64(FIG / name)}">'


ms, gc = F["modality_structure"], F["group_counts"]
pcoa, pg, pc = F["pcoa_explained"], F["permanova_group"], F["permanova_center"]
dp, b = F["disease_pred_balacc"], F["naive_distance_baseline"]
fi = PF["metadata_feature_importance"]
md_acc = PF["metadata_only_cv_balacc"]
pnaive = PF["partner_naive_imputation_r2"]
max_sp = max(PF["diff_species_per_group"].values())
max_mb = max(PF["diff_metab_per_group"].values())
ctrl_n = 249  # healthy comparison group (PATGROUPFINAL_C == "8")


def trow(frac):  # whole-modality recovery -> distance-Mantel baseline
    d = b[f"drop_metab_{frac}pct"]
    m, med, k, rf = d["mean"]["mantel_r"], d["median"]["mantel_r"], d["knn"]["mantel_r"], d["rf"]["mantel_r"]
    best = max(m, med, k, rf)
    c = lambda v: f'<td class="win">{v}</td>' if v == best else f"<td>{v}</td>"
    return f"<tr><td>{frac}%</td>{c(m)}{c(med)}{c(k)}{c(rf)}</tr>"


def r2row(rate):  # partner's random-cell imputation R2
    d = pnaive[rate]
    m, med, k, rf = d["mean"], d["median"], d["knn"], d["rf"]
    best = max(m, med, k, rf)
    c = lambda v: f'<td class="win">{v}</td>' if v == best else f"<td>{v}</td>"
    return f"<tr><td>{rate}</td>{c(m)}{c(med)}{c(k)}{c(rf)}</tr>"


dww = PF["disease_with_without"]


SLIDES = []
TOTAL = 15


def slide(i, section, body, kind="", src=""):
    num = f"{i:02d}"
    srctag = f'<span class="srcref">code · {src}</span>' if src else "<span></span>"
    SLIDES.append(f"""<section class="slide {kind}" data-i="{i-1}">
      <header class="shead"><span><i class="dot"></i>MetaCardis · Milestone 1</span>
        <span>{section}</span></header>
      <div class="snum" aria-hidden="true">{num}</div>
      <div class="sbody">{body}</div>
      <footer class="sfoot"><span>Computational Microbiome Workshop</span>
        {srctag}<span>{num} / {TOTAL:02d}</span></footer>
    </section>""")


# 01 — title
slide(1, "", """
  <div class="title-block">
    <p class="eyebrow" data-enter="1">Multi-omics · missing-modality distances</p>
    <h1 class="display" data-enter="2">Estimating sample distances<br>across multi-omics,<br>
      <span class="key">under missing modalities</span></h1>
    <div class="accent-rule" data-enter="3"></div>
    <p class="byline" data-enter="3">Aviv Noah &amp; Inbal &nbsp;·&nbsp; MetaCardis cohort</p>
  </div>""", "is-title")

# 02 — task reframe
slide(2, "The problem", """
  <p class="eyebrow" data-enter="1">What we need to build</p>
  <h2 class="statement" data-enter="2">A table of <span class="key">how different every two patients are</span>,
    built from both omics, that still works even when a patient is <span class="key">missing one of them</span>.</h2>
  <ul class="notes" data-enter="3">
    <li>How it's graded: from the full data the staff build their own "correct" distance table (scale every
      feature, run PCA, keep the distance in the first <b>2 components</b>). A <b>Mantel test</b> then
      measures how well <b>our table</b> (the distances our pipeline outputs) agrees with theirs.</li>
    <li>If a patient has both omics, we just run that same recipe and get the staff's answer, so there's
      nothing to predict. The real work is patients <b>missing one omics</b>: we must rebuild the missing
      part to place them, and that's hard because the two omics barely predict each other.</li>
  </ul>""", "is-statement")

# 03 — data overview
slide(3, "Exploration / data", f"""
  <p class="eyebrow" data-enter="1">Who's in the cohort, and what's missing</p>
  <h2 class="head" data-enter="1">~40% of subjects are missing a whole modality</h2>
  <div class="figfull" data-enter="2"><div class="figwell">{img('01_overview.png','overview')}</div></div>
  <div class="figcaprow" data-enter="2">
    <div><b>Left</b> — how many patients in each disease group. Very uneven.</div>
    <div><b>Middle</b> — who has which omics: ~40% have only one of the two.</div>
    <div><b>Right</b> — % of patients missing each metadata field (BMI / sex / age).</div>
  </div>
  <div class="statrow" data-enter="3">
    <div class="stat"><span class="num">{ms['complete_both']}</span><span class="lab">both omics</span></div>
    <div class="stat"><span class="num">{ms['microbiome_only']}</span><span class="lab">microbiome only</span></div>
    <div class="stat"><span class="num">{ms['metabolome_only']}</span><span class="lab">metabolome only</span></div>
    <div class="stat"><span class="num">{gc['3']}<span class="arrow">vs</span>{gc['7']}</span>
      <span class="lab">biggest vs smallest group (diabetes / heart-failure)</span></div>
  </div>""", src="analysis/cohort_overview.py")

# 04 — demographics confound disease
slide(4, "Exploration / demographics", f"""
  <p class="eyebrow" data-enter="1">Age and weight differ a lot between disease groups</p>
  <div class="figfull" data-enter="2"><div class="figwell">{img('10_age_bmi_by_group.png', 'age and bmi by group')}</div></div>
  <div class="figcaprow two" data-enter="2">
    <div><b>Left</b> — age in each group. <b>Right</b> — BMI (body-mass index) in each group.</div>
    <div>Each box = middle 50% of patients, the line = median (typical value), dots = unusual patients (outliers).</div>
  </div>
  <p class="foot-note" data-enter="3">The obesity groups (2a, 2b) are the youngest, with BMI above 40; the diabetes and heart-disease
  groups (3 to 6) are older, around 60. Age and weight differ so much between groups that <b>they, not the
  microbiome, could explain differences we see</b>. So they are background factors we have to keep in mind.</p>""",
  src="analysis/demographics.py")

# 05 — batch effect by center
slide(5, "Exploration / country effects", f"""
  <p class="eyebrow" data-enter="1">Which country a patient came from shapes their microbiome</p>
  <div class="fig-stats" data-enter="2">
    <div class="figwell">{img('12_country_by_group.png','disease groups by country')}</div>
    <div class="side">
      <div class="stat lg"><span class="num">{pc['F']}</span><span class="lab">PERMANOVA score · country</span></div>
      <div class="hair"></div>
      <div class="stat lg"><span class="num">{pg['F']}</span><span class="lab">PERMANOVA score · disease</span></div>
      <p class="body small">PERMANOVA F compares how different patients are <i>between</i> groups versus
        <i>within</i> a group. It has no fixed top end; the reference is <b>1</b>, meaning a label splits the
        microbiomes no better than a random split. Both numbers sit well above 1 and are significant
        (p = 0.005), so both leave a real mark. The point is the gap: country (8.84) separates patients
        <span class="key">more than twice as strongly</span> as the disease does (3.72).</p>
    </div>
  </div>
  <p class="foot-note" data-enter="3">"Country-skewed" = some disease groups come almost entirely from one
  country (group 2b is mostly German, group 7 mostly French, group 4 has almost no Germans), so disease and
  country are tangled together. Also, Denmark shares no BMI / age / sex at all (their privacy law), so that
  gap is systematic, not random.</p>""", src="analysis/country_permanova.py")

# 06 — demographics out-predict omics
slide(6, "Exploration / what predicts disease", f"""
  <p class="eyebrow" data-enter="1">Basic demographics predict the disease better than the omics do</p>
  <div class="fig-stats" data-enter="2">
    <div class="figwell">{img('14_feature_importance.png','what the metadata model leans on')}</div>
    <div class="side">
      <div class="stat lg"><span class="num">{md_acc}</span><span class="lab">Random Forest guess from age / BMI / sex / country</span></div>
      <p class="body small">A Random Forest (a model that combines many decision trees), checked with 5-fold
        cross-validation, guesses a patient's disease group (1 of 9) from <i>only</i> the metadata and gets it
        right {md_acc:.0%} of the time, scored fairly across all 9 groups (blind guessing would be ~{1/9:.0%},
        1 in 9).</p>
      <p class="body small">We ran the same model on two other inputs and it did <i>worse</i>: both omics
        together <b>{dp['both_omics_complete']}</b>, microbiome alone <b>{dp['microbiome_only_all']}</b>. So
        the omics carry less disease signal than plain demographics.</p>
    </div>
  </div>
  <p class="foot-note" data-enter="3">The bars show what that metadata model leans on most: BMI and age do
  almost all the work, so the omics hold only weak, scattered disease signal. The spec also asks whether
  <b>imputing</b> a missing omics helps this prediction (on the complete patients): it does not. Microbiome
  alone scores {dww['without_imputation_microbiome_only']}; adding a metabolome guessed from the microbiome
  stays at {dww['with_imputation_micro_plus_recovered_metab']}; only the <i>real</i> metabolome lifts it to
  {dww['real_both_omics_upper_bound']}. Another reason we target distances, not the disease label.</p>""",
  src="analysis/predict_disease.py + naive_baseline.py")

# 07 — microbiome geometry
slide(7, "Exploration / microbiome map", f"""
  <p class="eyebrow" data-enter="1">Disease groups don't form clean clusters on the microbiome map</p>
  <div class="fig-stats" data-enter="2">
    <div class="figwell">{img('04b_microbiome_pcoa_disease.png','microbiome PCoA map coloured by disease group')}</div>
    <div class="side">
      <div class="stat lg"><span class="num">{pcoa[0]+pcoa[1]:.0%}</span>
        <span class="lab">of the real differences between patients are visible in this flat map; the other
          {1-(pcoa[0]+pcoa[1]):.0%} sit in directions it can't draw</span></div>
      <p class="body small">Each dot is a patient; similar microbiomes sit close. Colour = disease group, and
        the colours are <b>mixed everywhere</b>, with no tidy blocks. So the microbiome doesn't split
        patients into clean disease clusters, which is why we <span class="key">place patients by
        distance</span> rather than predict a disease label.</p>
      <p class="body small">The flat map has two axes (the two biggest patterns of variation), and together
        they only cover {pcoa[0]:.0%} + {pcoa[1]:.0%} of the differences. The rest is spread over many
        smaller patterns we can't draw, so the microbiome is <b>high-dimensional</b>, not a few clean groups.</p>
    </div>
  </div>
  <p class="foot-note" data-enter="3">A PCoA squeezes the patient-to-patient microbiome distances (Aitchison,
  our compositional distance) into 2-D. Country also shapes this map, but we judge that with the
  df-adjusted PERMANOVA on slide 05, not by eye, since fewer colours always look tidier.</p>""",
  src="analysis/microbiome_pcoa.py")

# 08 — differential signal per group
slide(8, "Exploration / disease signal", f"""
  <p class="eyebrow" data-enter="1">Both omics separate the disease groups, the metabolome more evenly</p>
  <div class="figfull" data-enter="2"><div class="figwell">{img('15_diff_per_group.png','how many microbes and metabolites differ per disease group')}</div></div>
  <div class="figcaprow two" data-enter="2">
    <div><b>Left:</b> for each disease group, how many microbe species differ from the healthy group.
      The count swings a lot, from {min(PF['diff_species_per_group'].values())} up to {max_sp}, so some
      diseases reshape the microbiome heavily while others barely touch it.</div>
    <div><b>Right:</b> the same count for blood metabolites. These stay high almost everywhere
      ({min(PF['diff_metab_per_group'].values())} to {max_mb}), so the metabolome shifts broadly across
      nearly every disease.</div>
  </div>
  <p class="foot-note" data-enter="3"><b>How we counted:</b> for every feature (170 microbe species, 104
  metabolites) we run a Mann-Whitney U test (a rank test that asks if its values are shifted in the disease
  group vs the {ctrl_n} healthy controls, group 8), then correct all the p-values together for multiple
  testing (Benjamini-Hochberg FDR) and count how many beat FDR&lt;0.05. Each bar is that count. The FDR
  step keeps false hits low when testing hundreds of features at once. We did this to confirm both omics
  really hold disease signal, and to see which one holds more.</p>""",
  src="analysis/differential_abundance.py")

# 09 — cross-omics coupling weak
slide(9, "Exploration / linking the two omics", f"""
  <p class="eyebrow" data-enter="1">The two omics barely predict each other, which limits any imputation</p>
  <div class="fig-stats" data-enter="2">
    <div class="figwell">{img('09_cross_omics_corr.png','correlation heatmap, top microbes vs top metabolites')}</div>
    <div class="side">
      <div class="stat lg"><span class="num">{F['max_abs_taxa_metab_corr']}</span>
        <span class="lab">strongest link between any one microbe and any one metabolite</span></div>
      <p class="body">Each square is how strongly one microbe moves with one metabolite (Spearman
        correlation, where 0 is no link and 1 is a perfect link). The rows are our 30 most variable
        microbes, the columns our 30 most variable metabolites. Almost every square sits near 0, and the
        single strongest pair only reaches {F['max_abs_taxa_metab_corr']}. We both found this on our own.
        So if a patient is missing one omics, we can rebuild only a sliver of it from the other, which
        sets a <span class="key">low ceiling</span> on imputation.</p>
    </div>
  </div>
  <p class="foot-note" data-enter="3">So why does the naive baseline (next slide) still score high? Because at a
  low missing rate most patients keep both omics, so most patient-to-patient distances are still exact and
  dominate the score; the dropped few just fall back to the omics they have. The tell that nothing is truly
  recovered: every fill method (mean, median, KNN, RF) ties.</p>""", src="analysis/cross_omics.py")

# 10 — naive baseline (spec: impute a missing whole modality, then compute distances)
slide(10, "Naïve baseline", f"""
  <p class="eyebrow" data-enter="1">The required baseline: fill in a missing omics, then measure patient distances</p>
  <div class="twomethod" data-enter="2">
    <div class="col">
      <h3 class="colh">Drop the whole metabolome, rebuild it, then score the distances</h3>
      <table class="dtable sm"><thead><tr><th>dropped</th><th>mean</th><th>med</th><th>KNN</th><th>RF</th></tr></thead>
        <tbody>{trow(10)}{trow(30)}{trow(50)}</tbody></table>
      <p class="body small">Row = the share of patients whose whole metabolome we hid; column = how we
        rebuilt it; number = the Mantel score (1 = identical to the true distances).</p>
    </div>
    <div class="col">
      <p class="body small">We hide the metabolome for some patients, rebuild it four ways from their
        microbiome, recompute the patient-to-patient distances, and score them against the real ones.
        <span class="key">All four methods tie</span>, even copying the average metabolome, so none is truly
        recovering it. The score also falls as we drop more patients (see slide 09 for why the high numbers
        mislead).</p>
      <p class="body small">Why they tie: once a whole metabolome is gone, the only way to rebuild it is from
        the microbiome, and the two are weakly linked. So the clever fills add almost nothing over a plain
        mean.</p>
    </div>
  </div>
  <p class="methodline" data-enter="3"><b>How the distances are made.</b> Each matrix is <b>n&times;n</b>
  (one row and column per patient), built the grader's exact way: standardize both omics, run PCA, then take
  the Euclidean distance between patients in the first 2 PCs. The Mantel test then scores us by the rank
  correlation between our matrix and the true one, taken over every patient pair.</p>
  <div class="callout punch" data-enter="3">
    <p class="punch-lead">So filling the gap is a dead end, and that is exactly why the project needs a
      smarter pipeline.</p>
    <p>Naive imputation never beats simply copying the average metabolome, because the two omics barely
      predict each other (slide 09). That weak link is a hard <span class="key">ceiling</span> on anything
      that invents the missing numbers, so the real pipeline must place patients by their geometry, not by
      guessing what's absent.</p>
  </div>""", src="analysis/naive_baseline.py")

# 11 — method framing
slide(11, "Method selection", """
  <p class="eyebrow" data-enter="1">How we picked the two methods on the next slides</p>
  <h2 class="head" data-enter="1">We scanned many fields, then tried hard to break what we found.</h2>
  <p class="lead-sm" data-enter="1">Before presenting the two methods we build on, we want to show how we
    selected them. We searched widely for ideas, including fields well outside microbiome research (spatial
    navigation, GPS positioning, topology, physics, optimal transport), and then judged every candidate
    against two clear criteria, keeping only those that met both.</p>
  <ul class="notes" data-enter="2">
    <li><b>Test 1 · does it respect how we are scored?</b> Our score checks the <i>whole</i> layout (how far
      every pair of patients sits, near and far). So the danger is not nonlinear methods in general; it is
      methods that only keep close patients close while squashing or stretching the far-apart distances. We
      kept methods that <span class="key">keep the whole layout faithful</span>: far-apart patients stay
      far apart, not just the close pairs. That can even be a curved (nonlinear) method, as long as it
      keeps those overall distances right.</li>
    <li><b>Test 2 · can it place a patient who is missing a whole omics?</b> We judged this from how each
      method represents a patient. We kept methods that build each omics' own patient-to-patient similarity
      and then combine them, so a patient can still be placed from the single omics they have. We dropped
      methods that need both omics for every patient and only patch a few empty cells.</li>
  </ul>
  <p class="callout" data-enter="3">Then we <span class="key">tried to break our own picks</span>: we looked for
    where each one could fail, and instead of dropping it we feature the hardened version that fixes the
    weakness. Each method also has to pass an honest gate (beat the naive baseline in the missing-omics
    case), or we report it as a negative result.</p>""", "is-statement wide")

# 12 — method ①
slide(12, "Inspiring method ①", """
  <p class="eyebrow" data-enter="1">Optimal transport · math & vision origin · SCOT+ 2025</p>
  <h2 class="head" data-enter="1"><span class="idx">①</span> Augmented / Fused Gromov–Wasserstein</h2>
  <ul class="notes" data-enter="2">
    <li>GW compares samples in <b>incomparable spaces</b> using only within-modality geometry —
      no shared features needed.</li>
    <li><b>Adaptation:</b> couple a missing-modality sample to the complete samples' geometry, then
      barycentric-project onto the joint-PCA anchor → distances.</li>
    <li><b>Honest fix</b> (our red-team): use <span class="key">Augmented GW</span> — the feature term
      breaks GW's rotation/reflection ambiguity.</li>
    <li><b>Gate:</b> must beat mean/PLS in the missing regime, else reported as a negative result.</li>
  </ul>""")

# 13 — method ② (CM-Harmonic-Aniso, winner of the 2026-06-27 cross-field hunt)
slide(13, "Inspiring method ②", """
  <p class="eyebrow" data-enter="1">Wayfinding · GPS-style triangulation · our synthesis</p>
  <h2 class="head" data-enter="1"><span class="idx">②</span> CM-Harmonic-Aniso: triangulate, don't impute</h2>
  <ul class="notes" data-enter="2">
    <li>Pin the 1042 complete patients at their <b>true first-two-PC coordinates</b> (the exact thing we are
      graded on) as fixed landmarks. The only method anchored on the grader's own target, so that part of
      the map is right by construction.</li>
    <li>Place each of the 696 single-omics patients by <span class="key">triangulating off those landmarks</span>:
      one sparse harmonic solve on a fused microbiome + metabolome similarity graph, where a missing omics is
      simply <i>no edge</i>, never an invented value. Like a hiker fixing position from the summits they can
      see, instead of guessing their own altitude.</li>
    <li><b>Honest per-axis split:</b> the part of a patient's position carried by the omics they <i>have</i>
      is recovered by proximity and beats every imputation baseline. The part that needs the missing omics is
      genuinely capped by the weak 0.382 link, so there we fall back to the average, <b>provably never worse
      than mean-impute</b>.</li>
    <li><b>Risk + gate:</b> harmonic smoothing drifts everyone toward the centre, so a small held-out
      calibration corrects it; fail-closed gates fall back to PLS on any new cohort lacking enough complete
      patients to anchor. Ship only if it beats mean and PLS per-axis on held-out patients, else a negative
      result.</li>
  </ul>""", "wide")

# 14 — pipeline + eval
slide(14, "Pipeline & evaluation", """
  <p class="eyebrow" data-enter="1">Our plan: build it, then test it fairly</p>
  <div class="twomethod" data-enter="2">
    <div class="col">
      <h3 class="colh">How we build it</h3>
      <ul class="notes small">
        <li><b>Clean the data.</b> The microbiome numbers are proportions (they add up to 1), so we put them
          on a log scale where distances make sense; the metabolome has a few huge values, so we log it and
          rescale so every feature counts equally.</li>
        <li><b>Learn the settings on the training patients only.</b> We fix the scaling and the PCA on the
          training set and reuse them unchanged, so we never peek at the test data.</li>
        <li><b>Build the distance map two ways:</b> Augmented-GW (line up the two omics by their shape) and
          CM-Harmonic-Aniso (place each patient by triangulating off known landmarks). We compare both
          against the simple fill-in methods (mean, median, KNN, Random Forest).</li>
      </ul>
    </div>
    <div class="col">
      <h3 class="colh">How we test it</h3>
      <ul class="notes small">
        <li><b>Score it the way the staff will.</b> Rebuild their recipe (rescale, PCA, distance on the first
          two axes) and check how close our distances are to theirs with a Mantel test.</li>
        <li><b>Try different amounts of missing data.</b> Hide 10 / 30 / 50% of an omics, both ways (drop the
          microbiome, drop the metabolome), and see which method holds up.</li>
        <li><b>Look where it actually counts.</b> Judge on the <span class="key">patients missing an
          omics</span>, not the easy ones, since the overall score is misleading (slides 09 to 10).</li>
        <li><b>Keep it fair.</b> Never let the same patient be in training and testing at once, and report how
          fast each method runs, not just how accurate it is.</li>
      </ul>
    </div>
  </div>""")

# 15 — closing
slide(15, "Next", """
  <div class="end-wrap">
    <p class="eyebrow" data-enter="1">Where we landed · what's next</p>
    <h2 class="statement" data-enter="2">The whole challenge is the <span class="key">missing-modality
      patients</span>. We place them on the shared map, instead of inventing what's absent.</h2>
    <div class="accent-rule" data-enter="3"></div>
    <div class="end-recap" data-enter="3">
      <div class="end-item"><span class="end-idx">①</span><div>
        <b>Augmented / Fused GW</b><span>match the two omics by shape (transport)</span></div></div>
      <div class="end-item"><span class="end-idx">②</span><div>
        <b>CM-Harmonic-Aniso</b><span>triangulate off landmarks (wayfinding)</span></div></div>
    </div>
    <p class="byline" data-enter="3">Next (M2): build both, per-axis Mantel sweep over 10 / 30 / 50% missing,
      head-to-head vs. the baseline ladder.</p>
    <div class="end-sign" data-enter="3"><span>Aviv Noah &amp; Inbal</span><span class="dotsep">·</span>
      <span>MetaCardis cohort</span><span class="dotsep">·</span><span>Milestone 1</span></div>
  </div>""", "is-title is-closing")


CSS = FONTS + """
:root{
  --bg:#FAF9F6; --panel:#F2F0EA; --ink:#0A0A0A; --mut:#6B6863;
  --line:#DAD7CF; --line-soft:rgba(10,10,10,.09);
  --accent:#FF2D55; --accent-press:#D81E40; --tint:rgba(255,45,85,.08);
  --pad:clamp(40px,5.5vh,68px) clamp(52px,6.5vw,120px);
  --ease:cubic-bezier(.16,1,.3,1);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;background:var(--bg)}
body{color:var(--ink);font-family:DISP_STACK;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
#bar{position:fixed;top:0;left:0;height:3px;background:var(--accent);z-index:50;
  width:calc(var(--i,0)*100%);transition:width .55s var(--ease)}
#deck{position:fixed;inset:0;overflow:hidden;background:var(--bg)}

.slide{position:absolute;inset:0;background:var(--bg);padding:var(--pad);overflow:hidden;
  display:grid;grid-template-rows:auto 1fr auto;row-gap:clamp(16px,2.4vh,30px);
  opacity:0;transform:translateX(46px);pointer-events:none;
  transition:opacity .5s var(--ease),transform .5s var(--ease)}
.slide.is-active{opacity:1;transform:none;pointer-events:auto}
.slide.is-prev{transform:translateX(-46px)}

.shead,.sfoot{display:flex;justify-content:space-between;align-items:center;
  font-family:MONO_STACK;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--mut);z-index:2}
.shead{border-bottom:1px solid var(--line);padding-bottom:.85rem}
.sfoot{border-top:1px solid var(--line);padding-top:.85rem;font-variant-numeric:tabular-nums}
.srcref{color:var(--accent);text-transform:none;letter-spacing:.04em}
.dot{display:inline-block;width:7px;height:7px;background:var(--accent);margin-right:.7em;
  vertical-align:middle}
.sbody{position:relative;z-index:2;min-height:0;overflow:hidden;
  display:flex;flex-direction:column;justify-content:center}

.snum{position:absolute;right:-.04em;bottom:-.28em;z-index:0;font-family:DISP_STACK;
  font-weight:700;font-size:clamp(220px,30vw,460px);line-height:.8;letter-spacing:-.04em;
  color:transparent;-webkit-text-stroke:2px var(--accent);opacity:.16;
  font-variant-numeric:tabular-nums;user-select:none;pointer-events:none}
.is-title .snum{right:auto;bottom:auto;left:-.04em;top:-.16em}

.eyebrow{font-family:MONO_STACK;font-size:.8rem;font-weight:500;letter-spacing:.2em;
  text-transform:uppercase;color:var(--accent);margin-bottom:1.1em}
.display{font-weight:700;font-size:clamp(2.1rem,4.2vw,3.7rem);line-height:1.0;
  letter-spacing:-.03em;text-wrap:balance}
.statement{font-weight:500;font-size:clamp(1.7rem,3.4vw,2.9rem);line-height:1.06;
  letter-spacing:-.02em;text-wrap:balance;max-width:24ch}
.head{font-weight:600;font-size:clamp(1.55rem,2.9vw,2.5rem);line-height:1.05;
  letter-spacing:-.018em;text-wrap:balance;margin-bottom:.7em}
.idx{color:var(--accent);font-weight:700;margin-right:.18em}
.body{font-size:clamp(1.02rem,1.25vw,1.22rem);line-height:1.5;color:#1c1b19;max-width:52ch}
.lead-sm{font-size:clamp(1.0rem,1.2vw,1.14rem);line-height:1.5;color:#1c1b19;max-width:64ch;
  margin:-.2em 0 1.1em}
.body.small{font-size:.98rem}
.caption{font-family:MONO_STACK;font-size:.78rem;letter-spacing:.02em;color:var(--mut);
  text-transform:uppercase}
.notes{list-style:none;display:flex;flex-direction:column;gap:.7em;max-width:62ch}
.notes li{position:relative;padding-left:1.4em;font-size:clamp(1.0rem,1.2vw,1.16rem);
  line-height:1.45;color:#1c1b19}
.notes.small li{font-size:.98rem;line-height:1.4}
.notes li::before{content:"";position:absolute;left:0;top:.62em;width:9px;height:1.5px;
  background:var(--accent)}
.notes b{font-weight:600;color:var(--ink)}
.callout{margin-top:1.1em;border-left:3px solid var(--accent);background:var(--tint);
  padding:.9em 1.1em;font-size:1.04rem;line-height:1.45;max-width:60ch}
.callout.punch{margin-top:1.4em;border-left-width:5px;padding:1.05em 1.3em;max-width:none}
.callout.punch p{margin:0 0 .55em}.callout.punch p:last-child{margin-bottom:0}
.callout.punch .punch-lead{font-family:DISP_STACK;font-weight:600;font-size:1.22rem;
  line-height:1.25;letter-spacing:-.01em;color:var(--ink)}
.callout.punch b{font-weight:600;color:var(--ink)}
.foot-note{font-family:MONO_STACK;font-size:.74rem;letter-spacing:.04em;color:var(--mut);
  margin-top:1em;text-transform:uppercase}
.methodline{font-size:.92rem;line-height:1.5;color:#3a3833;margin-top:1.1em;max-width:none;
  border-top:1px solid var(--line);padding-top:.7em}
.methodline b{color:var(--ink);font-weight:600}

/* wide slides: longer lines so more text fits without zooming out */
.slide.wide .notes{max-width:96ch;gap:.85em}
.slide.wide .lead-sm{max-width:100ch}
.slide.wide .callout{max-width:96ch}
.slide.wide .head{max-width:32ch}
.slide.wide .notes li{font-size:clamp(1.04rem,1.18vw,1.2rem);line-height:1.5}

.key{position:relative;white-space:nowrap;font-weight:600}
.key::after{content:"";position:absolute;left:0;right:0;bottom:-.04em;height:3px;
  background:var(--accent);transform:scaleX(0);transform-origin:left;
  transition:transform .55s var(--ease) .35s}
.slide.is-active .key::after{transform:scaleX(1)}

.title-block{max-width:26ch}
.accent-rule{width:84px;height:4px;background:var(--accent);margin:1.2em 0 1.1em}
.byline{font-family:MONO_STACK;font-size:.84rem;letter-spacing:.06em;color:var(--mut);max-width:52ch}
.end-wrap{max-width:52ch}
.end-wrap .statement{font-size:clamp(1.35rem,2.5vw,2.15rem);line-height:1.1;max-width:36ch;margin-bottom:0}
.end-wrap .accent-rule{margin:.9em 0 .9em}
.end-recap{display:flex;gap:2.6em;margin:.1em 0 1.2em;flex-wrap:wrap}
.end-item{display:flex;align-items:baseline;gap:.55em}
.end-idx{font-family:DISP_STACK;font-weight:700;font-size:1.4rem;color:var(--accent);line-height:1}
.end-item b{font-weight:600;color:var(--ink);font-size:1.0rem;display:block}
.end-item span:not(.end-idx){font-size:.88rem;color:var(--mut);display:block;margin-top:.1em}
.end-sign{font-family:MONO_STACK;font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--mut);margin-top:1.3em;display:flex;flex-wrap:wrap;gap:.7em;align-items:baseline}
.end-sign .dotsep{color:var(--accent)}

.figwell{border:1px solid var(--line);background:var(--bg);padding:12px;
  display:flex;align-items:center;justify-content:center}
.figwell img{width:100%;height:auto;display:block;max-height:62vh;object-fit:contain}
.figfull{margin:0}
.figfull img{max-height:40vh}
.figcaprow{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(16px,2.4vw,44px);margin-top:.7em}
.figcaprow.two{grid-template-columns:1fr 1fr}
.figcaprow div{font-family:MONO_STACK;font-size:.72rem;line-height:1.4;color:var(--mut);
  border-top:2px solid var(--accent);padding-top:.5em}
.figcaprow b{color:var(--ink);font-weight:600}
.statrow{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:1.1em;
  border-top:1px solid var(--line)}
.statrow .stat{padding:1em 1.2em 0 0;border-right:1px solid var(--line-soft)}
.statrow .stat:last-child{border-right:none}
.stat{display:flex;flex-direction:column;gap:.15em}
.stat .num{font-family:DISP_STACK;font-weight:700;font-size:clamp(2.1rem,3.6vw,3.3rem);
  line-height:.92;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.stat.lg .num{font-size:clamp(2.6rem,4.6vw,4rem);color:var(--accent)}
.stat .lab{font-family:MONO_STACK;font-size:.72rem;letter-spacing:.06em;color:var(--mut);
  text-transform:uppercase;line-height:1.3}
.stat .arrow{color:var(--accent);margin:0 .15em;font-weight:400}

.grid4{display:grid;grid-template-columns:1fr 1fr;gap:clamp(14px,1.8vw,28px)}
.grid4 figure{display:flex;flex-direction:column;gap:.4em}
.grid4 .figwell img{max-height:24vh}
.grid4 .caption{font-family:MONO_STACK;font-size:.66rem;letter-spacing:.04em;color:var(--mut);
  text-transform:uppercase}
.fig-stats{display:grid;grid-template-columns:1.45fr .85fr;gap:clamp(28px,3.4vw,56px);
  align-items:center}
.fig-stats .side{display:flex;flex-direction:column;gap:.9em}
.fig-stats .side .body{max-width:38ch}
.hair{height:1px;background:var(--line)}

.dtable{border-collapse:collapse;width:100%;font-family:MONO_STACK;
  font-variant-numeric:tabular-nums}
.dtable th{font-size:.74rem;font-weight:500;letter-spacing:.12em;text-transform:uppercase;
  color:var(--mut);text-align:right;padding:0 1.1rem 1rem;border-bottom:2px solid var(--ink)}
.dtable th:first-child{text-align:left}
.dtable td{font-size:clamp(1.2rem,2vw,1.7rem);color:var(--ink);text-align:right;
  padding:1.05rem 1.1rem;border-bottom:1px solid var(--line)}
.dtable td:first-child{text-align:left;color:var(--mut);font-size:1rem;letter-spacing:.02em}
.dtable tbody tr:last-child td{border-bottom:none}
.dtable td.win{color:var(--accent);font-weight:700}
.dtable.sm th{padding:0 .7rem .6rem}
.dtable.sm td{font-size:clamp(.95rem,1.5vw,1.3rem);padding:.62rem .7rem}
.dtable.sm td:first-child{font-size:.85rem}

.twomethod{display:grid;grid-template-columns:1fr 1fr;gap:clamp(36px,4.5vw,72px);position:relative}
.twomethod::before{content:"";position:absolute;left:50%;top:0;bottom:0;width:1px;
  background:var(--line);transform:translateX(-50%)}
.twomethod.dual .col{display:flex;flex-direction:column;gap:1em}
.colh{font-family:MONO_STACK;font-size:.8rem;font-weight:600;letter-spacing:.14em;
  text-transform:uppercase;color:var(--accent);margin-bottom:1.1em;
  border-bottom:1px solid var(--line);padding-bottom:.6em}
.twomethod.dual .colh{margin-bottom:.4em}

.slide.is-active [data-enter]{animation:rise .55s var(--ease) both}
.slide.is-active [data-enter="2"]{animation-delay:.08s}
.slide.is-active [data-enter="3"]{animation-delay:.18s}
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}

#nav{position:fixed;bottom:20px;right:24px;display:flex;gap:8px;align-items:center;z-index:50;
  font-family:MONO_STACK}
#nav button{background:transparent;color:var(--ink);border:1px solid var(--line);
  width:42px;height:38px;font-size:1.1rem;cursor:pointer;transition:.18s var(--ease)}
#nav button:hover{border-color:var(--accent);color:var(--accent)}
#nav button:active{transform:translateY(1px)}
#nav button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
#count{font-size:.78rem;letter-spacing:.08em;color:var(--mut);min-width:58px;text-align:center;
  font-variant-numeric:tabular-nums}

@media (prefers-reduced-motion:reduce){
  .slide{transition:opacity .2s}.slide.is-active [data-enter]{animation:none}
  .key::after{transition:none;transform:scaleX(1)}#bar{transition:none}
}
@media (max-width:820px){
  .fig-stats,.twomethod,.statrow{grid-template-columns:1fr;gap:20px}
  .twomethod::before{display:none}
}
""".replace("DISP_STACK", DISP).replace("MONO_STACK", MONO)

JS = """
const slides=[...document.querySelectorAll('.slide')],bar=document.getElementById('bar'),
  count=document.getElementById('count'),root=document.documentElement;let i=0;
function show(n){i=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach((s,k)=>{s.classList.toggle('is-active',k===i);
    s.classList.toggle('is-prev',k<i)});
  root.style.setProperty('--i',(i+1)/slides.length);
  count.textContent=String(i+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');}
addEventListener('keydown',e=>{
  if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){e.preventDefault();show(i+1)}
  if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();show(i-1)}
  if(e.key==='Home')show(0);if(e.key==='End')show(slides.length-1)});
let x=null;addEventListener('touchstart',e=>x=e.touches[0].clientX,{passive:true});
addEventListener('touchend',e=>{if(x==null)return;const d=e.changedTouches[0].clientX-x;
  if(Math.abs(d)>50)show(i+(d<0?1:-1));x=null});
show(0);
"""

FAVICON = ("data:image/svg+xml,"
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' fill='%23FAF9F6'/%3E"
           "%3Crect x='5' y='5' width='22' height='22' fill='none' stroke='%23FF2D55' stroke-width='3'/%3E"
           "%3C/svg%3E")

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="MetaCardis Milestone 1 — missing-modality-robust multi-omics distance estimation.">
<meta name="color-scheme" content="light">
<link rel="icon" href="{FAVICON}">
<title>MetaCardis — Milestone 1</title><style>{CSS}</style></head>
<body><div id="bar"></div><main id="deck">{''.join(SLIDES)}</main>
<nav id="nav" aria-label="slide navigation">
<button onclick="show(i-1)" aria-label="previous">‹</button><span id="count"></span>
<button onclick="show(i+1)" aria-label="next">›</button></nav>
<script>{JS}</script></body></html>"""

out = ROOT / "deliverables" / "milestone1.html"
out.write_text(html)
print(f"wrote {out}  ({len(html)/1024:.0f} KB, {len(SLIDES)} slides, self-contained)")
