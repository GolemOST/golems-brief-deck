@echo off
title BriefDeck - Industrial Briefing Deck Generator
color 0E

REM ─── BriefDeck launcher ───────────────────────────────────────────────────
REM Double-click this file. A browser window will open with the app.
REM ─────────────────────────────────────────────────────────────────────────

cd /d "%~dp0"

cls
echo.
echo  ============================================================
echo  ^|                                                          ^|
echo  ^|              B R I E F   D E C K                         ^|
echo  ^|                                                          ^|
echo  ^|        Starting up... please wait 5-10 seconds.          ^|
echo  ^|        Your browser will open automatically.             ^|
echo  ^|                                                          ^|
echo  ============================================================
echo.
echo   WHAT TO DO NEXT:
echo.
echo   1. Wait for your browser to open the BriefDeck page
echo   2. On the LEFT SIDEBAR: paste your Anthropic API key
echo   3. In the MAIN AREA: paste a YouTube URL
echo   4. Click "Generate briefing deck"
echo   5. Download the .pptx when ready
echo.
echo   To stop BriefDeck:  close this black window
echo   First time?         get a free key at console.anthropic.com
echo.
echo  ============================================================
echo.

REM Verify Python is installed and reachable first.
python --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo  ============================================================
  echo   ERROR: Python is not installed or not on PATH.
  echo.
  echo   Please install Python 3.11+ from:
  echo       https://www.python.org/downloads/
  echo.
  echo   Make sure to tick "Add Python to PATH" during install.
  echo  ============================================================
  echo.
  pause
  exit /b 1
)

REM Launch via 'python -m streamlit' so we don't depend on the streamlit
REM CLI script being on PATH (it usually isn't on a fresh Windows install).
python -m streamlit run streamlit_app.py

REM Keep window open if streamlit crashed so the user can see the error.
if errorlevel 1 (
  echo.
  echo  ============================================================
  echo   BriefDeck stopped with an error. Read above and press
  echo   any key to close this window.
  echo.
  echo   If you saw "No module named streamlit", run this in a
  echo   terminal in this folder, then try again:
  echo       pip install -r requirements.txt
  echo  ============================================================
  pause >nul
)
