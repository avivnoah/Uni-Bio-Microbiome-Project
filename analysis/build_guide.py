"""Build deliverables/milestone1_guide.html — the presenter's companion / study guide.

A long-form, plain-English reference that sits behind the slide deck: project
primer, findings + the reasoning, naive baseline, the two methods explained
simply, pipeline/eval, a slide-by-slide cheat sheet, a Q&A bank, a glossary, and
a file map + how-to-run. Self-contained HTML (fonts embedded), sticky TOC,
print-friendly, matching the deck's paper/ink/rose design.
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "analysis" / "assets" / "fonts"
_ALL = {}
for _p in sorted((ROOT / "analysis" / "findings").glob("*.json")):
    _ALL.update(json.loads(_p.read_text()))
F = PF = _ALL

ms, gc = F["modality_structure"], F["group_counts"]
pcoa, pg, pc = F["pcoa_explained"], F["permanova_group"], F["permanova_center"]
dp, b = F["disease_pred_balacc"], F["naive_distance_baseline"]
fi, md_acc = PF["metadata_feature_importance"], PF["metadata_only_cv_balacc"]
pn = PF["partner_naive_imputation_r2"]
max_sp = max(PF["diff_species_per_group"].values())
max_mb = max(PF["diff_metab_per_group"].values())


def ff(path, fam):
    p = Path(path)
    if not p.exists():
        p = Path("/tmp") / Path(path).name
    if not p.exists():
        return ""
    d = base64.b64encode(p.read_bytes()).decode()
    return (f"@font-face{{font-family:'{fam}';font-weight:100 800;font-style:normal;"
            f"font-display:swap;src:url(data:font/woff2;base64,{d}) format('woff2')}}")


FONTS = (ff(FONTS_DIR / "geist.woff2", "Geist") + ff(FONTS_DIR / "sg.woff2", "SpaceG")
         + ff(FONTS_DIR / "jb.woff2", "JBMono"))
BODY = "Geist, system-ui, sans-serif" if "Geist" in FONTS else "system-ui, sans-serif"
DISP = "SpaceG, Geist, sans-serif" if "SpaceG" in FONTS else "system-ui, sans-serif"
MONO = "JBMono, ui-monospace, Menlo, monospace" if "JBMono" in FONTS else "monospace"

SECTIONS = []  # (id, toc_label, html)


def sec(sid, label, num, title, body):
    SECTIONS.append((sid, label, f"""
      <section id="{sid}" class="sec">
        <p class="kick">{num}</p><h2>{title}</h2>{body}
      </section>"""))


def k(t):
    return f'<span class="key">{t}</span>'


def callout(html, label="why it matters"):
    return f'<aside class="callout"><span class="cl-label">{label}</span>{html}</aside>'


def qa(q, a):
    return f'<div class="qa"><p class="q">{q}</p><p class="a">{a}</p></div>'


def gloss(term, d):
    return f'<div class="gl"><dt>{term}</dt><dd>{d}</dd></div>'


FIGDIR = ROOT / "analysis" / "figures"


def figg(name, cap):
    d = base64.b64encode((FIGDIR / name).read_bytes()).decode()
    return (f'<figure class="fig"><img alt="{cap}" src="data:image/png;base64,{d}">'
            f'<figcaption>{cap}</figcaption></figure>')


# ============================ CONTENT ============================
sec("tldr", "The 60-second version", "00", "The 60-second version", f"""
  <p class="lead">We are not classifying disease. We are building a <b>distance matrix</b>: a table of
  how (dis)similar every pair of subjects is, from their gut microbiome + blood metabolome
  combined — and it has to stay accurate even when a subject is <b>missing one whole omics
  modality</b>.</p>
  <ul class="bul">
    <li>The grader scores us with a <b>Mantel test</b> against their own distance matrix
      (standardise every feature → PCA → distance in the first 2 components). So the "true"
      geometry is <b>linear</b>.</li>
    <li>In our 1738 subjects, <b>{ms['microbiome_only']+ms['metabolome_only']}</b> already miss a
      whole modality ({ms['microbiome_only']} microbiome-only, {ms['metabolome_only']}
      metabolome-only, {ms['complete_both']} complete). The challenge is real, not hypothetical.</li>
    <li>Microbiome ↔ metabolome are only <b>weakly</b> linked (max correlation
      {F['max_abs_taxa_metab_corr']}), so you cannot just predict the missing modality well. That weak
      link is the whole difficulty.</li>
    <li>For milestone 1 we deliver: <b>data exploration</b>, a <b>naive baseline</b> (mandatory), and
      a <b>plan</b> built around two cutting-edge 2025 methods.</li>
  </ul>
  {callout("If you remember one sentence: <b>the easy part is recovering scattered missing cells "
           "within a modality; the hard part — and the real task — is placing a subject who is "
           "missing an entire modality, which is capped by how well the two omics predict each "
           "other.</b>", "the one idea")}""")

sec("project", "What the project is", "01", "What the project actually is (plain English)", f"""
  <p>Each subject in the MetaCardis cohort has two molecular "fingerprints":</p>
  <ul class="bul">
    <li><b>Microbiome</b> — which gut bacteria they carry and in what proportions (170 species).</li>
    <li><b>Metabolome</b> — small molecules measured in their blood (104 metabolites).</li>
  </ul>
  <p>The course's final goal is a pipeline that takes these and outputs an
  <b>n×n distance matrix</b> — for every pair of subjects, a number saying how different they are.
  Think of it as a similarity map of all patients built from both omics at once.</p>
  <p><b>Why distances and not disease prediction?</b> Two reasons. First, that is literally what the
  grader asks for and scores. Second (we show this in the data) the omics predict the disease
  <i>label</i> poorly — the useful structure lives in how samples relate to each other, not in a
  clean class boundary. {k("Distances, not labels, are the target.")}</p>
  <p><b>How are we graded?</b> The instructors build a reference distance matrix like this: take every
  feature of both omics, put them on the same scale (standardise), run <b>PCA</b> (find the 2 main
  axes of variation), and measure ordinary distance between samples in those 2 axes. Then they
  compare our matrix to theirs with a <b>Mantel test</b> (a correlation between two distance
  matrices). Higher correlation = better.</p>
  <p><b>The twist that makes it hard.</b> Some subjects are missing an entire modality. With both
  modalities present, reproducing the grader's matrix is trivial (just do what they do). So the
  real work is: given only one modality for a subject, place them correctly in the joint picture.</p>
  {callout("Because the grader's target is a <b>linear</b> PCA geometry, fancy non-linear methods can "
           "actually score <i>worse</i> (they bend the space away from the linear target). This single "
           "fact drove every method choice we made.")}""")

sec("data", "The data", "02", "The data we were given", f"""
  <p>Three aligned tables in <code>data/train/</code>, 1738 subjects each:</p>
  <table class="tbl">
    <thead><tr><th>file</th><th>what</th><th>notes</th></tr></thead>
    <tbody>
      <tr><td>microbiome.csv</td><td>170 species, relative abundance</td>
        <td>compositional (rows sum to 1) → we <b>CLR-transform</b></td></tr>
      <tr><td>metabolome.csv</td><td>104 serum metabolites</td>
        <td>heavy-tailed positive → <b>log + standardise</b></td></tr>
      <tr><td>metadata.csv</td><td>group, gender, BMI, age, center</td>
        <td>9 disease groups; some demographics missing</td></tr>
    </tbody>
  </table>
  <p><b>The missing-modality structure (the headline data fact):</b></p>
  <ul class="bul">
    <li><b>{ms['complete_both']}</b> subjects have both omics</li>
    <li><b>{ms['microbiome_only']}</b> have microbiome only (metabolome all-NaN)</li>
    <li><b>{ms['metabolome_only']}</b> have metabolome only (microbiome all-NaN)</li>
  </ul>
  <p>So ~40% miss a whole modality, and the two missing sets don't overlap. The tables look complete
  (every SampleID appears) but the values are blank — easy to miss if you only check the first rows.</p>
  <p><b>Disease groups (PATGROUPFINAL_C):</b> 1 = metabolic syndrome, 2a/2b = obesity, 3 = type-2
  diabetes (T2D, biggest, n={gc['3']}), 4/5/6 = coronary-artery-disease stages, 7 = heart failure
  (smallest, n={gc['7']}), 8 = healthy control. Heavily imbalanced.</p>
  {callout("Two <i>different</i> kinds of missingness, handled differently: (1) whole omics modality "
           "missing for ~40% — the project's core; (2) demographics (BMI/age/gender) missing for "
           "~27%, which is <b>100% of Denmark</b> by privacy law (a structured, non-random gap).")}""")

# findings
def baseline_table():
    rows = ""
    for frac in (10, 30, 50):
        d = b[f"drop_metab_{frac}pct"]
        m, med, kk, rf = d["mean"]["mantel_r"], d["median"]["mantel_r"], d["knn"]["mantel_r"], d["rf"]["mantel_r"]
        best = max(m, med, kk, rf)
        c = lambda v: f'<td class="win">{v}</td>' if v == best else f"<td>{v}</td>"
        rows += f"<tr><td>{frac}%</td>{c(m)}{c(med)}{c(kk)}{c(rf)}</tr>"
    return rows


def r2_table():
    rows = ""
    for rate in ("10%", "20%", "40%", "60%"):
        d = pn[rate]; m, med, kk, rf = d["mean"], d["median"], d["knn"], d["rf"]
        best = max(m, med, kk, rf)
        c = lambda v: f'<td class="win">{v}</td>' if v == best else f"<td>{v}</td>"
        rows += f"<tr><td>{rate}</td>{c(m)}{c(med)}{c(kk)}{c(rf)}</tr>"
    return rows


dww = PF["disease_with_without"]


sec("findings", "What we found & why", "03", "What the exploration found — and why each matters", f"""
  <p>Each result below is "<b>what we saw → why it matters for the pipeline</b>".</p>

  <h3>Class imbalance</h3>
  {figg('01_overview.png','Disease-group distribution · omics availability · metadata missingness')}
  <p>Groups range from T2D n={gc['3']} down to heart-failure n={gc['7']}.</p>
  {callout("Big groups dominate any statistic or model; the tiny group (7) is nearly invisible. We "
           "must use balanced metrics and not let group 3 drown everything.")}

  <h3>Demographics differ sharply between groups (confounders)</h3>
  {figg('10_age_bmi_by_group.png','Age and BMI by disease group')}
  {figg('13_gender_by_group.png','Gender composition by disease group')}
  <p>Obesity groups 2a/2b are youngest with BMI &gt; 40; diabetes/CVD groups 3–6 are older (~60).</p>
  {callout("Age and BMI track disease, and both are known to shift the microbiome and metabolome. So "
           "a difference we attribute to 'disease' might really be age/BMI. They are confounders.")}

  <h3>Recruitment center is a strong confounder (batch effect)</h3>
  {figg('12_country_by_group.png','Patient-group composition by recruitment center')}
  {figg('02_missing_by_center.png','Metadata missing fraction by center (Denmark = MNAR)')}
  <p><b>What is CENTER?</b> MetaCardis enrolled patients at clinical sites in three countries —
  <b>Denmark, France, Germany</b> (the <code>CENTER_C</code> column). "Recruitment center" = the
  site/country where a subject was signed up and sampled. It describes <i>where and how</i> the
  sample was collected, not a biological trait — but diet, lifestyle, sample handling and sequencing
  all differ by country, so it leaves a systematic fingerprint in the data (a {k("batch effect")}).</p>
  <p>Groups are country-skewed (2b≈German, 7≈French, 4 has no Germany). On a PERMANOVA test, the
  effect of <b>CENTER (F={pc['F']}) is larger than disease group (F={pg['F']})</b>.</p>
  {callout("Geography/diet/lab differ by country and structure the microbiome more than disease does. "
           "But note: the grader's own ground truth keeps the center effect, so blindly removing it "
           "could <i>hurt</i> our Mantel score. We flag it rather than auto-correct it.")}

  <h3>Demographics out-predict the omics for the disease label</h3>
  {figg('14_feature_importance.png','Metadata-only disease prediction: feature importance')}
  <p><b>Exactly what we did (a side-check, not our pipeline).</b> We trained a {k("Random Forest")} to name
  a patient's <b>disease group — one of the 9 groups</b> in <code>PATGROUPFINAL_C</code> — from a set of
  features, and measured it with <b>5-fold cross-validation</b> (train on 4/5 of patients, test on the
  held-out 1/5, rotate so every patient is tested once). The score is {k("balanced accuracy")}: the hit
  rate averaged per group so the big groups don't dominate. Blind guessing across 9 equal groups is about
  <b>0.11</b>. We ran the same model three times with different inputs:</p>
  <ul class="bul">
    <li><b>Metadata only</b> (BMI, age, gender, country): balanced accuracy <b>{md_acc}</b>, on the patients
      who have all three demographics — this drops Denmark, who share none. The importance bars show
      <b>BMI ({fi['BMI_C']}) and age ({fi['AGE']})</b> do almost all the work.</li>
    <li><b>Both omics</b> (microbiome + metabolome together): <b>{dp['both_omics_complete']}</b>, on the
      {ms['complete_both']} patients who have both.</li>
    <li><b>Microbiome only</b>: <b>{dp['microbiome_only_all']}</b>, on every patient who has a microbiome.</li>
  </ul>
  <p>So <b>demographics beat both omics, which beat microbiome alone</b>. One honest caveat: the three runs
  use different patient subsets and different features, so this is a rough ordering, not a perfectly
  controlled head-to-head — but the takeaway holds either way.</p>
  {callout("The omics carry only weak, distributed disease signal (barely above chance, and below plain "
           "demographics). This is strong evidence that the right target is the <b>distance geometry</b>, "
           "not a disease classifier.")}

  <h3>Microbiome geometry shows only partial separation</h3>
  {figg('04_microbiome_pcoa.png','Microbiome PCoA (Aitchison) by disease group and by center')}
  {figg('06_between_group_distance.png','Average microbiome (Aitchison) distance between disease groups')}
  {figg('03_alpha_diversity.png','Shannon alpha-diversity by disease group')}
  <p><b>What PCoA is.</b> We have a distance between every pair of subjects' microbiomes — a 1738×1738
  table, impossible to eyeball. PCoA (principal coordinates analysis) compresses it into a simple 2-D
  scatter plot: each subject is one dot, and dots that sit close together = similar microbiomes. It
  keeps the biggest patterns and throws away fine detail so we can actually look at the data.</p>
  <p><b>First, "variation" and "direction".</b> Picture every subject as a point in a 170-dimensional
  space — one axis per bacterial species, the point's position = how much of each species they carry.
  <b>Variation</b> just means how spread out these points are: some species differ a lot from person to
  person, others barely. A <b>direction</b> is a straight line (a vector) through that cloud of points —
  a particular mix of species — along which we can read off where each subject sits. We hunt for the
  directions with the most spread because they carry the most information about what makes subjects
  different; a handful of them summarise the 170-D cloud well enough to draw in 2-D.</p>
  <p><b>PC1, PC2 and the percentages.</b> PC1 (horizontal axis) is the single direction that captures
  the <i>most</i> variation across subjects; PC2 (vertical axis) is the next-most. "PC1 = {pcoa[0]:.0%}"
  means that one axis accounts for {pcoa[0]:.0%} of all the variation in the data, and PC2 another
  {pcoa[1]:.0%} — together about {pcoa[0]+pcoa[1]:.0%}. The remaining ~{1-pcoa[0]-pcoa[1]:.0%} is
  spread thinly over many smaller directions we don't draw. Higher percentages = the 2-D picture is
  more faithful to the real high-dimensional data.</p>
  <p><b>How we know the groups overlap.</b> We colour each dot by disease group. If a disease had a
  distinctive microbiome, its colour would form a separate cluster; instead all colours are mixed
  together across the plot — so the microbiome <i>alone</i> does not cleanly separate the diseases.</p>
  <p><b>So what does "partial separation" mean?</b> Not zero, not clean. The groups aren't randomly
  jumbled (there <i>is</i> some structure — e.g. the obesity groups drift toward one side), but they
  also don't form tidy, separate islands. They mostly sit on top of each other with only a gentle
  shift between them. "Partial" = a weak, blurry tendency rather than a clear split.</p>
  <p><b>One honest caveat on the country view.</b> Colouring the same dots by country looks tidier — but
  that is partly because three colours always look cleaner than nine, not proof that country separates
  better. So we do not judge "country vs disease" by eye here; the fair test is the degrees-of-freedom
  adjusted PERMANOVA above (country F={pc['F']} &gt; disease F={pg['F']}), which already accounts for the
  number of groups. On the slide deck we therefore show only the disease-coloured map and leave the
  country comparison to that statistic.</p>
  <p><b>Why this matters for the pipeline.</b> No clean disease clusters means a classifier is the wrong
  tool; the patients sit on a continuous, high-dimensional cloud, so the right object to model is the
  <i>distance</i> between them. And because PC1+PC2 capture only ~{int(round((pcoa[0]+pcoa[1])*100))}% of
  the differences, any 2-D summary is lossy: the real geometry lives in many directions at once.</p>
  <h3>How we actually made these three charts</h3>
  <p>All three start from the microbiome table (170 species per subject) and the plain steps we ran:</p>
  <ol class="bul">
    <li><b>CLR-transform the species table</b> (the compositional fix from the pipeline section): add a
      tiny pseudocount, take logs, subtract each subject's mean log. Now ordinary distance is meaningful.</li>
    <li><b>Compute the distance between every pair of subjects</b> = straight-line (Euclidean) distance
      on those CLR values. On compositional data this is called <span class="key">Aitchison distance</span>.
      That gives one big 1390×1390 table of "how different is subject i from subject j".</li>
    <li><b>PCoA chart (04):</b> feed that distance table into <code>PCoA</code> (principal coordinates
      analysis) — it finds 2 coordinates per subject that best preserve those distances — and scatter the
      subjects, coloured once by disease group and once by center. (Mechanically: double-centre the
      squared-distance table, take its top 2 eigenvectors. We coded this by hand in <code>analysis/eda.py</code>.)</li>
    <li><b>Between-group distance heatmap (06):</b> using the same pairwise distances, average them
      <i>across</i> each pair of groups (e.g. mean distance of every group-2b subject to every control)
      → an 9×9 table → heatmap. Bright cells = groups whose microbiomes are most different on average.</li>
    <li><b>Shannon-diversity boxplot (03):</b> a separate, per-subject number — how even/rich their
      bacteria are, <code>H = −Σ p·ln p</code> over the species proportions — then a box per disease group.</li>
  </ol>
  <p><b>Reading the between-group matrix — why the diagonal isn't 0.</b> A cell is the <i>average</i>
  distance between two <i>groups of people</i>, not between a subject and itself. The "1 vs 1" cell
  (~35.9) averages the distances between <span class="key">different</span> members of group 1 — and
  two different people's microbiomes are genuinely far apart, so the average is large. A subject vs
  <i>itself</i> would be 0, but that never enters a group-vs-group average. So the diagonal measures the
  <i>spread within</i> a group; off-diagonal measures distance <i>between</i> groups. A group is
  "tight/distinctive" only when its diagonal is small and its off-diagonals are large.</p>
  <p><b>And why ~35, not 0–1?</b> Aitchison distance lives in 170-dimensional CLR space, so the raw
  numbers are just large magnitudes — there's no fixed scale. Only <i>relative</i> values matter: a
  35.9 vs a 39 tells you which pair of groups is more different, not an absolute "amount".</p>
  <p><b>Reading the Shannon-diversity boxplot (the ~1.5–4.5 numbers).</b> Shannon (H) is one number per
  subject for <i>how diverse</i> their gut community is — it rewards both <i>how many</i> species are
  present and <i>how evenly</i> they're spread. <code>H = 0</code> means one species totally dominates;
  bigger H means more species sharing the space more evenly. A handy reading: <code>e^H</code> ≈ the
  "effective number of species" — so H≈3.7 ≈ ~40 species effectively carrying the community. Each box
  shows the spread of H across the subjects in one disease group (line = median, box = middle 50%, dots
  = outliers). Here the boxes sit around 3.5–4 and <span class="key">look similar across groups</span> —
  so overall diversity barely differs by disease; the disease signal is in <i>which</i> species, not in
  how many.</p>
  {callout("No single modality cleanly separates disease — signal is spread across modalities, which "
           "is exactly why combining them into a distance is worthwhile.")}

  <h3>Both omics carry signal, at different scales</h3>
  {figg('15_diff_per_group.png','Significant species & metabolites vs control per group (FDR<0.05)')}
  {figg('07_diff_abundance.png','Top differentially abundant species: T2D vs control')}
  {figg('08_metabolome_trends.png','Most group-variable metabolites (z-scored) — elevated/reduced by group')}
  <p><b>"Vs. controls" = compared to the healthy group</b> (group 8). For each disease group we check,
  one feature at a time, whether its level is systematically different in patients than in healthy
  people. "Differ" means a <i>statistically significant</i> difference in that species' abundance (or
  that metabolite's level) between the group and the controls.</p>
  <p><b>What FDR is.</b> We run thousands of these tests (170 species × many groups, plus 104
  metabolites), so some will look "significant" by pure chance. The <b>false discovery rate (FDR)</b>
  correction guards against that: "FDR &lt; 0.05" keeps only features where we expect at most ~5% to be
  false alarms. Counting the survivors: up to <b>{max_sp} species</b> and <b>{max_mb} metabolites</b>
  differ from healthy in the most-affected groups.</p>
  <p><b>"Metabolite shifts are broad"</b> = many metabolites move (some up, some down vs. control) in
  almost every disease group — the blood-metabolite signal is widespread, not confined to one disease.</p>
  {callout("There is real biology to capture — the task is representing it as robust distances, not "
           "proving the differences exist.")}

  <h3>Cross-omics coupling is weak (the ceiling)</h3>
  {figg('09_cross_omics_corr.png','Spearman correlation: top-variance taxa vs metabolites')}
  <p><b>What the correlation measures.</b> Take one bacterial species and one metabolite. Look across
  all subjects: when that bacterium is more abundant, does that metabolite tend to be higher (or lower)?
  A <b>Spearman correlation (ρ)</b> scores that link on a −1 to +1 scale — 0 = no relationship, +1 =
  move perfectly together, −1 = perfectly opposite. We compute ρ for <i>every</i> species×metabolite
  pair (170 × 104 pairs) and look at the strongest ones.</p>
  <p><b>What we found.</b> Even the single strongest pair reaches only
  <b>{F['max_abs_taxa_metab_corr']}</b>, and the top pairs sit below ρ = 0.25 — weak links. Both
  partners computed this separately and got the same picture. In plain terms: knowing a subject's
  microbiome tells you very little about their metabolome, and vice versa.</p>
  {callout("This is the <b>ceiling</b>. When a whole modality is missing, you cannot accurately rebuild "
           "it from the other one — there isn't enough shared signal. Every method, ours included, is "
           "capped by this, which is why brute-force imputation can't win. Recognising this ceiling is "
           "the key insight of the project.")}""")

sec("baseline", "The naive baseline", "04", "The mandatory naive baseline", f"""
  <p>The brief is explicit: <i>"impute the missing data (KNN, Random Forest, mean/median) and then
  compute distances."</i> And the missingness is whole-modality — a person is missing their <i>entire</i>
  metabolome or microbiome (our data: 348 + 348 such people). So the benchmark below mirrors exactly
  that: drop a whole modality, recover it, recompute the distances, and see how close we land.</p>

  <p><b>What "naive baseline" means.</b> The simplest, dumbest ways to fill in missing data — no clever
  modelling. They set the <i>floor</i>: whatever sophisticated pipeline we build later must beat these,
  or it isn't worth the extra complexity. "Naive" = a sanity benchmark, not the goal.</p>
  <ul class="bul">
    <li><b>Mean</b> — fill a missing value with the <i>average</i> of that feature across all subjects
      who have it. One number for everyone; ignores who the subject is.</li>
    <li><b>Median</b> — fill with the <i>middle</i> value instead of the average. More robust when a
      feature is skewed or has outliers (a few huge values won't drag it).</li>
    <li><b>KNN (k-nearest neighbours)</b> — find the <i>k most similar subjects</i> (by the data they do
      share) and fill the gap with their average. Borrows from "people like you" instead of the whole
      population — so it can use within-sample structure.</li>
    <li><b>Random Forest</b> — train a model (many decision trees voting together) to <i>predict</i> the
      missing feature from the other features. The most flexible of the four; can capture non-linear
      patterns, but needs a real learnable signal or it overfits.</li>
  </ul>
  {callout("Applied <b>cross-modally</b> here: when a whole modality is gone there's nothing within it to "
           "borrow, so mean/median fill from the population, while KNN and Random Forest <i>predict</i> the "
           "missing modality from the one the subject still has.", "how they're used here")}

  <h3>The benchmark, step by step</h3>
  <ol class="bul">
    <li>Take the complete subjects. For a fraction (10 / 30 / 50%), throw away their <b>whole</b>
      metabolome — every metabolite, the way the real data is missing.</li>
    <li>Recover that missing metabolome four ways — <b>mean</b>, <b>median</b> (population fill),
      <b>KNN</b> and <b>Random Forest</b> (guess it from the microbiome the subject still has).</li>
    <li>Glue microbiome + recovered metabolome together and run the grader's exact recipe: standardise →
      PCA → <b>Euclidean distance in the first 2 PCs</b>, giving an <b>n×n</b> matrix (one row and column
      per subject, entry = how far apart that pair is).</li>
    <li>Compare our n×n matrix to the full-data one with a <b>Mantel test</b> = the rank (Spearman)
      correlation between the two matrices, taken over <i>every</i> subject pair (1.0 = identical).</li>
  </ol>
  <p><b>How to read the table:</b> row = fraction whose whole metabolome was dropped; column = recovery
  method; number = the Mantel score (how close our distances are to the truth).</p>
  <table class="tbl mono"><thead><tr><th>dropped</th><th>mean</th><th>median</th><th>KNN</th><th>RF</th></tr></thead>
    <tbody>{baseline_table()}</tbody></table>
  <p><b>Takeaway: all four tie</b>, and even a plain mean already clears ~0.77 at 50% missing. Why: once
  the whole metabolome is gone, the only way to rebuild it is from the microbiome — and the two are
  weakly linked (correlation ≤ {F['max_abs_taxa_metab_corr']}). So KNN/RF guessing adds almost nothing
  over a trivial mean. The microbiome you still have already places people fairly well, which is why the
  scores stay high.</p>
  {callout("The lesson: naïve imputation can't beat a trivial mean here, because rebuilding a whole "
           "missing modality is capped by weak cross-modal signal. That ceiling — not coding effort — is "
           "the wall our real pipeline (OT / CM-Harmonic-Aniso) has to break.", "the lesson")}

  <h3>Does imputing the missing modality help predict disease?</h3>
  <p>The brief asks this directly. We test it on the complete subjects by classifying disease group
  (Random Forest, balanced accuracy; chance ≈ 0.11) three ways:</p>
  <table class="tbl mono"><thead><tr><th>setting</th><th>bal. acc</th></tr></thead><tbody>
    <tr><td>without imputation — microbiome only</td><td>{dww['without_imputation_microbiome_only']}</td></tr>
    <tr><td>with imputation — microbiome + recovered metabolome</td><td>{dww['with_imputation_micro_plus_recovered_metab']}</td></tr>
    <tr><td class="win">real both omics (upper bound)</td><td class="win">{dww['real_both_omics_upper_bound']}</td></tr>
  </tbody></table>
  <p><b>Imputation does not help.</b> Adding a metabolome <i>recovered from the microbiome</i> gives
  {dww['with_imputation_micro_plus_recovered_metab']} — essentially the same as microbiome alone
  ({dww['without_imputation_microbiome_only']}), and well below having the <i>real</i> metabolome
  ({dww['real_both_omics_upper_bound']}). Because the two omics are weakly linked, a guessed metabolome
  carries almost no new disease signal — only the genuine measurement does.</p>
  <p class="note">Note for honesty: an earlier draft of this benchmark reported R² value-recovery
  numbers, but those mixed targets (some methods imputed microbiome, one predicted metabolome) and
  scales, so the ranking wasn't comparable. We replaced it with the single spec-aligned benchmark above
  (drop a whole modality → recover → compute distances), which matches the project's real missingness
  and the grader's metric. We also sanity-checked recovering scattered <i>within-modality</i> cells
  (KNN/RF do well there) — but that isn't the project's situation, so it's not the benchmark.</p>""")

sec("methods", "The two methods", "05", "The two inspiring methods (explained simply)", f"""
  <p>We scouted many fields, including ones well outside biology (spatial navigation, GPS positioning,
  topology, physics, optimal transport), and ran an adversarial review that killed our flashiest ideas
  honestly. Most exotic ideas turned out to secretly rebuild the missing modality, so they hit the same
  weak-coupling ceiling as plain imputation. The two we feature survive that scrutiny: one matches the two
  omics by their shape, the other places people by triangulating off known landmarks.</p>

  <h3>① Augmented / Fused Gromov–Wasserstein (Optimal Transport)</h3>
  <p><b>Plain idea:</b> imagine two maps of the same cities but with no shared landmarks — one shows
  road distances, the other flight distances. Optimal transport / Gromov–Wasserstein (GW) matches
  the two maps using only the <i>internal</i> distance patterns, no shared reference needed. Here the
  "two maps" are the microbiome geometry and the metabolome geometry.</p>
  <p><b>How we'd use it:</b> for a subject missing a modality, match their within-modality distances to
  the complete subjects, then place them in the joint PCA picture (a weighted average of where their
  matches sit — "barycentric projection").</p>
  <p><b>The honest catch:</b> plain GW can place a point at a mirror-flipped location (it's blind to
  rotations/reflections). The fix is {k("Augmented GW")}, which adds feature information to break that
  ambiguity. We only keep it if it beats the mean/PLS baseline.</p>
  <p class="src">Origin: pure math + computer vision · SCOT+ (Bioinformatics Advances, 2025).</p>

  <h3>② CM-Harmonic-Aniso (wayfinding by triangulation)</h3>
  <p><b>Plain idea:</b> the grader builds its answer-key map from the 1042 people who have both omics, so we
  already know exactly where those people belong. Pin them down as fixed landmarks. Then place each person
  missing an omics by <b>triangulating off those landmarks</b> through a similarity graph, the way a hiker
  with no GPS fixes their position from the summits they can see — never by guessing their own altitude.</p>
  <p><b>Why it fits:</b> it aims straight at the grader's own target map instead of building a separate map
  and hoping it lines up. A missing omics is just <i>no link</i> in the graph, so we never invent fake
  values for it.</p>
  <p><b>The honest catch:</b> the part of a person's position that needs the omics they are missing is still
  capped by the weak cross-modal link, so there we fall back to the average (provably no worse than
  mean-imputation). The win is on the part carried by the omics they <i>do</i> have.</p>
  <p class="src">Origin: spatial navigation / GPS trilateration + graph signal processing · our synthesis,
  hardened in a 2026 cross-field method hunt.</p>

  <h3>How the two methods actually work (and how they relate)</h3>
  <p>First, the shared idea. Each subject has been measured two ways: their <b>microbiome</b> (gut
  bacteria) and their <b>metabolome</b> (blood chemicals). For some people we only have <i>one</i> of
  the two. Both methods below fill that gap so we can still say how far apart any two people are.</p>
  <p><b>1. AGW-OT (Augmented/Fused Gromov–Wasserstein Optimal Transport).</b> Start with two tables. One
  says how similar every pair of people is by microbiome; the other, by metabolome. <span class="key">
  Gromov–Wasserstein</span> is a matching trick: it lines up the two tables using only their
  <i>internal</i> similarity patterns, even though the two measurements share no common features.
  <b>How, in short:</b> it searches over ways to pair people across the two tables and keeps the pairing
  that best <i>preserves relationships</i> — if persons A and B are close in microbiome, their matched
  partners should be close in metabolome too. It scores how badly a pairing breaks that rule and nudges
  toward the lowest-mismatch pairing (a "soft" matching where each person can split weight across
  several partners), solved by repeated refinement. So it matches the <i>pattern of distances</i>, never
  the raw features. The
  result is a soft matching between microbiome-people and metabolome-people. For someone missing their
  metabolome, we place them as a weighted blend of the metabolome-people they got matched to (called
  <code>barycentric projection</code>), giving them a spot in a shared space where we can finally read
  off distances.</p>
  <aside class="callout"><span class="cl-label">why "fused"</span><p>Plain matching has a flaw: with a
  weak signal it can line a shape up with its mirror image (consistent-looking but wrong). The
  "fused/augmented" part adds a few real <b>anchors</b> from the 1042 people who have BOTH measurements,
  pinning the alignment the right way up.</p></aside>
  <p><i>Analogy:</i> aligning two maps of the same city that share no street names, just by matching the
  pattern of distances between places, and using a few known landmarks so the map never flips.</p>
  <p><b>2. CM-Harmonic-Aniso (place people by triangulating off landmarks).</b> Start from the grader's
  own answer key. Its map is built from the 1042 people who have BOTH omics, so we know their true spot on
  it exactly — <span class="key">pin them in place as fixed landmarks</span>. Now build a friendship graph:
  link people who are similar in microbiome, link people who are similar in metabolome, and overlay the two.
  A person missing an omics simply draws no links in the side they lack, so we never invent any values for
  them. <b>How, in short:</b> we apply one rule to all the unknown people at once — each one settles at the
  weighted-average position of its graph neighbours (a single sparse solve, called <code>harmonic
  extension</code>). The unknowns relax into the smoothest arrangement that agrees with the fixed landmarks.
  Two honest fixes finish it: harmonic averaging drifts everyone toward the centre, so a tiny calibration
  learned on held-out landmarks corrects the squashing; and for the axis that genuinely needs the missing
  omics, we fall back to the average, which is provably no worse than mean-imputation.</p>
  <p><i>Analogy:</i> a hiker with no GPS fixing their location by triangulating off mountain peaks they can
  see, instead of guessing their own altitude.</p>
  <p><b>3. How they relate.</b> These are <span class="key">two separate, complete methods</span> that
  solve the SAME job in different ways — NOT two stages of one pipeline. AGW-OT matches the two omics by
  their shape (a transport idea); CM-Harmonic-Aniso places people by proximity to landmarks (a wayfinding
  idea). We run each one start-to-finish, compare them head-to-head against the simple baseline (using the
  Mantel score), and keep what works. They can optionally be averaged at the very end, but that is a bonus
  experiment, not a requirement.</p>

  <h3>Backbone & baselines we compare against</h3>
  <p>A linear coupled-factorisation (ACMTF, 2026) that learns a shared latent space and measures
  distances from only the <b>cross-modally shared part</b> (so it commits only to what's recoverable),
  plus the full baseline ladder (mean / KNN / RF / PLS→frozen-PCA).</p>

  <h3>Three terms from the plan, in plain words</h3>
  <p><b>1. Linear coupled factorisation (CMTF/ACMTF).</b> Both measurements describe the SAME people. It
  learns one shared "summary" per person (a handful of numbers) that explains both measurements at once,
  plus a way to translate those numbers back into each measurement's features. Because the summary is
  shared, a person with only one measurement still gets their summary from the side they do have.
  "Handles missing blocks natively" = it simply ignores the absent values while learning, with no need
  to guess them first. <i>Linear</i> = it only adds and scales numbers (no curvy transforms), matching
  the grader's linear PCA target. <i>Analogy:</i> one short "profile" per person that both a food diary
  and a blood test agree on.</p>
  <p><b>2. Cross-modally shared vs modality-specific components.</b> Some summary numbers capture
  patterns seen in BOTH measurements (<span class="key">shared</span>); others appear in only one
  (<span class="key">specific</span>). We measure distances using ONLY the shared ones, because those
  are the only ones recoverable no matter which measurement is missing. Committing only to what is
  recoverable is what makes it <b>robust</b>.</p>
  <p><b>3. Frozen PCA.</b> <code>PCA</code> (principal component analysis) squeezes many numbers down to
  a few that carry most of the information. "Frozen" = we fit the scaler and PCA <i>once</i> on the
  training people, then for any new person just apply those fixed settings (never recompute on test
  data). Recomputing on test data would leak information and shift the axes, so distances would stop
  being comparable. <i>Analogy:</i> mark the ruler once, then measure everyone with that same ruler.</p>""")

sec("plan", "Pipeline & evaluation", "06", "Our pipeline & evaluation plan", """
  <h3>Pipeline</h3>
  <ol class="bul">
    <li><b>Clean the microbiome data:</b> first replace exact zeros with a tiny placeholder number (a
      <code>pseudocount</code>) so logarithms work, then apply the <span class="key">CLR transform</span>
      (centered log-ratio), which puts this compositional data — numbers that are really proportions of
      a whole — onto a log scale where ordinary distance becomes meaningful.</li>
    <li><b>Clean the metabolome data:</b> take logs (to tame very large values) and standardise (rescale
      so features are comparable).</li>
    <li><b>Fit on training data only:</b> learn the scaler and PCA settings on the training people alone,
      then freeze them.</li>
    <li><b>Run the core methods:</b> AGW-OT and CM-Harmonic-Aniso.</li>
    <li><b>Compare against the baseline ladder:</b> stack them against simple fill-in methods (mean,
      median, KNN, Random Forest, PLS).</li>
    <li><b>Run the comparator:</b> ACMTF coupled factorisation, taking distances from the shared
      components only.</li>
  </ol>
  <h3>Evaluation</h3>
  <ol class="bul">
    <li><b>Score with Mantel correlation:</b> the <span class="key">Mantel</span> test measures how well
      two distance matrices agree; we compare ours to the grader's recipe (standardise → PCA → distance
      in the first 2 components).</li>
    <li><b>Test several missing rates:</b> hide 10%, 30%, and 50% of the data.</li>
    <li><b>Test both directions:</b> in some runs drop the metabolome, in others drop the microbiome.</li>
    <li><b>Use subject-level splits:</b> never let the same person appear in both train and test.
      Distances between people aren't independent, so we hold out whole people and measure only on that
      held-out block.</li>
    <li><b>Keep scaler and PCA frozen on train:</b> so no test information leaks in.</li>
    <li><b>Report both quality and speed:</b> the Mantel score (how good) and runtime (how fast) vs. the
      baseline.</li>
  </ol>
  <aside class="callout"><span class="cl-label">success goal</span><p>We win if a principled method beats
  plain mean-imputation on the Mantel score at 30%+ missing data. Then in milestones 2–3 we build it,
  check how much performance drops as the missing percentage rises, and validate on the two extra
  datasets the instructors give us.</p></aside>""")

# slide-by-slide cheat sheet
SLIDE_ROWS = [
 ("01 Title", "Project title + framing.", "We estimate sample distances across two omics, robust to missing modalities.", "—"),
 ("02 The problem", "The task restated.", "Output a distance matrix graded by Mantel vs a 2-PC PCA truth; the hard part is missing modalities.", "Why distances, not classification?"),
 ("03 Data", "Availability + imbalance.", "1042 both / 348+348 single-modality; the missingness is real and in the data.", "Is the missingness random?"),
 ("04 Confounders", "Age & BMI by group.", "Obesity groups young/high-BMI; diabetes/CVD older — age & BMI confound.", "How will you handle confounders?"),
 ("05 Batch", "Country composition.", "CENTER (F=8.84) structures microbiome more than disease (F=3.72).", "Will you remove the batch effect?"),
 ("06 What predicts disease", "Metadata feature importance.", "Demographics out-predict omics (0.34 vs 0.26); and imputing a missing omics doesn't help prediction either.", "Why is omics disease-signal weak?"),
 ("07 Microbiome map", "Disease-coloured PCoA.", "No clean disease clusters; PC1+PC2 only ~39%, so structure is high-dimensional → model distances.", "What is PCoA / Aitchison?"),
 ("08 Differential", "Per-group diff counts.", "Up to 131 species / 77 metabolites differ vs control.", "Multiple-testing correction?"),
 ("09 Coupling", "Cross-omics correlation.", "Max |r|=0.38 — weak coupling caps cross-modal recovery.", "Why does this cap imputation?"),
 ("10 Naive baseline", "Recovery → Mantel table.", "Drop a whole omics, rebuild it, score the distances; all four fills tie → the cross-modal ceiling is the wall.", "Why does mean tie KNN/RF here?"),
 ("11 Method choice", "Selection + review.", "Scout + adversarial review; we feature de-risked, sound, novel methods.", "Why not just a neural net?"),
 ("12 Method ①", "Augmented-GW OT.", "Match modality geometries with no shared features; AGW fixes the mirror flaw.", "What is Gromov–Wasserstein?"),
 ("13 Method ②", "CM-Harmonic-Aniso.", "Pin complete patients as landmarks; triangulate the rest by graph proximity, no imputation.", "How is this different from KNN?"),
 ("14 Pipeline", "Plan + evaluation.", "Clean → fix settings on train only → build distances two ways vs simple fills → Mantel sweep on missing-only patients, fair splits.", "How do you avoid leakage?"),
 ("15 Next", "Closing + next steps.", "The challenge is the missing-modality patients; place them on the shared map, then build both methods and sweep missing-%.", "What's the biggest risk?"),
]
rows = "".join(f"<tr><td>{a}</td><td>{c}</td><td>{d}</td><td class='lq'>{e}</td></tr>"
               for a, c, d, e in SLIDE_ROWS)
sec("cheat", "Slide-by-slide cheat sheet", "07", "Slide-by-slide cheat sheet", f"""
  <p>For each of the 15 deck slides: what's shown, the one line to say, and the question it invites.</p>
  <table class="tbl cheat"><thead><tr><th>slide</th><th>shows</th><th>say this</th><th>likely Q</th></tr></thead>
  <tbody>{rows}</tbody></table>""")

# Q&A bank
QAS = [
 ("Why a distance matrix instead of predicting disease?",
  "It's what the grader scores (Mantel vs their distance matrix), and our data shows the omics predict the disease label poorly — the structure lives in sample-to-sample relationships, not a clean class boundary."),
 ("What is a Mantel test, in one line?",
  "A correlation between two distance matrices: it asks whether pairs that are far apart in our matrix are also far apart in the grader's."),
 ("Why first 2 PCs / why is the target 'linear'?",
  "The grader standardises features, runs PCA, and uses distance in the first 2 principal components. PCA is a linear projection, so the target geometry is linear — non-linear methods risk drifting away from it."),
 ("Why CLR-transform the microbiome?",
  "Microbiome data is compositional (relative abundances summing to 1), so raw values are not independent. CLR (centered log-ratio) maps them to a space where ordinary (Euclidean) distance is meaningful — that distance is called Aitchison distance."),
 ("Why log-transform the metabolome?",
  "It's heavy-tailed and positive (values 0.01–582). A log makes the scale comparable across metabolites so a few large ones don't dominate after standardising."),
 ("Is the missing data random?",
  "No. Whole-modality missingness (~40%) is spread fairly evenly, but demographic missingness is structured — 100% of Denmark lacks BMI/age/gender by privacy law (MNAR: missing not at random)."),
 ("Why does mean imputation tie/beat KNN and PLS in your distance baseline?",
  "Because the target is linear PCA of standardised features: a mean-filled block becomes ≈0 after standardising and stops contributing, so the distance correctly falls back to the modality you have. Cross-modal correlation is only ~0.38, too weak for regression to help."),
 ("But your partner's table said mean was best for imputation — and you said KNN. Which is it?",
  "Different tasks. Scattered missing cells within a modality → KNN wins (it borrows from the same sample's other values). A whole modality gone → mean ties (no within-modality info to borrow). Both are correct; we show both."),
 ("What's the cross-modal ceiling?",
  "The best you can recover about a missing modality is limited by how well the other modality predicts it. Here that's weak (ρ<0.25 for top pairs), so there's a hard cap — important to state honestly."),
 ("Why is CENTER a problem, and will you correct it?",
  "Country structures the microbiome more than disease (PERMANOVA F 8.84 vs 3.72), so disease differences can be confounded by geography. We won't blindly remove it: the grader's ground truth contains the center effect, so de-batching could lower our Mantel score. We test it rather than assume."),
 ("How will you handle class imbalance?",
  "Balanced metrics (balanced accuracy), grouped CV, and — since the real target is distances, not class prediction — imbalance matters less than in a classifier."),
 ("What is PCoA and how does it differ from PCA?",
  "PCoA (principal coordinates analysis) is PCA applied to a distance matrix — it places samples in 2-D so that distances are preserved. We use it to visualise microbiome (Aitchison) distances."),
 ("What is PERMANOVA?",
  "A permutation test that asks whether groups differ in their multivariate distances; the pseudo-F is the effect size (bigger = groups more separated)."),
 ("How does Gromov–Wasserstein work, simply?",
  "It compares two datasets that live in different feature spaces by matching their internal distance patterns (not the features themselves), then can transport one onto the other."),
 ("What's the 'mirror' problem with GW, and the fix?",
  "GW only sees internal distances, so it can't tell a shape from its rotation/reflection — it might place a point at a flipped location. Augmented/Fused GW adds feature information to break that symmetry."),
 ("How is CM-Harmonic-Aniso different from KNN imputation?",
  "KNN fills in a subject's missing values, then you compute distances. CM-Harmonic-Aniso never fills values — it pins the complete subjects at their true coordinates on the grader's own map and places everyone else by graph proximity to those landmarks (one harmonic solve), so a missing modality is just an absent link, not an invented number."),
 ("Why not just train a deep neural network?",
  "n is small (1738), the target is linear, and deep models risk overfitting and decorrelating from the linear Mantel target. Our adversarial review specifically killed an over-parameterised distance-distillation idea for this reason."),
 ("How do you avoid data leakage in evaluation?",
  "Subject-grouped CV (a subject never appears in both train and test, because distance pairs aren't independent) and fitting the scaler/PCA on training folds only."),
 ("What's your definition of success for milestone 2?",
  "Beat the mean-imputation Mantel curve at ≥30% missing with a principled, justified method — and report runtime too."),
 ("What are the main risks / limitations?",
  "The cross-modal ceiling (weak coupling) limits any method; non-linear methods may not match the linear target; and the center confound interacts with the grader's own ground truth."),
 ("Where does the second modality actually help?",
  "Both-omics disease prediction (0.26) beats microbiome-only (0.19), so there is complementary signal — just weak and metabolite-specific, which is what we aim to exploit."),
 ("What did each partner do?",
  "We worked independently and our analyses converged (a good sign). One partner led the broad EDA (demographics, batch, feature importance, per-group differential counts); the other led the distance-matrix framing, the Mantel baseline, and the method review. We merged and cross-checked all numbers."),
]
qhtml = "".join(qa(q, a) for q, a in QAS)
sec("qa", "Q&A bank", "08", "Anticipated questions (with answers)", f"""
  <p>The questions a reviewer is most likely to ask, with short answers you can give directly.</p>
  {qhtml}""")

# glossary
GL = [
 ("Relative abundance", "Each species as a fraction of the sample's total — values sum to 1 (compositional)."),
 ("Compositional data", "Data that are parts of a whole; only ratios are meaningful, so special transforms are needed."),
 ("CLR", "Centered log-ratio: log each value, subtract the row's mean log — turns compositions into a space where Euclidean distance works."),
 ("Aitchison distance", "Euclidean distance computed on CLR-transformed data; the standard compositional distance."),
 ("PCA", "Principal component analysis: finds the main linear axes of variation in the data."),
 ("PCoA", "Principal coordinates analysis: PCA applied to a distance matrix, for visualising distances."),
 ("PERMANOVA", "Permutation test for whether groups differ in multivariate distance; pseudo-F = effect size."),
 ("Mantel test", "Correlation between two distance matrices (our scoring metric)."),
 ("Spearman correlation", "Rank-based correlation; robust to non-linear monotonic relationships."),
 ("FDR / Bonferroni", "Multiple-testing corrections that control false positives when testing many features."),
 ("KNN", "k-nearest-neighbours: predict a value from the most similar samples."),
 ("PLS", "Partial least squares: a linear regression that predicts one block of features from another."),
 ("Random Forest", "An ensemble of decision trees used here for prediction/feature importance."),
 ("Balanced accuracy", "Accuracy averaged across classes — fair under imbalance (chance = 1/#classes)."),
 ("MNAR", "Missing not at random: the fact a value is missing depends on something systematic (e.g. country)."),
 ("CENTER / recruitment center", "The clinical site/country (Denmark, France, Germany) where a subject was enrolled and sampled — a 'where/how it was collected' label, not biology."),
 ("Batch effect / confounder", "A non-biological factor (here, recruitment center) that creates differences mistaken for biology."),
 ("Optimal transport", "Math for the cheapest way to move one distribution onto another."),
 ("Gromov–Wasserstein", "Optimal transport between datasets in different spaces, using internal distances only."),
 ("Barycentric projection", "Placing a transported point as a weighted average of where it maps to."),
 ("Harmonic extension", "Placing unknown points at the weighted average of their graph neighbours by one sparse solve, holding known points fixed (the basis of CM-Harmonic-Aniso)."),
 ("Trilateration / wayfinding", "Fixing an unknown position from its distances to several known landmarks (as in GPS); here, placing a missing-modality patient relative to complete-patient landmarks."),
 ("ACMTF / CMTF", "Coupled matrix-tensor factorisation: learn a shared latent space across modalities; handles missing blocks natively."),
 ("Modality", "One data type/source — here, microbiome or metabolome."),
]
glhtml = "".join(gloss(t, d) for t, d in GL)
sec("glossary", "Glossary", "09", "Glossary (plain definitions)", f'<dl class="glist">{glhtml}</dl>')

# files & how to run
sec("files", "Files & how to run", "10", "Where everything lives & how to run it", """
  <h3>Data</h3>
  <table class="tbl files"><tbody>
    <tr><td>data/train/microbiome.csv</td><td>170 species × 1738 subjects (relative abundance)</td></tr>
    <tr><td>data/train/metabolome.csv</td><td>104 metabolites × 1738 subjects (serum)</td></tr>
    <tr><td>data/train/metadata.csv</td><td>group, gender, BMI, age, center</td></tr>
  </tbody></table>
  <h3>Analysis code (analysis/)</h3>
  <table class="tbl files"><tbody>
    <tr><td>eda.py</td><td>Our EDA + the distance-Mantel naive baseline → writes figures + <code>findings.json</code></td></tr>
    <tr><td>partner_eda.py</td><td>Re-runs the partner's exploration on our data (verify + restyle) → figures + <code>partner_findings.json</code></td></tr>
    <tr><td>build_html.py</td><td>Builds the slide deck <code>milestone1.html</code></td></tr>
    <tr><td>build_deck.py</td><td>Builds the PowerPoint twin <code>milestone1.pptx</code></td></tr>
    <tr><td>build_guide.py</td><td>Builds this companion (<code>milestone1_guide.html</code>)</td></tr>
    <tr><td>findings.json / partner_findings.json</td><td>All the numbers, so decks/guide stay in sync</td></tr>
    <tr><td>figures/*.png</td><td>Every figure (paper/ink/rose styled)</td></tr>
    <tr><td>assets/fonts/</td><td>Embedded fonts (Space Grotesk, JetBrains Mono, Geist)</td></tr>
  </tbody></table>
  <h3>Deliverables (deliverables/)</h3>
  <table class="tbl files"><tbody>
    <tr><td>milestone1.html</td><td><b>The presentation deck</b> (open in a browser, navigate ← →)</td></tr>
    <tr><td>milestone1.pptx</td><td>PowerPoint version of the same deck</td></tr>
    <tr><td>milestone1.ipynb</td><td>Reproducible notebook of the analysis</td></tr>
    <tr><td>findings.md</td><td>Talking points + report notes + the partner-integration review</td></tr>
    <tr><td>milestone1_guide.html</td><td>This study guide</td></tr>
  </tbody></table>
  <h3>How to regenerate everything</h3>
  <pre class="code">cd /Users/avivnoah/Uni/Project
source .venv/bin/activate
python analysis/eda.py            # EDA + baseline + figures + findings.json
python analysis/partner_eda.py    # partner EDA reproduced + restyled
python analysis/build_html.py     # rebuild the deck
python analysis/build_deck.py     # rebuild the pptx
python analysis/build_guide.py    # rebuild this guide
open deliverables/milestone1.html</pre>
  <p class="note">Fonts live in <code>analysis/assets/fonts/</code> and are embedded into the HTML at
  build time, so the output files are fully self-contained and work offline.</p>""")


# ============================ RENDER ============================
TOC = "".join(f'<li><a href="#{sid}"><span class="tn">{i:02d}</span>{label}</a></li>'
              for i, (sid, label, _) in enumerate(SECTIONS))
BODY_HTML = "".join(h for _, _, h in SECTIONS)

CSS = FONTS + """
:root{--bg:#FAF9F6;--ink:#0A0A0A;--ink2:#1f1e1c;--mut:#6B6863;--line:#E2DFD8;
  --line2:#DAD7CF;--accent:#FF2D55;--tint:rgba(255,45,85,.07);--win:#c81d44;}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink2);font-family:BODY_STACK;font-size:17px;line-height:1.65;
  -webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{display:grid;grid-template-columns:260px minmax(0,760px) 1fr;gap:0;max-width:1240px;margin:0 auto}
/* sticky TOC */
nav.toc{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;padding:48px 24px 48px 32px;
  border-right:1px solid var(--line)}
nav.toc .brand{font-family:MONO_STACK;font-size:.72rem;letter-spacing:.18em;text-transform:uppercase;
  color:var(--accent);margin-bottom:.3em}
nav.toc .brand b{color:var(--ink);display:block;font-size:.95rem;letter-spacing:.04em;margin-top:.4em}
nav.toc ul{list-style:none;margin-top:1.8em}
nav.toc li a{display:flex;gap:.7em;align-items:baseline;text-decoration:none;color:var(--mut);
  font-size:.9rem;padding:.38em 0;border-left:2px solid transparent;padding-left:.9em;margin-left:-.9em;
  transition:.15s}
nav.toc li a:hover{color:var(--ink)}
nav.toc li a.active{color:var(--ink);border-left-color:var(--accent);font-weight:500}
nav.toc .tn{font-family:MONO_STACK;font-size:.72rem;color:var(--accent);min-width:1.6em}
/* article */
main{padding:64px 56px 120px}
.hero{margin-bottom:3.5em}
.hero .ey{font-family:MONO_STACK;font-size:.78rem;letter-spacing:.2em;text-transform:uppercase;
  color:var(--accent);margin-bottom:1.1em}
.hero h1{font-family:DISP_STACK;font-weight:700;font-size:clamp(2.2rem,4.5vw,3.4rem);line-height:1.02;
  letter-spacing:-.03em;color:var(--ink);text-wrap:balance}
.hero .sub{font-size:1.18rem;color:var(--mut);margin-top:.9em;max-width:60ch}
.hero .use{margin-top:1.6em;font-family:MONO_STACK;font-size:.8rem;color:var(--mut);
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:.9em 0}
.sec{padding:2.6em 0;border-top:1px solid var(--line)}
.sec .kick{font-family:MONO_STACK;font-size:.8rem;color:var(--accent);letter-spacing:.1em;margin-bottom:.3em}
.sec h2{font-family:DISP_STACK;font-weight:650;font-size:clamp(1.5rem,2.6vw,2rem);letter-spacing:-.02em;
  color:var(--ink);line-height:1.1;margin-bottom:.8em;text-wrap:balance}
.sec h3{font-family:DISP_STACK;font-weight:600;font-size:1.18rem;color:var(--ink);
  margin:1.6em 0 .5em;letter-spacing:-.01em}
.sec h3 .sub{font-family:MONO_STACK;font-size:.7rem;color:var(--mut);letter-spacing:.06em;
  text-transform:uppercase;margin-left:.4em}
.sec p{margin:.7em 0;max-width:68ch}
.lead{font-size:1.18rem;color:var(--ink2)}
.bul{margin:.6em 0 .6em 1.3em;max-width:66ch}.bul li{margin:.4em 0}
.fig{margin:1.4em 0}
.fig img{width:100%;height:auto;display:block;border:1px solid var(--line2);background:#fff}
.fig figcaption{font-family:MONO_STACK;font-size:.72rem;color:var(--mut);margin-top:.5em;
  letter-spacing:.03em;text-transform:uppercase}
.note{font-size:.92rem;color:var(--mut);border-left:2px solid var(--line2);padding-left:1em;margin-top:1em}
.src{font-family:MONO_STACK;font-size:.76rem;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
b{color:var(--ink);font-weight:600}
.key{font-weight:600;background:linear-gradient(var(--accent),var(--accent)) no-repeat 0 100%/100% 2px;
  padding-bottom:1px}
code{font-family:MONO_STACK;font-size:.86em;background:#efece5;padding:.1em .4em;border-radius:2px;
  color:var(--ink)}
.code{font-family:MONO_STACK;font-size:.82rem;line-height:1.7;background:#15140f;color:#f3efe6;
  padding:1.1em 1.3em;border-radius:4px;margin:1em 0;overflow:auto;white-space:pre}
/* callout */
.callout{position:relative;background:var(--tint);border-left:3px solid var(--accent);
  padding:1.1em 1.3em;margin:1.3em 0;max-width:68ch}
.cl-label{display:block;font-family:MONO_STACK;font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--accent);margin-bottom:.5em}
.callout p{margin:0}
/* tables */
.tbl{border-collapse:collapse;width:100%;margin:1.1em 0;font-size:.92rem}
.tbl th{font-family:MONO_STACK;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);
  text-align:left;padding:.6em .8em;border-bottom:2px solid var(--ink)}
.tbl td{padding:.62em .8em;border-bottom:1px solid var(--line2);vertical-align:top}
.tbl.mono{font-family:MONO_STACK;font-variant-numeric:tabular-nums}
.tbl.mono th:not(:first-child),.tbl.mono td:not(:first-child){text-align:right}
.tbl.mono td.win{color:var(--win);font-weight:700}
.tbl.files td:first-child{font-family:MONO_STACK;font-size:.84rem;color:var(--ink);white-space:nowrap}
.tbl.cheat td:first-child{font-family:MONO_STACK;font-size:.8rem;white-space:nowrap;color:var(--ink)}
.tbl.cheat .lq{color:var(--accent);font-size:.86rem}
/* Q&A */
.qa{padding:1em 0;border-bottom:1px solid var(--line)}
.qa .q{font-family:DISP_STACK;font-weight:600;color:var(--ink);margin:0 0 .3em}
.qa .q::before{content:"Q  ";font-family:MONO_STACK;color:var(--accent);font-weight:700}
.qa .a{margin:0;color:var(--ink2)}
.qa .a::before{content:"A  ";font-family:MONO_STACK;color:var(--mut);font-weight:700}
/* glossary */
.glist{margin:1em 0}
.gl{display:grid;grid-template-columns:200px 1fr;gap:1.2em;padding:.7em 0;border-bottom:1px solid var(--line)}
.gl dt{font-family:MONO_STACK;font-size:.82rem;color:var(--ink);font-weight:600}
.gl dd{margin:0;color:var(--ink2);font-size:.95rem}
::selection{background:var(--accent);color:#fff}
a:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
@media (max-width:980px){
  .wrap{grid-template-columns:1fr}
  nav.toc{position:static;height:auto;border-right:none;border-bottom:1px solid var(--line);
    padding:28px 32px}
  nav.toc ul{columns:2;margin-top:1em}main{padding:36px 28px 80px}
  .gl{grid-template-columns:1fr;gap:.2em}
}
@media print{
  nav.toc{display:none}.wrap{grid-template-columns:1fr;max-width:none}
  main{padding:0}.sec,.qa{break-inside:avoid}body{font-size:11pt}
  .code{background:#f2f0ea;color:#000;border:1px solid #ccc}
}
""".replace("BODY_STACK", BODY).replace("DISP_STACK", DISP).replace("MONO_STACK", MONO)

JS = """
const links=[...document.querySelectorAll('nav.toc a')];
const map=new Map(links.map(a=>[a.getAttribute('href').slice(1),a]));
const io=new IntersectionObserver((es)=>{es.forEach(e=>{
  if(e.isIntersecting){links.forEach(l=>l.classList.remove('active'));
    const a=map.get(e.target.id); if(a)a.classList.add('active');}})},
  {rootMargin:'-10% 0px -80% 0px'});
document.querySelectorAll('section.sec').forEach(s=>io.observe(s));
"""

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' fill='%23FAF9F6'/%3E%3Crect x='5' y='5' width='22' height='22'"
           " fill='none' stroke='%23FF2D55' stroke-width='3'/%3E%3C/svg%3E")

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="MetaCardis Milestone 1 — presenter's companion & study guide.">
<meta name="color-scheme" content="light">
<link rel="icon" href="{FAVICON}">
<title>Milestone 1 — Study Guide</title><style>{CSS}</style></head>
<body><div class="wrap">
<nav class="toc"><div class="brand">MetaCardis · Milestone 1<b>Presenter's companion</b></div>
<ul>{TOC}</ul></nav>
<main>
  <header class="hero">
    <p class="ey">Study guide · everything behind the deck</p>
    <h1>Milestone 1 — the work, explained for us</h1>
    <p class="sub">A plain-English companion to the presentation: what we built, what we found and why,
      every term defined, the questions we'll be asked, and where every file lives.</p>
    <p class="use">HOW TO USE — read top-to-bottom once; then jump via the left menu to answer any
      question the deck raises. Searchable (Ctrl/Cmd-F) and printable to PDF.</p>
  </header>
  <article>{BODY_HTML}</article>
</main></div><script>{JS}</script></body></html>"""

out = ROOT / "deliverables" / "milestone1_guide.html"
out.write_text(html)
print(f"wrote {out}  ({len(html)/1024:.0f} KB, {len(SECTIONS)} sections, self-contained)")
