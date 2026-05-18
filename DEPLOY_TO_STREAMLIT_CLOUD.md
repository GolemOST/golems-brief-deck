# Deploy BriefDeck to Streamlit Cloud — Step-by-Step

This walks you through getting BriefDeck live at a public URL like
`briefdeck.streamlit.app` so non-technical users can use it **without installing
anything** — they just visit the link.

Time required: ~30 minutes the first time.

---

## What you'll end up with

A public URL like `https://briefdeck-rcapisinio.streamlit.app` that:
- Anyone can visit (no install)
- Has the polished UI we just built — with the **Research Report / Briefing Deck** mode selector
- Lets users paste their own Gemini / OpenAI / Anthropic API key (BYO model — they pay the provider directly, you pay nothing)
- Auto-redeploys whenever you push to GitHub
- Is free (Streamlit Community Cloud — free tier)

---

## Step 1 — Make sure you have a GitHub account

If you already do, skip to Step 2.

1. Go to [github.com](https://github.com/) and sign up (free).
2. Verify your email.

---

## Step 2 — Push the BriefDeck code to GitHub

Easiest way is with **GitHub Desktop** (which you already have at
`C:\Users\Raymond\AppData\Local\GitHubDesktop\`).

1. Open **GitHub Desktop**.
2. **File → Add Local Repository** → browse to `C:\Projects\BRIEFDECK\`.
3. If it warns *"This directory doesn't appear to be a Git repository"*,
   click **create a repository**.
4. Set:
   - **Name:** `briefdeck`
   - **Description:** "Industrial briefing decks from YouTube videos"
   - **Git ignore:** Python (it will use the .gitignore we already wrote)
   - **License:** MIT
5. Click **Create repository**.
6. At the top of GitHub Desktop, click **Publish repository**.
7. Choose:
   - ☑️ Public  *(required for free Streamlit Cloud)*
   - Or ☐ Private if you have a Streamlit Cloud paid tier
8. Click **Publish Repository**.

Your code is now at `https://github.com/<your-username>/briefdeck`.

---

## Step 3 — Connect to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2. Click **New app**.
3. Fill in:
   - **Repository:** `<your-username>/briefdeck`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL:** pick something like `briefdeck-rcapisinio` (becomes
     `briefdeck-rcapisinio.streamlit.app`)
4. Click **Advanced settings** (optional):
   - Set **Python version:** 3.11 or 3.12
5. Click **Deploy!**

First deploy takes ~3-5 minutes (it installs all the dependencies from
`requirements.txt`).

---

## Step 4 — Verify it works

1. Wait until you see *"Your app is in the oven"* finish.
2. Visit your URL — should land on the BriefDeck welcome page.
3. Paste an API key in the sidebar (click **Use once** — Streamlit Cloud
   doesn't persist files across sessions anyway). Gemini is the fastest
   start: free, no credit card.
4. Click **Try with a sample video**, pick **Research Report** or
   **Briefing Deck**, then click **Generate**.
5. Download the `.md` or `.pptx` — confirm it opens cleanly.

---

## Step 5 — Share with users

Send people the URL with a one-paragraph intro:

> Hey — I built a tool that turns any YouTube video into either a structured
> research report (markdown) or a professional briefing deck (PowerPoint), in
> about 30–60 seconds. It's free to use — you just need a free Google Gemini
> API key (instructions inside the app) which is FREE on Gemini's 1,500/day
> free tier.
>
> Try it: https://briefdeck-rcapisinio.streamlit.app

---

## Updating the app later

Just push commits to GitHub. Streamlit Cloud auto-redeploys within ~60 seconds.

```powershell
# Make changes locally, then in GitHub Desktop:
# 1. Review your changes in the left panel
# 2. Write a commit message
# 3. Click "Commit to main"
# 4. Click "Push origin"
# That's it — the live site updates automatically.
```

---

## Costs

| What | Who pays | Amount |
|---|---|---|
| Streamlit hosting | You (free tier) | $0 — free forever for public apps |
| GitHub repo | You (free tier) | $0 — free for public repos |
| Gemini API (FREE tier) | The user (BYO key) | $0 — 1,500/day on free tier |
| OpenAI API (optional) | The user (BYO key) | ~$0.02–0.05 per run |
| Anthropic API (optional) | The user (BYO key) | ~$0.05–0.15 per run |

**You pay nothing.**

---

## Troubleshooting

### *"ModuleNotFoundError: No module named 'briefdeck'"*
Streamlit Cloud isn't picking up the package. Fix by adding a one-line
`packages.txt` or moving `briefdeck/` into the root. Try also adding to
`requirements.txt`:
```
-e .
```
…on its own line.

### *"Anthropic API key invalid"*
The user pasted the key wrong. Tell them to check for spaces and that it starts
with `sk-ant-`.

### *App is slow to start*
First request after idle takes ~30 sec to spin up the container. Streamlit
Cloud sleeps inactive apps. Not avoidable on free tier.

### *Want a custom domain like briefdeck.refineryost.cc?*
Streamlit Cloud free tier doesn't support custom domains. Either upgrade to
Streamlit Cloud paid (~$25/mo) or deploy elsewhere (Cloudflare Pages + Workers,
or eventually the PyInstaller `.exe` for offline-first).

---

## What this DOESN'T cover

This guide ships the cloud version. The Windows `.exe` for offline/no-internet
users is a separate path (see `plans/briefdeck_v1_plan.md` for that roadmap).
