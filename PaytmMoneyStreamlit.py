import os
import streamlit as st
import requests
from urllib.parse import urlencode

# --- 1. INITIAL APP & ENVIRONMENT VALIDATION ---
st.set_page_config(page_title="Paytm Money Secure Client", layout="wide")

# Fetch credentials directly from environment variables
API_KEY = os.environ.get("PAYTM_API_KEY")
API_SECRET = os.environ.get("PAYTM_API_SECRET")

# Enforce a hard stop if credentials are not exposed to the environment
if not API_KEY or not API_SECRET:
    st.error("### 🔑 Missing API Configuration Credentials!")
    st.markdown(
        """
        The application could not locate your environment flags. Please configure them using one of these options:
        
        1. **Local Secret File (Recommended for Streamlit):** Create a folder `.streamlit/` containing a `secrets.toml` file:
           ```toml
           PAYTM_API_KEY = "your_key"
           PAYTM_API_SECRET = "your_secret"
           ```
        2. **System Terminal Variables:** Export them to your current terminal environment before running the server:
           ```bash
           export PAYTM_API_KEY="your_key"
           export PAYTM_API_SECRET="your_secret"
