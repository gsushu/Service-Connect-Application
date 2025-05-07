import streamlit as st
from client import session
import pandas as pd  # For better table display
from datetime import datetime # Import datetime for formatting
import requests # Import requests for exception handling
import json # Import json for error parsing
from user_profile import show_profile # Import the profile function
from user_services import show_services # Import the services function
# Import our new style utilities
from utils.style_utils import apply_custom_css, add_role_based_styles, format_status_with_badge, display_welcome_header

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
def show_dashboard():
    # Check if user has the correct role
    if st.session_state.get("role") != "User":
        st.error("Access denied: This page is only accessible to users.")
        # Return early to prevent showing the content
        return

    # Apply our custom CSS styling
    apply_custom_css()
    add_role_based_styles("User")

    user_info = st.session_state.get("user_info", {})
    user_id = user_info.get("id")
    access_token = st.session_state.get("access_token")

    # Display welcome header with username
    display_welcome_header(user_info.get("username", "User"), "User")

    # --- Placeholder for WebSocket Connection ---
    # Display toast notifications if any exist in session state
    if 'new_notification' in st.session_state and st.session_state.new_notification:
        st.toast(st.session_state.new_notification, icon="🔔")
        st.session_state.new_notification = None # Clear notification after showing

    tab2, tab3, tab4, tab5 = st.tabs(["📝 Create Request", "📋 My Requests", "👤 My Profile", "🛠️ Show Services"]) # Added Profile tab

    with tab2:
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
        st.subheader("My Service Requests")
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
                    'user_quoted_price': 'Your Initial Price', # Renamed for clarity
                    'created_at': 'Created',
                    'updated_at': 'Last Updated'
                }
                # Ensure all columns exist in the dataframe, add if missing
                for col in display_cols.keys():
                    if col not in df.columns:
                        df[col] = None
                # Add quotes column if missing (will be list or None)
                if 'quotes' not in df.columns:
                    df['quotes'] = None

                df_display = df[list(display_cols.keys())].copy()
                df_display.rename(columns=display_cols, inplace=True)

                # Format datetime columns
                df_display['Created'] = df_display['Created'].apply(format_datetime)
                df_display['Last Updated'] = df_display['Last Updated'].apply(format_datetime)

                # Format price columns
                df_display['Your Initial Price'] = df_display['Your Initial Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")

                # Update status column to use HTML badges
                df_display['Status'] = df_display['Status'].apply(lambda x: format_status_with_badge(x))

                # Display the main dataframe with HTML formatting
                st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

                st.divider()
                st.subheader("Manage Requests & View Quotes")

                # Iterate through requests to provide actions and display quotes
                for index, req in df.iterrows():
                    req_id = req['request_id']
                    status = req['status']
                    user_price = req['user_quoted_price'] # User's initial price

                    # Expander for each request
                    with st.expander(f"Details for Request ID: {req_id} (Status: {status.upper()})"):
                        st.write(f"**Description:** {req.get('description', 'N/A')}")
                        st.write(f"**Your Initial Price:** {f'${user_price:.2f}' if user_price else 'Not set'}")

                        # Display Quotes Section
                        st.markdown("**Received Quotes:**")
                        quotes = [] # Initialize empty list for quotes
                        fetch_error = None
                        if status in ['pending', 'quoted']:
                            try:
                                quotes_resp = session.get(f"http://localhost:8000/requests/{req_id}/quotes")
                                quotes_resp.raise_for_status()
                                quotes = quotes_resp.json()
                            except requests.exceptions.RequestException as e:
                                fetch_error = e
                            except Exception as e:
                                fetch_error = e

                        if fetch_error:
                            st.error(f"Could not load quotes for request {req_id}: {fetch_error}")
                        elif status in ['pending', 'quoted'] and quotes:
                            for quote in quotes:
                                quote_id = quote.get('quote_id')
                                worker_id = quote.get('worker_id')
                                worker_username = quote.get('worker_username', f'Worker {worker_id}')
                                quote_price = quote.get('worker_quoted_price')
                                quote_comments = quote.get('worker_comments', 'No comments')
                                quote_created = format_datetime(quote.get('created_at'))

                                quote_col1, quote_col2 = st.columns([3, 1])
                                with quote_col1:
                                    price_display = f"${quote_price:.2f}" if quote_price is not None else "N/A"
                                    st.markdown(f"- **{worker_username}**: {price_display} ({quote_created})")
                                    st.caption(f"> {quote_comments}")
                                with quote_col2:
                                    if status in ['pending', 'quoted'] and quote_id:
                                        if st.button(f"Accept Quote {quote_id}", key=f"accept_quote_{req_id}_{quote_id}", type="primary"):
                                            try:
                                                accept_resp = session.post(f"http://localhost:8000/requests/{req_id}/accept_quote/{quote_id}")
                                                accept_resp.raise_for_status()
                                                st.success(f"Quote {quote_id} from {worker_username} accepted for request {req_id}! Status updated.")
                                                st.rerun()
                                            except requests.exceptions.RequestException as e:
                                                handle_api_error(e, f"accept quote {quote_id} for request {req_id}")
                                            except Exception as e:
                                                st.error(f"An unexpected error occurred: {e}")
                                st.markdown("---")
                        elif status in ['pending', 'quoted'] and not quotes and not fetch_error:
                            st.info("No quotes received yet.")
                        elif status not in ['pending', 'quoted']:
                             st.info(f"Request is in '{status}' status. Quotes are not applicable or viewable here.")

                        if status in ['pending', 'quoted']:
                             st.markdown("**Update Your Initial Price (Optional):**")
                             with st.form(f"quote_form_{req_id}", clear_on_submit=False):
                                 new_price = st.number_input(
                                     "Set/Update Your Initial Price",
                                     min_value=0.01,
                                     value=float(user_price) if user_price else 10.0,
                                     format="%.2f",
                                     key=f"price_input_{req_id}"
                                 )
                                 quote_submitted = st.form_submit_button("Update My Initial Price")
                                 if quote_submitted:
                                     try:
                                         quote_resp = session.put(
                                             f"http://localhost:8000/requests/{req_id}/quote",
                                             json={"price": new_price}
                                         )
                                         quote_resp.raise_for_status()
                                         st.success(f"Initial price updated for request {req_id}!")
                                         st.rerun()
                                     except requests.exceptions.RequestException as e:
                                         handle_api_error(e, f"update initial price for request {req_id}")
                                     except Exception as e:
                                         st.error(f"An unexpected error occurred: {e}")

            else:
                st.info("ℹ️ You haven't created any service requests yet.")

        except requests.exceptions.RequestException as e:
            handle_api_error(e, "fetch service requests")
        except Exception as e:
            st.error(f"❌ Error processing service requests: {e}")

    with tab4:
        show_profile()

    with tab5:
        show_services()

# Keep the main guard if you want to run this file directly for testing
if __name__ == "__main__":
    if "access_token" not in st.session_state:
        st.session_state.access_token = "mock_token"
        st.session_state.user_info = {"username": "testuser", "id": 1}
        st.session_state.role = "User"
    show_dashboard()