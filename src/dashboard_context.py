
from pathlib import Path
import sys
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.metrics import load_data, validate_data, calculate_analysis

@st.cache_data(show_spinner="Loading operational datasets...")
def get_bundle():
    data = load_data(ROOT / "data")
    validation = validate_data(data)
    results = calculate_analysis(data)
    return data, validation, results
