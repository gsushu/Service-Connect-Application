import streamlit as st
from client import session  # Use the persistent session
import requests
import user_main  # Import user_main for dashboard access


st.set_page_config(page_title="Service Connect", page_icon=":guardsman:", layout="wide", initial_sidebar_state="collapsed")
# Initialize session state variables
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "role" not in st.session_state:
    st.session_state.role = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# --- Define Logout Function ---
def logout():
    st.session_state.access_token = None
    st.session_state.role = None
    st.session_state.user_info = None
    st.session_state.page = "login"
    # Optionally clear other states if needed
    st.rerun()

def validate_role_access(required_role):
    """Validates that the user has the required role to access a page"""
    current_role = st.session_state.get("role")
    if current_role != required_role:
        st.error(f"Access denied: You need to be logged in as {required_role} to access this page.")
        # Clear session state and redirect to login
        logout()
        return False
    return True

# --- Routing Logic ---
# Check if a role is set in the session state after successful login
is_logged_in = st.session_state.get("role") is not None

if is_logged_in: # Simplified check: if role is set, user is logged in
    # Sidebar Navigation for Logged-in Users
    # Ensure user_info exists before trying to access it
    user_info = st.session_state.get("user_info", {})
    st.sidebar.title(f"Welcome, {user_info.get('username', 'N/A')}!")
    st.sidebar.write(f"Role: {st.session_state.role}")
    st.sidebar.divider()

    if st.session_state.role == "User":
        # Add role validation before allowing access to user pages
        if validate_role_access("User"):
            user_main.show_dashboard()
            if st.sidebar.button("Logout"):
                logout() # User logout might need specific handling if JWT involved server-side

    elif st.session_state.role == "Worker":
        # Add role validation before allowing access to worker pages
        if validate_role_access("Worker"):
            if st.sidebar.button("Logout"):
                # Worker logout handling
                try:
                    # Ensure session object exists and is usable
                    if session:
                        # Call worker logout endpoint (uses session cookie automatically)
                        session.post("http://localhost:8000/worker/logout")
                    else:
                        st.sidebar.warning("Session object not available for logout.")
                except Exception as e:
                    st.sidebar.error(f"Logout failed: {e}") # Show error but proceed
                logout() # Clear frontend state

            # Import and show worker dashboard
            import worker_main
            worker_main.show_dashboard() # This should now work correctly with session auth

    elif st.session_state.role == "Admin":
        # Add role validation before allowing access to admin pages
        if validate_role_access("Admin"):
            if st.sidebar.button("Logout"):
                # Admin logout
                try:
                    session.post("http://localhost:8000/admin/logout") # Call admin logout endpoint
                except Exception as e:
                    st.sidebar.error(f"Logout failed: {e}") # Show error but proceed
                logout() # Clear frontend state

            # Import and show admin dashboard
            import admin_main
            admin_main.show_dashboard()

    else:
        # Fallback if role is invalid while logged in
        st.error("Invalid role detected. Logging out.")
        logout()

else:
    # Not logged in: Show Login or Register page
    if st.session_state.page == "login":
        import login
        login.app()
    elif st.session_state.page == "register":
        import register
        register.app()
    else: # Default to login
        st.session_state.page = "login"
        import login
        login.app()