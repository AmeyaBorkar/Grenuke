#!/usr/bin/env python3
"""Build the Grand Finale deck on the organisers' template: finale/Grenuke_Finale_Deck.pptx.

    python finale/build_deck.py

The journey, in 11 slides (about 9 minutes). One idea per slide; the script is in the speaker notes.
Every number comes from knowledge/numbers.md. Template kept as given: the dark title and closing slides,
the white content slide (grey frame, white rounded panel, amazon logo, two-tone title, sub-header),
the embedded Ember fonts and the theme colours.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "MLC_Presentation_template.pptx"
OUT = HERE / "Grenuke_Finale_Deck.pptx"
ADD_SLIDE = Path.home() / ".claude/skills/synced/d42418a9-4952-416b-af08-af549e2a2647_89c0a8db-9e14-479f-bfbc-9452aba93f36/pptx/scripts/add_slide.py"

NAVY, ORANGE, WHITE = RGBColor(0x16, 0x1D, 0x26), RGBColor(0xFF, 0x62, 0x00), RGBColor(0xFF, 0xFF, 0xFF)
WARM, BLUEGREY, PEACH = RGBColor(0xF5, 0xF3, 0xEF), RGBColor(0xD6, 0xDC, 0xE7), RGBColor(0xFF, 0xB2, 0x8B)
MUTED, SOFT = RGBColor(0x6B, 0x72, 0x80), RGBColor(0xB8, 0xC0, 0xCC)
FONT = "Ember Modern Display Standard"
STEPS = ["Data", "Principles", "Blocking", "Pipeline", "Leaderboard", "France", "Team", "Results", "Lessons"]


# ---------- drawing helpers ----------

def text(slide, x, y, w, h, paras, size=14, color=NAVY, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=0):
    """paras: a string, or a list of paragraphs; a paragraph is a string or a list of (text, overrides) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(paras, str):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing and i:
            p.space_before = Pt(spacing)
        runs = [(para, {})] if isinstance(para, str) else para
        for t, o in runs:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name, f.size, f.bold = FONT, Pt(o.get("size", size)), o.get("bold", bold)
            f.color.rgb = o.get("color", color)
    return tb


def box(slide, x, y, w, h, fill, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius / min(w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def chevron(slide, x, y, size=0.2, color=ORANGE):
    return box(slide, x, y, size, size, color, shape=MSO_SHAPE.CHEVRON)


def dot(slide, x, y, d, fill, label=None, size=12, color=WHITE):
    c = box(slide, x, y, d, d, fill, shape=MSO_SHAPE.OVAL)
    if label:
        text(slide, x, y, d, d, label, size=size, color=color, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return c


def remove(shape):
    el = shape._element
    el.getparent().remove(el)


def frame(slide, dark, orange, sub, step, principles):
    """Fill the template's two-tone title and sub-header; add the journey tracker and the principle tag."""
    for sh in list(slide.shapes):
        if sh.shape_id == 2:
            runs = sh.text_frame.paragraphs[0].runs
            runs[0].text, runs[1].text, runs[2].text, runs[3].text = dark, " ", orange, sub
        elif sh.has_text_frame and sh.text_frame.text.startswith("Lorem") or sh.name == "Google Shape;288;p42":
            remove(sh)
    runs = []
    for i, name in enumerate(STEPS):
        if i:
            runs.append(("   ·   ", {"color": SOFT}))
        runs.append((name, {"color": ORANGE if name == step else MUTED, "bold": name == step}))
    text(slide, 0.55, 5.04, 6.0, 0.22, [runs], size=8.5)
    text(slide, 6.2, 5.04, 3.25, 0.22, [[("● ", {"color": ORANGE, "size": 7}), (principles, {})]],
         size=8.5, color=MUTED, align=PP_ALIGN.RIGHT)


def notes(slide, script):
    slide.notes_slide.notes_text_frame.text = script


# ---------- slides ----------

def title_slide(s):
    slots = [sh for sh in s.shapes if sh.shape_type == 14]           # picture placeholders, left to right
    names = sorted([sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip() == "NAME HERE"],
                   key=lambda sh: sh.left)
    slots.sort(key=lambda sh: sh.left)
    remove(slots[3]); remove(names[3])
    for i, (slot, name, who) in enumerate(zip(slots[:3], names[:3], ["AMEYA BORKAR", "AARUSH BAKSHI", "SACHI DHOKA"])):
        x = 1.79 + i * 2.24
        slot.left, slot.top, slot.width, slot.height = Inches(x), Inches(2.04), Inches(1.94), Inches(2.21)
        name.left = Inches(x + 0.03)
        name.text_frame.paragraphs[0].runs[0].text = who
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.startswith("Team"):
            sh.text_frame.paragraphs[0].runs[1].text = "Grenuke"
    text(s, 0.85, 1.62, 8.3, 0.3, "Business Entity Resolution   ·   Amazon ML Challenge 2026 Grand Finale",
         size=13, color=BLUEGREY, align=PP_ALIGN.CENTER)
    notes(s, "[0:15] Hi, we are team Grenuke: Ameya, Aarush and Sachi. In the next nine minutes we will walk you "
             "through our journey on the entity resolution challenge: what we saw in the data, what we built, what "
             "the leaderboard taught us, and what we would do next.")


def data_slide(s):
    frame(s, "First, the", "Data", "Before writing a model, we read the data. Each fact changed a design choice.",
          "Data", "Dive Deep  ·  Learn and Be Curious")
    facts = [("+23%", "more records per entity in test, but the same true matches", "The extras are look-alikes"),
             ("1 in 2", "entities share their name with another entity", "The address decides"),
             ("0", "records belong to two entities (7.6M checked)", "One owner per record"),
             ("15%", "of the test set is France, never seen in training", "Plan for the unknown")]
    for i, (num, fact, so) in enumerate(facts):
        x, y = 0.55 + (i % 2) * 3.0, 1.5 + (i // 2) * 1.72
        box(s, x, y, 2.85, 1.57, WARM)
        text(s, x + 0.2, y + 0.13, 2.5, 0.45, num, size=26, color=ORANGE, bold=True)
        text(s, x + 0.2, y + 0.62, 2.5, 0.45, fact, size=11.5)
        text(s, x + 0.2, y + 1.14, 2.5, 0.3, [[("→  ", {"color": ORANGE}), (so, {})]], size=12.5, bold=True)
    box(s, 6.65, 1.5, 2.8, 3.29, NAVY)
    text(s, 6.88, 1.72, 2.4, 0.25, "WHY WE STARTED HERE", size=9, color=ORANGE, bold=True)
    text(s, 6.88, 2.05, 2.4, 1.3, "If we don't understand the data, the model is only guessing.", size=16,
         color=WHITE, bold=True)
    stats = [("24.2M", " records"), ("3", " sources"), ("3", " countries, one unseen")]
    text(s, 6.88, 3.55, 2.4, 1.0, [[(n, {"color": ORANGE, "bold": True}), (t, {})] for n, t in stats], size=12.5,
         color=WHITE, spacing=4)
    notes(s, "[1:10] The problem reached us on Friday morning, and the first thing we did was not to train a model. "
             "We spent the first hours reading the data, because if you don't understand the data, the model is "
             "only guessing. Four facts shaped everything. The test set had about 23% more records per entity than "
             "training, but the same number of true matches, so the extra records were look-alikes, decoys. About "
             "half the entities share their name with another one, so the address has to decide. Not a single "
             "record in 7.6 million true pairs belongs to two entities, so we give every record one owner. And 15% of "
             "the test set is France, a country we had no labels for. So from the first hour, we planned for the "
             "unknown.")


def principles_slide(s):
    frame(s, "Two", "Principles", "The metric and the data shaped every choice after this.", "Principles",
          "Customer Obsession  ·  Think Big")
    box(s, 0.55, 1.5, 4.3, 3.29, NAVY)
    dot(s, 0.8, 1.72, 0.42, ORANGE, "1", size=15)
    text(s, 1.38, 1.76, 3.3, 0.4, "Decide like the metric", size=18, color=WHITE, bold=True)
    text(s, 0.8, 2.45, 3.85, 0.5, "1 false merge = 4 missed copies", size=19, color=ORANGE, bold=True)
    text(s, 0.8, 3.1, 3.85, 1.5, ["F0.5 rewards precision, so every entity gets its own best answer.",
                                   "An empty answer is often right: 5.6% of entities have no match."],
         size=12.5, color=WHITE, spacing=6)
    box(s, 5.15, 1.5, 4.3, 3.29, WARM)
    dot(s, 5.4, 1.72, 0.42, ORANGE, "2", size=15)
    text(s, 5.98, 1.76, 3.3, 0.4, "Compute where it's unsure", size=18, bold=True)
    text(s, 5.4, 2.38, 1.5, 0.6, "2.6%", size=30, color=ORANGE, bold=True)
    text(s, 6.9, 2.47, 2.3, 0.5, "of pairs ever reach a transformer model", size=12.5, bold=True)
    text(s, 5.4, 3.1, 3.85, 1.5, ["A cheap model reads every pair.",
                                   "Big models read only the pairs it is unsure about."], size=12.5, spacing=6)
    notes(s, "[0:45] Two principles came straight out of that. First, decide like the metric. F0.5 weighs a false "
             "merge as heavily as four missed copies, and merging two different businesses is exactly the mistake "
             "that hurts a real customer. So we are precision first, and each entity gets its own best set of "
             "matches, including an empty one. Second, spend compute only where the model is unsure. A cheap model "
             "reads every pair, and the expensive models read about 2.6% of them.")


def blocking_slide(s):
    frame(s, "Smart", "Blocking", "From every possible pair to 3.7 candidates per entity, keeping 98.4% of true matches.",
          "Blocking", "Invent and Simplify")
    stages = [(0.55, 1.5, 2.55, 2.45, BLUEGREY, "Every possible pair", "17 trillion", "1.7M entities × 10M records"),
              (3.5, 1.75, 2.55, 1.95, WARM, "Retrieval", "58.4M", "34 per entity · 99.1% of true matches"),
              (6.45, 1.87, 3.0, 1.71, NAVY, "Learned cut", "", "6.4M pairs · 98.4% of true matches")]
    for x, y, w, h, fill, label, num, sub in stages:
        box(s, x, y, w, h, fill)
        dark = fill == NAVY
        text(s, x + 0.22, y + 0.2, w - 0.4, 0.3, label, size=12.5, color=WHITE if dark else MUTED, bold=True)
        if num:
            text(s, x + 0.22, y + 0.55, w - 0.4, 0.6, num, size=26, bold=True)
        if sub:
            text(s, x + 0.22, y + h - 0.42, w - 0.4, 0.3, sub, size=10.5, color=WHITE if dark else NAVY)
    text(s, 6.67, 2.3, 2.6, 0.6, [[("3.7", {"size": 32, "color": ORANGE, "bold": True}),
                                  ("  per entity", {"size": 13, "color": WHITE, "bold": True})]])
    chevron(s, 3.19, 2.63); chevron(s, 6.14, 2.63)
    chips = ["Per country", "Name + address", "Name only, when the address is empty", "Fixes: OCR, web names, Hindi → Latin"]
    widths = [1.35, 1.6, 2.75, 2.9]
    x = 0.55
    for c, w in zip(chips, widths):
        box(s, x, 4.22, w, 0.42, WARM, radius=0.21)
        text(s, x, 4.22, w, 0.42, c, size=10.5, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += w + 0.1
    notes(s, "[1:00] Comparing every entity with every record would mean about 17 trillion pairs, so blocking decides "
             "the ceiling. We search each country separately, by name and address together, plus a names-only "
             "search for records whose address is empty. We repair names before searching: OCR digits, web-style "
             "names, and Hindi-to-Latin spellings that we learned from the training pairs. That retrieves 58 million "
             "pairs and keeps 99.1% of true matches. A learned cut then takes it to 3.7 candidates per entity while "
             "keeping 98.4%. We chose soft address matching over hard city or state keys, because many true copies "
             "have an empty or landmark-only address, and a hard key would lose them.")


def pipeline_slide(s):
    frame(s, "The", "Pipeline", "Cheap models read everything; expensive models only where they pay off.", "Pipeline",
          "Frugality")
    steps = [("Retrieve", "58.4M pairs", False), ("Score", "XGBoost, every pair", False),
             ("Re-read", "transformers, 1.49M unsure pairs", True), ("Decide", "best set per entity", False),
             ("Clean", "known error patterns", False), ("Re-check", "7B model, confident answers", True)]
    for i, (name, sub, heavy) in enumerate(steps):
        x = 0.55 + i * 1.52
        box(s, x, 1.62, 1.3, 0.9, NAVY if heavy else WARM)
        text(s, x, 1.62, 1.3, 0.9, name, size=14.5, color=ORANGE if heavy else NAVY, bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x, 2.62, 1.3, 0.6, sub, size=10.5, color=MUTED, align=PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            chevron(s, x + 1.33, 1.98, size=0.16)
    text(s, 0.55, 3.62, 1.7, 0.7, "2.6%", size=36, color=ORANGE, bold=True)
    text(s, 2.35, 3.6, 7.1, 0.75, ["of pairs ever reach a transformer. Scoring all 58M pairs with the 7B model would take "
                                    "about 27 GPU-hours, so it only re-checks answers we were already sure of."], size=13)
    box(s, 2.35, 4.47, 7.1, 0.12, BLUEGREY, radius=0.06)
    box(s, 2.35, 4.47, 0.19, 0.12, ORANGE, radius=0.06)
    notes(s, "[1:00] This is the whole pipeline. Retrieval gives the candidates. XGBoost, a fast tree model, scores "
             "every pair with name, address and context features. Only the pairs it is unsure about, about 1.5 "
             "million or 2.6%, are re-read by transformer models: e5, bge and Qwen. Then for each entity we pick the "
             "set of records with the highest expected F0.5, instead of one global threshold. Rules clean up known "
             "error patterns. Last, a 7B model re-checks the answers the pipeline was most confident about, because "
             "those were never read by a transformer. Scoring everything with the 7B would cost about 27 GPU-hours; "
             "using it this way costs a fraction.")


def leaderboard_slide(s):
    frame(s, "The Leaderboard", "Talked Back", "Our first scores exposed a gap our own validation could not see.",
          "Leaderboard", "Insist on the Highest Standards")
    text(s, 0.55, 1.5, 4.0, 0.62, "0.9888", size=32, bold=True)
    text(s, 0.55, 2.1, 4.0, 0.3, "our validation: US and India", size=12, color=MUTED)
    text(s, 0.55, 2.5, 4.0, 0.62, "0.9796", size=32, color=ORANGE, bold=True)
    text(s, 0.55, 3.1, 4.0, 0.3, "our first leaderboard score", size=12, color=MUTED)
    box(s, 0.55, 3.62, 4.0, 1.17, NAVY)
    text(s, 0.78, 3.78, 3.6, 0.4, [[("The gap was France: ", {}), ("≈ 0.93", {"color": ORANGE})]], size=16,
         color=WHITE, bold=True)
    text(s, 0.78, 4.27, 3.6, 0.35, "estimated: France has no labels", size=10.5, color=PEACH)
    text(s, 5.0, 1.55, 4.4, 0.35, "How we tracked it down", size=14, bold=True)
    steps = ["Ruled out the metric and our own files",
             "Split the gap by country: US and India matched our validation",
             "Read French errors: one word swapped, same address"]
    for i, t in enumerate(steps):
        y = 2.1 + i * 0.88
        dot(s, 5.0, y, 0.4, ORANGE, str(i + 1), size=13)
        text(s, 5.6, y + 0.02, 3.85, 0.7, t, size=13.5)
    notes(s, "[1:00] Our first uploads were humbling. Validation said 0.989; the leaderboard said 0.980. Instead of "
             "tuning blindly, we treated the gap as a bug report. We ruled out the metric and our files, then split "
             "the gap by country: US and India behaved exactly like our validation, so the whole gap was France, at "
             "roughly 0.93. Then we read the French mistakes by hand. The data generator makes decoys by swapping one "
             "word of the name at the same address, and in France our model was accepting them. That one finding "
             "redirected our whole second day.")


def france_slide(s):
    frame(s, "A Country We", "Never Saw", "France had no labels, so we let the data teach us, with guards.", "France",
          "Are Right, A Lot")
    cards = [("Learn its words", "Label-free word statistics told look-alike words from harmless noise."),
             ("Teach itself, carefully", "Self-training on confident French decisions. No pair ever grades itself."),
             ("Get a second opinion", "Diverse model families, then a 7B model re-checks confident answers.")]
    for i, (h, b) in enumerate(cards):
        x = 0.55 + i * 3.025
        box(s, x, 1.5, 2.85, 2.0, WARM)
        dot(s, x + 0.22, 1.7, 0.4, ORANGE, str(i + 1), size=13)
        text(s, x + 0.22, 2.25, 2.45, 0.35, h, size=14.5, bold=True)
        text(s, x + 0.22, 2.68, 2.45, 0.75, b, size=11.5)
    box(s, 0.55, 3.7, 8.9, 1.09, NAVY)
    text(s, 0.8, 3.8, 1.2, 0.3, "FRANCE", size=10, color=PEACH, bold=True)
    text(s, 0.8, 4.05, 3.4, 0.6, "≈ 0.93  →  ≈ 0.98", size=26, color=ORANGE, bold=True)
    text(s, 4.55, 3.88, 4.7, 0.8, ["Estimated: France was never measured directly.",
                                    "Self-training failed twice before we got it right."], size=12, color=WHITE,
         spacing=4)
    notes(s, "[1:10] France was the heart of the problem: no labels at all. We did three things. First, we learned "
             "its vocabulary without labels, from how words behave around moved house numbers, so French look-alike "
             "words stopped looking harmless. Second, the model taught itself: we took its most confident French "
             "decisions as training labels, with guards, and cross-fitted so no pair is ever graded by a model that "
             "saw its own label. Honestly, this failed twice before it worked. Third, a second opinion: different "
             "model families disagree four times more in France, so we combined them, and a 7B model re-checks "
             "confident answers. Our estimate is that France went from about 0.93 to about 0.98, but we say "
             "estimate, because France was never measured directly.")


def team_slide(s):
    frame(s, "Three People,", "Every Idea Tested", "We tried everything we could, and kept only what the evidence supported.",
          "Team", "Bias for Action  ·  Ownership  ·  Earn Trust")
    stats = [("329", "experiments", "177 kept · 126 dropped"), ("13", "leaderboard uploads", "each one a controlled test"),
             ("247", "decisions written down", "with the reason and the evidence")]
    for i, (n, l, sub) in enumerate(stats):
        x = 0.55 + i * 3.0
        text(s, x, 1.45, 2.8, 0.65, n, size=34, color=ORANGE, bold=True)
        text(s, x, 2.12, 2.8, 0.3, l, size=13.5, bold=True)
        text(s, x, 2.43, 2.8, 0.3, sub, size=10.5, color=MUTED)
    box(s, 0.55, 3.0, 8.9, 1.79, NAVY)
    team = [("Ameya", "Data analysis, blocking, the pipeline, France"),
            ("Aarush", "The 7B model, the re-check, the final composite"),
            ("Sachi", "Testing gates, the Qwen LoRA model, synthetic French")]
    for i, (n, f) in enumerate(team):
        x = 0.82 + i * 2.95
        text(s, x, 3.2, 2.6, 0.35, n, size=15, color=ORANGE, bold=True)
        text(s, x, 3.58, 2.6, 0.6, f, size=11.5, color=WHITE)
    text(s, 0.82, 4.4, 8.4, 0.3, "Our rule: when two ideas tie, keep the simpler one.", size=11, color=PEACH)
    notes(s, "[0:55] We were three people, and we used that to try everything. Over the weekend we ran 329 measured "
             "experiments, kept 177 and dropped 126, and every one of our 13 leaderboard uploads was designed as a "
             "test of one change. Every decision is written down with its reason and evidence. Ameya led the data "
             "analysis, blocking, the pipeline and France. Aarush trained the 7B model, built the re-check and the "
             "final composite. Sachi built our testing gates, the Qwen LoRA model and a synthetic French generator. "
             "And one rule kept us honest: when two ideas tie, keep the simpler one.")


def climb_slide(s):
    frame(s, "The", "Climb", "Every step up came from one change we understood.", "Results", "Deliver Results")
    cats = ["first\nmodel", "+ legal\nforms", "+ France\nrules", "+ stage 3,\nrepairs", "+ trans-\nformers",
            "+ self-\ntraining", "+ decision\nlayer", "+ French\nmodels", "+ France\nlayer", "+ 7B"]
    vals = [0.97608, 0.97961, 0.98781, 0.988609, 0.989721, 0.990179, 0.990264, 0.990545, 0.990699, 0.990879]
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("public leaderboard", vals)
    gf = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.45), Inches(1.42), Inches(6.35), Inches(3.5), cd)
    ch = gf.chart
    ch.has_legend = False
    ch.has_title = False
    ch.font.name, ch.font.size = FONT, Pt(8.5)
    ch.font.color.rgb = MUTED
    va = ch.value_axis
    va.minimum_scale, va.maximum_scale, va.major_unit = 0.975, 0.992, 0.005
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = RGBColor(0xE5, 0xE7, 0xEB)
    va.tick_labels.number_format, va.tick_labels.number_format_is_linked = "0.000", False
    va.format.line.fill.background()
    ca = ch.category_axis
    ca.format.line.color.rgb = SOFT
    ser = ch.plots[0].series[0]
    ser.smooth = False
    ser.format.line.color.rgb = ORANGE
    ser.format.line.width = Pt(2.5)
    ser.marker.style, ser.marker.size = XL_MARKER_STYLE.CIRCLE, 7
    ser.marker.format.fill.solid()
    ser.marker.format.fill.fore_color.rgb = NAVY
    ser.marker.format.line.fill.background()
    for i, label in [(0, "0.976"), (2, "0.988"), (4, "0.990"), (9, "0.9909")]:
        dl = ser.points[i].data_label
        dl.has_text_frame = True
        dl.text_frame.text = label
        for r in dl.text_frame.paragraphs[0].runs:
            r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(10), True, NAVY, FONT
        dl.position = XL_LABEL_POSITION.ABOVE if i else XL_LABEL_POSITION.RIGHT
    box(s, 7.0, 1.5, 2.45, 3.29, NAVY)
    text(s, 7.22, 1.7, 2.1, 0.25, "FINAL, PUBLIC LEADERBOARD", size=8.5, color=PEACH, bold=True)
    text(s, 7.22, 1.98, 2.1, 0.55, "0.990879", size=24, color=ORANGE, bold=True)
    box(s, 7.22, 2.72, 2.0, 0.02, RGBColor(0x3A, 0x45, 0x55), radius=0.01)
    text(s, 7.22, 2.9, 2.1, 0.7, [[("2nd", {"size": 34, "bold": True}), ("  of the Top 10", {"size": 13})]], color=WHITE)
    text(s, 7.22, 3.65, 2.1, 0.3, "among 32,000+ teams", size=11.5, color=PEACH)
    text(s, 7.22, 4.2, 2.1, 0.45, "local validation 0.9913, without France", size=10, color=SOFT)
    notes(s, "[0:50] Here is the climb on the public leaderboard, from 0.976 to 0.9909. The biggest single jump came "
             "from the France fixes on day two. Transformers on the uncertain pairs added about a thousandth, "
             "self-training on France half of that, and the 7B parts the last two ten-thousandths. Each point is one "
             "upload, and each one changed one thing we understood. Our final submission scored 0.990879, and the "
             "final ranking put us second of the Top 10, among more than 32,000 teams. Our local validation says "
             "0.9913, but it cannot include France, so we quote the leaderboard.")


def lessons_slide(s):
    frame(s, "What We", "Learned", "And what we would do next, at Amazon scale.", "Lessons",
          "Success and Scale Bring Broad Responsibility")
    box(s, 0.55, 1.5, 4.3, 3.29, WARM)
    text(s, 0.8, 1.7, 3.8, 0.35, "Lessons", size=15, color=ORANGE, bold=True)
    left = [("Read the data first. ", "It drove every good decision."),
            ("Doubt your own estimates. ", "Ours shared our model's blind spots."),
            ("Diversity beats one strong model, ", "most of all in a country you have never seen.")]
    text(s, 0.8, 2.15, 3.85, 2.5, [[(a, {"bold": True}), (b, {})] for a, b in left], size=13, spacing=12)
    box(s, 5.15, 1.5, 4.3, 3.29, NAVY)
    text(s, 5.4, 1.7, 3.8, 0.35, "Next, at Amazon scale", size=15, color=ORANGE, bold=True)
    right = [("Label 500 French pairs ", "where our models disagree most."),
             ("Shard by country and region; ", "the same cascade runs on each shard."),
             ("Keep candidates near 3 to 4 per entity: ", "every later step pays per pair.")]
    text(s, 5.4, 2.15, 3.85, 2.5, [[(a, {"bold": True}), (b, {})] for a, b in right], size=13, color=WHITE, spacing=12)
    notes(s, "[0:50] Three lessons. Read the data first; every good decision we made traced back to it. Doubt your own "
             "estimates: our label-free estimates for France were built from our own model's probabilities, so they "
             "shared its blind spots, and the leaderboard corrected us. And diversity beats one strong model, "
             "especially for a country you have never seen. With more time and at Amazon scale, we would label a few "
             "hundred French pairs where our models disagree, shard the same cascade by country and region, and keep "
             "the candidates per entity small, because every later step pays per candidate pair.")


def closing_slide(s):
    pill = next(sh for sh in s.shapes if sh.name == "Google Shape;572;p58")
    text(s, 0.53, 1.15, 8.95, 0.9, [[("Thank ", {}), ("You", {"color": ORANGE})]], size=44, color=WHITE, bold=True,
         align=PP_ALIGN.CENTER)
    text(s, 1.0, 2.35, 8.0, 0.4, "Read the data.   Decide like the metric.   Spend compute where it matters.",
         size=15, color=BLUEGREY, align=PP_ALIGN.CENTER)
    pill.fill.solid()
    pill.fill.fore_color.rgb = ORANGE
    pill.line.fill.background()
    pill.text_frame.text = "Questions welcome"
    for r in pill.text_frame.paragraphs[0].runs:
        r.font.name, r.font.size, r.font.bold, r.font.color.rgb = FONT, Pt(12), True, WHITE
    pill.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    pill.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    text(s, 0.53, 4.1, 8.95, 0.3, "Team Grenuke  ·  Ameya Borkar  ·  Aarush Bakshi  ·  Sachi Dhoka", size=11,
         color=SOFT, align=PP_ALIGN.CENTER)
    notes(s, "[0:10] To sum up: read the data, decide the way the metric scores, and spend compute where it matters. "
             "Thank you, we are happy to take your questions.")


def main() -> int:
    work = OUT.with_suffix(".tmp.pptx")
    shutil.copy(TEMPLATE, work)
    for _ in range(8):                      # nine content slides from the template's white slide
        subprocess.run([sys.executable, str(ADD_SLIDE), str(work), "slide2.xml", "--after", "slide2.xml"],
                       check=True, capture_output=True)
    prs = Presentation(work)
    sl = list(prs.slides)
    builders = [title_slide, data_slide, principles_slide, blocking_slide, pipeline_slide, leaderboard_slide,
                france_slide, team_slide, climb_slide, lessons_slide, closing_slide]
    assert len(sl) == len(builders), len(sl)
    for slide, build in zip(sl, builders):
        build(slide)
    prs.save(OUT)
    work.unlink()
    print(f"{OUT.name}: {len(sl)} slides")
    return 0


if __name__ == "__main__":
    sys.exit(main())
