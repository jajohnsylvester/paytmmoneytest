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
           ```
        """
    )
    st.stop()

# --- 2. ENDPOINT STRUCTURE CONFIGURATIONS ---
REDIRECT_URL = "http://localhost:8501/" 
AUTH_BASE_URL = "https://login.paytmmoney.com/merchant-login"
API_BASE_URL = "https://developer.paytmmoney.com"

# Keep the JWT alive inside Streamlit's session state structure
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None

# --- UI Header Layout ---
st.title("🛡️ Paytm Money Native OAuth2 Portal")
st.caption("Zero-dependency architecture accessing configuration metrics securely via os.environ.")
st.markdown("---")

# --- 3. THE HANDSHAKE: CATCHING THE INCOMING REDIRECT TOKEN ---
query_params = st.query_params

if "requestToken" in query_params and not st.session_state.jwt_token:
    request_token = query_params["requestToken"]
    st.info("⚡ Callback intercepted! Executing session exchange token payload...")

    with st.spinner("Exchanging token for secure JWT Session..."):
        try:
            # Paytm Money API v2 endpoint for token processing
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
                
                st.success("🔒 Session successfully verified and token locked!")
                st.query_params.clear()  # Purge token parameter from URL address bar
                st.rerun()
            else:
                st.error(f"Handshake Rejected ({response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"Network processing failed: {e}")

# --- 4. SIDEBAR MANAGEMENT INTERFACES ---
with st.sidebar:
    st.header("Authentication Status")
    
    if not st.session_state.jwt_token:
        st.warning("⚠️ Access Status: Disconnected")
        
        # Build discovery login redirection path parameters
        auth_params = {
            "apiKey": API_KEY,
            "state": "streamlit_prod_session"
        }
        discovery_login_url = f"{AUTH_BASE_URL}?{urlencode(auth_params)}"
        
        # Safe embedded browser redirect element structured as an actionable button link
        st.markdown(
            f'<a href="{discovery_login_url}" target="_self" style="text-decoration:none;">'
            f'<div style="background-color:#00baf2;color:white;text-align:center;padding:12px;border-radius:6px;font-weight:bold;cursor:pointer;">'
            f'🔑 Connect Paytm Money Account'
            f'</div></a>', 
            unsafe_allow_html=True
        )
    else:
        st.success("🛰️ Status: Verified Gateway")
        if st.button("Disconnect Session"):
            st.session_state.jwt_token = None
            st.query_params.clear()
            st.rerun()

# --- 5. MAIN CORE DATA DISPLAY WRAPPERS ---
if st.session_state.jwt_token:
    st.subheader("Your Real-time Demat Portfolio Holdings")
    
    if st.button("Fetch Account Holdings", type="primary"):
        with st.spinner("Extracting portfolio entries..."):
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
                        st.metric(label="Total Unique Positions", value=len(holdings_list))
                        st.dataframe(holdings_list, use_container_width=True)
                    else:
                        st.info("Authentication worked cleanly, but this Demat portfolio contains zero delivery shares.")
                    
                    with st.expander("Inspect Raw JSON Metadata"):
                        st.json(data)
                else:
                    st.error(f"Holdings retrieval error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Failed to access API gateway points: {e}")
else:
    st.info("👋 Use the sidebar link to trigger authorization login. Once returned, your portfolio controls will unlock here.")
