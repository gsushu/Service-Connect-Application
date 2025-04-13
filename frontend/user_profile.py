# filepath: d:\Other\adbms\Service-Connect-Application-main\frontend\user_profile.py
import streamlit as st
from client import session
import pandas as pd

# Function to display the profile page
def show_profile():
    st.subheader("User Details")
    try:
        response = session.get("http://localhost:8000/profile") # Requires JWT
        if response.status_code == 200:
            user_data = response.json()

            st.text_input("Username", value=user_data.get("username", "N/A"), disabled=True)

            with st.form("update_profile_form"):
                email = st.text_input("Email", value=user_data.get("email", ""))
                mobile = st.text_input("Mobile", value=user_data.get("mobile", ""))
                submitted = st.form_submit_button("Update Profile")
                if submitted:
                    update_data = {"email": email, "mobile": mobile}
                    try:
                        update_response = session.put("http://localhost:8000/profile", json=update_data) # Requires JWT
                        if update_response.status_code == 200:
                            st.success("Profile updated successfully!")
                            st.rerun() # Refresh to show updated data
                        else:
                            st.error(f"Failed to update profile: {update_response.json().get('detail', update_response.text)}")
                    except Exception as e:
                        st.error(f"Error updating profile: {e}")

        else:
            st.error(f"Failed to load profile: {response.json().get('detail', response.text)}")
    except Exception as e:
        st.error(f"Error loading profile: {e}")

    st.divider()

    # --- Manage Addresses ---
    st.subheader("My Addresses")

    # Fetch addresses
    addresses = []
    try:
        addr_response = session.get("http://localhost:8000/addresses") # Requires JWT
        if addr_response.status_code == 200:
            addresses = addr_response.json()
            if addresses:
                df_addr = pd.DataFrame(addresses)
                st.dataframe(df_addr[['location_id', 'address', 'pincode']], use_container_width=True)
            else:
                st.info("No addresses found. Add one below.")
        else:
             st.error(f"Failed to load addresses: {addr_response.json().get('detail', addr_response.text)}")
    except Exception as e:
        st.error(f"Error loading addresses: {e}")

    # Add new address form
    with st.expander("Add New Address"):
        with st.form("new_address_form", clear_on_submit=True):
            new_address = st.text_area("Full Address")
            new_pincode = st.text_input("Pincode")
            addr_submitted = st.form_submit_button("Add Address")
            if addr_submitted:
                if not new_address or not new_pincode:
                    st.warning("Please provide both address and pincode.")
                else:
                    addr_data = {"address": new_address, "pincode": new_pincode}
                    try:
                        add_resp = session.post("http://localhost:8000/addresses", json=addr_data) # Requires JWT
                        if add_resp.status_code == 200 or add_resp.status_code == 201:
                            st.success("Address added successfully!")
                            st.rerun() # Refresh address list
                        else:
                            st.error(f"Failed to add address: {add_resp.json().get('detail', add_resp.text)}")
                    except Exception as e:
                        st.error(f"Error adding address: {e}")

    # Add functionality to Edit/Delete addresses if needed (requires more backend endpoints and frontend logic)


if __name__ == "__main__":
     # Mock session state for direct execution testing
    if "access_token" not in st.session_state:
         st.session_state.access_token = "mock_token" # Add a mock token
         st.session_state.user_info = {"username": "testuser", "id": 1}
         st.session_state.role = "User"
    show_profile()