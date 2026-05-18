"""BriefDeck CLI — YouTube URL → research report (.md) or briefing deck (.pptx)."""

import argparse
import sys
from datetime import date
from pathlib import Path

from briefdeck import __version__
from briefdeck.config import get_api_key, save_api_key
from briefdeck.ingest.youtube import fetch_transcript, extract_video_id
from briefdeck.render.builder import build_deck
from briefdeck.synthesize import (
    synthesize_outline, synthesize_explore,
    DEFAULT_SLIDE_COUNT, DEFAULT_QUALITY,
)


def _resolve_api_key(cli_key: str | None, save: bool) -> str:
    key = cli_key or get_api_key()
    if not key:
        sys.stderr.write(
            "ERROR: No API key found.\n"
            "  Provide one via:\n"
            "    --api-key AIza...          (Gemini — FREE tier)\n"
            "    --api-key sk-ant-...       (Anthropic)\n"
            "    --api-key sk-proj-... / sk-... (OpenAI)\n"
            "  Or set GEMINI_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY,\n"
            "  or run once with --api-key ... --save-key to persist it.\n"
        )
        sys.exit(2)
    if cli_key and save:
        save_api_key(cli_key)
        print(f"Saved API key to {Path.home() / '.briefdeck' / 'config.json'}")
    return key


def _default_output_name(url: str, mode: str) -> str:
    try:
        vid = extract_video_id(url)
    except ValueError:
        vid = "out"
    stamp = date.today().strftime("%Y%m%d")
    if mode == "report":
        return f"briefdeck_research_{vid}_{stamp}.md"
    return f"briefdeck_{vid}_{stamp}.pptx"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="briefdeck",
        description=(
            "BriefDeck — turn a YouTube video into a research report (.md) "
            "or a briefing deck (.pptx)."
        ),
    )
    parser.add_argument("source", help="YouTube URL or 11-char video ID")
    parser.add_argument("-m", "--mode", choices=["report", "deck"], default="deck",
                        help="Output mode: 'report' = markdown research brief, "
                             "'deck' = PowerPoint briefing (default: deck)")
    parser.add_argument("-t", "--topic", default="",
                        help="Topic / framing for the output (improves quality)")
    parser.add_argument("-o", "--out", default=None,
                        help="Output path (default depends on --mode)")
    parser.add_argument("-n", "--slides", type=int, default=DEFAULT_SLIDE_COUNT,
                        help=f"Deck mode only: target slide count (default: {DEFAULT_SLIDE_COUNT})")
    parser.add_argument("-q", "--quality", choices=["best", "fast"], default=DEFAULT_QUALITY,
                        help="Model quality tier (default: best). 'fast' = cheaper/quicker.")
    parser.add_argument("-a", "--angle", default="",
                        help="Optional: your specific angle/audience — adds a custom "
                             "'Your Angle' section (report) or slide (deck).")
    parser.add_argument("--api-key", default=None,
                        help="API key — Gemini (AIza...), Anthropic (sk-ant-...) or OpenAI (sk-...)")
    parser.add_argument("--save-key", action="store_true",
                        help="Persist the supplied --api-key to ~/.briefdeck/config.json")
    parser.add_argument("--version", action="version", version=f"briefdeck {__version__}")

    args = parser.parse_args(argv)

    api_key = _resolve_api_key(args.api_key, args.save_key)
    out_path = Path(args.out) if args.out else Path(_default_output_name(args.source, args.mode))

    print(f"[1/3] Fetching transcript for: {args.source}")
    transcript = fetch_transcript(args.source)
    print(f"      ✓  {transcript['segment_count']} segments  ·  "
          f"{transcript['char_count']:,} chars  ·  "
          f"{transcript['duration_sec']/60:.1f} min")

    topic = args.topic or "General briefing"

    if args.mode == "report":
        print(f"[2/3] Writing research report ({args.quality} quality, topic: {topic!r})")
        md = synthesize_explore(
            source_text=transcript["text"],
            topic=topic,
            api_key=api_key,
            quality=args.quality,
            angle=args.angle,
            source_meta={
                "url": transcript["url"],
                "video_id": transcript["video_id"],
                "duration_sec": transcript["duration_sec"],
                "char_count": transcript["char_count"],
                "segment_count": transcript["segment_count"],
            },
            report_date=date.today().strftime("%Y-%m-%d"),
        )
        print(f"      ✓  Report ready  ({len(md):,} chars  ·  ~{len(md.split()):,} words)")

        print(f"[3/3] Writing markdown → {out_path}")
        out_path.write_text(md, encoding="utf-8")
        print(f"      ✓  Saved: {out_path}")
        return 0

    # Deck mode
    print(f"[2/3] Synthesizing outline ({args.slides} slides, "
          f"{args.quality} quality, topic: {topic!r})")
    outline = synthesize_outline(
        source_text=transcript["text"],
        topic=topic,
        slide_count=args.slides,
        api_key=api_key,
        quality=args.quality,
        angle=args.angle,
    )
    print(f"      ✓  Got outline:  '{outline.get('title', '(no title)')}'  "
          f"({len(outline.get('slides', []))} slides)")

    print(f"[3/3] Rendering deck → {out_path}")
    saved = build_deck(outline, out_path)
    print(f"      ✓  Saved: {saved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
