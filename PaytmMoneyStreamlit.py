import streamlit as st
import requests
from urllib.parse import urlencode

# --- 1. CONFIGURATION & CREDENTIALS ---
st.set_page_config(page_title="Paytm Money Package-Free OAuth", layout="wide")

# Replace with your actual credentials from the Paytm Money Developer Console
API_KEY = "your_paytm_money_api_key"
API_SECRET = "your_paytm_money_api_secret"

# Ensure this matches the Redirect/Return URL in your console exactly
REDIRECT_URL = "http://localhost:8501/" 

# API Base URL Endpoint Layouts
AUTH_BASE_URL = "https://login.paytmmoney.com/merchant-login"
API_BASE_URL = "https://developer.paytmmoney.com"

# Keep state data safe over interface interactions using session_state
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None

# --- UI Header ---
st.title("🛡️ Paytm Money Native OAuth2 Handshake")
st.caption("A pure REST implementation running fully within Streamlit's state architecture.")
st.markdown("---")

# --- 2. THE HANDSHAKE: CATCHING RE-ENTRY PARAMETERS ---
# Detect query arguments pushed dynamically by Paytm's redirect browser routing
query_params = st.query_params

if "requestToken" in query_params and not st.session_state.jwt_token:
    request_token = query_params["requestToken"]
    st.info("⚡ Request Token detected! Finalizing security handshake...")

    with st.spinner("Exchanging token for secure JWT Session..."):
        try:
            # Paytm Money token generation uses the /accounts/v2/gettoken endpoint
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
                # Store the Access JWT inside the app context state
                st.session_state.jwt_token = response_data.get("access_token")
                
                st.success("🔒 Authorization Completed! Your credentials are now secured.")
                # Clear URL parameters to prevent redundant calls on refresh
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
        
        # Step 1: Formulate the explicit authorization login URL discoverable pattern
        auth_params = {
            "apiKey": API_KEY,
            "state": "streamlit_handshake_flow"
        }
        discovery_login_url = f"{AUTH_BASE_URL}?{urlencode(auth_params)}"
        
        # UI Button Action Trigger Container for Client Execution Redirect
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
                        st.info("Authenticated successfully, but your DEMAT portfolio currently contains no delivery shares.")
                    
                    with st.expander("Show Complete API JSON Metadata"):
                        st.json(data)
                else:
                    st.error(f"Holdings retrieval error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"Failed to access API gateway points: {e}")
else:
    st.info("💡 Application waiting for authentication. Use the sidebar button to login to your account.")