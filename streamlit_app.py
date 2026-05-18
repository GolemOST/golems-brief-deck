import sys
import streamlit as st

st.title("Golem Brief Deck - Startup Test")
st.write(f"Python: {sys.version}")
st.write("If you see this, Streamlit Cloud works.")

try:
    from briefdeck import __version__
    st.success(f"briefdeck imported OK — v{__version__}")
except Exception as e:
    st.error(f"briefdeck import failed: {e}")

try:
    from briefdeck.render.builder import build_deck
    st.success("render.builder imported OK")
except Exception as e:
    st.error(f"render.builder failed: {e}")

try:
    from briefdeck.synthesize import synthesize_outline
    st.success("synthesize imported OK")
except Exception as e:
    st.error(f"synthesize failed: {e}")

try:
    from briefdeck.ingest.youtube import fetch_transcript
    st.success("youtube ingest imported OK")
except Exception as e:
    st.error(f"youtube ingest failed: {e}")
