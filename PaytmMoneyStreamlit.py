import os
import streamlit as st
import requests
from urllib.parse import urlencode

# --- 1. CONFIGURATION & SECURE CREDENTIALS ---
st.set_page_config(page_title="Paytm Money Secure REST OAuth", layout="wide")

# Retrieve keys from environment variables
API_KEY = os.environ.get("PAYTM_API_KEY")
API_SECRET = os.environ.get("PAYTM_API_SECRET")

# Safeguard check: Alert the user if the environment variables are missing
if not API_KEY or not API_SECRET:
    st.error("🔑 **Missing Credentials:** Please set `PAYTM_API_KEY` and `PAYTM_API_SECRET` in your environment or `.streamlit/secrets.toml` file.")
    st.stop()

# Ensure this matches the Redirect/Return URL in your developer console exactly
REDIRECT_URL = "http://localhost:8501/" 

# API Base URL Endpoint Layouts
AUTH_BASE_URL = "https://login.paytmmoney.com/merchant-login"
API_BASE_URL = "https://developer.paytmmoney.com"

# Keep state data safe over interface interactions using session_state
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None

# --- UI Header ---
st.title("🛡️ Secure Paytm Money OAuth2 Handshake")
st.caption("Credentials loaded safely from environment variables.")
st.markdown("---")

# --- 2. THE HANDSHAKE: CATCHING RE-ENTRY PARAMETERS ---
query_params = st.query_params

if "requestToken" in query_params and not st.session_state.jwt_token:
    request_token = query_params["requestToken"]
    st.info("⚡ Request Token detected! Finalizing security handshake...")

    with st.spinner("Exchanging token for secure JWT Session..."):
        try:
            token_endpoint = f"{API_BASE_URL}/accounts/v2/gettoken"
            
            payload = {
                "api_key": API_KEY,
                "api_secret_key": API_SECRET,
                "request_token": request_token
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(token_endpoint, json=payload, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                st.session_state.jwt_token = response_data.get("access_token")
                
                st.success("🔒 Authorization Completed! Your credentials are now secured.")
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"Handshake Rejected ({response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"Network processing failed: {e}")

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Session Management")
    
    if not st.session_state.jwt_token:
        st.warning("⚠️ Access Status: Unauthorized")
        
        auth_params = {
            "apiKey": API_KEY,
            "state": "streamlit_handshake_flow"
        }
        discovery_login_url = f"{AUTH_BASE_URL}?{urlencode(auth_params)}"
        
        st.markdown(
            f'<a href="{discovery_login_url}" target="_self" style="text-decoration:none;">'
            f'<div style="background-color:#00baf2;color:white;text-align:center;padding:12px;border-radius:6px;font-weight:bold;cursor:pointer;">'
            f'🔑 Authorize App via Paytm'
            f'</div></a>', 
            unsafe_allow_html=True
        )
    else:
        st.success("🛰️ Connected to Core API Gateway")
        if st.button("Reset Session & Logout"):
            st.session_state.jwt_token = None
            st.query_params.clear()
            st.rerun()

# --- 4. DATA PORTAL ACTION PANEL ---
if st.session_state.jwt_token:
    st.subheader("📊 Live Portfolio Holdings")
    
    if st.button("Fetch Current Holdings", type="primary"):
        with st.spinner("Extracting active assets..."):
            try:
                holdings_endpoint = f"{API_BASE_URL}/holdings/v1/get-user-holdings-data"
                headers = {
                    "x-jwt-token": st.session_state.jwt_token,
                    "Accept": "application/json"
                }
                
                response = requests.get(holdings_endpoint, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    holdings_list = data.get("results", [])
                    
                    if holdings_list:
                        st.metric(label="Total Unique Assets", value=len(holdings_list))
                        st.dataframe(holdings_list, use_container_width=True)
                    else:
                        st.info("Authenticated successfully, but your portfolio currently contains no delivery shares.")
                    
                    with st.expander("Show Complete API JSON Metadata"):
                        st.json(data)
                else:
                    st.error(f"Holdings retrieval error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Failed to access API gateway points: {e}")
else:
    st.info("💡 Application waiting for authentication. Use the sidebar button to login to your account.")
