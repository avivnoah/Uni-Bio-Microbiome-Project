"""Build deliverables/milestone1.pptx — paper/ink/rose "bold mono / editorial"
deck matching milestone1.html. Static PowerPoint twin of the HTML deck.

Fonts: Space Grotesk (display) + JetBrains Mono (labels). PowerPoint substitutes
if the viewer lacks them; install from fontsource for an exact match.
"""
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "analysis" / "figures"
F = json.loads((ROOT / "analysis" / "findings.json").read_text())

PAPER = RGBColor(0xFA, 0xF9, 0xF6)
INK = RGBColor(0x0A, 0x0A, 0x0A)
INK2 = RGBColor(0x1C, 0x1B, 0x19)
MUT = RGBColor(0x6B, 0x68, 0x63)
LINE = RGBColor(0xDA, 0xD7, 0xCF)
ACCENT = RGBColor(0xFF, 0x2D, 0x55)
ROSE_GHOST = RGBColor(0xF1, 0xC9, 0xD2)  # faint numeral
DISP = "Space Grotesk"
MONO = "JetBrains Mono"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = prs.slide_width, prs.slide_height
ML, MR = 0.85, 0.85
TOTAL = 13


def slide_bg(s, color=PAPER):
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = color


def box(s, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def para(tf, runs, size, font=DISP, color=INK, bold=False, first=False,
         align=PP_ALIGN.LEFT, spacing=1.0, space_after=6, tracking=None, caps=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.line_spacing = spacing
    p.space_after = Pt(space_after)
    p.space_before = Pt(0)
    if isinstance(runs, str):
        runs = [(runs, {})]
    for text, ov in runs:
        if caps:
            text = text.upper()
        r = p.add_run()
        r.text = text
        r.font.name = ov.get("font", font)
        r.font.size = Pt(ov.get("size", size))
        r.font.bold = ov.get("bold", bold)
        r.font.italic = ov.get("italic", False)
        r.font.color.rgb = ov.get("color", color)
        if tracking is not None:
            _track(r, tracking)
    return p


def _track(run, pts):
    rPr = run._r.get_or_add_rPr()
    rPr.set("spc", str(int(pts * 100)))


def line(s, x, y, w, color=LINE, weight=1.0):
    ln = s.shapes.add_connector(2, Inches(x), Inches(y), Inches(x + w), Inches(y))
    ln.line.color.rgb = color
    ln.line.width = Pt(weight)
    return ln


def vline(s, x, y, h, color=LINE, weight=1.0):
    ln = s.shapes.add_connector(2, Inches(x), Inches(y), Inches(x), Inches(y + h))
    ln.line.color.rgb = color
    ln.line.width = Pt(weight)
    return ln


def rect(s, x, y, w, h, color=ACCENT):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def shell(s, section, n):
    """running header, faint bleeding numeral, mono footer."""
    slide_bg(s)
    # numeral (faint, behind, bottom-right bleed)
    nt = box(s, 8.7, 4.0, 5.6, 3.9)
    para(nt, f"{n:02d}", 250, font=DISP, color=ROSE_GHOST, bold=True,
         first=True, align=PP_ALIGN.RIGHT)
    # header
    rect(s, ML, 0.46, 0.10, 0.10, ACCENT)
    ht = box(s, ML + 0.22, 0.4, 7.0, 0.3)
    para(ht, "METACARDIS · MILESTONE 1", 9.5, font=MONO, color=MUT, first=True, tracking=1.6)
    hr = box(s, W.inches - MR - 6.0, 0.4, 6.0, 0.3)
    para(hr, section.upper(), 9.5, font=MONO, color=MUT, first=True,
         align=PP_ALIGN.RIGHT, tracking=1.6)
    line(s, ML, 0.82, W.inches - ML - MR, LINE, 1.0)
    # footer
    line(s, ML, 6.86, W.inches - ML - MR, LINE, 1.0)
    ft = box(s, ML, 6.95, 7.0, 0.3)
    para(ft, "COMPUTATIONAL MICROBIOME WORKSHOP", 9, font=MONO, color=MUT, first=True, tracking=1.4)
    fr = box(s, W.inches - MR - 3.0, 6.95, 3.0, 0.3)
    para(fr, f"{n:02d} / {TOTAL:02d}", 9, font=MONO, color=MUT, first=True,
         align=PP_ALIGN.RIGHT, tracking=1.4)


def eyebrow(s, x, y, text, w=9.0):
    tf = box(s, x, y, w, 0.35)
    para(tf, text, 11, font=MONO, color=ACCENT, bold=False, first=True, tracking=1.8)


def new():
    s = prs.slides.add_slide(BLANK)
    return s


def pic(s, name, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    return s.shapes.add_picture(str(FIG / name), Inches(x), Inches(y), **kw)


def stat(s, x, y, num_runs, label, w=2.9, big=44):
    tf = box(s, x, y, w, 1.0)
    para(tf, num_runs, big, font=DISP, color=INK, bold=True, first=True, spacing=0.95)
    lf = box(s, x, y + 0.78, w, 0.5)
    para(lf, label, 9, font=MONO, color=MUT, first=True, tracking=1.2)


ms, gc = F["modality_structure"], F["group_counts"]
pcoa, pg, pc = F["pcoa_explained"], F["permanova_group"], F["permanova_center"]
dp, b = F["disease_pred_balacc"], F["naive_distance_baseline"]


# ---- 01 title ----
s = new(); slide_bg(s)
nt = box(s, -0.2, -0.4, 6.0, 3.5)
para(nt, "01", 250, font=DISP, color=ROSE_GHOST, bold=True, first=True)
rect(s, ML, 0.46, 0.10, 0.10, ACCENT)
ht = box(s, ML + 0.22, 0.4, 7.0, 0.3)
para(ht, "METACARDIS · MILESTONE 1", 9.5, font=MONO, color=MUT, first=True, tracking=1.6)
line(s, ML, 0.82, W.inches - ML - MR, LINE, 1.0)
eyebrow(s, ML, 1.7, "MULTI-OMICS · MISSING-MODALITY DISTANCES")
tf = box(s, ML, 2.15, 9.6, 3.2)
para(tf, "Estimating sample distances", 40, font=DISP, color=INK, bold=True, first=True, spacing=1.0)
para(tf, "across multi-omics,", 40, font=DISP, color=INK, bold=True, spacing=1.0)
para(tf, [("under missing modalities", {"color": ACCENT})], 40, font=DISP, bold=True, spacing=1.0)
rect(s, ML, 5.25, 1.15, 0.05, ACCENT)
bf = box(s, ML, 5.5, 9.0, 0.4)
para(bf, "Group ____________   ·   MetaCardis cohort", 11, font=MONO, color=MUT, first=True, tracking=0.8)

# ---- 02 statement ----
s = new(); shell(s, "The problem", 2)
eyebrow(s, ML, 1.6, "WHAT WE ARE ACTUALLY ASKED TO BUILD")
tf = box(s, ML, 2.1, 10.6, 1.7)
para(tf, [("A sample×sample ", {}), ("distance matrix", {"color": ACCENT, "bold": True}),
          (" from two omics — that holds up when an entire modality is ", {}),
          ("missing", {"color": ACCENT, "bold": True}), (".", {})],
     30, font=DISP, color=INK, bold=False, first=True, spacing=1.04)
bf = box(s, ML, 4.4, 11.2, 2.0)
para(bf, [("Graded by ", {}), ("Mantel test", {"bold": True}),
          (" vs. ground truth: standardise all features → PCA → Euclidean in the first 2 PCs. The target geometry is linear.", {})],
     15, font=DISP, color=INK2, first=True, spacing=1.3, space_after=10)
para(bf, [("With both modalities present that target is trivially recomputable — so the whole problem lives in the ", {}),
          ("missing-modality regime", {"color": ACCENT, "bold": True}), (".", {})],
     15, font=DISP, color=INK2, spacing=1.3)

# ---- 03 data overview ----
s = new(); shell(s, "Exploration / data", 3)
eyebrow(s, ML, 1.1, "THE DATA ALREADY CONTAINS THE CHALLENGE")
tf = box(s, ML, 1.5, 11.0, 0.8)
para(tf, "~40% of subjects are missing a whole modality", 26, font=DISP, color=INK, bold=True, first=True)
pic(s, "01_overview.png", ML, 2.45, w=11.63)
line(s, ML, 5.75, W.inches - ML - MR, LINE, 1.0)
xs = ML
for num, lab in [([("1042", {})], "BOTH OMICS"), ([("348", {})], "MICROBIOME ONLY"),
                 ([("348", {})], "METABOLOME ONLY"),
                 ([("528", {}), (" → ", {"color": ACCENT}), ("18", {})], "T2D → CHF (IMBALANCE)")]:
    stat(s, xs, 5.95, num, lab, w=2.9, big=40)
    xs += 2.95

# ---- 04 missing by center ----
s = new(); shell(s, "Exploration / missingness", 4)
eyebrow(s, ML, 1.15, "MISSINGNESS IS STRUCTURED, NOT RANDOM")
pic(s, "02_missing_by_center.png", ML, 1.9, w=6.6)
sx = 8.2
tf = box(s, sx, 2.0, 4.3, 4.4)
para(tf, [("Metadata is ", {}), ("MNAR by country", {"color": ACCENT, "bold": True}),
          (" — Denmark 100% missing BMI / age / sex (privacy law), France ~2%, Germany 0%.", {})],
     14, font=DISP, color=INK2, first=True, spacing=1.32, space_after=12)
para(tf, "Omics missingness (the 348 / 348) is spread evenly across center and disease group — a different mechanism.",
     14, font=DISP, color=INK2, spacing=1.32, space_after=14)
rect(s, sx, 5.0, 0.04, 0.95, ACCENT)
cf = box(s, sx + 0.25, 5.0, 4.0, 1.0)
para(cf, "Two missingness types → handled separately in the pipeline.", 14, font=DISP, color=INK, bold=True, first=True, spacing=1.3)

# ---- 05 PCoA / center ----
s = new(); shell(s, "Exploration / structure", 5)
eyebrow(s, ML, 1.15, "CENTER STRUCTURES THE MICROBIOME MORE THAN DISEASE")
pic(s, "04_microbiome_pcoa.png", ML, 1.85, w=7.4)
sx = 8.9
cf = box(s, sx, 1.95, 3.6, 0.4)
para(cf, f"PCoA (AITCHISON) · PC1 {pcoa[0]:.0%} · PC2 {pcoa[1]:.0%}", 9, font=MONO, color=MUT, first=True, tracking=0.8)
stat(s, sx, 2.5, [(f"{pc['F']}", {"color": ACCENT})], "PERMANOVA F · CENTER", w=3.6, big=46)
line(s, sx, 3.65, 3.5, LINE, 1.0)
stat(s, sx, 3.8, [(f"{pg['F']}", {"color": ACCENT})], "PERMANOVA F · DISEASE GROUP", w=3.6, big=46)
tf = box(s, sx, 5.0, 3.6, 1.6)
para(tf, [("Both p≈0.005 → ", {}), ("batch/geography dominates", {"color": ACCENT, "bold": True}),
          (". The grader's truth keeps it, so de-batching may hurt Mantel.", {})],
     12.5, font=DISP, color=INK2, first=True, spacing=1.3)

# ---- 06 two figures ----
s = new(); shell(s, "Exploration / per-omics signal", 6)
eyebrow(s, ML, 1.15, "STRONG SIGNAL EXISTS WITHIN EACH OMICS")
pic(s, "07_diff_abundance.png", ML, 1.85, h=4.2)
cf = box(s, ML, 6.15, 6.0, 0.4)
para(cf, f"{F['da_n_sig_bonferroni']}/170 SPECIES DIFFER T2D VS CONTROL (BONFERRONI)", 9, font=MONO, color=MUT, first=True, tracking=0.6)
pic(s, "08_metabolome_trends.png", 7.0, 2.25, h=4.0)
cf2 = box(s, 7.0, 6.35, 5.4, 0.4)
para(cf2, "METABOLITE GRADIENTS TRACK DISEASE STATE", 9, font=MONO, color=MUT, first=True, tracking=0.6)

# ---- 07 cross-omics ----
s = new(); shell(s, "Exploration / coupling", 7)
eyebrow(s, ML, 1.15, "CROSS-OMICS COUPLING IS WEAK — THIS CAPS IMPUTATION")
pic(s, "09_cross_omics_corr.png", ML, 1.85, h=4.7)
sx = 7.8
stat(s, sx, 2.1, [(f"{F['max_abs_taxa_metab_corr']}", {"color": ACCENT})], "MAX |SPEARMAN| TAXA ↔ METABOLITE", w=4.6, big=52)
tf = box(s, sx, 3.5, 4.6, 2.8)
para(tf, [("Only a metabolite-specific subset is predictable from microbiome → any cross-modal imputation has a ", {}),
          ("low ceiling", {"color": ACCENT, "bold": True}), (".", {})],
     14, font=DISP, color=INK2, first=True, spacing=1.3, space_after=12)
para(tf, [("Disease prediction (RF, balanced acc, 9-class, chance≈0.11): both omics ", {}),
          (f"{dp['both_omics_complete']}", {"bold": True}), (" · microbiome-only ", {}),
          (f"{dp['microbiome_only_all']}", {"bold": True}), (".", {})],
     13, font=DISP, color=INK2, spacing=1.3)

# ---- 08 baseline table ----
s = new(); shell(s, "Naïve baseline", 8)
eyebrow(s, ML, 1.2, "MANDATORY BASELINE — AND A RESULT THAT SHAPES EVERYTHING")
tf = box(s, ML, 1.7, 5.4, 1.2)
para(tf, [("Mean imputation ", {}), ("ties or beats", {"color": ACCENT, "bold": True}),
          (" KNN and PLS.", {})], 26, font=DISP, color=INK, bold=True, first=True, spacing=1.0)
nf = box(s, ML, 3.2, 5.6, 3.2)
para(nf, "Drop metabolome for x% of complete samples, impute, recompute distances, Mantel vs. full-data truth.",
     12.5, font=DISP, color=MUT, first=True, spacing=1.3, space_after=10)
for t in ["Linear PCA target → a mean-imputed block ≈ 0 after standardising, so it stops contributing.",
          "Cross-modal r≤0.38 is too weak for regression to beat that.",
          "Bar at 50% missing ≈ 0.77, already cleared trivially."]:
    para(nf, [("— ", {"color": ACCENT}), (t, {})], 12.5, font=DISP, color=INK2, spacing=1.25, space_after=8)

# editorial table, manual hairlines
tx, tw = 7.0, 5.4
cols = [tx, tx + 1.7, tx + 2.95, tx + 4.2]
cw = 1.25
ty = 1.9
hdr = box(s, tx, ty, tw, 0.4)
# header row via 4 boxes
for cx, label, al in [(cols[0], "DROPPED", PP_ALIGN.LEFT), (cols[1], "MEAN", PP_ALIGN.RIGHT),
                      (cols[2], "KNN", PP_ALIGN.RIGHT), (cols[3], "PLS", PP_ALIGN.RIGHT)]:
    hb = box(s, cx, ty, cw, 0.35)
    para(hb, label, 10, font=MONO, color=MUT, first=True, align=al, tracking=1.2)
line(s, tx, ty + 0.42, tw, INK, 2.0)
rows = [("10%", b["drop_metab_10pct"]), ("30%", b["drop_metab_30pct"]), ("50%", b["drop_metab_50pct"])]
ry = ty + 0.62
for frac, d in rows:
    m, k, p = d["mean"]["mantel_r"], d["knn"]["mantel_r"], d["pls"]["mantel_r"]
    best = max(m, k, p)
    lb = box(s, cols[0], ry, cw, 0.5)
    para(lb, frac, 13, font=MONO, color=MUT, first=True)
    for cx, v in [(cols[1], m), (cols[2], k), (cols[3], p)]:
        vb = box(s, cx, ry - 0.05, cw, 0.5)
        col = ACCENT if v == best else INK
        para(vb, f"{v}", 22, font=MONO, color=col, bold=(v == best), first=True, align=PP_ALIGN.RIGHT)
    line(s, tx, ry + 0.62, tw, LINE, 1.0)
    ry += 0.78
fn = box(s, ML, 6.4, 6.0, 0.35)
para(fn, "MANTEL R VS. PCA-2PC GROUND TRUTH · ● = BEST IN ROW", 9, font=MONO, color=MUT, first=True, tracking=0.8)

# ---- 09 method framing ----
s = new(); shell(s, "Method selection", 9)
eyebrow(s, ML, 1.5, "HOW WE CHOSE THE INSPIRING METHODS")
tf = box(s, ML, 1.95, 11.0, 0.9)
para(tf, "Broad cross-field scout, then an adversarial review.", 26, font=DISP, color=INK, bold=True, first=True)
nf = box(s, ML, 3.0, 11.4, 2.0)
for lead, rest in [("Filter 1", " — sound for a linear Mantel target (deep/nonlinear methods risk decorrelating)."),
                   ("Filter 2", " — native whole-modality missingness, not entry-level imputation."),
                   ("Filter 3", " — genuinely cutting-edge (2024–2026), novel for microbiome+metabolome.")]:
    para(nf, [("— ", {"color": ACCENT}), (lead, {"bold": True}), (rest, {})],
         14.5, font=DISP, color=INK2, spacing=1.3, space_after=9, first=(lead == "Filter 1"))
rect(s, ML, 5.4, 0.04, 1.0, ACCENT)
cf = box(s, ML + 0.25, 5.4, 11.0, 1.1)
para(cf, [("The review ", {}), ("killed our flashiest first picks", {"color": ACCENT, "bold": True}),
          (" honestly — Gromov–Wasserstein's mirror-placement ambiguity; distance-distillation overfitting a linear target. We feature de-risked versions.", {})],
     14, font=DISP, color=INK, first=True, spacing=1.3)

# ---- method slide helper ----
def method_slide(n, section, eyebrow_txt, idx, title, bullets):
    s = new(); shell(s, section, n)
    eyebrow(s, ML, 1.45, eyebrow_txt)
    tf = box(s, ML, 1.9, 11.4, 1.0)
    para(tf, [(idx + "  ", {"color": ACCENT, "bold": True}), (title, {})],
         30, font=DISP, color=INK, bold=True, first=True)
    nf = box(s, ML, 3.15, 11.4, 3.4)
    for i, runs in enumerate(bullets):
        para(nf, [("— ", {"color": ACCENT})] + runs, 14.5, font=DISP, color=INK2,
             spacing=1.3, space_after=11, first=(i == 0))
    return s

method_slide(10, "Inspiring method ①", "OPTIMAL TRANSPORT · MATH & VISION ORIGIN · SCOT+ 2025", "①",
    "Augmented / Fused Gromov–Wasserstein",
    [[("GW compares samples in ", {}), ("incomparable spaces", {"bold": True}), (" using only within-modality geometry — no shared features needed.", {})],
     [("Adaptation: ", {"bold": True}), ("couple a missing-modality sample to the complete samples' geometry, then barycentric-project onto the joint-PCA anchor → distances.", {})],
     [("Honest fix (red-team): use ", {}), ("Augmented GW", {"color": ACCENT, "bold": True}), (" — the feature term breaks GW's rotation/reflection ambiguity.", {})],
     [("Gate: ", {"bold": True}), ("must beat mean/PLS in the missing regime, else reported as a negative result.", {})]])

method_slide(11, "Inspiring method ②", "SIMILARITY NETWORK FUSION · BIOINFORMATICS 2025", "②",
    "miss-SNF",
    [[("First SNF variant for ", {}), ("completely missing data sources", {"bold": True}), (". One similarity network per modality, fused by cross-diffusion.", {})],
     [("A sample missing a source is reconstructed through its ", {}), ("shared neighbours", {"color": ACCENT, "bold": True}), (" — no feature imputation.", {})],
     [("Output is a fused n×n similarity → distance", {"bold": True}), (" — our exact deliverable.", {})],
     [("Risk we watch: diffusion is nonlinear → verify Mantel alignment vs. the linear target.", {})]])

# ---- 12 pipeline + eval ----
s = new(); shell(s, "Pipeline & evaluation", 12)
eyebrow(s, ML, 1.3, "THE PLAN")
midx = 6.55
vline(s, midx, 1.9, 4.6, LINE, 1.0)
# left
lh = box(s, ML, 1.9, 5.3, 0.4)
para(lh, "PIPELINE", 11, font=MONO, color=ACCENT, bold=True, first=True, tracking=1.6)
line(s, ML, 2.32, 5.3, LINE, 1.0)
lf = box(s, ML, 2.5, 5.3, 3.8)
for i, runs in enumerate([
    [("CLR(microbiome), log1p+standardise(metabolome); scaler & PCA fit on ", {}), ("train only", {"bold": True}), (".", {})],
    [("Core: AGW-OT and/or miss-SNF vs. the baseline ladder.", {})],
    [("Sound comparator: coupled factorisation (ACMTF-R, 2026) — distances from the ", {}), ("common components only", {"bold": True}), (".", {})],
    [("Baseline ladder: mean / KNN / RF / PLS→frozen-PCA.", {})]]):
    para(lf, [("— ", {"color": ACCENT})] + runs, 13, font=DISP, color=INK2, spacing=1.28, space_after=9, first=(i == 0))
# right
rh = box(s, midx + 0.35, 1.9, 5.3, 0.4)
para(rh, "EVALUATION", 11, font=MONO, color=ACCENT, bold=True, first=True, tracking=1.6)
line(s, midx + 0.35, 2.32, 5.3, LINE, 1.0)
rf = box(s, midx + 0.35, 2.5, 5.5, 3.8)
for i, runs in enumerate([
    [("Mantel r vs. PCA-2PC ground truth (reproduce the grader exactly).", {})],
    [("Sweep missing-% = 10/30/50, ", {}), ("both directions", {"bold": True}), (".", {})],
    [("Subject-grouped CV", {"color": ACCENT, "bold": True}), (" — distance pairs are non-iid; no leakage.", {})],
    [("Report performance and runtime vs. the baseline.", {})]]):
    para(rf, [("— ", {"color": ACCENT})] + runs, 13, font=DISP, color=INK2, spacing=1.28, space_after=9, first=(i == 0))

# ---- 13 closing ----
s = new(); slide_bg(s)
nt = box(s, 8.7, -0.4, 5.6, 3.5)
para(nt, "13", 250, font=DISP, color=ROSE_GHOST, bold=True, first=True, align=PP_ALIGN.RIGHT)
rect(s, ML, 0.46, 0.10, 0.10, ACCENT)
ht = box(s, ML + 0.22, 0.4, 7.0, 0.3)
para(ht, "METACARDIS · MILESTONE 1", 9.5, font=MONO, color=MUT, first=True, tracking=1.6)
line(s, ML, 0.82, W.inches - ML - MR, LINE, 1.0)
eyebrow(s, ML, 2.2, "KEY CHALLENGES → NEXT STEPS")
tf = box(s, ML, 2.7, 11.0, 1.8)
para(tf, [("Beat mean imputation by exploiting the ", {}),
          ("predictable cross-modal subset", {"color": ACCENT, "bold": True}),
          (" + the metabolome-only direction.", {})], 30, font=DISP, color=INK, bold=False, first=True, spacing=1.05)
rect(s, ML, 4.9, 1.15, 0.05, ACCENT)
bf = box(s, ML, 5.2, 11.0, 0.8)
para(bf, "Next: implement AGW-OT + miss-SNF · full Mantel-vs-missing% sweep vs. the baseline ladder.",
     12, font=MONO, color=MUT, first=True, tracking=0.4)

prs.save(str(ROOT / "deliverables" / "milestone1.pptx"))
print("saved deliverables/milestone1.pptx with", len(prs.slides._sldIdLst), "slides")
