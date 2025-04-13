import streamlit as st
import requests
from frontend.api_utils import get_api_url # Assuming api_utils exists
# Import functions for each tab's content (replace with actual imports)
# from frontend.worker_pages import dashboard, view_open, view_accepted, notifications, profile

# Function to handle logout (assuming similar logic exists)
def logout():
    response = requests.post(f"{get_api_url()}/workers/logout")
    if response.status_code == 200:
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_info = None
        st.success("Logged out successfully!")
        st.rerun() # Rerun to redirect to login page
    else:
        st.error("Logout failed.")

# --- Page Configuration (Optional but Recommended) ---
# st.set_page_config(layout="wide")

# --- Check Login Status ---
if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "worker":
    st.warning("Please log in as a worker to access this page.")
    st.stop() # Stop execution if not logged in as worker

# --- Header with Logout Button ---
col1, col2 = st.columns([0.9, 0.1])
with col1:
    st.title(f"Welcome, {st.session_state.user_info.get('username', 'Worker')}!")
with col2:
    if st.button("Logout", key="worker_logout"):
        logout()

st.markdown("---") # Separator

# --- Tab Navigation ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "View Open Requests", "My Accepted Requests", "Notifications", "Profile"])

with tab1:
    st.header("Worker Dashboard")
    # dashboard.show() # Replace with actual function call or content
    st.write("Worker dashboard content goes here.")
    # Example: Display stats, assigned tasks summary

with tab2:
    st.header("Available Service Requests")
    # view_open.show() # Replace with actual function call or content
    st.write("List of open service requests goes here.")
    # Example: Display requests available for quoting/acceptance

with tab3:
    st.header("My Accepted Requests")
    # view_accepted.show() # Replace with actual function call or content
    st.write("List of requests accepted by the worker goes here.")
    # Example: Display ongoing/quoted requests

with tab4:
    st.header("Notifications")
    # notifications.show() # Replace with actual function call or content
    st.write("Worker notifications go here.")
    # Example: Display alerts about new requests, updates, etc.

with tab5:
    st.header("My Profile")
    # profile.show() # Replace with actual function call or content
    st.write("Worker profile management goes here.")
    # Example: Allow workers to view/update their details, skills, etc.

# --- Footer (Optional) ---
# st.markdown("---")
# st.text("Service Connect Application")
