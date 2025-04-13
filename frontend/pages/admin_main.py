import streamlit as st
import requests
from frontend.api_utils import get_api_url # Assuming api_utils exists
# Import functions for each tab's content (replace with actual imports)
# from frontend.admin_pages import dashboard, manage_users, manage_workers, manage_services

# Function to handle logout (assuming similar logic exists)
def logout():
    response = requests.post(f"{get_api_url()}/admins/logout")
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
if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "admin":
    st.warning("Please log in as an admin to access this page.")
    st.stop() # Stop execution if not logged in as admin

# --- Header with Logout Button ---
col1, col2 = st.columns([0.9, 0.1])
with col1:
    st.title(f"Admin Panel - Welcome, {st.session_state.user_info.get('username', 'Admin')}!")
with col2:
    if st.button("Logout", key="admin_logout"):
        logout()

st.markdown("---") # Separator

# --- Tab Navigation ---
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Manage Users", "Manage Workers", "Manage Services"])

with tab1:
    st.header("Admin Dashboard")
    # dashboard.show() # Replace with actual function call or content
    st.write("Admin dashboard overview goes here.")
    # Example: Display system statistics, pending approvals, etc.

with tab2:
    st.header("Manage Users")
    # manage_users.show() # Replace with actual function call or content
    st.write("User management interface goes here.")
    # Example: Table of users with options to view/edit/delete

with tab3:
    st.header("Manage Workers")
    # manage_workers.show() # Replace with actual function call or content
    st.write("Worker management interface goes here.")
    # Example: Table of workers with options to view/approve/edit/delete

with tab4:
    st.header("Manage Services")
    # manage_services.show() # Replace with actual function call or content
    st.write("Service type management interface goes here.")
    # Example: Add/edit/remove service categories offered

# --- Footer (Optional) ---
# st.markdown("---")
# st.text("Service Connect Application - Admin")
