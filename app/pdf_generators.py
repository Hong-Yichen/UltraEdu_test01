"""Generates the original, non-copyrighted Primary 5 Science coursebook PDF
used as demo content.

This is a standalone dev tool, not a runtime dependency -- its output is
committed at app/static/sample_content/p5_science_coursebook.pdf and seed.py
just copies that file into place, so `flask seed` never needs reportlab
installed. Re-run this module (requires `pip install reportlab` separately)
only if you want to regenerate/tweak the PDF's content:

    python -c "from app.pdf_generators import generate_p5_science_pdf as g; \
        g('app/static/sample_content/p5_science_coursebook.pdf')"
"""
import math
import random

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

W, H = A4
TEAL = HexColor("#2f8f7a")
INDIGO = HexColor("#4a5fd1")
VIOLET = HexColor("#8a5fc9")
INK = HexColor("#232323")
MUTED = HexColor("#666666")
LIGHT = HexColor("#eef2f0")


def _header_footer(c, chapter, page_num):
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, H - 14 * mm, "Primary 5 Science")
    c.drawRightString(W - 20 * mm, H - 14 * mm, chapter)
    c.setStrokeColor(HexColor("#dddddd"))
    c.line(20 * mm, H - 16 * mm, W - 20 * mm, H - 16 * mm)
    c.drawCentredString(W / 2, 12 * mm, f"{page_num}")
    c.setFillColor(INK)


def _wrap_text(c, text, x, y, max_width, font="Helvetica", size=10.5, leading=15, color=INK):
    c.setFont(font, size)
    c.setFillColor(color)
    words = text.split()
    line = ""
    for word in words:
        trial = (line + " " + word).strip()
        if c.stringWidth(trial, font, size) > max_width:
            c.drawString(x, y, line)
            y -= leading
            line = word
        else:
            line = trial
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def _chapter_heading(c, number, title):
    c.setFillColor(TEAL)
    c.rect(20 * mm, H - 42 * mm, 6 * mm, 10 * mm, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(30 * mm, H - 39 * mm, f"Chapter {number}: {title}")
    c.setStrokeColor(TEAL)
    c.setLineWidth(1.2)
    c.line(20 * mm, H - 46 * mm, W - 20 * mm, H - 46 * mm)


def _bullet_list(c, items, x, y, max_width, leading=14):
    for item in items:
        c.setFillColor(TEAL)
        c.circle(x + 1.2 * mm, y + 2.6, 1, stroke=0, fill=1)
        y = _wrap_text(c, item, x + 6 * mm, y, max_width - 6 * mm, leading=leading)
        y -= 2
    return y


def _arrow(c, x1, y1, x2, y2, color):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(2.4)
    c.line(x1, y1, x2, y2)
    ang = math.atan2(y2 - y1, x2 - x1)
    head = 4 * mm
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - head * math.cos(ang - math.pi / 7), y2 - head * math.sin(ang - math.pi / 7))
    p.lineTo(x2 - head * math.cos(ang + math.pi / 7), y2 - head * math.sin(ang + math.pi / 7))
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def generate_p5_science_pdf(output_path):
    """Writes an 8-page original Primary 5 Science coursebook to output_path.
    Deterministic (fixed random seed) so the page-1/Chapter-1 layout this is
    demonstrated with never shifts between runs."""
    c = pdfcanvas.Canvas(output_path, pagesize=A4)

    # ---------- Page 1: Cover ----------
    c.setFillColor(HexColor("#f4f1ff"))
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(INDIGO)
    c.rect(0, H - 90 * mm, W, 90 * mm, stroke=0, fill=1)
    c.setFillColor(HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(W / 2, H - 40 * mm, "PRIMARY 5")
    c.setFont("Helvetica-Bold", 46)
    c.drawCentredString(W / 2, H - 58 * mm, "SCIENCE")
    c.setFont("Helvetica", 14)
    c.drawCentredString(W / 2, H - 72 * mm, "Coursebook — Term 3 Edition")

    icon_y = H - 130 * mm
    c.setFillColor(TEAL)
    c.ellipse(W / 2 - 70 * mm, icon_y, W / 2 - 50 * mm, icon_y + 24 * mm, stroke=0, fill=1)
    c.setFillColor(VIOLET)
    c.rect(W / 2 - 12 * mm, icon_y, 24 * mm, 22 * mm, stroke=0, fill=1)
    c.setFillColor(INDIGO)
    c.circle(W / 2 + 62 * mm, icon_y + 12 * mm, 12 * mm, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont("Helvetica", 11)
    c.drawCentredString(W / 2, 40 * mm, "UltraEdu Learning Press")
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawCentredString(W / 2, 33 * mm, "This coursebook is original content created for the UltraEdu platform.")
    c.showPage()

    # ---------- Page 2: Table of Contents ----------
    _header_footer(c, "Contents", 2)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20 * mm, H - 34 * mm, "Table of Contents")
    toc = [
        ("Chapter 1", "Living and Non-Living Things", "3"),
        ("Chapter 2", "Life Cycles of Animals", "4"),
        ("Chapter 3", "States of Matter", "5"),
        ("Chapter 4", "Forces and Energy", "6"),
        ("Chapter 5", "The Water Cycle", "7"),
        ("", "Chapter Review Questions & Glossary", "8"),
    ]
    y = H - 55 * mm
    for label, title, page in toc:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(INDIGO)
        c.drawString(20 * mm, y, label)
        c.setFont("Helvetica", 11)
        c.setFillColor(INK)
        c.drawString(52 * mm, y, title)
        c.setFillColor(MUTED)
        c.drawRightString(W - 20 * mm, y, page)
        c.setStrokeColor(HexColor("#eeeeee"))
        c.line(20 * mm, y - 4, W - 20 * mm, y - 4)
        y -= 12 * mm
    c.showPage()

    # ---------- Page 3: Chapter 1 ----------
    _header_footer(c, "Chapter 1", 3)
    _chapter_heading(c, 1, "Living and Non-Living Things")
    y = H - 56 * mm
    y = _wrap_text(
        c,
        "All things around us can be sorted into two groups: living things and non-living things. "
        "Living things share a set of characteristics that non-living things do not have.",
        20 * mm, y, W - 40 * mm,
    )
    y -= 6
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEAL)
    c.drawString(20 * mm, y, "Characteristics of living things:")
    y -= 8
    y = _bullet_list(c, [
        "They can grow and change in size.",
        "They need food, water, and air to survive.",
        "They can respond to things around them.",
        "They can reproduce to make more of their own kind.",
        "They can move on their own, either the whole body or parts of it.",
    ], 22 * mm, y, W - 42 * mm)
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEAL)
    c.drawString(20 * mm, y, "Try it yourself:")
    y -= 8
    _wrap_text(
        c,
        "Look around your classroom. List three living things and three non-living things you can see. "
        "For each living thing, name one characteristic that shows it is alive.",
        20 * mm, y, W - 40 * mm, color=MUTED,
    )
    box_y = 60 * mm
    c.setFillColor(LIGHT)
    c.roundRect(20 * mm, box_y, 78 * mm, 32 * mm, 3 * mm, stroke=0, fill=1)
    c.roundRect(W - 98 * mm, box_y, 78 * mm, 32 * mm, 3 * mm, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(20 * mm + 39 * mm, box_y + 24 * mm, "LIVING")
    c.setFillColor(INK)
    c.setFont("Helvetica", 8)
    c.drawCentredString(20 * mm + 39 * mm, box_y + 15 * mm, "e.g. a plant, a bird, a fish")
    c.setFillColor(VIOLET)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W - 98 * mm + 39 * mm, box_y + 24 * mm, "NON-LIVING")
    c.setFillColor(INK)
    c.setFont("Helvetica", 8)
    c.drawCentredString(W - 98 * mm + 39 * mm, box_y + 15 * mm, "e.g. a rock, a chair, water")
    c.showPage()

    # ---------- Page 4: Chapter 2 ----------
    _header_footer(c, "Chapter 2", 4)
    _chapter_heading(c, 2, "Life Cycles of Animals")
    y = H - 56 * mm
    y = _wrap_text(
        c,
        "A life cycle shows the stages an animal goes through as it grows from the start of its life "
        "to when it can have young of its own. Different animals have different life cycles.",
        20 * mm, y, W - 40 * mm,
    )
    y -= 6
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEAL)
    c.drawString(20 * mm, y, "Example: Life cycle of a butterfly")

    cx, cy, r = W / 2, 100 * mm, 34 * mm
    stages = ["Egg", "Caterpillar\n(larva)", "Pupa\n(chrysalis)", "Adult\nbutterfly"]
    stage_colors = [TEAL, INDIGO, VIOLET, HexColor("#e0a530")]
    for i, (stage, col) in enumerate(zip(stages, stage_colors)):
        angle = math.pi / 2 - i * (2 * math.pi / 4)
        sx = cx + r * math.cos(angle)
        sy = cy + r * math.sin(angle)
        c.setFillColor(col)
        c.circle(sx, sy, 15 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 8)
        lines = stage.split("\n")
        ly = sy + (4 if len(lines) > 1 else 0)
        for ln in lines:
            c.drawCentredString(sx, ly, ln)
            ly -= 9
    c.setStrokeColor(MUTED)
    c.setLineWidth(1)
    c.setDash(3, 2)
    c.circle(cx, cy, r, stroke=1, fill=0)
    c.setDash()
    _wrap_text(
        c,
        "This kind of life cycle, where the young looks very different from the adult, is called "
        "complete metamorphosis. Other animals, like grasshoppers, go through incomplete metamorphosis, "
        "where the young already looks like a small version of the adult.",
        20 * mm, 55 * mm, W - 40 * mm,
    )
    c.showPage()

    # ---------- Page 5: Chapter 3 ----------
    _header_footer(c, "Chapter 3", 5)
    _chapter_heading(c, 3, "States of Matter")
    y = H - 56 * mm
    y = _wrap_text(
        c,
        "Matter is anything that takes up space and has mass. Matter can exist in three states: "
        "solid, liquid, and gas. The particles in each state are arranged differently.",
        20 * mm, y, W - 40 * mm,
    )
    y -= 10

    box_w, box_h = 52 * mm, 42 * mm
    gap = 8 * mm
    start_x = 20 * mm
    labels = ["SOLID", "LIQUID", "GAS"]
    descs = [
        "Particles packed\ntightly, fixed shape",
        "Particles close but\ncan move, takes shape\nof container",
        "Particles spread\nfar apart, fills\nany container",
    ]
    rng = random.Random(5)
    for i, (label, desc) in enumerate(zip(labels, descs)):
        bx = start_x + i * (box_w + gap)
        by = y - box_h
        c.setFillColor(LIGHT)
        c.roundRect(bx, by, box_w, box_h, 2 * mm, stroke=0, fill=1)
        c.setFillColor(INDIGO)
        if label == "SOLID":
            for row in range(4):
                for col in range(5):
                    px = bx + 6 + col * 8.5
                    py = by + box_h - 10 - row * 8
                    c.circle(px, py, 2.6, stroke=0, fill=1)
        elif label == "LIQUID":
            for _ in range(20):
                px = bx + 6 + rng.random() * (box_w - 12)
                py = by + 4 + rng.random() * (box_h * 0.55)
                c.circle(px, py, 2.6, stroke=0, fill=1)
        else:
            for _ in range(14):
                px = bx + 4 + rng.random() * (box_w - 8)
                py = by + 4 + rng.random() * (box_h - 8)
                c.circle(px, py, 2.4, stroke=0, fill=1)
        c.setFillColor(TEAL)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(bx + box_w / 2, by + box_h + 6, label)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        ly = by - 6
        for ln in desc.split("\n"):
            c.drawCentredString(bx + box_w / 2, ly, ln)
            ly -= 9

    y = y - box_h - 42
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEAL)
    c.drawString(20 * mm, y, "Changing state")
    y -= 8
    _wrap_text(
        c,
        "Matter can change from one state to another when it is heated or cooled. For example, "
        "ice (solid) melts into water (liquid) when heated, and water freezes into ice when cooled.",
        20 * mm, y, W - 40 * mm,
    )
    c.showPage()

    # ---------- Page 6: Chapter 4 ----------
    _header_footer(c, "Chapter 4", 6)
    _chapter_heading(c, 4, "Forces and Energy")
    y = H - 56 * mm
    y = _wrap_text(
        c,
        "A force is a push or a pull. Forces can make an object start moving, stop moving, speed up, "
        "slow down, or change direction. Forces can also change the shape of an object.",
        20 * mm, y, W - 40 * mm,
    )
    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEAL)
    c.drawString(20 * mm, y, "Common types of forces:")
    y -= 8
    _bullet_list(c, [
        "Gravitational force — pulls objects towards the Earth.",
        "Frictional force — acts between two surfaces in contact, opposing motion.",
        "Magnetic force — a push or pull between magnets and certain metals.",
        "Elastic force — found in stretched or compressed springs and rubber bands.",
    ], 22 * mm, y, W - 42 * mm)

    diag_y = 90 * mm
    c.setFillColor(HexColor("#cfcfcf"))
    c.roundRect(W / 2 - 15 * mm, diag_y, 30 * mm, 24 * mm, 2 * mm, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(W / 2, diag_y + 11 * mm, "BOX")

    _arrow(c, W / 2 - 55 * mm, diag_y + 12 * mm, W / 2 - 17 * mm, diag_y + 12 * mm, TEAL)
    c.setFillColor(TEAL)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2 - 40 * mm, diag_y + 17 * mm, "PUSH")
    _arrow(c, W / 2 + 55 * mm, diag_y + 12 * mm, W / 2 + 17 * mm, diag_y + 12 * mm, VIOLET)
    c.setFillColor(VIOLET)
    c.drawCentredString(W / 2 + 40 * mm, diag_y + 17 * mm, "PULL")

    _wrap_text(
        c,
        "Energy is needed to make a force act on an object. When you push a box, you use energy from "
        "your muscles. Machines use energy from fuel or electricity to produce forces that do work.",
        20 * mm, 60 * mm, W - 40 * mm,
    )
    c.showPage()

    # ---------- Page 7: Chapter 5 ----------
    _header_footer(c, "Chapter 5", 7)
    _chapter_heading(c, 5, "The Water Cycle")
    y = H - 56 * mm
    y = _wrap_text(
        c,
        "The water cycle describes how water moves between the Earth's surface and the atmosphere. "
        "It has no beginning or end — it is a continuous cycle made up of several stages.",
        20 * mm, y, W - 40 * mm,
    )
    y -= 10

    stages2 = [
        ("Evaporation", "The sun heats water in the sea, rivers and lakes, turning it into water vapour."),
        ("Condensation", "Water vapour rises, cools, and forms tiny water droplets which make clouds."),
        ("Precipitation", "When clouds get heavy with water droplets, water falls as rain, hail or snow."),
        ("Collection", "Rain collects in seas, rivers, lakes and underground, ready to evaporate again."),
    ]
    cycle_colors = [TEAL, INDIGO, VIOLET, HexColor("#e0a530")]
    sy = y
    for i, ((name, desc), col) in enumerate(zip(stages2, cycle_colors)):
        c.setFillColor(col)
        c.circle(28 * mm, sy - 4, 4.5 * mm, stroke=0, fill=1)
        c.setFillColor(HexColor("#ffffff"))
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(28 * mm, sy - 6.5, str(i + 1))
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(38 * mm, sy, name)
        sy2 = _wrap_text(c, desc, 38 * mm, sy - 8, W - 60 * mm, size=9.5, leading=12, color=INK)
        if i < len(stages2) - 1:
            c.setStrokeColor(HexColor("#cccccc"))
            c.setDash(2, 2)
            c.line(28 * mm, sy - 8, 28 * mm, sy2 - 6)
            c.setDash()
        sy = sy2 - 10
    c.showPage()

    # ---------- Page 8: Review + Glossary ----------
    _header_footer(c, "Review", 8)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, H - 34 * mm, "Chapter Review Questions")
    y = H - 48 * mm
    questions = [
        "1. Name three characteristics that all living things share.",
        "2. Draw and label the four stages of a butterfly's life cycle.",
        "3. Give one example each of a solid, a liquid, and a gas found in your kitchen.",
        "4. Describe two ways a force can change how an object moves.",
        "5. Put the four stages of the water cycle in the correct order.",
    ]
    for q in questions:
        y = _wrap_text(c, q, 20 * mm, y, W - 40 * mm)
        y -= 6

    y -= 10
    c.setStrokeColor(HexColor("#dddddd"))
    c.line(20 * mm, y, W - 20 * mm, y)
    y -= 14
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(INK)
    c.drawString(20 * mm, y, "Glossary")
    y -= 12
    glossary = [
        ("Matter", "Anything that takes up space and has mass."),
        ("Force", "A push or a pull acting on an object."),
        ("Evaporation", "The process of a liquid changing into a gas."),
        ("Metamorphosis", "The process of changing form during a life cycle."),
    ]
    for term, defn in glossary:
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(TEAL)
        c.drawString(20 * mm, y, term + ":")
        c.setFont("Helvetica", 10)
        c.setFillColor(INK)
        y = _wrap_text(c, defn, 55 * mm, y, W - 75 * mm, leading=12)
        y -= 6
    c.showPage()

    c.save()
