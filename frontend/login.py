import streamlit as st
from client import session
import json # Import json for parsing form data for user login

def app():
    st.title("Login Page")

    role = st.selectbox("Select Role", options=["User", "Worker", "Admin"], index=0)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        url = None
        data = None
        headers = {'Content-Type': 'application/x-www-form-urlencoded'} # Header for form data

        if role == "User":
            url = "http://localhost:8000/login"
            # User login now expects form data due to OAuth2PasswordRequestForm
            data = {'username': username, 'password': password}
            # We will send data as x-www-form-urlencoded, not JSON
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        elif role == "Worker":
            url = "http://localhost:8000/worker/login"
            data = {"username": username, "password": password} # Worker login still uses JSON
            headers = {'Content-Type': 'application/json'}
        elif role == "Admin":
            url = "http://localhost:8000/admin/login"
            data = {"username": username, "password": password} # Admin login still uses JSON
            headers = {'Content-Type': 'application/json'}
        else:
            st.error("Invalid role selected.")
            return

        try:
            # Send request with appropriate data format and headers
            if role == "User":
                 # For form data, pass data directly to 'data' param, not 'json'
                response = session.post(url, data=data, headers=headers)
            else:
                # For Worker/Admin, use json param
                response = session.post(url, json=data, headers=headers)


            if response.status_code == 200:
                st.success("Login successful!")
                response_data = response.json()

                # --- Handle different roles ---
                if role == "Admin":
                    # Admin login uses sessions, doesn't return access_token
                    # Check for expected admin data instead
                    if "admin_id" in response_data and "username" in response_data:
                        st.session_state.role = role
                        st.session_state.user_info = {
                            "username": response_data["username"],
                            "id": response_data["admin_id"]
                        }
                        st.session_state.access_token = None # Explicitly set token to None for Admin
                        st.session_state.page = "admin_dashboard" # Navigate to admin dashboard
                        st.rerun()
                    else:
                        st.error("Admin login succeeded but response data is missing expected fields.")

                elif role == "Worker":
                    # Worker login uses sessions, check for worker_id and username
                    if "worker_id" in response_data and "username" in response_data:
                        st.session_state.role = role
                        st.session_state.user_info = {
                            "username": response_data["username"],
                            "id": response_data["worker_id"]
                        }
                        st.session_state.access_token = None # Explicitly set token to None for Worker
                        st.session_state.page = "worker_dashboard" # Navigate to worker dashboard
                        st.rerun()
                    else:
                        st.error("Worker login succeeded but response data is missing expected fields.")

                elif role == "User":
                    # User uses JWT
                    if "access_token" in response_data:
                        st.session_state.access_token = response_data["access_token"]
                        st.session_state.token_type = response_data.get("token_type", "bearer")
                        st.session_state.user_info = {
                            "username": response_data.get("username", username),
                            "id": response_data.get("user_id") # User ID from token payload
                        }
                        st.session_state.role = role
                        st.session_state.page = f"{role.lower()}_dashboard" # Navigate based on role
                        st.rerun()
                    else:
                        # Handle cases where login is successful but no token is returned
                        st.error("Login successful, but no authentication token received.")
                else:
                     st.error("Login successful, but encountered an unexpected role.")


            else:
                error_detail = response.json().get("detail", f"Login failed ({response.status_code}). Please check your credentials.")
                st.error(error_detail)
        except Exception as e:
            st.error(f"Error connecting to the server: {e}")

    if role != "Admin":
        if st.button("Register"):
            st.session_state.page = "register"
            st.session_state.register_role = role
            st.rerun() # Use st.rerun()

if __name__ == "__main__":
    app()
