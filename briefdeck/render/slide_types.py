"""Slide-type renderers. Each function takes (slide, data, accent_color) and draws."""

from pptx.util import Inches
from pptx.enum.text import PP_ALIGN

from briefdeck.render.theme import (
    NAVY, NAVY_DARK, GOLD, WHITE, LIGHT_GREY, DARK_GREY, MID_GREY, PALE_BLUE,
    RED_DARK,
    add_text_box, add_rect, add_multi_line, add_header_bar, add_gold_borders,
    set_bg, truncate,
)


def render_title(slide, data, accent=GOLD):
    """data: {title, subtitle, hero_quote, footer}"""
    set_bg(slide, NAVY)
    add_gold_borders(slide)

    add_text_box(slide, data.get("title", ""), Inches(1), Inches(1.0),
                 Inches(11.3), Inches(1.2),
                 font_size=52, bold=True, color=GOLD, align=PP_ALIGN.CENTER)

    if data.get("subtitle"):
        add_text_box(slide, data["subtitle"], Inches(1), Inches(2.3),
                     Inches(11.3), Inches(0.7),
                     font_size=22, color=WHITE, align=PP_ALIGN.CENTER)

    if data.get("hero_quote"):
        add_rect(slide, Inches(1.5), Inches(3.5), Inches(10.3), Inches(2.2), NAVY_DARK)
        add_rect(slide, Inches(1.5), Inches(3.5), Inches(0.1), Inches(2.2), GOLD)
        add_text_box(slide, "The line to remember:",
                     Inches(1.75), Inches(3.65), Inches(10), Inches(0.4),
                     font_size=12, bold=True, color=GOLD)
        add_text_box(slide, f'"{data["hero_quote"]}"',
                     Inches(1.75), Inches(4.05), Inches(10), Inches(1.5),
                     font_size=20, italic=True, color=WHITE, align=PP_ALIGN.CENTER)

    if data.get("footer"):
        add_text_box(slide, data["footer"], Inches(1), Inches(6.85),
                     Inches(11.3), Inches(0.4),
                     font_size=11, color=MID_GREY, align=PP_ALIGN.CENTER)


def render_stat_shock(slide, data, accent=GOLD):
    """data: {title, stat, stat_label, reasons: [{label, body}]}"""
    set_bg(slide, LIGHT_GREY)
    add_rect(slide, Inches(0), Inches(0), Inches(0.08), Inches(7.5), NAVY)
    add_header_bar(slide, data.get("title", "").upper())

    if data.get("preamble"):
        add_text_box(slide, data["preamble"], Inches(0.5), Inches(1.2),
                     Inches(12.3), Inches(0.4),
                     font_size=14, italic=True, color=DARK_GREY, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(2.5), Inches(1.8), Inches(8.3), Inches(2.4), RED_DARK)
    add_text_box(slide, str(data.get("stat", "")),
                 Inches(2.5), Inches(1.85), Inches(8.3), Inches(1.4),
                 font_size=80, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text_box(slide, data.get("stat_label", ""),
                 Inches(2.5), Inches(3.25), Inches(8.3), Inches(0.8),
                 font_size=16, color=WHITE, align=PP_ALIGN.CENTER, bold=True)

    reasons = (data.get("reasons") or [])[:3]
    if reasons:
        for i, r in enumerate(reasons):
            lft = Inches(0.5) + i * Inches(4.2)
            top = Inches(4.7)
            add_rect(slide, lft, top, Inches(4.0), Inches(2.0), WHITE)
            add_rect(slide, lft, top, Inches(4.0), Inches(0.5), accent)
            add_text_box(slide, truncate(r.get("label", ""), 60),
                         lft + Inches(0.15), top + Inches(0.08),
                         Inches(3.7), Inches(0.4),
                         font_size=12, bold=True, color=WHITE)
            add_text_box(slide, truncate(r.get("body", ""), 200),
                         lft + Inches(0.15), top + Inches(0.65),
                         Inches(3.7), Inches(1.3),
                         font_size=11, color=DARK_GREY)


def render_definition(slide, data, accent=GOLD):
    """data: {title, term, definition, source}"""
    set_bg(slide, LIGHT_GREY)
    add_rect(slide, Inches(0), Inches(0), Inches(0.08), Inches(7.5), NAVY)
    add_header_bar(slide, data.get("title", "").upper())

    add_rect(slide, Inches(1), Inches(2.0), Inches(11.3), Inches(3.5), WHITE)
    add_rect(slide, Inches(1), Inches(2.0), Inches(0.12), Inches(3.5), accent)
    add_text_box(slide, data.get("term", ""), Inches(1.3), Inches(2.2),
                 Inches(10.8), Inches(0.7),
                 font_size=24, bold=True, color=NAVY)
    add_text_box(slide, data.get("definition", ""),
                 Inches(1.3), Inches(3.05), Inches(10.8), Inches(2.3),
                 font_size=14, color=DARK_GREY, italic=True)

    if data.get("source"):
        add_text_box(slide, f"— {data['source']}",
                     Inches(1), Inches(6.5), Inches(11.3), Inches(0.4),
                     font_size=11, italic=True, color=MID_GREY, align=PP_ALIGN.CENTER)


def render_bullets(slide, data, accent=GOLD):
    """data: {title, bullets: [str], footer}"""
    set_bg(slide, LIGHT_GREY)
    add_rect(slide, Inches(0), Inches(0), Inches(0.08), Inches(7.5), NAVY)
    add_header_bar(slide, data.get("title", "").upper())

    bullets = [f"•  {truncate(b, 130)}" for b in (data.get("bullets") or [])[:10]]
    add_multi_line(slide, bullets, Inches(0.6), Inches(1.4),
                   Inches(12.1), Inches(5.5),
                   font_size=14, color=DARK_GREY, line_spacing=8)

    if data.get("footer"):
        add_text_box(slide, data["footer"], Inches(0.4), Inches(7.1),
                     Inches(12.5), Inches(0.3),
                     font_size=11, italic=True, color=MID_GREY, align=PP_ALIGN.CENTER)


def render_two_col(slide, data, accent=GOLD):
    """data: {title, left: {label, items}, right: {label, items}}"""
    from briefdeck.render.theme import LIGHT_GREEN, GREEN, LIGHT_RED, RED_DARK
    set_bg(slide, LIGHT_GREY)
    add_rect(slide, Inches(0), Inches(0), Inches(0.08), Inches(7.5), NAVY)
    add_header_bar(slide, data.get("title", "").upper())

    left = data.get("left") or {}
    right = data.get("right") or {}

    # Left panel — green
    add_rect(slide, Inches(0.4), Inches(1.15), Inches(6.2), Inches(5.9), LIGHT_GREEN)
    add_rect(slide, Inches(0.4), Inches(1.15), Inches(6.2), Inches(0.5), GREEN)
    add_text_box(slide, truncate(left.get("label", "PROS"), 40),
                 Inches(0.6), Inches(1.23), Inches(5.8), Inches(0.4),
                 font_size=15, bold=True, color=WHITE)
    add_multi_line(slide, [f"✓  {truncate(x, 110)}" for x in (left.get("items") or [])[:10]],
                   Inches(0.6), Inches(1.85), Inches(5.8), Inches(5.0),
                   font_size=12, color=DARK_GREY, line_spacing=5)

    # Right panel — red
    add_rect(slide, Inches(6.9), Inches(1.15), Inches(6.2), Inches(5.9), LIGHT_RED)
    add_rect(slide, Inches(6.9), Inches(1.15), Inches(6.2), Inches(0.5), RED_DARK)
    add_text_box(slide, truncate(right.get("label", "CONS"), 40),
                 Inches(7.1), Inches(1.23), Inches(5.8), Inches(0.4),
                 font_size=15, bold=True, color=WHITE)
    add_multi_line(slide, [f"×  {truncate(x, 110)}" for x in (right.get("items") or [])[:10]],
                   Inches(7.1), Inches(1.85), Inches(5.8), Inches(5.0),
                   font_size=12, color=DARK_GREY, line_spacing=5)


def render_matrix_2x2(slide, data, accent=GOLD):
    """data: {title, x_label, y_label, quadrants: [{label, body, color_hint}] (4 items)}"""
    from briefdeck.render.theme import (
        LIGHT_GREEN, GREEN, LIGHT_AMBER, LIGHT_BLUE, BLUE, LIGHT_RED, RED_DARK,
    )
    set_bg(slide, WHITE)
    add_header_bar(slide, data.get("title", "").upper())

    quads = (data.get("quadrants") or [])[:4]
    while len(quads) < 4:
        quads.append({"label": "", "body": ""})

    palette = [(LIGHT_GREEN, GREEN), (LIGHT_AMBER, GOLD),
               (LIGHT_BLUE, BLUE), (LIGHT_RED, RED_DARK)]

    add_text_box(slide, truncate(data.get("x_label", ""), 80),
                 Inches(0.5), Inches(1.2), Inches(12.3), Inches(0.4),
                 font_size=12, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    positions = [(Inches(1.7), Inches(2.1)),
                 (Inches(7.5), Inches(2.1)),
                 (Inches(1.7), Inches(4.5)),
                 (Inches(7.5), Inches(4.5))]

    for i, (q, pos, (bg, fg)) in enumerate(zip(quads, positions, palette)):
        lft, top = pos
        w = Inches(5.6) if i % 2 == 0 else Inches(5.4)
        add_rect(slide, lft, top, w, Inches(2.3), bg)
        add_rect(slide, lft, top, w, Inches(0.5), fg)
        add_text_box(slide, truncate(q.get("label", ""), 60),
                     lft + Inches(0.15), top + Inches(0.08),
                     w - Inches(0.3), Inches(0.4),
                     font_size=13, bold=True, color=WHITE)
        add_text_box(slide, truncate(q.get("body", ""), 220),
                     lft + Inches(0.15), top + Inches(0.65),
                     w - Inches(0.3), Inches(1.5),
                     font_size=11, color=DARK_GREY)

    if data.get("y_label"):
        add_text_box(slide, data["y_label"],
                     Inches(0.4), Inches(3.3), Inches(1.2), Inches(1.0),
                     font_size=11, bold=True, color=NAVY, align=PP_ALIGN.CENTER)

    if data.get("footer"):
        add_text_box(slide, data["footer"],
                     Inches(0.4), Inches(7.05), Inches(12.5), Inches(0.4),
                     font_size=11, italic=True, color=NAVY,
                     align=PP_ALIGN.CENTER, bold=True)


def render_quote(slide, data, accent=GOLD):
    """data: {title, quote, attribution}"""
    set_bg(slide, NAVY)
    add_gold_borders(slide)

    if data.get("title"):
        add_text_box(slide, data["title"].upper(),
                     Inches(0.5), Inches(0.5), Inches(12.3), Inches(0.7),
                     font_size=22, bold=True, color=GOLD, align=PP_ALIGN.CENTER)

    add_rect(slide, Inches(1.5), Inches(2.0), Inches(10.3), Inches(3.5), NAVY_DARK)
    add_rect(slide, Inches(1.5), Inches(2.0), Inches(0.12), Inches(3.5), GOLD)
    add_text_box(slide, f'"{data.get("quote", "")}"',
                 Inches(1.75), Inches(2.3), Inches(10), Inches(2.8),
                 font_size=22, italic=True, color=WHITE, align=PP_ALIGN.CENTER)

    if data.get("attribution"):
        add_text_box(slide, f"— {data['attribution']}",
                     Inches(1), Inches(5.8), Inches(11.3), Inches(0.5),
                     font_size=14, italic=True, color=GOLD, align=PP_ALIGN.CENTER)


def render_takeaway(slide, data, accent=GOLD):
    """data: {title, items: [{label, body}]} — expects exactly 3 items"""
    set_bg(slide, NAVY)
    add_gold_borders(slide)

    add_text_box(slide, (data.get("title") or "SO WHAT  —  3 TAKEAWAYS").upper(),
                 Inches(0.5), Inches(0.4), Inches(12.3), Inches(0.7),
                 font_size=30, bold=True, color=GOLD, align=PP_ALIGN.CENTER)

    items = (data.get("items") or [])[:3]
    while len(items) < 3:
        items.append({"label": "", "body": ""})

    for i, it in enumerate(items):
        top = Inches(1.4) + i * Inches(1.75)
        add_rect(slide, Inches(0.5), top, Inches(12.3), Inches(1.55), NAVY_DARK)
        add_rect(slide, Inches(0.5), top, Inches(0.08), Inches(1.55), GOLD)
        add_text_box(slide, f"{i+1}.  {truncate(it.get('label', ''), 60).upper()}",
                     Inches(0.75), top + Inches(0.15),
                     Inches(12.0), Inches(0.5),
                     font_size=15, bold=True, color=GOLD)
        add_text_box(slide, truncate(it.get("body", ""), 350),
                     Inches(0.75), top + Inches(0.7),
                     Inches(12.0), Inches(0.85),
                     font_size=12, color=WHITE)

    if data.get("footer"):
        add_text_box(slide, data["footer"],
                     Inches(0.5), Inches(7.0), Inches(12.3), Inches(0.3),
                     font_size=11, italic=True, color=MID_GREY, align=PP_ALIGN.CENTER)


# ─── Dispatch table ───────────────────────────────────────────────────────────
RENDERERS = {
    "title": render_title,
    "stat_shock": render_stat_shock,
    "definition": render_definition,
    "bullets": render_bullets,
    "two_col": render_two_col,
    "matrix_2x2": render_matrix_2x2,
    "quote": render_quote,
    "takeaway": render_takeaway,
}
