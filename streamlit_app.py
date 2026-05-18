"""BriefDeck — Streamlit UI.

Two output modes:
  1. RESEARCH REPORT  — a structured markdown briefing (.md file)
  2. BRIEFING DECK    — a navy-and-gold PowerPoint deck (.pptx file)

Same source (a YouTube video). Same key. Different deliverable.
The UI is built for a non-technical colleague — every field has a one-line
explanation, every error has a plain-English fix, and the sample-video button
demonstrates the end-to-end flow without forcing them to find a URL.
"""

import traceback
from datetime import date
from tempfile import NamedTemporaryFile

import streamlit as st

from briefdeck import __version__
from briefdeck.config import get_api_key, save_api_key, clear_api_key
from briefdeck.ingest.youtube import (
    fetch_transcript,
    extract_video_id,
)
from briefdeck.render.builder import build_deck
from briefdeck.synthesize import (
    synthesize_outline, synthesize_explore,
    DEFAULT_SLIDE_COUNT, DEFAULT_QUALITY,
    detect_provider, model_for,
)


SAMPLE_URL = "https://www.youtube.com/watch?v=LIkYVsxMpS8"
SAMPLE_TOPIC = "AI Investment Strategy for Industrial Operations"
SAMPLE_ANGLE = (
    "I run alumina refinery operations in the UAE. I want to convince a "
    "Plant Manager that capturing structured shift-handover data this year "
    "unlocks predictive maintenance next year."
)


ERROR_MESSAGES = {
    "TranscriptsDisabled":
        "**This video has captions disabled.** YouTube creators can turn off transcripts. "
        "Try a different video — most TED talks, podcasts, and educational channels have them on.",
    "NoTranscriptFound":
        "**No English transcript available** for this video. Try one with English captions.",
    "ValueError":
        "**Bad input.** That doesn't look like a valid YouTube URL or a recognised API key. "
        "URLs should look like `https://www.youtube.com/watch?v=…`. "
        "API keys start with `sk-ant-` (Anthropic) or `sk-proj-` / `sk-` (OpenAI) or `AIza` (Gemini).",
    "AuthenticationError":
        "**Your API key was rejected.** Double-check the prefix matches the provider "
        "(`AIza` for Gemini, `sk-ant-` for Anthropic, `sk-proj-` / `sk-` for OpenAI) and "
        "that you copied it without extra spaces. For Gemini, the key must be enabled at "
        "aistudio.google.com.",
    "ClientError":
        "**The AI provider rejected the request.** Check the technical details "
        "below for the exact reason. Common fixes: try the Best Quality tier (newer model), "
        "generate a new Gemini key at aistudio.google.com, or wait 60 seconds and retry.",
    "PermissionDeniedError":
        "**Your API key doesn't have permission for this model.** "
        "If you're on OpenAI, make sure your key has access to `gpt-4o-mini` "
        "(any new key does).",
    "RateLimitError":
        "**The provider rate-limited the request.** Wait a minute and try again, or check "
        "your usage limits at your provider's console.",
    "APIConnectionError":
        "**Couldn't reach the AI provider.** Check your internet connection and try again.",
    "BadRequestError":
        "**The AI provider rejected the request.** Often means the source content was "
        "too long or contained something the model wouldn't process. Try a shorter video.",
}


def _friendly_error(exc: Exception) -> tuple[str, str]:
    """Return (user-facing message, dev traceback)."""
    name = type(exc).__name__
    pretty = ERROR_MESSAGES.get(name)
    if not pretty:
        msg = str(exc)
        if name == "RuntimeError" and "Gemini" in msg:
            pretty = (
                f"**Gemini request failed.** Here's what happened:\n\n"
                f"```\n{msg}\n```\n\n"
                f"Most common fixes: switch to Best Quality tier, regenerate your key, "
                f"or paste an OpenAI key instead."
            )
        else:
            pretty = (
                f"**{name}**: {exc}\n\n"
                f"If this keeps happening, the developer can use the technical details below."
            )
    return pretty, traceback.format_exc()


# ─── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BriefDeck — Industrial Research & Briefing Decks",
    page_icon="📊",
    layout="centered",
)

st.markdown(
    """
    <style>
      .briefdeck-title { color: #003366; font-size: 2.4em; font-weight: 800;
                         margin-bottom: 0.1em; letter-spacing: -0.02em; }
      .briefdeck-tag   { color: #C8961E; font-size: 1.1em; margin-top: 0;
                         font-style: italic; margin-bottom: 1.2em; }
      .step-pill { display: inline-block; background: #003366; color: white;
                   padding: 0.15em 0.7em; border-radius: 1em; font-weight: 600;
                   font-size: 0.85em; margin-right: 0.5em; }
      .mode-box {
        background: #f5f7fa;
        border-left: 4px solid #C8961E;
        padding: 0.8em 1.1em;
        border-radius: 6px;
        margin: 0.6em 0 1.2em 0;
        color: #003366;
      }
      .stButton > button { background-color: #003366; color: white;
                           font-weight: 600; padding: 0.6em 1.4em; border: none; }
      .stButton > button:hover { background-color: #C8961E; color: #003366; }
      .stButton > button[kind="primary"] { background-color: #C8961E; color: #003366; }
      .stButton > button[kind="primary"]:hover { background-color: #003366; color: #C8961E; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="briefdeck-title">BriefDeck</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="briefdeck-tag">Turn any YouTube video into a research report or a briefing deck.</p>',
    unsafe_allow_html=True,
)


# ─── Helper: do we have a key yet? ────────────────────────────────────────────
def _has_key():
    return bool(st.session_state.get("session_api_key") or get_api_key())


def _get_effective_key() -> str | None:
    return st.session_state.get("session_api_key") or get_api_key()


# ─── Onboarding banner (only shown when no key is set yet) ────────────────────
if not _has_key():
    st.markdown(
        """
<div style="background: linear-gradient(135deg, #003366 0%, #1a4d80 100%);
            border-left: 6px solid #C8961E;
            padding: 1.4em 1.6em;
            border-radius: 8px;
            color: white;
            margin: 0.5em 0 1em 0;">
  <h3 style="color: #C8961E; margin-top: 0; margin-bottom: 0.4em;">
    🎁  No API key yet?  Get one FREE in 60 seconds.
  </h3>
  <p style="color: #DCE6F0; font-size: 1.05em; margin-bottom: 1em;">
    BriefDeck works with <b>3 different AI providers</b> — but Google Gemini
    is the easiest to start with because <b>no credit card is needed.</b>
  </p>
  <ol style="color: white; font-size: 1.0em; margin-bottom: 0.4em;">
    <li>Go to <a href="https://aistudio.google.com/app/apikey"
                style="color: #C8961E; font-weight: 600;"
                target="_blank">aistudio.google.com/app/apikey</a> (opens in new tab)</li>
    <li>Sign in with your Google account</li>
    <li>Click <b>"Create API key"</b> → copy the key (starts with <code style="color: #C8961E;">AIza</code>)</li>
    <li>Come back here. Paste it in the <b>sidebar on the left</b>.</li>
    <li>Done!  You get 1,500 free generations per day on Gemini's free tier.</li>
  </ol>
</div>
""",
        unsafe_allow_html=True,
    )


# ─── First-time explainer ────────────────────────────────────────────────────
with st.expander("👋  First time here?  What is BriefDeck?", expanded=False):
    st.markdown(
        """
**What BriefDeck does:** You paste a YouTube link. BriefDeck reads the
transcript, then either (A) asks an AI to write a structured **research
report** (markdown file you can paste into Notion, Docs, or a memo), or
(B) asks the AI to design a **briefing deck** (PowerPoint file styled for
technical / industrial executives).

**Two output modes, same source video:**

| Mode | Output | Best for |
|---|---|---|
| 📑 **Research Report** | A `.md` markdown file — sections, tables, verbatim quotes, your custom angle | Strategy memos, due-diligence dumps, prep before a meeting |
| 📊 **Briefing Deck** | A `.pptx` PowerPoint — navy/gold, 8-22 slides, exec-ready | Putting in front of a Plant Manager / CEO / investor |

**Three AI providers, your choice:**

| Provider | Cost | Free option? | Best for |
|---|---|---|---|
| 🌟 **Google Gemini** | **FREE** (1,500/day) | ✅ No credit card needed | Anyone — recommended first try |
| **OpenAI** | ~$0.02–0.05 per run | ❌ Credit card required | Existing OpenAI users |
| **Anthropic** | ~$0.05–0.15 per run | ❌ Credit card required | Best quality on technical content |

BriefDeck auto-detects which provider's key you paste.

**What BriefDeck does NOT do:**
- Send your data to a server I control. Everything runs on your machine.
- Store your API key on the internet. It stays in a local file on YOUR computer.
- Charge you anything. You pay the AI provider directly (often $0).
"""
    )


# ─── Sidebar: API key management ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='color:#003366; margin-top:0;'>"
        "🔑  STEP 1<br>"
        "<span style='color:#C8961E; font-size:0.7em;'>"
        "PASTE YOUR API KEY HERE</span></h2>",
        unsafe_allow_html=True,
    )
    st.caption("Works with **Gemini** (free), **OpenAI**, or **Anthropic** — paste any.")

    existing = get_api_key()
    session_key = st.session_state.get("session_api_key")
    active_key = session_key or existing

    if active_key:
        masked = active_key[:7] + "…" + active_key[-4:]
        provider = detect_provider(active_key)
        provider_label = {
            "gemini": "🌟  Google Gemini  (gemini-2.5-flash · FREE tier)",
            "openai": "🟢  OpenAI  (gpt-4o-mini)",
            "anthropic": "🟣  Anthropic  (Claude Sonnet 4.6)",
            "unknown": "⚠️  Unknown provider",
        }.get(provider, "")
        scope_label = "session only" if session_key else "saved to disk"
        st.success(f"**{provider_label}**\nKey: `{masked}`  ·  {scope_label}")
    else:
        st.warning("No key set yet. Get a FREE Gemini key 👇 then paste it below.")

    with st.expander("🌟  Get a FREE key (Gemini)", expanded=True):
        st.markdown(
            "**Recommended for new users — no credit card needed.**\n"
            "1. Open [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) (opens new tab)\n"
            "2. Sign in with your Google account\n"
            "3. Click **Create API key** → copy it (starts with `AIza`)\n"
            "4. Paste it below 👇\n"
            "\n"
            "*Gemini free tier = 1,500 generations per day. Plenty.*"
        )

    with st.expander("Other key options (paid)"):
        st.markdown(
            "**OpenAI**  (~$0.02 per run)\n"
            "1. [platform.openai.com/api-keys](https://platform.openai.com/api-keys)\n"
            "2. Sign up · add credit · create key (starts with `sk-` or `sk-proj-`)\n"
            "\n"
            "**Anthropic**  (~$0.05–0.15 per run)\n"
            "1. [console.anthropic.com](https://console.anthropic.com/)\n"
            "2. Sign up · add credit · create key (starts with `sk-ant-`)\n"
        )

    new_key = st.text_input(
        "Paste your key",
        type="password",
        placeholder="AIza...  or  sk-ant-...  or  sk-proj-...  or  sk-...",
        label_visibility="collapsed",
    )
    if new_key.strip():
        detected = detect_provider(new_key.strip())
        hint = {
            "gemini": "✓  🌟 Looks like a Gemini key (will use gemini-2.5-flash · FREE)",
            "openai": "✓  Looks like an OpenAI key (will use gpt-4o-mini)",
            "anthropic": "✓  Looks like an Anthropic key (will use Claude Sonnet 4.6)",
            "unknown": "⚠️  Doesn't look like a Gemini, OpenAI, or Anthropic key",
        }.get(detected, "")
        if detected == "unknown":
            st.warning(hint)
        else:
            st.caption(hint)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Save", use_container_width=True):
            if not new_key.strip():
                st.error("Paste a key first.")
            else:
                save_api_key(new_key.strip())
                st.success("Saved.")
                st.rerun()
    with col_b:
        if st.button("Use once", use_container_width=True,
                     help="Use for this session only — don't save to disk."):
            if not new_key.strip():
                st.error("Paste a key first.")
            else:
                st.session_state["session_api_key"] = new_key.strip()
                st.success("Loaded.")
                st.rerun()

    if existing or session_key:
        if st.button("Clear key", use_container_width=True):
            clear_api_key()
            st.session_state.pop("session_api_key", None)
            st.rerun()

    st.divider()
    with st.expander("Why do you need my key?"):
        st.markdown(
            "BriefDeck calls an AI provider (Gemini, OpenAI, or Anthropic) to "
            "generate your report or deck. To avoid building a paywall, "
            "BriefDeck uses **your** key — so you pay the provider directly "
            "(often $0 on Gemini's free tier).\n\n"
            "Your key is stored locally at `~/.briefdeck/config.json` "
            "(or only in your browser tab, if you click *Use once*). "
            "It never leaves your machine except to call the provider."
        )

    st.caption(f"BriefDeck v{__version__}")


# ─── Main form ────────────────────────────────────────────────────────────────

# Step 2 — MODE SELECTOR
st.markdown("### 🎯  STEP 2 — Pick what you want BriefDeck to make")

mode = st.radio(
    "Output mode",
    options=["report", "deck"],
    format_func=lambda m: (
        "📑  Research Report  —  a structured markdown briefing (.md)"
        if m == "report" else
        "📊  Briefing Deck  —  a navy/gold PowerPoint (.pptx)"
    ),
    horizontal=False,
    label_visibility="collapsed",
)

if mode == "report":
    st.markdown(
        '<div class="mode-box">'
        "📑  <b>Research Report mode.</b>  You'll get a <code>.md</code> file with "
        "structured sections — Source, Core Thesis, the source's named framework, "
        "Pros / Cons, Trends, plus an optional <b>custom angle</b> section that "
        "ties everything back to your situation. Best for memos, pre-meeting prep, "
        "due-diligence notes, or anything you'll paste into Notion / Docs."
        "</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="mode-box">'
        "📊  <b>Briefing Deck mode.</b>  You'll get a <code>.pptx</code> file with "
        "8–22 slides — title, headline stat, definitions, two-column comparisons, "
        "2×2 matrices, and a closing 3-takeaway slide. Navy + gold corporate style. "
        "Best for putting in front of an executive, customer, or investor."
        "</div>",
        unsafe_allow_html=True,
    )


# Step 3 — YouTube URL
st.markdown("### 📺  STEP 3 — Paste a YouTube link")
st.caption("Any public video with English captions works. Most TED talks, podcasts, "
           "and educational channels have captions enabled.")

if st.button("🎬  Or try with a sample video  →  (Nate B Jones' '5 Levers')",
             help="Pre-fills the form so you can see the app work end-to-end"):
    st.session_state["url_input"] = SAMPLE_URL
    st.session_state["topic_input"] = SAMPLE_TOPIC
    st.session_state["angle_input"] = SAMPLE_ANGLE
    st.rerun()

url = st.text_input(
    "YouTube URL",
    key="url_input",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed",
)


# Step 4 — Topic
st.markdown("### 💬  STEP 4 — What's the topic? *(optional but recommended)*")
st.caption("One short phrase telling the AI what frame to use. "
           "Without it, BriefDeck will just summarise the video literally. "
           "With it, the AI angles every section toward your topic.")
topic = st.text_input(
    "Topic",
    key="topic_input",
    placeholder="e.g.  AI Investment Strategy for Refineries",
    label_visibility="collapsed",
)


# Step 5 — Angle / Audience
st.markdown("### 🧭  STEP 5 — What's YOUR angle? *(optional but powerful)*")
if mode == "report":
    st.caption(
        "If you tell BriefDeck who you are and what you care about, the report "
        "ends with a dedicated **\"Your Angle\"** section — a table mapping the "
        "source's framework onto YOUR domain, quotes you can lift into your own "
        "pitch, and a customer-discovery question tailored to your situation."
    )
else:
    st.caption(
        "If you tell BriefDeck who you are and what you care about, the deck "
        "adds a dedicated **\"Your Angle\"** slide connecting the video back "
        "to your specific situation."
    )
angle = st.text_area(
    "Your angle / audience",
    key="angle_input",
    placeholder=(
        "e.g.  I run alumina refinery operations in the UAE.  "
        "I'm trying to convince a Plant Manager that capturing structured "
        "shift-handover data this year unlocks predictive maintenance next year."
    ),
    label_visibility="collapsed",
    height=110,
)


# Step 6 — Mode-specific options
if mode == "deck":
    st.markdown("### 📏  STEP 6 — How many slides?")
    slides = st.slider(
        "Number of slides",
        min_value=8, max_value=22, value=DEFAULT_SLIDE_COUNT,
        label_visibility="collapsed",
        help="12–16 is the sweet spot for most briefings",
    )
else:
    # Research reports don't have a slide count — but we still want to expose
    # ONE knob so the user feels in control. Quality is the only one that
    # really matters here.
    slides = DEFAULT_SLIDE_COUNT  # unused, set for safety


st.markdown("### ⚙️  STEP 7 — Quality tier")
quality = st.radio(
    "Quality",
    options=["best", "fast"],
    format_func=lambda q: (
        "🌟  Best  (recommended — sharper, slightly slower)" if q == "best"
        else "⚡  Fast & Cheap  (smaller model, quicker, lower cost)"
    ),
    index=0,
    label_visibility="collapsed",
    help=(
        "Best = gpt-4o · Claude Sonnet 4.6 · Gemini 2.5 Flash. "
        "Fast = gpt-4o-mini · Claude Haiku · Gemini 2.0 Flash. "
        "Default is Best — costs a few cents more but the output is noticeably sharper."
    ),
)
eff_key_preview = _get_effective_key()
if eff_key_preview:
    prov = detect_provider(eff_key_preview)
    if prov in ("gemini", "openai", "anthropic"):
        st.caption(f"Will use: `{model_for(quality, prov)}`")


# Step 8 — Generate button
st.markdown("### ✨  STEP 8 — Click to generate")
button_label = (
    "📑   GENERATE RESEARCH REPORT" if mode == "report"
    else "📊   GENERATE BRIEFING DECK"
)
generate = st.button(button_label, type="primary", use_container_width=True)


# ─── Generation flow ──────────────────────────────────────────────────────────
if generate:
    key = _get_effective_key()
    if not key:
        st.error("⚠  Add your API key in the sidebar first.")
        st.stop()
    if not url.strip():
        st.error("⚠  Paste a YouTube URL first. Click the sample-video button to try one quickly.")
        st.stop()

    try:
        with st.status("Working…", expanded=True) as status:
            st.write("🎧  Listening to the video…")
            transcript = fetch_transcript(url.strip())
            st.write(
                f"   ↳ Got the transcript "
                f"(**{transcript['duration_sec']/60:.1f} min**, "
                f"{transcript['char_count']:,} characters)"
            )

            prov = detect_provider(key)
            chosen_model = model_for(quality, prov) if prov != "unknown" else "?"
            video_id = extract_video_id(url.strip())
            today_str = date.today().strftime("%Y-%m-%d")

            if mode == "report":
                # ─────── Research report path ───────
                st.write(
                    f"🧠  Writing your research report "
                    f"({quality} quality · `{chosen_model}`)…"
                )
                md = synthesize_explore(
                    source_text=transcript["text"],
                    topic=topic.strip() or "General briefing",
                    api_key=key,
                    quality=quality,
                    angle=angle.strip(),
                    source_meta={
                        "url": transcript["url"],
                        "video_id": transcript["video_id"],
                        "duration_sec": transcript["duration_sec"],
                        "char_count": transcript["char_count"],
                        "segment_count": transcript["segment_count"],
                    },
                    report_date=today_str,
                )

                fname = f"briefdeck_research_{video_id}_{today_str.replace('-', '')}.md"
                file_bytes = md.encode("utf-8")
                mime = "text/markdown"
                st.write(f"   ↳ Report ready:  **{len(md):,} characters**  "
                         f"(~{len(md.split()):,} words)")

                status.update(label="✓  Done!", state="complete", expanded=False)

                st.success(
                    f"🎉  Your research report is ready — "
                    f"~{len(md.split()):,} words, ~{len(file_bytes)/1024:.0f} KB  "
                    f"·  generated with `{chosen_model}`"
                )
                st.download_button(
                    label=f"⬇  Download  {fname}",
                    data=file_bytes,
                    file_name=fname,
                    mime=mime,
                    use_container_width=True,
                )

                with st.expander("📖  Preview the report"):
                    st.markdown(md)

            else:
                # ─────── Briefing deck path ───────
                st.write(
                    f"🧠  Designing your **{slides}-slide** deck "
                    f"({quality} quality · `{chosen_model}`)…"
                )
                outline = synthesize_outline(
                    source_text=transcript["text"],
                    topic=topic.strip() or "General briefing",
                    slide_count=slides,
                    api_key=key,
                    quality=quality,
                    angle=angle.strip(),
                )
                st.write(
                    f"   ↳ Outline ready:  **{outline.get('title', '(untitled)')}**  "
                    f"({len(outline.get('slides', []))} slides)"
                )

                st.write("🎨  Painting your deck in navy + gold…")
                fname = f"briefdeck_{video_id}_{today_str.replace('-', '')}.pptx"
                with NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
                    tmp_path = tmp.name
                build_deck(outline, tmp_path)
                with open(tmp_path, "rb") as f:
                    deck_bytes = f.read()

                status.update(label="✓  Done!", state="complete", expanded=False)

                model_used = outline.get("_model_used") or chosen_model
                st.success(
                    f"🎉  Your deck is ready — **{len(outline.get('slides', []))} slides**, "
                    f"~{len(deck_bytes)/1024:.0f} KB  ·  generated with `{model_used}`"
                )
                st.download_button(
                    label=f"⬇  Download  {fname}",
                    data=deck_bytes,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True,
                )

                with st.expander("Curious? Show the AI's outline"):
                    st.json(outline)

    except Exception as e:
        pretty, tb = _friendly_error(e)
        st.error(pretty)
        with st.expander("Technical details (for developers)"):
            st.code(tb, language="text")


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    """
<div style="text-align: center; color: #888; font-size: 0.85em; margin-top: 3em;">
  Built by Raymond P. Capisinio  ·
  <a href="https://github.com/" style="color: #003366;">source on GitHub</a>  ·
  MIT licensed
</div>
""",
    unsafe_allow_html=True,
)
