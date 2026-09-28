"""Figures for Documentation_template.md: fig1_pipeline.png, fig2_score.png (300 dpi, sized for an A4 text column)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

INK, SUB, CNT = "#1b1f24", "#3d4650", "#0b4f9c"
C = {"data": "#eceff3", "block": "#dbe9f7", "xgb": "#dff1e2", "ce": "#ece3f5", "dec": "#fde9d4",
     "llm": "#f9dde0", "out": "#e4e7eb"}
EDGE = {"data": "#8a96a3", "block": "#5b8fc7", "xgb": "#5da56a", "ce": "#8d6bb7", "dec": "#d98b3a",
        "llm": "#c85a66", "out": "#8a96a3"}


def box(ax, x0, y, w, h, kind, title, detail=None, count=None):
    ax.add_patch(FancyBboxPatch((x0, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=C[kind], ec=EDGE[kind], lw=1.4))
    lines = [(title, 10.5, "bold", INK)]
    if detail:
        lines.append((detail, 8.8, "normal", SUB))
    if count:
        lines.append((count, 9, "bold", CNT))
    step = 0.27
    top = y + step * (len(lines) - 1) / 2
    for i, (t, s, wgt, col) in enumerate(lines):
        ax.text(x0 + w / 2, top - i * step, t, ha="center", va="center", fontsize=s, fontweight=wgt, color=col)


def arrow(ax, p, q, color="#55606b", style="-|>", ls="-", rad=0.0, lw=1.5):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=style, color=color, lw=lw, linestyle=ls,
                                                    shrinkA=0, shrinkB=0, connectionstyle=f"arc3,rad={rad}"))


def fig1():
    fig, ax = plt.subplots(figsize=(7.2, 7.65))
    ax.set_xlim(0, 10.4)
    ax.set_ylim(1.3, 12.35)
    ax.axis("off")
    X0, W, H3, H2 = 2.45, 7.85, 1.0, 0.78
    cx = X0 + W / 2
    rows = [
        ("data", "23.7M business records", "Source 1 (US, India, France) and Source 2/3 vendor copies", None),
        ("block", "Blocking, per country", "IDF token views · names-only view · domain, OCR and Indic repairs",
         "58.4M test pairs · keeps 99.1% of true pairs"),
        ("xgb", "Stages 0-1: XGBoost + candidate cut", "name, address, house-number and legal-form features",
         "6.41M candidates, 3.70 per S1  →  candidate_pairs.tsv"),
        ("ce", "Cross-encoders on the uncertain band",
         "e5-small, e5-large, bge-reranker, Qwen2.5-1.5B and 7B (LoRA)",
         "1.49M pairs (0.02 ≤ p1 ≤ 0.99) · one averaged score"),
        ("xgb", "Stage 2: XGBoost + calibration", "adds the cross-encoder score, per-S1 and cluster features", None),
        ("xgb", "Stage 3: XGBoost in S1 context", "each pair re-scored against its S1's other candidates", None),
        ("dec", "Decision: expected-F0.5 set per S1", "one owner per record · rules: acronym join, caps, French layers",
         None),
        ("llm", "Qwen2.5-7B re-check", "re-reads the confident pairs (p1 > 0.99) that no cross-encoder saw",
         "drops the 1,150 it rejects (logit < −6)"),
        ("out", "5.85M matches, 3.38 per S1", "→  matching_results.tsv", None),
    ]
    gap, y = 0.36, 12.2
    ys, hs = [], []
    for kind, t, d, c in rows:
        h = H3 if c else H2
        y -= h / 2
        box(ax, X0, y, W, h, kind, t, d, c)
        ys.append(y)
        hs.append(h)
        y -= h / 2 + gap
    for i in range(len(rows) - 1):
        arrow(ax, (cx, ys[i] - hs[i] / 2), (cx, ys[i + 1] + hs[i + 1] / 2))
    # France self-training loop: decisions -> pseudo-labels -> cross-encoders and stage 2
    orange = "#c96a12"
    dash = (0, (4, 2.5))
    i_ce, i_s2, i_dec = 3, 4, 6
    xl = 2.1
    ax.plot([X0, xl], [ys[i_dec], ys[i_dec]], color=orange, lw=1.6, ls=dash)
    ax.plot([xl, xl], [ys[i_dec], ys[i_ce]], color=orange, lw=1.6, ls=dash)
    arrow(ax, (xl, ys[i_ce]), (X0, ys[i_ce]), color=orange, ls=dash, lw=1.6)
    arrow(ax, (xl, ys[i_s2]), (X0, ys[i_s2]), color=orange, ls=dash, lw=1.6)
    label = "\n".join(["France has no", "labels: our own", "decisions become", "pseudo-labels",
                       "(2 rounds) for", "the cross-encoders", "and stage 2"])
    ax.text(0.98, (ys[i_s2] + ys[i_dec]) / 2, label, ha="center", va="center", fontsize=8.5, color=orange,
            linespacing=1.35)
    fig.savefig(OUT / "fig1_pipeline.png", dpi=300, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def fig2():
    steps = [
        ("Stages 0-2 + rules, 3.70 candidates per S1", 0.98781),
        ("+ blocking repairs, e5-small, stage 3, rules v3", 0.988609),
        ("+ two multilingual-e5-large cross-encoders", 0.989721),
        ("+ French self-training, round 1", 0.990179),
        ("+ expected-F0.5 sets + stacked rules", 0.990264),
        ("+ Qwen2.5-1.5B, bge, self-trained e5-large", 0.990545),
        ("+ round-2 labels, look-alike drop, French F0.5 sets", 0.990699),
        ("+ Qwen2.5-7B in the mix and the 7B re-check", 0.990879),
    ]
    base = 0.9875
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    ys = list(range(len(steps)))[::-1]
    prev = None
    for y, (label, v) in zip(ys, steps):
        last = label.startswith("+ Qwen2.5-7B")
        ax.barh(y, v - base, left=base, height=0.62, color="#0b4f9c" if last else "#8fb3dc",
                edgecolor="#0b4f9c", lw=0.8)
        txt = f"{v:.6f}".rstrip("0") if v != 0.98781 else "0.98781"
        if prev is not None:
            txt += f"   (+{v - prev:.6f})"
        ax.text(v + 0.00004, y, txt, va="center", fontsize=9, color=INK, fontweight="bold" if last else "normal")
        prev = v
    ax.set_yticks(ys)
    ax.set_yticklabels([s[0] for s in steps], fontsize=9.4)
    ax.set_xlim(base, 0.99158)
    ax.set_xticks([0.988, 0.989, 0.990, 0.991])
    ax.set_xticklabels(["0.988", "0.989", "0.990", "0.991"], fontsize=9)
    ax.set_xlabel("public leaderboard, macro F0.5", fontsize=9.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color="#e3e6ea", lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_score.png", dpi=300, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    print("figures written to", OUT)
