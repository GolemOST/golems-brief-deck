"""LLM call: source text → structured deck outline (JSON).

Auto-detects provider from the API key prefix:
  AIza...                     → Google Gemini   (FREE tier, no credit card needed)
  sk-ant-...                  → Anthropic Claude
  sk-proj-... or sk-...       → OpenAI
"""

import json
import re
from pathlib import Path


# ─── Model maps ────────────────────────────────────────────────────────────────
# Two quality tiers. Default is "best" — much better outputs than the cheap tier.
MODELS = {
    "best": {
        "anthropic": "claude-sonnet-4-6",
        "openai":    "gpt-4o",
        # Gemini 2.5-pro is PAID-only on Gemini API (free-tier quota = 0).
        # Default to 2.5-flash, which is on the free tier AND high quality.
        # Paid users can override via --model gemini-2.5-pro.
        "gemini":    "gemini-2.5-flash",
    },
    "fast": {
        "anthropic": "claude-haiku-4-5-20251001",
        "openai":    "gpt-4o-mini",
        "gemini":    "gemini-2.0-flash-001",
    },
}

# Gemini-only fallback chain. If the user's chosen model is unavailable on
# their key (different keys have different access), we try these in order.
# All are JSON-mode capable and on the free tier.
GEMINI_FALLBACKS = (
    "gemini-2.5-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
)
DEFAULT_QUALITY = "best"
DEFAULT_MAX_TOKENS = 6000
DEFAULT_SLIDE_COUNT = 14


def model_for(quality: str, provider: str) -> str:
    """Resolve quality tier + provider → concrete model ID."""
    tier = MODELS.get(quality) or MODELS[DEFAULT_QUALITY]
    return tier.get(provider) or MODELS[DEFAULT_QUALITY][provider]


# Back-compat exports (older callers may import these)
DEFAULT_ANTHROPIC_MODEL = MODELS["best"]["anthropic"]
DEFAULT_OPENAI_MODEL = MODELS["best"]["openai"]
DEFAULT_GEMINI_MODEL = MODELS["best"]["gemini"]


def detect_provider(api_key: str) -> str:
    """Return 'gemini' | 'anthropic' | 'openai' | 'unknown' based on the key prefix."""
    k = (api_key or "").strip()
    if k.startswith("AIza"):
        return "gemini"
    if k.startswith("sk-ant-"):
        return "anthropic"
    if k.startswith("sk-proj-") or k.startswith("sk-"):
        return "openai"
    return "unknown"


def _load_system_prompt() -> str:
    p = Path(__file__).parent / "prompts" / "outline_system.txt"
    return p.read_text(encoding="utf-8")


def _load_explore_system_prompt() -> str:
    p = Path(__file__).parent / "prompts" / "explore_system.txt"
    return p.read_text(encoding="utf-8")


def _strip_json_fences(text: str) -> str:
    """Some models occasionally wrap JSON in ```json fences despite instructions."""
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text)
    return m.group(1).strip() if m else text


def _truncate_source(text: str, max_chars: int = 60_000) -> str:
    """Defensive truncation. ~60K chars ≈ 15K tokens."""
    if len(text) <= max_chars:
        return text
    head = text[: max_chars - 200]
    return head + "\n\n[... source truncated for length ...]"


def _parse_json_response(raw: str) -> dict:
    """Parse + validate the model's JSON. Tolerates fences + leading prose."""
    if not raw.strip():
        raise RuntimeError("LLM returned an empty response.")
    cleaned = _strip_json_fences(raw)
    try:
        outline = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if not m:
            raise RuntimeError(
                f"Model did not return valid JSON. First 300 chars: {cleaned[:300]!r}"
            )
        outline = json.loads(m.group(0))

    if not isinstance(outline, dict) or "slides" not in outline:
        raise RuntimeError(
            f"Model returned JSON but it does not match the expected schema. "
            f"Got: {list(outline.keys()) if isinstance(outline, dict) else type(outline)}"
        )
    return outline


def _build_user_message(source_text: str, topic: str, slide_count: int, angle: str = "") -> str:
    angle_block = ""
    if angle.strip():
        angle_block = (
            f"User's angle / audience  (use this to design the closing 'Your Angle' slide):\n"
            f"{angle.strip()}\n\n"
        )
    return (
        f"Topic: {topic}\n"
        f"Target slide count: {slide_count}\n"
        f"\n"
        f"{angle_block}"
        f"Source content:\n"
        f"---\n"
        f"{_truncate_source(source_text)}\n"
        f"---\n"
        f"\n"
        f"Return the JSON outline now."
    )


# ─── Provider implementations ────────────────────────────────────────────────
def _synthesize_anthropic(api_key, model, user_msg, max_tokens):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _load_system_prompt()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system_prompt,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text if response.content else ""
    return _parse_json_response(raw)


def _synthesize_openai(api_key, model, user_msg, max_tokens):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    system_prompt = _load_system_prompt()
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )
    raw = response.choices[0].message.content or ""
    return _parse_json_response(raw)


def _synthesize_gemini(api_key, model, user_msg, max_tokens):
    """Gemini call with automatic fallback to other models if the chosen one
    isn't available on this key."""
    from google import genai
    from google.genai import types as gtypes

    client = genai.Client(api_key=api_key)
    system_prompt = _load_system_prompt()
    config = gtypes.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        max_output_tokens=max_tokens,
        temperature=0.4,
    )

    # Build the model list: chosen first, then fallbacks (deduped, preserving order).
    seen = set()
    to_try = []
    for m in (model, *GEMINI_FALLBACKS):
        if m and m not in seen:
            seen.add(m)
            to_try.append(m)

    errors = []
    for m in to_try:
        try:
            response = client.models.generate_content(
                model=m, contents=user_msg, config=config,
            )
            raw = response.text or ""
            if not raw.strip():
                errors.append(f"{m}: empty response")
                continue
            outline = _parse_json_response(raw)
            outline.setdefault("_model_used", m)
            return outline
        except Exception as e:  # noqa: BLE001 — we want a broad catch here to try the next model
            err_msg = str(e)[:300]
            errors.append(f"{m}: {type(e).__name__}: {err_msg}")
            # If the error mentions auth/key invalid, no point trying other models.
            lowered = err_msg.lower()
            if any(s in lowered for s in ("api_key", "api key", "unauthorized", "permission", "denied")):
                break

    raise RuntimeError(
        "Gemini request failed for all attempted models. Details:\n  "
        + "\n  ".join(errors)
        + "\n\nIf this persists, check the key at https://aistudio.google.com/app/apikey "
          "or pick a different provider in the sidebar."
    )


# ─── Public entry point ────────────────────────────────────────────────────────
def synthesize_outline(
    source_text: str,
    topic: str,
    slide_count: int = DEFAULT_SLIDE_COUNT,
    api_key: str | None = None,
    quality: str = DEFAULT_QUALITY,
    model: str | None = None,
    angle: str = "",
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """
    Synthesise a deck outline.  Provider is chosen from the api_key prefix.

    Args:
        source_text:   The raw source content (transcript, article, etc.)
        topic:         User-supplied topic / framing
        slide_count:   Target number of slides
        api_key:       Gemini (AIza...), Anthropic (sk-ant-...), or OpenAI (sk-...) key
        quality:       "best" (default) or "fast" — picks the right model per provider
        model:         Hard-override the model ID (advanced)
        angle:         Optional — the user's specific angle / audience / point of view.
                       When set, the LLM will produce a closing "Your Angle" slide.
        max_tokens:    Max output tokens

    Raises:
        ValueError       — if api_key is missing or in an unrecognised format
        RuntimeError     — if the LLM response doesn't parse / validate
    """
    if not api_key:
        raise ValueError(
            "API key is required. Pass api_key=... or set GEMINI_API_KEY, "
            "ANTHROPIC_API_KEY, or OPENAI_API_KEY in your environment."
        )

    provider = detect_provider(api_key)
    if provider == "unknown":
        raise ValueError(
            f"Unrecognised API key format. Expected:\n"
            f"  - Gemini key starting with 'AIza'  (FREE — no credit card required)\n"
            f"  - Anthropic key starting with 'sk-ant-'\n"
            f"  - OpenAI key starting with 'sk-proj-' or 'sk-'\n"
            f"Got a key starting with: {api_key[:8]!r}"
        )

    chosen_model = model or model_for(quality, provider)
    user_msg = _build_user_message(source_text, topic, slide_count, angle)

    if provider == "gemini":
        return _synthesize_gemini(api_key, chosen_model, user_msg, max_tokens)
    if provider == "anthropic":
        return _synthesize_anthropic(api_key, chosen_model, user_msg, max_tokens)
    if provider == "openai":
        return _synthesize_openai(api_key, chosen_model, user_msg, max_tokens)


# ═════════════════════════════════════════════════════════════════════════════
# RESEARCH REPORT MODE
# ═════════════════════════════════════════════════════════════════════════════
# Returns markdown (NOT JSON). Uses the explore_system.txt template so the
# output mirrors the user's hand-curated explore.md report format.

# Research reports are longer than decks — bump the token ceiling.
DEFAULT_EXPLORE_MAX_TOKENS = 12_000


def _strip_markdown_fences(text: str) -> str:
    """If the model wraps the whole document in ```markdown ... ```, unwrap it."""
    text = text.strip()
    m = re.match(r"^```(?:markdown|md)?\s*([\s\S]*?)\s*```$", text)
    return m.group(1).strip() if m else text


def _build_explore_user_message(
    source_text: str,
    topic: str,
    angle: str,
    source_meta: dict,
    report_date: str,
) -> str:
    """
    Build the user-side message for the research-report prompt.

    source_meta carries the structured facts the prompt needs — video URL,
    duration, segment count, etc. — so the model doesn't have to guess.
    """
    meta_lines = [
        f"video_url:      {source_meta.get('url', 'unknown')}",
        f"video_id:       {source_meta.get('video_id', 'unknown')}",
        f"duration_sec:   {int(source_meta.get('duration_sec', 0))}",
        f"duration_min:   {source_meta.get('duration_sec', 0) / 60:.1f}",
        f"char_count:     {source_meta.get('char_count', len(source_text))}",
        f"segment_count:  {source_meta.get('segment_count', 'unknown')}",
        f"channel:        {source_meta.get('channel', 'unknown — infer from transcript or leave blank')}",
        f"video_title:    {source_meta.get('title', 'unknown — infer from transcript')}",
    ]

    angle_block = ""
    if angle.strip():
        angle_block = (
            "User's angle / audience  (write the dedicated angle section using "
            "this person's vocabulary, product names, and stated context):\n"
            f"{angle.strip()}\n\n"
        )

    return (
        f"Topic / framing:  {topic}\n"
        f"Report date:      {report_date}\n"
        f"\n"
        f"Source metadata (use verbatim where the template asks for it — "
        f"do NOT invent or alter these values):\n"
        f"{chr(10).join(meta_lines)}\n"
        f"\n"
        f"{angle_block}"
        f"Source transcript:\n"
        f"---\n"
        f"{_truncate_source(source_text, max_chars=120_000)}\n"
        f"---\n"
        f"\n"
        f"Now produce the full markdown research report. Begin with "
        f"`# Explore Report:` and end with the closing italic footer line. "
        f"Do not wrap the document in code fences."
    )


def _synthesize_explore_anthropic(api_key, model, user_msg, max_tokens):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _load_explore_system_prompt()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system_prompt,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text if response.content else ""
    return _strip_markdown_fences(raw)


def _synthesize_explore_openai(api_key, model, user_msg, max_tokens):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    system_prompt = _load_explore_system_prompt()
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )
    raw = response.choices[0].message.content or ""
    return _strip_markdown_fences(raw)


def _synthesize_explore_gemini(api_key, model, user_msg, max_tokens):
    """Gemini call with the same fallback chain pattern as the deck path."""
    from google import genai
    from google.genai import types as gtypes

    client = genai.Client(api_key=api_key)
    system_prompt = _load_explore_system_prompt()
    config = gtypes.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=max_tokens,
        temperature=0.4,
    )

    seen = set()
    to_try = []
    for m in (model, *GEMINI_FALLBACKS):
        if m and m not in seen:
            seen.add(m)
            to_try.append(m)

    errors = []
    for m in to_try:
        try:
            response = client.models.generate_content(
                model=m, contents=user_msg, config=config,
            )
            raw = response.text or ""
            if not raw.strip():
                errors.append(f"{m}: empty response")
                continue
            return _strip_markdown_fences(raw)
        except Exception as e:  # noqa: BLE001
            err_msg = str(e)[:300]
            errors.append(f"{m}: {type(e).__name__}: {err_msg}")
            lowered = err_msg.lower()
            if any(s in lowered for s in ("api_key", "api key", "unauthorized", "permission", "denied")):
                break

    raise RuntimeError(
        "Gemini request failed for all attempted models. Details:\n  "
        + "\n  ".join(errors)
        + "\n\nIf this persists, check the key at https://aistudio.google.com/app/apikey "
          "or pick a different provider in the sidebar."
    )


def synthesize_explore(
    source_text: str,
    topic: str,
    api_key: str | None = None,
    quality: str = DEFAULT_QUALITY,
    model: str | None = None,
    angle: str = "",
    source_meta: dict | None = None,
    report_date: str = "",
    max_tokens: int = DEFAULT_EXPLORE_MAX_TOKENS,
) -> str:
    """
    Generate a research-report markdown document from a source transcript.

    Args:
        source_text:   The raw transcript / article text.
        topic:         User-supplied topic / framing.
        api_key:       Gemini / Anthropic / OpenAI key.
        quality:       "best" or "fast".
        model:         Override model ID.
        angle:         Optional — the user's angle / context. Triggers a custom
                       "{{User}}'s Angle" section at the end of the report.
        source_meta:   Dict carrying video metadata (url, video_id,
                       duration_sec, char_count, segment_count, channel,
                       title). Passed verbatim into the prompt.
        report_date:   The date to stamp on the report (YYYY-MM-DD).
        max_tokens:    Max output tokens. Research reports default higher
                       than decks because they are longer.

    Returns:
        A markdown string starting with `# Explore Report:`. No JSON wrapping,
        no code fences.

    Raises:
        ValueError    — missing or unrecognised api_key.
        RuntimeError  — provider failed for all attempts (Gemini) or the
                        model returned an empty response.
    """
    if not api_key:
        raise ValueError(
            "API key is required. Pass api_key=... or set GEMINI_API_KEY, "
            "ANTHROPIC_API_KEY, or OPENAI_API_KEY in your environment."
        )

    provider = detect_provider(api_key)
    if provider == "unknown":
        raise ValueError(
            f"Unrecognised API key format. Expected:\n"
            f"  - Gemini key starting with 'AIza'  (FREE — no credit card required)\n"
            f"  - Anthropic key starting with 'sk-ant-'\n"
            f"  - OpenAI key starting with 'sk-proj-' or 'sk-'\n"
            f"Got a key starting with: {api_key[:8]!r}"
        )

    chosen_model = model or model_for(quality, provider)
    user_msg = _build_explore_user_message(
        source_text=source_text,
        topic=topic,
        angle=angle,
        source_meta=source_meta or {},
        report_date=report_date,
    )

    if provider == "gemini":
        return _synthesize_explore_gemini(api_key, chosen_model, user_msg, max_tokens)
    if provider == "anthropic":
        return _synthesize_explore_anthropic(api_key, chosen_model, user_msg, max_tokens)
    if provider == "openai":
        return _synthesize_explore_openai(api_key, chosen_model, user_msg, max_tokens)
