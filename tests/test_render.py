"""Smoke test for the renderer. No API key needed."""

import tempfile
from pathlib import Path

from briefdeck.render.builder import build_deck


SAMPLE_OUTLINE = {
    "title": "TEST DECK",
    "subtitle": "Smoke test for BriefDeck render layer",
    "hero_quote": "If this opens cleanly in PowerPoint, the renderer works.",
    "footer": "01 Jan 2026 — BriefDeck smoke test",
    "slides": [
        {
            "type": "title",
            "title": "TEST DECK",
            "subtitle": "Smoke test for BriefDeck render layer",
            "hero_quote": "If this opens cleanly in PowerPoint, the renderer works.",
            "footer": "01 Jan 2026 — BriefDeck smoke test",
        },
        {
            "type": "stat_shock",
            "title": "The Hook Statistic",
            "preamble": "Anchor stat for the briefing.",
            "stat": "40%+",
            "stat_label": "of agentic AI projects will be killed by end of 2027",
            "reasons": [
                {"label": "COST", "body": "Spend balloons before value appears."},
                {"label": "UNCLEAR VALUE", "body": "Nobody can describe 'good'."},
                {"label": "INADEQUATE RISK", "body": "No audit trails or bounds."},
            ],
        },
        {
            "type": "bullets",
            "title": "Core Thesis",
            "bullets": [
                "AI investment is a workflow question, not an AI question.",
                "Every workflow has only 5 levers: Automate / Build / Buy / Hire / Wait.",
                "You cannot pick a lever until you can describe the workflow.",
                "Do not automate what you cannot describe.",
            ],
            "footer": "Source: Nate B Jones, May 2026.",
        },
        {
            "type": "two_col",
            "title": "Build vs Buy",
            "left": {"label": "BUILD WHEN", "items": [
                "Work is unique to your company",
                "Lots of edge cases",
                "You can describe 'good'",
                "You have evaluation discipline",
            ]},
            "right": {"label": "BUY WHEN", "items": [
                "Work is generic / commodity",
                "Market solution is mature",
                "80-90% workflow overlap with vendor",
                "You only need primitives, not a full pipeline",
            ]},
        },
        {
            "type": "matrix_2x2",
            "title": "The Investment Matrix",
            "x_label": "HOW SPECIFIC IS THIS WORK TO YOUR COMPANY?",
            "y_label": "MARKET\nMATURITY",
            "quadrants": [
                {"label": "BUY whole solution", "body": "Workday. Stripe. Standard help desk."},
                {"label": "BUY primitives, BUILD workflow", "body": "Where ambitious teams live."},
                {"label": "PROTOTYPE or WAIT", "body": "Category still defining itself."},
                {"label": "BUILD — your moat", "body": "Refinery OS lives here."},
            ],
            "footer": "Hiring cuts across all four quadrants.",
        },
        {
            "type": "quote",
            "title": "The Golden Rule",
            "quote": "Do not automate what you cannot describe.",
            "attribution": "Nate B Jones, AI News & Strategy Daily",
        },
        {
            "type": "takeaway",
            "title": "SO WHAT  —  3 TAKEAWAYS",
            "items": [
                {"label": "WHAT THIS IS",
                 "body": "A workflow-first framework for allocating capital across AI investments."},
                {"label": "BIGGEST OPPORTUNITY",
                 "body": "Speak this vocabulary in customer calls — bypass 'what is your AI?' objections."},
                {"label": "ONE THING TO DO NEXT",
                 "body": "Lift the 40% statistic and the 'do not automate what you cannot describe' line into the pitch deck this week."},
            ],
        },
    ],
}


def test_smoke_render():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "smoke.pptx"
        saved = build_deck(SAMPLE_OUTLINE, out_path)
        assert saved.exists(), "PPTX was not written."
        assert saved.stat().st_size > 5_000, "PPTX file looks empty / corrupted."
        print(f"OK — wrote {saved}  ({saved.stat().st_size:,} bytes)")


if __name__ == "__main__":
    test_smoke_render()
