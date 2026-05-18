# BriefDeck

**Research reports and briefing decks from any YouTube video.** Paste a URL, pick a mode, and get either a structured markdown research report (`.md`) or a navy/gold PowerPoint deck (`.pptx`) — both designed for technical and industrial executives.

Runs locally. Your data and your API key never leave your machine except to call your chosen AI provider (Gemini, OpenAI, or Anthropic) directly.

---

## Why this exists

Generic AI tools (Gamma, Tome, ChatGPT) produce generic outputs. BriefDeck is opinionated for **industrial briefings** — Plant Managers, Reliability Engineers, Ops Directors, investors in industrial AI. Two surfaces, same backbone:

- **Research Report mode** — a markdown briefing with Source table, Core Thesis, the source's named framework, Pros / Cons, Latest Trends, and an optional dedicated "Your Angle" section that maps the source onto your specific situation.
- **Briefing Deck mode** — a corporate navy + gold PowerPoint, 8–22 slides, no emoji, no clipart, no "AI shimmer". Every slide is structured for a technical reader.

---

## Quick start (developers)

```bash
# Clone + install
git clone https://github.com/<your-org>/briefdeck.git
cd briefdeck
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e .

# Set an API key — Gemini is FREE; OpenAI and Anthropic are paid
$env:GEMINI_API_KEY = "AIza..."           # PowerShell
# or:  $env:ANTHROPIC_API_KEY = "sk-ant-..."
# or:  $env:OPENAI_API_KEY    = "sk-proj-..."

# CLI — briefing deck (default)
briefdeck "https://www.youtube.com/watch?v=LIkYVsxMpS8" --topic "AI Investment" -o brief.pptx

# CLI — research report
briefdeck "https://www.youtube.com/watch?v=LIkYVsxMpS8" --mode report --topic "AI Investment" --angle "I run alumina refinery operations in the UAE."

# UI
streamlit run streamlit_app.py
```

---

## Quick start (non-technical users)

**The easiest way:** visit the hosted version — no install, no setup. *(Live URL added after you deploy — see [DEPLOY_TO_STREAMLIT_CLOUD.md](DEPLOY_TO_STREAMLIT_CLOUD.md).)*

**On a Windows machine with Python already installed:** double-click **`Start BriefDeck.bat`** in this folder. The app opens in your browser. See [READ ME FIRST.txt](READ%20ME%20FIRST.txt) for plain-language step-by-step instructions.

**Coming soon:** standalone `briefdeck.exe` — single download, no Python required.

---

## CLI usage

```
briefdeck <youtube-url-or-id> [options]

Options:
  -m, --mode         Output mode: 'deck' (default) or 'report'
  -t, --topic        Topic / framing for the output (improves quality)
  -a, --angle        Your specific angle/audience — adds a custom 'Your Angle'
                     section (report) or slide (deck)
  -o, --out          Output path (default depends on --mode)
  -n, --slides       Deck mode only: target slide count (default 14, min 8, max 22)
  -q, --quality      'best' (default) or 'fast'
  --api-key          API key — Gemini / Anthropic / OpenAI (auto-detected)
  --save-key         Persist --api-key to ~/.briefdeck/config.json
  --version          Show version
```

---

## How it works

```
YouTube URL
  │
  ▼
[ingest/youtube.py]  ─── youtube-transcript-api ──→ full transcript text
  │
  ▼
[synthesize.py]      ─── Gemini / OpenAI / Anthropic
  │                   ├── synthesize_outline()  ─→ structured JSON outline
  │                   └── synthesize_explore()  ─→ markdown research report
  ▼
  ├─ deck mode  → [render/builder.py] ─ python-pptx ─→ .pptx file
  └─ report mode → write markdown directly         ─→ .md  file
```

Three modules, two output modes, ~900 lines of Python.

---

## Slide types

BriefDeck ships with 8 layout types. Claude picks which to use per section.

| Type | Use case |
|---|---|
| `title` | Hero slide with central quote |
| `stat_shock` | Headline number + 3 supporting reasons |
| `definition` | Concept + plain-English explanation |
| `bullets` | Standard content with up to 10 bullets |
| `two_col` | Pros/cons, before/after, do/don't |
| `matrix_2x2` | Decision frameworks with 4 quadrants |
| `quote` | Centered hero quote with attribution |
| `takeaway` | Closing slide — 3 numbered takeaways |

---

## Configuration

API key resolution order:
1. `--api-key` flag on the CLI
2. `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` environment variable
3. `~/.briefdeck/config.json` (created by `--save-key` or the UI)

---

## Roadmap

**v0.1** — YouTube URL → PPTX · CLI + Streamlit UI · BYO API key

**v0.2 (now)** — Research Report mode (markdown output with custom "Your Angle" section) · `--mode report` CLI flag · Streamlit mode selector

**v0.3 (planned)** — Folder ingestion (.md/.txt/.pdf/.docx) · multiple web URLs · `.exe` build

**v0.4 (planned)** — Alt themes (light/dense/executive) · Mac/Linux builds · sample gallery

---

## License

MIT — see [LICENSE](LICENSE).

---

## Built by

Raymond P. Capisinio · rcapisinio@gmail.com · Abu Dhabi, UAE
