"""Take a structured outline (dict) → produce a .pptx file."""

from pathlib import Path

from pptx import Presentation

from briefdeck.render.theme import SLIDE_W, SLIDE_H, ACCENT_ROTATION
from briefdeck.render.slide_types import RENDERERS


def build_deck(outline: dict, output_path: str | Path) -> Path:
    """
    outline schema:
    {
      "title": "...",
      "subtitle": "...",
      "hero_quote": "...",
      "footer": "...",
      "slides": [
        {"type": "title", ...},
        {"type": "bullets", "title": "...", "bullets": [...]},
        ...
      ]
    }
    """
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank_layout = prs.slide_layouts[6]

    slides = outline.get("slides") or []
    if not slides:
        raise ValueError("Outline contains no slides.")

    # First slide is always title — merge outline-level fields into it
    first = slides[0]
    if first.get("type") != "title":
        slides.insert(0, {
            "type": "title",
            "title": outline.get("title", ""),
            "subtitle": outline.get("subtitle", ""),
            "hero_quote": outline.get("hero_quote", ""),
            "footer": outline.get("footer", ""),
        })
    else:
        # Backfill title-slide fields from outline if missing
        for k in ("title", "subtitle", "hero_quote", "footer"):
            first.setdefault(k, outline.get(k, ""))

    for i, slide_data in enumerate(slides):
        slide = prs.slides.add_slide(blank_layout)
        slide_type = slide_data.get("type", "bullets")
        renderer = RENDERERS.get(slide_type, RENDERERS["bullets"])
        accent = ACCENT_ROTATION[i % len(ACCENT_ROTATION)]
        try:
            renderer(slide, slide_data, accent=accent)
        except Exception as e:
            # Never crash silently per Raymond's CLAUDE.md rule —
            # but also never let one bad slide kill the deck. Add an error slide.
            from briefdeck.render.slide_types import render_bullets
            render_bullets(slide, {
                "title": f"Slide {i+1} — Render Error",
                "bullets": [
                    f"Slide type: {slide_type}",
                    f"Error: {type(e).__name__}: {e}",
                    "Other slides rendered successfully.",
                ],
                "footer": "Check the source data for this slide.",
            }, accent=accent)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return out
