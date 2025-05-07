import streamlit as st
import requests
from client import session
import json  # Import json for parsing form data for user login
# Import our new style utilities
from utils.style_utils import apply_custom_css

def app():
    # Apply basic styling
    apply_custom_css()

    st.title("Service Connect")

    # Create a more visually appealing login container
    st.markdown("""
    <div style="padding: 20px; background-color: white; border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto;">
        <h2 style="text-align: center; margin-bottom: 20px; color: #2c3e50;">Login</h2>
    </div>
    """, unsafe_allow_html=True)

    # Add colorful role selector
    role_options = ["User", "Worker", "Admin"]
    role_colors = {
        "User": "#4e73df",  # Blue
        "Worker": "#1cc88a", # Green
        "Admin": "#e74a3b"   # Red
    }

    # Initialize selected_role in session state if not present
    if "selected_role" not in st.session_state:
        st.session_state.selected_role = "User"

    # Create a single radio selection for role
    st.write("### Select your role:")
    selected_role = st.radio(
        "Select role",
        role_options,
        index=role_options.index(st.session_state.selected_role),
        label_visibility="collapsed",
        horizontal=True,
        key="role_selector"
    )

    # Update session state with selected role
    st.session_state.selected_role = selected_role

    # Display colored role buttons (visual only)
    cols = st.columns(3)
    for i, role in enumerate(role_options):
        with cols[i]:
            bg_color = role_colors[role]
            # Add highlight effect if this is the selected role
            border = "3px solid #333" if role == selected_role else "none"
            opacity = "1.0" if role == selected_role else "0.7"

            st.markdown(f"""
            <div style="text-align: center;">
                <div style="background-color: {bg_color}; color: white; padding: 20px 10px;
                           border-radius: 10px; margin-bottom: 5px; border: {border}; opacity: {opacity}">
                    <h3 style="margin: 0;">{role}</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Get the selected role from session state
    role = st.session_state.selected_role
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # All authentication endpoints now expect form data
        if role == "User":
            url = "http://localhost:8000/login"
        elif role == "Worker":
            url = "http://localhost:8000/worker/login"
        elif role == "Admin":
            url = "http://localhost:8000/admin/login"
        else:
            st.error("Invalid role selected.")
            return

        try:
            # Send request with form data for all roles
            response = session.post(
                url,
                data={'username': username, 'password': password},
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code == 200:
                response_data = response.json()
                st.success("Login successful!")

                # For all roles, set role in session state and navigate to dashboard
                st.session_state.role = role
                st.session_state.user_info = {
                    "username": response_data.get("username", username),
                    "id": response_data.get(f"{role.lower()}_id") or response_data.get("id")
                }

                if role == "User":
                    # User uses JWT token
                    st.session_state.access_token = response_data.get("access_token")
                    st.session_state.token_type = response_data.get("token_type", "bearer")
                else:
                    # Admin & Worker use sessions, no token needed
                    st.session_state.access_token = None

                # Set page to appropriate dashboard
                st.session_state.page = f"{role.lower()}_dashboard"
                st.rerun()
            else:
                error_detail = response.json().get("detail", f"Login failed ({response.status_code}). Please check your credentials.")
                st.error(error_detail)
        except Exception as e:
            st.error(f"Error connecting to the server: {e}")

    if role != "Admin":
        if st.button("Register"):
            st.session_state.page = "register"
            st.session_state.register_role = role
            st.rerun()  # Use st.rerun()

if __name__ == "__main__":
    app()
