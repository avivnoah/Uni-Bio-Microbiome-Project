"""Build deliverables/milestone1.html — bold-mono / Awwwards-editorial slide deck.

Self-contained single file: Space Grotesk (display) + JetBrains Mono embedded as
base64 woff2, figures base64-embedded, keyboard/click/swipe nav. Light "paper"
theme, near-black ink, one rose accent, broken 12-col grid, oversized outlined
numerals, hairline rules, sharp corners, push transitions + staggered entry.
Design system from the taste-skill design team (see commit message).
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "analysis" / "figures"
F = json.loads((ROOT / "analysis" / "findings.json").read_text())


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


def trow(frac):
    d = b[f"drop_metab_{frac}pct"]
    m, k, p = d["mean"]["mantel_r"], d["knn"]["mantel_r"], d["pls"]["mantel_r"]
    best = max(m, k, p)
    cell = lambda v: f'<td class="win">{v}</td>' if v == best else f"<td>{v}</td>"
    return f"<tr><td>{frac}%</td>{cell(m)}{cell(k)}{cell(p)}</tr>"


SLIDES = []


def slide(i, section, body, kind=""):
    """One slide: running header, bleeding numeral, body, mono footer."""
    num = f"{i:02d}"
    SLIDES.append(f"""<section class="slide {kind}" data-i="{i-1}">
      <header class="shead"><span><i class="dot"></i>MetaCardis · Milestone 1</span>
        <span>{section}</span></header>
      <div class="snum" aria-hidden="true">{num}</div>
      <div class="sbody">{body}</div>
      <footer class="sfoot"><span>Computational Microbiome Workshop</span>
        <span>{num} / {TOTAL:02d}</span></footer>
    </section>""")


TOTAL = 13

# 01 — title
slide(1, "Title", """
  <div class="title-block">
    <p class="eyebrow" data-enter="1">Multi-omics · missing-modality distances</p>
    <h1 class="display" data-enter="2">Estimating sample distances<br>across multi-omics,<br>
      <span class="key">under missing modalities</span></h1>
    <div class="accent-rule" data-enter="3"></div>
    <p class="byline" data-enter="3">Group ____________ &nbsp;·&nbsp; MetaCardis cohort</p>
  </div>""", "is-title")

# 02 — statement / task reframe
slide(2, "The problem", """
  <p class="eyebrow" data-enter="1">What we are actually asked to build</p>
  <h2 class="statement" data-enter="2">A sample×sample <span class="key">distance matrix</span> from
    two omics — that holds up when an entire modality is <span class="key">missing</span>.</h2>
  <ul class="notes" data-enter="3">
    <li>Graded by <b>Mantel test</b> vs. a ground truth: standardise all features → PCA →
      Euclidean distance in the first <b>2 PCs</b>. The target geometry is <b>linear</b>.</li>
    <li>With both modalities present that target is trivially recomputable — so the entire
      scientific problem lives in the <b>missing-modality regime</b>.</li>
  </ul>""", "is-statement")

# 03 — data overview (wide figure full, stat row)
slide(3, "Exploration / data", f"""
  <p class="eyebrow" data-enter="1">The data already contains the challenge</p>
  <h2 class="head" data-enter="1">~40% of subjects are missing a whole modality</h2>
  <div class="figfull" data-enter="2"><div class="figwell">{img('01_overview.png','overview')}</div></div>
  <div class="statrow" data-enter="3">
    <div class="stat"><span class="num">{ms['complete_both']}</span><span class="lab">both omics</span></div>
    <div class="stat"><span class="num">{ms['microbiome_only']}</span><span class="lab">microbiome only</span></div>
    <div class="stat"><span class="num">{ms['metabolome_only']}</span><span class="lab">metabolome only</span></div>
    <div class="stat"><span class="num">{gc['3']}<span class="arrow">→</span>{gc['7']}</span>
      <span class="lab">T2D → CHF (imbalance)</span></div>
  </div>""")

# 04 — missing by center (fig left, text right)
slide(4, "Exploration / missingness", f"""
  <p class="eyebrow" data-enter="1">Missingness is structured, not random</p>
  <div class="fig-stats" data-enter="2">
    <div class="figwell">{img('02_missing_by_center.png','missing by center')}</div>
    <div class="side">
      <p class="body">Metadata is <span class="key">MNAR by country</span> — Denmark 100% missing
        BMI / age / sex (privacy law), France ~2%, Germany 0%.</p>
      <p class="body">Omics missingness (the 348 / 348) is spread evenly across center and disease
        group — a different mechanism.</p>
      <p class="callout">Two missingness types → handled separately in the pipeline.</p>
    </div>
  </div>""")

# 05 — PCoA / CENTER
slide(5, "Exploration / structure", f"""
  <p class="eyebrow" data-enter="1">CENTER structures the microbiome more than disease</p>
  <div class="fig-stats" data-enter="2">
    <div class="figwell">{img('04_microbiome_pcoa.png','pcoa')}</div>
    <div class="side">
      <p class="caption">PCoA (Aitchison) · PC1 {pcoa[0]:.0%} · PC2 {pcoa[1]:.0%}</p>
      <div class="stat lg"><span class="num">{pc['F']}</span><span class="lab">PERMANOVA F · CENTER</span></div>
      <div class="hair"></div>
      <div class="stat lg"><span class="num">{pg['F']}</span><span class="lab">PERMANOVA F · disease group</span></div>
      <p class="body small">Both p≈0.005 → <span class="key">batch/geography dominates</span>.
        The grader's ground truth keeps it, so de-batching may <i>hurt</i> Mantel.</p>
    </div>
  </div>""")

# 06 — two figures
slide(6, "Exploration / per-omics signal", f"""
  <p class="eyebrow" data-enter="1">Strong signal exists within each omics</p>
  <div class="twofig" data-enter="2">
    <figure class="figwell a"><div>{img('07_diff_abundance.png','diff abundance')}</div>
      <figcaption class="caption">{F['da_n_sig_bonferroni']}/170 species differ T2D vs control (Bonferroni)</figcaption></figure>
    <figure class="figwell b"><div>{img('08_metabolome_trends.png','metabolome trends')}</div>
      <figcaption class="caption">metabolite gradients track disease state</figcaption></figure>
  </div>""")

# 07 — cross-omics weak
slide(7, "Exploration / coupling", f"""
  <p class="eyebrow" data-enter="1">Cross-omics coupling is weak — this caps imputation</p>
  <div class="fig-stats" data-enter="2">
    <div class="figwell">{img('09_cross_omics_corr.png','cross omics')}</div>
    <div class="side">
      <div class="stat lg"><span class="num">{F['max_abs_taxa_metab_corr']}</span>
        <span class="lab">max |Spearman| taxa ↔ metabolite</span></div>
      <p class="body">Only a metabolite-specific subset is predictable from microbiome → any
        cross-modal imputation has a <span class="key">low ceiling</span>.</p>
      <p class="body small">Disease prediction (RF, balanced acc, 9-class, chance≈0.11):
        both omics <b>{dp['both_omics_complete']}</b> · microbiome-only <b>{dp['microbiome_only_all']}</b>.</p>
    </div>
  </div>""")

# 08 — baseline table
slide(8, "Naïve baseline", f"""
  <p class="eyebrow" data-enter="1">Mandatory baseline — and a result that shapes everything</p>
  <div class="table-split" data-enter="2">
    <div class="tl">
      <h2 class="head">Mean imputation <span class="key">ties or beats</span> KNN and PLS.</h2>
      <p class="body small">Drop metabolome for x% of complete samples, impute, recompute distances,
        Mantel vs. full-data truth.</p>
      <ul class="notes small">
        <li>Linear PCA target → a mean-imputed block ≈ 0 after standardising, so it stops
          contributing — the correct linear fallback.</li>
        <li>Cross-modal r≤0.38 is too weak for regression to beat that.</li>
        <li><b>Bar at 50% missing ≈ 0.77</b>, already cleared trivially.</li>
      </ul>
    </div>
    <table class="dtable">
      <thead><tr><th>dropped</th><th>mean</th><th>KNN</th><th>PLS</th></tr></thead>
      <tbody>{trow(10)}{trow(30)}{trow(50)}</tbody>
    </table>
  </div>
  <p class="foot-note" data-enter="3">Mantel r vs. PCA-2PC ground truth · ● = best in row</p>""")

# 09 — method framing
slide(9, "Method selection", """
  <p class="eyebrow" data-enter="1">How we chose the inspiring methods</p>
  <h2 class="head" data-enter="1">Broad cross-field scout, then an adversarial review.</h2>
  <ul class="notes" data-enter="2">
    <li><b>Filter 1</b> — sound for a <i>linear</i> Mantel target (deep/nonlinear methods risk decorrelating).</li>
    <li><b>Filter 2</b> — native <i>whole-modality</i> missingness, not entry-level imputation.</li>
    <li><b>Filter 3</b> — genuinely cutting-edge (2024–2026), novel for microbiome+metabolome.</li>
  </ul>
  <p class="callout" data-enter="3">The review <span class="key">killed our flashiest first picks</span> honestly —
    Gromov–Wasserstein's mirror-placement ambiguity; distance-distillation overfitting a linear target.
    We feature de-risked versions.</p>""", "is-statement")

# 10 — method ①
slide(10, "Inspiring method ①", """
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

# 11 — method ②
slide(11, "Inspiring method ②", """
  <p class="eyebrow" data-enter="1">Similarity network fusion · Bioinformatics 2025</p>
  <h2 class="head" data-enter="1"><span class="idx">②</span> miss-SNF</h2>
  <ul class="notes" data-enter="2">
    <li>First SNF variant for <b>completely missing data sources</b>. One similarity network per
      modality, fused by cross-diffusion.</li>
    <li>A sample missing a source is reconstructed through its <span class="key">shared neighbours</span> —
      no feature imputation.</li>
    <li><b>Output is a fused n×n similarity → distance</b> — our exact deliverable.</li>
    <li>Risk we watch: diffusion is nonlinear → verify Mantel alignment vs. the linear target.</li>
  </ul>""")

# 12 — pipeline + eval (two columns split by hairline)
slide(12, "Pipeline & evaluation", """
  <p class="eyebrow" data-enter="1">The plan</p>
  <div class="twomethod" data-enter="2">
    <div class="col">
      <h3 class="colh">Pipeline</h3>
      <ul class="notes small">
        <li>CLR(microbiome), log1p+standardise(metabolome); scaler &amp; PCA fit on <b>train only</b>.</li>
        <li>Core: AGW-OT and/or miss-SNF vs. the baseline ladder.</li>
        <li>Sound comparator: coupled factorisation (ACMTF-R, 2026) — distances from the
          <b>common components only</b>.</li>
        <li>Baseline ladder: mean / KNN / RF / PLS→frozen-PCA.</li>
      </ul>
    </div>
    <div class="col">
      <h3 class="colh">Evaluation</h3>
      <ul class="notes small">
        <li>Mantel r vs. PCA-2PC ground truth (reproduce the grader exactly).</li>
        <li>Sweep missing-% = 10/30/50, <b>both directions</b>.</li>
        <li><span class="key">Subject-grouped CV</span> — distance pairs are non-iid; no leakage.</li>
        <li>Report performance <i>and</i> runtime vs. the baseline.</li>
      </ul>
    </div>
  </div>""")

# 13 — closing
slide(13, "Next", """
  <div class="title-block">
    <p class="eyebrow" data-enter="1">Key challenges → next steps</p>
    <h2 class="statement" data-enter="2">Beat mean imputation by exploiting the
      <span class="key">predictable cross-modal subset</span> + the metabolome-only direction.</h2>
    <div class="accent-rule" data-enter="3"></div>
    <p class="byline" data-enter="3">Next: implement AGW-OT + miss-SNF · full Mantel-vs-missing% sweep vs. the baseline ladder.</p>
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

/* running header / footer */
.shead,.sfoot{display:flex;justify-content:space-between;align-items:center;
  font-family:MONO_STACK;font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--mut);z-index:2}
.shead{border-bottom:1px solid var(--line);padding-bottom:.85rem}
.sfoot{border-top:1px solid var(--line);padding-top:.85rem;font-variant-numeric:tabular-nums}
.dot{display:inline-block;width:7px;height:7px;background:var(--accent);margin-right:.7em;
  vertical-align:middle}
.sbody{position:relative;z-index:2;min-height:0;overflow:hidden;
  display:flex;flex-direction:column;justify-content:center}

/* oversized outlined numeral, bleeding off the lower-right */
.snum{position:absolute;right:-.04em;bottom:-.28em;z-index:0;font-family:DISP_STACK;
  font-weight:700;font-size:clamp(220px,30vw,460px);line-height:.8;letter-spacing:-.04em;
  color:transparent;-webkit-text-stroke:2px var(--accent);opacity:.16;
  font-variant-numeric:tabular-nums;user-select:none;pointer-events:none}
.is-title .snum{right:auto;bottom:auto;left:-.04em;top:-.16em}

/* typography */
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
.foot-note{font-family:MONO_STACK;font-size:.74rem;letter-spacing:.04em;color:var(--mut);
  margin-top:1em;text-transform:uppercase}

/* key term — accent underline drawn on entry */
.key{position:relative;white-space:nowrap;font-weight:600}
.key::after{content:"";position:absolute;left:0;right:0;bottom:-.04em;height:3px;
  background:var(--accent);transform:scaleX(0);transform-origin:left;
  transition:transform .55s var(--ease) .35s}
.slide.is-active .key::after{transform:scaleX(1)}

/* title block */
.title-block{max-width:26ch}
.accent-rule{width:84px;height:4px;background:var(--accent);margin:1.2em 0 1.1em}
.byline{font-family:MONO_STACK;font-size:.84rem;letter-spacing:.06em;color:var(--mut)}

/* figure wells (figures already render on paper) */
.figwell{border:1px solid var(--line);background:var(--bg);padding:12px;
  display:flex;align-items:center;justify-content:center}
.figwell img{width:100%;height:auto;display:block;max-height:62vh;object-fit:contain}
.figfull{margin:0}
.figfull img{max-height:46vh}
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

/* figure-left + stats-right */
.fig-stats{display:grid;grid-template-columns:1.45fr .85fr;gap:clamp(28px,3.4vw,56px);
  align-items:center}
.fig-stats .side{display:flex;flex-direction:column;gap:.9em}
.fig-stats .side .body{max-width:38ch}
.hair{height:1px;background:var(--line)}

/* two-figure, staggered */
.twofig{display:grid;grid-template-columns:1.1fr .9fr;gap:clamp(28px,3vw,52px);align-items:start}
.twofig figure{display:flex;flex-direction:column;gap:.7em}
.twofig figure.b{margin-top:clamp(20px,5vh,60px)}
.twofig .figwell img{max-height:52vh}

/* data table */
.table-split{display:grid;grid-template-columns:.9fr 1.1fr;gap:clamp(32px,4vw,64px);
  align-items:center}
.dtable{border-collapse:collapse;width:100%;font-family:MONO_STACK;
  font-variant-numeric:tabular-nums}
.dtable th{font-size:.74rem;font-weight:500;letter-spacing:.12em;text-transform:uppercase;
  color:var(--mut);text-align:right;padding:0 1.1rem 1rem;border-bottom:2px solid var(--ink)}
.dtable th:first-child{text-align:left}
.dtable td{font-size:clamp(1.2rem,2vw,1.7rem);color:var(--ink);text-align:right;
  padding:1.05rem 1.1rem;border-bottom:1px solid var(--line)}
.dtable td:first-child{text-align:left;color:var(--mut);font-size:1rem;letter-spacing:.02em}
.dtable tbody tr:last-child td{border-bottom:none}
.dtable td.win{color:var(--accent);font-weight:700;position:relative}

/* two-method split by single hairline */
.twomethod{display:grid;grid-template-columns:1fr 1fr;gap:clamp(36px,4.5vw,72px);position:relative}
.twomethod::before{content:"";position:absolute;left:50%;top:0;bottom:0;width:1px;
  background:var(--line);transform:translateX(-50%)}
.colh{font-family:MONO_STACK;font-size:.8rem;font-weight:600;letter-spacing:.14em;
  text-transform:uppercase;color:var(--accent);margin-bottom:1.1em;
  border-bottom:1px solid var(--line);padding-bottom:.6em}

/* staggered entry */
.slide.is-active [data-enter]{animation:rise .55s var(--ease) both}
.slide.is-active [data-enter="2"]{animation-delay:.08s}
.slide.is-active [data-enter="3"]{animation-delay:.18s}
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}

/* nav */
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
  .fig-stats,.table-split,.twofig,.twomethod,.statrow{grid-template-columns:1fr;gap:20px}
  .twomethod::before{display:none}.twofig figure.b{margin-top:0}
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
