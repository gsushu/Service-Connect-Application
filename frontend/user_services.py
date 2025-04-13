# filepath: d:\Other\adbms\Service-Connect-Application-main\frontend\user_services.py
import streamlit as st
from client import session
import pandas as pd

# Function to display available services
def show_services():
    st.write("Here is a list of services offered on the platform.")

    try:
        # This endpoint might not strictly require authentication, depends on design
        # If it does, the token will be sent automatically by client.py
        response = session.get("http://localhost:8000/allservices")
        if response.status_code == 200:
            services_data = response.json()
            if services_data:
                df_services = pd.DataFrame(services_data)
                # Display relevant columns
                st.dataframe(df_services[['service_id', 'name', 'description']], use_container_width=True)
            else:
                st.info("No services currently available.")
        else:
            st.error(f"Failed to load services: {response.json().get('detail', response.text)}")
    except Exception as e:
        st.error(f"Error loading services: {e}")

if __name__ == "__main__":
    # Mock session state for direct execution testing (optional)
    if "access_token" not in st.session_state:
         st.session_state.access_token = "mock_token"
         st.session_state.user_info = {"username": "testuser", "id": 1}
         st.session_state.role = "User"
    show_services()