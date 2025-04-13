import streamlit as st
from client import session
import pandas as pd  # For better table display
from datetime import datetime # Import datetime for formatting
import requests # Import requests for exception handling
import json # Import json for error parsing
from user_profile import show_profile # Import the profile function
from user_services import show_services # Import the services function

# Helper function for API error handling (similar to worker_main)
def handle_api_error(e, action_msg="perform action"):
    error_detail = "Unknown error"
    status_code = 'N/A'
    if isinstance(e, requests.exceptions.RequestException) and e.response is not None:
        status_code = e.response.status_code
        try:
            error_detail = e.response.json().get('detail', e.response.text)
        except json.JSONDecodeError:
            error_detail = e.response.text
    st.error(f"Failed to {action_msg}: {error_detail} (Status: {status_code})")

# Function to format datetime (similar to worker_main)
def format_datetime(dt_str):
    if dt_str:
        try:
            dt = datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return str(dt_str) # Fallback
    return "N/A"

# Function to display the main user interface with tabs
def show_dashboard(): # Renamed back from user_interface
    st.title("User Portal")
    # Note: Logout button is typically handled in the main app.py using columns for layout
    # Example for main app.py:
    # col1, col2 = st.columns([0.9, 0.1])
    # with col1:
    #     st.title("User Portal")
    # with col2:
    #     if st.button("Logout"):
    #         # Logout logic here (clear session state, etc.)
    #         st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📝 Create Request", "📋 My Requests", "👤 My Profile", "🛠️ Show Services"]) # Added Profile tab

    with tab1:
        st.header("Welcome to your Dashboard")
        st.markdown("---")
        st.write("Overview and summary information can be displayed here.")
        # Add any relevant dashboard widgets or summaries later

    with tab2:
        st.header("Create New Service Request")
        st.markdown("---") # Add a horizontal rule for visual separation

        # Fetch available services for dropdown
        services = {}
        try:
            response = session.get("http://localhost:8000/allservices")
            if response.status_code == 200:
                services_data = response.json()
                if services_data: # Check if data is not empty
                    services = {s['name']: s['service_id'] for s in services_data}
                else:
                    st.warning("No services available to select.")
            else:
                st.warning(f"Could not load services list ({response.status_code}).")
        except Exception as e:
            st.error(f"Error loading services: {e}")
            services = {} # Ensure services is empty on error

        # Fetch user locations for dropdown
        locations = {}
        try:
            response = session.get("http://localhost:8000/addresses")  # Requires JWT
            if response.status_code == 200:
                locations_data = response.json()
                if locations_data: # Check if data is not empty
                    locations = {f"{loc['address']} ({loc['pincode']})": loc['location_id'] for loc in locations_data}
                else:
                    st.warning("No locations found. Add an address in your profile first.")
            else:
                st.warning(f"Could not load locations ({response.status_code}). Add an address in your profile.")
        except Exception as e:
            st.error(f"Error loading locations: {e}")
            locations = {} # Ensure locations is empty on error

        # Only show form if services and locations are available
        if services and locations:
            with st.form("new_request_form", clear_on_submit=True):
                selected_service_name = st.selectbox("Select Service", options=list(services.keys()), key="new_req_service")
                selected_location_desc = st.selectbox("Select Location", options=list(locations.keys()), key="new_req_loc")
                description = st.text_area("Description / Details", key="new_req_desc", placeholder="Describe the issue...")
                urgency_level = st.selectbox("Urgency Level", options=["Low", "Medium", "High"], index=1, key="new_req_urgency") # Added urgency
                additional_notes = st.text_area("Additional Notes (Optional)", key="new_req_notes", placeholder="e.g., specific instructions, gate codes...") # Added notes
                # Add optional initial price quote
                user_quoted_price = st.number_input("Your Initial Price Quote (Optional, 0 to skip)", min_value=0.0, format="%.2f", key="new_req_price")

                submitted = st.form_submit_button("Submit Request", type="primary") # Use primary button style
                if submitted:
                    # Double-check selections inside the submit block
                    if not selected_service_name or not selected_location_desc or not description: # Ensure description is also filled
                        st.error("Please select a service, location, and provide a description.")
                    else:
                        service_id = services[selected_service_name]
                        location_id = locations[selected_location_desc]
                        data = {
                            "service_id": service_id,
                            "description": description,
                            "location_id": location_id,
                            "urgency_level": urgency_level, # Include urgency
                            "additional_notes": additional_notes, # Include notes
                            # Include price only if > 0
                            "user_quoted_price": user_quoted_price if user_quoted_price > 0 else None
                        }
                        try:
                            response = session.post("http://localhost:8000/requests", json=data)
                            if response.status_code == 200 or response.status_code == 201:
                                st.success("✅ Request created successfully! Check the 'My Requests' tab.")
                                # Consider if rerun is needed or just clear form
                            else:
                                handle_api_error(response.raise_for_status(), "create service request") # Use handler
                        except requests.exceptions.RequestException as e:
                             handle_api_error(e, "create service request")
                        except Exception as e:
                            st.error(f"❌ An unexpected error occurred: {e}")
        elif not services:
             st.info("ℹ️ Cannot create requests as no services are currently defined.")
        elif not locations:
             st.info("ℹ️ Cannot create requests. Please add an address in your Profile page first.")


    with tab3:
        st.header("My Service Requests")
        st.markdown("---")
        try:
            response = session.get("http://localhost:8000/myrequests")  # Requires JWT
            response.raise_for_status() # Raise HTTPError for bad responses
            my_requests_data = response.json()

            if my_requests_data:
                df = pd.DataFrame(my_requests_data)
                # Select and rename columns for better readability
                display_cols = {
                    'request_id': 'ID',
                    'service_id': 'Service ID', # Consider joining service name later
                    'status': 'Status',
                    'description': 'Description',
                    'user_quoted_price': 'Your Price',
                    'worker_quoted_price': 'Worker Price',
                    'final_price': 'Final Price',
                    'worker_comments': 'Worker Comments',
                    'created_at': 'Created',
                    'updated_at': 'Last Updated'
                }
                # Ensure all columns exist in the dataframe, add if missing
                for col in display_cols.keys():
                    if col not in df.columns:
                        df[col] = None

                df_display = df[list(display_cols.keys())].copy()
                df_display.rename(columns=display_cols, inplace=True)

                # Format datetime columns
                df_display['Created'] = df_display['Created'].apply(format_datetime)
                df_display['Last Updated'] = df_display['Last Updated'].apply(format_datetime)

                # Format price columns
                for price_col in ['Your Price', 'Worker Price', 'Final Price']:
                    df_display[price_col] = df_display[price_col].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")

                # Function to apply color based on status
                def style_status(status):
                    if status == 'pending':
                        return 'background-color: #FFF3CD; color: #856404;' # Yellowish
                    elif status == 'negotiating':
                        return 'background-color: #CCE5FF; color: #004085;' # Bluish
                    elif status == 'accepted':
                        return 'background-color: #D4EDDA; color: #155724;' # Greenish
                    elif status == 'inprogress':
                        return 'background-color: #D1ECF1; color: #0C5460;' # Cyanish
                    elif status == 'completed':
                        return 'background-color: #C3E6CB; color: #155724; font-weight: bold;' # Darker Green
                    elif status == 'cancelled':
                        return 'background-color: #F8D7DA; color: #721C24;' # Reddish
                    else:
                        return '' # Default style

                # Display the main dataframe
                st.dataframe(
                    df_display.style.applymap(style_status, subset=['Status']),
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()
                st.subheader("Request Actions")

                # Iterate through requests to provide actions
                for index, req in df.iterrows():
                    req_id = req['request_id']
                    status = req['status']
                    user_price = req['user_quoted_price']
                    worker_price = req['worker_quoted_price']
                    can_quote = status in ['pending', 'negotiating']
                    can_agree = status == 'negotiating' and user_price is not None and worker_price is not None and user_price == worker_price

                    # Use an expander for actions on pending/negotiating requests
                    if can_quote or can_agree:
                        with st.expander(f"Actions for Request ID: {req_id} (Status: {status.upper()})"):
                            st.write(f"**Description:** {req.get('description', 'N/A')}")
                            st.write(f"**Your Current Quote:** {f'${user_price:.2f}' if user_price else 'Not set'}")
                            st.write(f"**Worker's Current Quote:** {f'${worker_price:.2f}' if worker_price else 'Not set'}")
                            if req.get('worker_comments'):
                                st.info(f"**Worker Comments:** {req['worker_comments']}")

                            # --- User Quote/Update Price Form ---
                            if can_quote:
                                with st.form(f"quote_form_{req_id}", clear_on_submit=False):
                                    new_price = st.number_input(
                                        "Set/Update Your Price Quote",
                                        min_value=0.01,
                                        value=float(user_price) if user_price else 10.0, # Sensible default or current price
                                        format="%.2f",
                                        key=f"price_input_{req_id}"
                                    )
                                    quote_submitted = st.form_submit_button("Submit/Update My Price")
                                    if quote_submitted:
                                        try:
                                            quote_resp = session.put(
                                                f"http://localhost:8000/requests/{req_id}/quote",
                                                json={"price": new_price}
                                            )
                                            quote_resp.raise_for_status()
                                            st.success(f"Price updated for request {req_id}!")
                                            st.rerun() # Rerun to refresh this tab's data
                                        except requests.exceptions.RequestException as e:
                                            handle_api_error(e, f"update price for request {req_id}")
                                        except Exception as e:
                                            st.error(f"An unexpected error occurred: {e}")

                            # --- User Agree Price Button ---
                            if can_agree:
                                st.write("---") # Separator
                                if st.button(f"Agree to Price (${user_price:.2f}) for Request {req_id}", key=f"agree_btn_{req_id}", type="primary"):
                                    try:
                                        agree_resp = session.put(f"http://localhost:8000/requests/{req_id}/agree")
                                        agree_resp.raise_for_status()
                                        st.success(f"Price agreed for request {req_id}! Status updated.")
                                        st.rerun() # Rerun to refresh this tab's data
                                    except requests.exceptions.RequestException as e:
                                        handle_api_error(e, f"agree to price for request {req_id}")
                                    except Exception as e:
                                        st.error(f"An unexpected error occurred: {e}")
                            elif status == 'negotiating' and user_price is not None and worker_price is not None and user_price != worker_price:
                                st.warning("Prices do not match. Cannot agree yet.")
                            elif status == 'negotiating' and (user_price is None or worker_price is None):
                                 st.warning("Both parties must quote a price before agreement is possible.")

            else:
                st.info("ℹ️ You haven't created any service requests yet.")

        except requests.exceptions.RequestException as e:
            handle_api_error(e, "fetch service requests")
        except Exception as e:
            st.error(f"❌ Error processing service requests: {e}")

    with tab4: # Content for the new Profile tab
        # Call the profile function to display user profile details
        show_profile()
        # Consider adding a button to refresh the profile data if needed
        if st.button("Refresh Profile Data"):
            show_profile()
            st.success("Profile data refreshed!")

    with tab5:
        # Consider adding a button to refresh the services data if needed
        if st.button("Refresh Services Data"):
            show_services()
            st.success("Services data refreshed!")


# Keep the main guard if you want to run this file directly for testing
if __name__ == "__main__":
    # Mock session state for direct execution testing
    if "access_token" not in st.session_state:
        st.session_state.access_token = "mock_token"  # Add a mock token
        st.session_state.user_info = {"username": "testuser", "id": 1}
        st.session_state.role = "User"
    show_dashboard() # Call the renamed function
