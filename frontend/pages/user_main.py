import streamlit as st
import requests
from frontend.api_utils import get_api_url # Assuming api_utils exists
# Import functions for each tab's content (replace with actual imports)
# from frontend.user_pages import dashboard, request_service, view_requests, profile

# Function to handle logout (assuming similar logic exists)
def logout():
    response = requests.post(f"{get_api_url()}/users/logout")
    if response.status_code == 200:
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_info = None
        st.success("Logged out successfully!")
        st.rerun() # Rerun to redirect to login page
    else:
        st.error("Logout failed.")

# --- Page Configuration (Optional but Recommended) ---
# st.set_page_config(layout="wide") # Example: Use wide layout

# --- Check Login Status ---
if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "user":
    st.warning("Please log in as a user to access this page.")
    st.stop() # Stop execution if not logged in as user

# --- Header with Logout Button ---
col1, col2 = st.columns([0.9, 0.1])
with col1:
    st.title(f"Welcome, {st.session_state.user_info.get('username', 'User')}!")
with col2:
    if st.button("Logout", key="user_logout"):
        logout()

st.markdown("---") # Separator

# --- Tab Navigation ---
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Request Service", "View Requests", "Profile"])

with tab1:
    st.header("Dashboard")
    # dashboard.show() # Replace with actual function call or content
    st.write("User dashboard content goes here.")
    # Example: Display summary, recent activity, etc.

with tab2:
    st.header("Request New Service")
    # request_service.show() # Replace with actual function call or content
    st.write("Service request form goes here.")
    # Example: Use st.form for service requests

with tab3:
    st.header("My Service Requests")
    # view_requests.show() # Replace with actual function call or content
    st.write("List of user's service requests goes here.")
    # Example: Display requests in a table or list

with tab4:
    st.header("My Profile")
    # profile.show() # Replace with actual function call or content
    st.write("User profile management goes here.")
    # Example: Allow users to view/update their details

# --- Footer (Optional) ---
# st.markdown("---")
# st.text("Service Connect Application")
