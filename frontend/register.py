import streamlit as st
from client import session  # Use the persistent session
import requests # Import requests for exception handling

# Function to fetch service categories
@st.cache_data(ttl=300) # Cache for 5 minutes
def fetch_service_categories():
    try:
        response = session.get("http://localhost:8000/service-categories")
        response.raise_for_status()
        return {cat['name']: cat['category_id'] for cat in response.json()}
    except Exception as e:
        st.error(f"Error fetching service categories: {e}")
        return {}

def app():
    st.title("Register")

    # Dropdown to select role
    role = st.selectbox("Select Role", options=["Worker", "User"])

    # Input fields for registration details
    username = st.text_input("Username")
    email = st.text_input("Email")
    mobile = st.text_input("Mobile")
    pincode = None
    selected_category_ids = [] # Initialize outside the if block

    if role == "Worker":
        employee_id = st.text_input("Employee Number")
        pincode = st.text_input("Pincode (Service Area)")

        # Fetch and display service categories for selection
        service_categories_map = fetch_service_categories()
        if service_categories_map:
            selected_category_names = st.multiselect(
                "Select Service Categories You Offer",
                options=list(service_categories_map.keys())
            )
            # Convert selected names back to IDs
            selected_category_ids = [service_categories_map[name] for name in selected_category_names]
        else:
            st.warning("Could not load service categories. You can add them later in your profile.")


    password = st.text_input("Password", type="password")

    # When the sign-up button is clicked, send the details to the signup endpoint
    if st.button("Sign Up"):
        if role == "Worker":
            # Validate worker-specific fields
            if not employee_id or not pincode:
                 st.error("Employee Number and Pincode are required for workers.")
                 return # Stop processing
            # Optional: Validate if at least one category is selected
            # if not selected_category_ids:
            #     st.error("Please select at least one service category.")
            #     return

            data = {
                "username": username,
                "email": email,
                "mobile": mobile,
                "password": password,
                "employee_number": employee_id,
                "pincode": pincode,
                "category_ids": selected_category_ids # Include selected category IDs
            }
            try:
                response = session.post("http://localhost:8000/worker/signup", json=data)
                # Check for 200 or 201 based on backend endpoint
                if response.status_code == 200 or response.status_code == 201:
                    st.success("Worker registration submitted for approval!")
                    st.info("Please wait for admin approval before logging in.")
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(f"Registration failed: {response.json().get('detail', response.text)}")
            except Exception as e:
                st.error(f"Error connecting to the server: {e}")
        else: # User registration
            data = {
                "username": username,
                "email": email,
                "mobile": mobile,
                "password": password
            }
            try:
                response = session.post("http://localhost:8000/signup", json=data)
                # Check for 200 or 201 based on backend endpoint
                if response.status_code == 200 or response.status_code == 201:
                    st.success("User registration successful!")
                    # Optionally log the user in directly or redirect to login
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(f"Registration failed: {response.json().get('detail', response.text)}")
            except Exception as e:
                st.error(f"Error connecting to the server: {e}")

    # Button to go back to the login page
    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

if __name__ == "__main__":
    app()
