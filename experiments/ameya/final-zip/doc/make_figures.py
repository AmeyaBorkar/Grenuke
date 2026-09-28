"""Figures for Documentation_template.md, drawn at print size (6.6 in wide) so the fonts stay >= 8 pt in the PDF.

fig1_pipeline.png : the pipeline, left to right, titles only (the numbers are in the text)
fig2_strategy.png : the solution strategy, challenge -> what we did -> measured gain
fig3_score.png    : the public leaderboard score after each submission step
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
INK, SUB, ACC = "#1b1f24", "#46505b", "#0b4f9c"
FILL = {"block": ("#dbe9f7", "#5b8fc7"), "xgb": ("#dff1e2", "#5da56a"), "ce": ("#ece3f5", "#8d6bb7"),
        "dec": ("#fde9d4", "#d98b3a"), "llm": ("#f9dde0", "#c85a66")}


def box(ax, xc, yc, w, h, kind, title, sub):
    fc, ec = FILL[kind]
    ax.add_patch(FancyBboxPatch((xc - w / 2, yc - h / 2), w, h, boxstyle="round,pad=0.0,rounding_size=0.08",
                                fc=fc, ec=ec, lw=1.3))
    ax.text(xc, yc + 0.09, title, ha="center", va="center", fontsize=9.2, fontweight="bold", color=INK)
    ax.text(xc, yc - 0.12, sub, ha="center", va="center", fontsize=8.2, color=SUB)


def arrow(ax, p, q, color="#55606b", ls="-", lw=1.3):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, linestyle=ls,
                                                    shrinkA=0, shrinkB=0, mutation_scale=11))


def fig1():
    W, H = 6.4, 1.9
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    bw, bh, y, gap = 1.1, 0.54, 0.86, 0.2
    xs = [0.05 + bw / 2 + i * (bw + gap) for i in range(5)]
    spec = [("block", "Blocking", "per country"), ("xgb", "Candidates", "XGBoost 0-1"),
            ("xgb", "Pair scores", "XGBoost 2-3"), ("dec", "Decision", "best F0.5 set"),
            ("llm", "7B re-check", "confident pairs")]
    for x, (k, t, s) in zip(xs, spec):
        box(ax, x, y, bw, bh, k, t, s)
    for a, b in zip(xs, xs[1:]):
        arrow(ax, (a + bw / 2, y), (b - bw / 2, y))
    # cross-encoders read only the uncertain pairs between the two XGBoost blocks
    cx, cy = (xs[1] + xs[2]) / 2, 1.6
    box(ax, cx, cy, 1.62, 0.48, "ce", "Cross-encoders", "uncertain pairs only")
    arrow(ax, (xs[1], y + bh / 2), (cx - 0.42, cy - 0.24))
    arrow(ax, (cx + 0.42, cy - 0.24), (xs[2], y + bh / 2))
    # France self-training loop, below
    orange, dash = "#c96a12", (0, (4, 2.5))
    yl = 0.26
    ax.plot([xs[3], xs[3]], [y - bh / 2, yl], color=orange, lw=1.4, ls=dash)
    ax.plot([xs[3], xs[2]], [yl, yl], color=orange, lw=1.4, ls=dash)
    arrow(ax, (xs[2], yl), (xs[2], y - bh / 2), color=orange, ls=dash, lw=1.4)
    ax.text((xs[2] + xs[3]) / 2, yl - 0.12, "France: our own decisions become pseudo-labels", fontsize=8.3,
            color=orange, ha="center", va="top")
    fig.savefig(OUT / "fig1_pipeline.png", dpi=300, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def fig2():
    steps = [("XGBoost\n+ rules", 0.98781), ("+ stage 3,\nrepairs", 0.988609), ("+ e5-large\nencoders", 0.989721),
             ("+ French\nself-training", 0.990179), ("+ F0.5\nsets", 0.990264), ("+ Qwen 1.5B\n+ bge", 0.990545),
             ("+ round 2\nFrance", 0.990699), ("+ Qwen 7B\n+ re-check", 0.990879)]
    xs = list(range(1, len(steps) + 1))
    ys = [v for _, v in steps]
    fig, ax = plt.subplots(figsize=(6.4, 2.0))
    ax.plot(xs, ys, color="#8fb3dc", lw=2, zorder=1)
    ax.scatter(xs[:-1], ys[:-1], s=34, color="#5b8fc7", zorder=2)
    ax.scatter(xs[-1:], ys[-1:], s=60, color=ACC, zorder=3)
    for x, v in zip(xs, ys):
        last = x == xs[-1]
        ax.text(x, v + 0.00017, f"{v:.6f}".rstrip("0") if v != 0.98781 else "0.98781", ha="center", va="bottom",
                fontsize=8.4, color=ACC if last else INK, fontweight="bold" if last else "normal")
    ax.set_xticks(xs)
    ax.set_xticklabels([s for s, _ in steps], fontsize=8.2, color=INK)
    ax.set_xlim(0.5, len(steps) + 0.5)
    ax.set_ylim(0.9874, 0.99135)
    ax.set_yticks([0.988, 0.989, 0.990, 0.991])
    ax.set_yticklabels(["0.988", "0.989", "0.990", "0.991"], fontsize=8.2)
    ax.set_ylabel("public LB, macro F0.5", fontsize=8.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e3e6ea", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0, pad=4)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_score.png", dpi=300, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def fig_strategy():
    """Challenge -> what we did -> measured gain, one row per strategic choice."""
    W = 6.4
    rows = [
        (("58M pairs to score,", "limited compute"),
         ("Cascade: XGBoost on every pair,", "cross-encoders on the 1.49M uncertain"), ("+0.0011 LB",)),
        (("F0.5 punishes wrong", "merges, scored per S1"),
         ("Pick each S1's whole set", "by expected F0.5"), ("+0.000048", "local")),
        (("France has no labels", "(test set only)"),
         ("Guarded self-training, 2 rounds", "cross-fitted, on our own decisions"), ("+0.00046 and", "+0.00015 LB")),
        (("Decoys the features", "accept with confidence"),
         ("Qwen2.5-7B re-check", "of the predictions with p1 > 0.99"), ("about", "+0.00011 LB")),
    ]
    rh, gap, top = 0.46, 0.1, 0.28
    H = top + len(rows) * (rh + gap)
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    lx, lw, rx, rw, gx = 0.02, 1.75, 2.03, 3.0, 5.76
    for x, t in ((lx + lw / 2, "What makes it hard"), (rx + rw / 2, "What we did"), (gx, "Measured gain")):
        ax.text(x, H - 0.12, t, ha="center", va="center", fontsize=9.0, fontweight="bold", color=INK)
    for i, (left, right, gain) in enumerate(rows):
        yc = H - top - i * (rh + gap) - rh / 2
        ax.add_patch(FancyBboxPatch((lx, yc - rh / 2), lw, rh, boxstyle="round,pad=0.0,rounding_size=0.07",
                                    fc="#f4e6e1", ec="#c47a64", lw=1.2))
        ax.add_patch(FancyBboxPatch((rx, yc - rh / 2), rw, rh, boxstyle="round,pad=0.0,rounding_size=0.07",
                                    fc="#dbe9f7", ec="#5b8fc7", lw=1.2))
        arrow(ax, (lx + lw + 0.03, yc), (rx - 0.03, yc))
        ax.text(lx + lw / 2, yc + 0.09, left[0], ha="center", va="center", fontsize=8.3, color=INK)
        ax.text(lx + lw / 2, yc - 0.1, left[1], ha="center", va="center", fontsize=8.3, color=INK)
        ax.text(rx + rw / 2, yc + 0.09, right[0], ha="center", va="center", fontsize=8.5, color=INK, fontweight="bold")
        ax.text(rx + rw / 2, yc - 0.1, right[1], ha="center", va="center", fontsize=8.3, color=INK)
        if len(gain) == 1:
            ax.text(gx, yc, gain[0], ha="center", va="center", fontsize=8.6, color=ACC, fontweight="bold")
        else:
            ax.text(gx, yc + 0.095, gain[0], ha="center", va="center", fontsize=8.6, color=ACC, fontweight="bold")
            ax.text(gx, yc - 0.1, gain[1], ha="center", va="center", fontsize=8.6, color=ACC, fontweight="bold")
    fig.savefig(OUT / "fig2_strategy.png", dpi=300, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig_strategy()
    fig2()
    print("figures written to", OUT)
