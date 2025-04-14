import streamlit as st
from client import session
import pandas as pd
from datetime import datetime
import requests
import json
from typing import Optional, Dict # Import Optional, Dict

# Helper function to format datetime (same as admin_main)
def format_datetime(dt_str):
    if dt_str:
        try:
            dt = datetime.fromisoformat(str(dt_str).replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return str(dt_str) # Fallback
    return "N/A"

# Helper function for API error handling
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

# Function to fetch service categories (similar to register.py)
@st.cache_data(ttl=300) # Cache for 5 minutes
def fetch_service_categories() -> Dict[str, int]:
    try:
        response = session.get("http://localhost:8000/service-categories")
        response.raise_for_status()
        # Return name: id mapping
        return {cat['name']: cat['category_id'] for cat in response.json()}
    except Exception as e:
        # Don't show error directly here, handle it where called
        print(f"Error fetching service categories: {e}") # Log error
        return {}

# Function to display the worker dashboard
def show_dashboard():
    user_info = st.session_state.get("user_info", {})
    st.write(f"Welcome, {user_info.get('username', 'Worker')}!")
    service_categories_map = fetch_service_categories()
    # Create reverse map for displaying names from IDs
    category_id_to_name_map = {v: k for k, v in service_categories_map.items()}

    # Add "Create Service" tab
    tab_open, tab_active, tab_create_service, tab_history, tab_profile = st.tabs([
        "📢 Open Requests", "⚡ My Active Requests", "➕ Create Service", "📜 History", "⚙️ Profile"
    ])

    # --- Tab 1: Open Requests (Pending) ---
    with tab_open:
        st.subheader("Available Service Requests (Nearby & Pending)")
        try:
            response = session.get("http://localhost:8000/worker/openrequests")
            response.raise_for_status()
            open_requests = response.json()

            if open_requests:
                df_open = pd.DataFrame(open_requests)
                # Format and select columns
                df_open['created_at'] = df_open['created_at'].apply(format_datetime)
                # Add user price if available
                if 'user_quoted_price' not in df_open.columns:
                    df_open['user_quoted_price'] = None
                # Add address/pincode if available
                if 'user_address' not in df_open.columns: df_open['user_address'] = 'N/A'
                if 'user_pincode' not in df_open.columns: df_open['user_pincode'] = 'N/A'

                df_open_display = df_open[[
                    'request_id', 'service_id', 'description', 'urgency_level',
                    'user_address', 'user_pincode', # Added address fields
                    'user_quoted_price', 'created_at'
                ]].copy()
                df_open_display.rename(columns={
                    'request_id': 'ID', 'service_id': 'Service ID', 'description': 'Description',
                    'urgency_level': 'Urgency',
                    'user_address': 'User Address', 'user_pincode': 'User Pincode', # Renamed
                    'user_quoted_price': 'User Price', 'created_at': 'Created'
                }, inplace=True)
                # Format price
                df_open_display['User Price'] = df_open_display['User Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")

                st.dataframe(df_open_display, use_container_width=True, hide_index=True)

                # --- Quote Price for Open Request ---
                st.divider()
                st.subheader("Quote Price for a Request")
                st.caption("Submitting a quote will assign the request to you and change its status to 'Negotiating'.")

                open_request_ids = [req['request_id'] for req in open_requests]
                selected_request_id_quote = st.selectbox(
                    "Select Request ID to Quote",
                    options=[""] + open_request_ids,
                    key="quote_open_request_select"
                )

                if selected_request_id_quote:
                    # Find the selected request details
                    selected_req_details = next((req for req in open_requests if req['request_id'] == selected_request_id_quote), None)

                    if selected_req_details:
                        st.write(f"**Selected Request {selected_request_id_quote}:** {selected_req_details.get('description', 'N/A')}")
                        st.write(f"**User's Initial Price:** {f'${selected_req_details.get("user_quoted_price"):.2f}' if selected_req_details.get("user_quoted_price") else 'Not set'}")

                        with st.form(f"quote_form_open_{selected_request_id_quote}", clear_on_submit=False):
                            worker_price = st.number_input(
                                "Your Price Quote",
                                min_value=0.01,
                                format="%.2f",
                                key=f"worker_price_open_{selected_request_id_quote}"
                            )
                            worker_comments = st.text_area(
                                "Comments (Optional)",
                                key=f"worker_comments_open_{selected_request_id_quote}"
                            )
                            quote_submitted = st.form_submit_button("Submit Quote & Claim Request", type="primary")

                            if quote_submitted:
                                payload = {
                                    "price": worker_price,
                                    "comments": worker_comments if worker_comments else None
                                }
                                try:
                                    quote_resp = session.put(
                                        f"http://localhost:8000/worker/requests/{selected_request_id_quote}/quote",
                                        json=payload
                                    )
                                    quote_resp.raise_for_status()
                                    st.success(f"Quote submitted for request {selected_request_id_quote}! It's now assigned to you.")
                                    st.rerun()
                                except requests.exceptions.RequestException as e:
                                    handle_api_error(e, f"submit quote for request {selected_request_id_quote}")
                                except Exception as e:
                                    st.error(f"An unexpected error occurred: {e}")
                    else:
                        st.error("Selected request details not found.")

            else:
                st.info("No open requests available matching your profile (area/categories).")

        except requests.exceptions.RequestException as e:
            # Specific check for 400 which might indicate profile issue
            if e.response is not None and e.response.status_code == 400:
                 try:
                     detail = e.response.json().get('detail', '')
                     if "pincode" in detail or "radius" in detail or "categories" in detail: # Check for category message too
                         st.warning(f"⚠️ Please complete your profile (pincode/radius/categories) in the 'Profile' tab to see relevant open requests. Details: {detail}")
                     else:
                         handle_api_error(e, "load open requests")
                 except json.JSONDecodeError:
                     handle_api_error(e, "load open requests")
            else:
                handle_api_error(e, "load open requests")
        except Exception as e:
            st.error(f"An unexpected error occurred while loading open requests: {e}")

    # --- Tab 2: My Active Requests (Negotiating, Accepted, InProgress) ---
    with tab_active:
        st.subheader("Requests Assigned To You (Negotiating, Accepted, In Progress)")
        try:
            response = session.get("http://localhost:8000/worker/myrequests")
            response.raise_for_status()
            my_requests = response.json()

            # Filter for active statuses
            active_statuses = ['negotiating', 'accepted', 'inprogress']
            active_requests = [req for req in my_requests if req.get('status') in active_statuses]

            if active_requests:
                df_active = pd.DataFrame(active_requests)
                # Format and select columns
                df_active['created_at'] = df_active['created_at'].apply(format_datetime)
                df_active['updated_at'] = df_active['updated_at'].apply(format_datetime)

                # Ensure price/comment/address columns exist
                cols_to_check = ['user_quoted_price', 'worker_quoted_price', 'final_price', 'worker_comments', 'user_address', 'user_pincode']
                for col in cols_to_check:
                    if col not in df_active.columns:
                        df_active[col] = None

                df_active_display = df_active[[
                    'request_id', 'status', 'description', 'urgency_level',
                    'user_address', 'user_pincode', # Added address
                    'user_quoted_price', 'worker_quoted_price', 'final_price', 'worker_comments',
                    'created_at', 'updated_at'
                ]].copy()
                df_active_display.rename(columns={
                    'request_id': 'ID', 'status': 'Status', 'description': 'Description',
                    'urgency_level': 'Urgency',
                    'user_address': 'User Address', 'user_pincode': 'User Pincode', # Renamed
                    'user_quoted_price': 'User Price',
                    'worker_quoted_price': 'Your Price', 'final_price': 'Final Price',
                    'worker_comments': 'Your Comments', 'created_at': 'Created', 'updated_at': 'Last Update'
                }, inplace=True)

                # Format prices
                for price_col in ['User Price', 'Your Price', 'Final Price']:
                     df_active_display[price_col] = df_active_display[price_col].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")

                # Display styled dataframe
                st.dataframe(
                    df_active_display.style.applymap(style_status, subset=['Status']),
                    use_container_width=True,
                    hide_index=True
                )

                # --- Actions for Active Requests ---
                st.divider()
                st.subheader("Manage Active Request")

                active_request_ids = [req['request_id'] for req in active_requests]
                selected_request_id_manage = st.selectbox(
                    "Select Request ID to Manage",
                    options=[""] + active_request_ids,
                    key="manage_active_request_select"
                )

                if selected_request_id_manage:
                    # Find the selected request details
                    req = next((r for r in active_requests if r['request_id'] == selected_request_id_manage), None)

                    if req:
                        req_id = req['request_id']
                        status = req['status']
                        user_price = req['user_quoted_price']
                        worker_price = req['worker_quoted_price']
                        can_update_quote = status == 'negotiating'
                        can_agree = status == 'negotiating' and user_price is not None and worker_price is not None and user_price == worker_price
                        can_complete_cancel = status in ['accepted', 'inprogress']

                        st.write(f"**Details for Request {req_id} (Status: {status.upper()})**")
                        st.write(f"**Description:** {req.get('description', 'N/A')}")
                        st.write(f"**User's Price:** {f'${user_price:.2f}' if user_price else 'Not set'}")
                        st.write(f"**Your Price:** {f'${worker_price:.2f}' if worker_price else 'Not set'}")
                        st.write(f"**User Address:** {req.get('user_address', 'N/A')} ({req.get('user_pincode', 'N/A')})") # Display address
                        if req.get('worker_comments'):
                            st.info(f"**Your Comments:** {req['worker_comments']}")

                        # --- Update Quote / Agree (for Negotiating) ---
                        if status == 'negotiating':
                            with st.expander("Update Quote / Agree Price"):
                                # Update Quote Form
                                with st.form(f"update_quote_form_{req_id}", clear_on_submit=False):
                                    new_worker_price = st.number_input(
                                        "Update Your Price Quote",
                                        min_value=0.01,
                                        value=float(worker_price) if worker_price else 10.0,
                                        format="%.2f",
                                        key=f"update_worker_price_{req_id}"
                                    )
                                    new_worker_comments = st.text_area(
                                        "Update Comments (Optional)",
                                        value=req.get('worker_comments', ''),
                                        key=f"update_worker_comments_{req_id}"
                                    )
                                    update_quote_submitted = st.form_submit_button("Update My Quote")
                                    if update_quote_submitted:
                                        payload = {
                                            "price": new_worker_price,
                                            "comments": new_worker_comments if new_worker_comments else None
                                        }
                                        try:
                                            update_resp = session.put(
                                                f"http://localhost:8000/worker/requests/{req_id}/quote",
                                                json=payload
                                            )
                                            update_resp.raise_for_status()
                                            st.success(f"Quote updated for request {req_id}!")
                                            st.rerun()
                                        except requests.exceptions.RequestException as e:
                                            handle_api_error(e, f"update quote for request {req_id}")
                                        except Exception as e:
                                            st.error(f"An unexpected error occurred: {e}")

                                # Agree Button
                                if can_agree:
                                    st.write("---")
                                    if st.button(f"Agree to Price (${user_price:.2f}) for Request {req_id}", key=f"worker_agree_btn_{req_id}", type="primary"):
                                        try:
                                            agree_resp = session.put(f"http://localhost:8000/worker/requests/{req_id}/agree")
                                            agree_resp.raise_for_status()
                                            st.success(f"Price agreed for request {req_id}! Status updated.")
                                            st.rerun()
                                        except requests.exceptions.RequestException as e:
                                            handle_api_error(e, f"agree to price for request {req_id}")
                                        except Exception as e:
                                            st.error(f"An unexpected error occurred: {e}")
                                elif user_price is not None and worker_price is not None and user_price != worker_price:
                                    st.warning("Prices do not match. Cannot agree yet.")
                                elif user_price is None or worker_price is None:
                                    st.warning("Both parties must quote a price before agreement is possible.")

                        # --- Complete/Cancel (for Accepted/InProgress) ---
                        if can_complete_cancel:
                             with st.expander("Mark Complete / Cancel"):
                                if st.button(f"✅ Mark Complete {req_id}", key=f"complete_request_btn_{req_id}", use_container_width=True):
                                    try:
                                        # Determine target status (inprogress -> completed, accepted -> completed)
                                        target_status = "completed"
                                        modify_resp = session.patch(
                                            "http://localhost:8000/worker/modifyrequest",
                                            json={"request_id": req_id, "status": target_status}
                                        )
                                        modify_resp.raise_for_status()
                                        st.success(f"Request {req_id} marked as completed!")
                                        st.rerun()
                                    except requests.exceptions.RequestException as e:
                                        handle_api_error(e, f"complete request {req_id}")
                                    except Exception as e:
                                        st.error(f"An unexpected error occurred: {e}")

                                # Allow starting work if 'accepted'
                                if status == 'accepted':
                                     if st.button(f"▶️ Start Work {req_id}", key=f"start_request_btn_{req_id}", use_container_width=True):
                                        try:
                                            modify_resp = session.patch(
                                                "http://localhost:8000/worker/modifyrequest",
                                                json={"request_id": req_id, "status": "inprogress"}
                                            )
                                            modify_resp.raise_for_status()
                                            st.success(f"Request {req_id} status set to In Progress!")
                                            st.rerun()
                                        except requests.exceptions.RequestException as e:
                                            handle_api_error(e, f"start work for request {req_id}")
                                        except Exception as e:
                                            st.error(f"An unexpected error occurred: {e}")

                                if st.button(f"❌ Cancel Request {req_id}", key=f"cancel_request_btn_{req_id}", type="secondary", use_container_width=True):
                                    try:
                                        modify_resp = session.patch(
                                            "http://localhost:8000/worker/modifyrequest",
                                            json={"request_id": req_id, "status": "cancelled"}
                                        )
                                        modify_resp.raise_for_status()
                                        st.success(f"Request {req_id} cancelled!")
                                        st.rerun()
                                    except requests.exceptions.RequestException as e:
                                        handle_api_error(e, f"cancel request {req_id}")
                                    except Exception as e:
                                        st.error(f"An unexpected error occurred: {e}")
                    else:
                        st.error("Selected request details not found.")
            else:
                st.info("You have no active requests currently (Negotiating, Accepted, or In Progress).")

        except requests.exceptions.RequestException as e:
            handle_api_error(e, "load your active requests")
        except Exception as e:
            st.error(f"An unexpected error occurred while loading your active requests: {e}")

    # --- Tab 3: Create Service ---
    with tab_create_service:
        st.subheader("Suggest a New Service")
        st.caption("Propose a new service within an existing category. Admins may review these.")

        if not service_categories_map:
            st.warning("Cannot create services: Service categories are currently unavailable. Please try again later or contact support.")
        else:
            with st.form("new_service_form_worker", clear_on_submit=True):
                new_service_name = st.text_input("Service Name *", help="Enter a clear and concise name for the service.")
                new_service_desc = st.text_area("Service Description (Optional)", help="Provide details about what the service includes.")
                # Category selection
                selected_category_name_add = st.selectbox(
                    "Select Category *",
                    options=[""] + list(service_categories_map.keys()), # Add placeholder
                    key="add_service_category_select_worker",
                    help="Choose the most relevant category for this service."
                )
                submitted = st.form_submit_button("Submit New Service Suggestion")

                if submitted:
                    if not new_service_name:
                        st.warning("Service name is required.")
                    elif not selected_category_name_add:
                        st.warning("Please select a category.")
                    else:
                        selected_category_id_add = service_categories_map[selected_category_name_add]
                        service_payload = {
                            "name": new_service_name,
                            "description": new_service_desc if new_service_desc else None,
                            "category_id": selected_category_id_add
                        }
                        try:
                            # --- IMPORTANT: Assumes a NEW backend endpoint exists ---
                            # You need to create POST /worker/services in your FastAPI backend
                            add_resp = session.post("http://localhost:8000/worker/services", json=service_payload)
                            # --- End of Important Section ---

                            # Check for 201 Created or potentially 200 OK depending on backend implementation
                            if add_resp.status_code in [200, 201]:
                                st.success(f"Service '{new_service_name}' submitted successfully!")
                                # No st.rerun() needed unless you display worker-created services elsewhere
                            else:
                                # Use handle_api_error for consistency
                                handle_api_error(requests.exceptions.RequestException(response=add_resp), f"submit service '{new_service_name}'")
                        except requests.exceptions.RequestException as e:
                             handle_api_error(e, f"submit service '{new_service_name}'")
                        except Exception as e:
                            st.error(f"An unexpected error occurred: {e}")

    # --- Tab 4: History (Completed/Cancelled) ---
    with tab_history:
        st.subheader("Completed & Cancelled Requests")
        try:
            # Reuse the fetched data if available, otherwise fetch again
            if 'my_requests' not in locals():
                response = session.get("http://localhost:8000/worker/myrequests")
                response.raise_for_status()
                my_requests = response.json()

            history_statuses = ['completed', 'cancelled']
            history_requests = [req for req in my_requests if req.get('status') in history_statuses]

            if history_requests:
                 df_history = pd.DataFrame(history_requests)
                 df_history['created_at'] = df_history['created_at'].apply(format_datetime)
                 df_history['updated_at'] = df_history['updated_at'].apply(format_datetime)

                 # Ensure final_price exists
                 if 'final_price' not in df_history.columns:
                     df_history['final_price'] = None

                 df_history_display = df_history[[
                     'request_id', 'status', 'description', 'final_price', 'updated_at' # Keep it concise
                 ]].copy()
                 df_history_display.rename(columns={
                     'request_id': 'ID', 'status': 'Final Status', 'description': 'Description',
                     'final_price': 'Final Price', 'updated_at': 'Completed/Cancelled On'
                 }, inplace=True)

                 # Format price
                 df_history_display['Final Price'] = df_history_display['Final Price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")

                 # Apply styling to the 'Final Status' column
                 st.dataframe(
                     df_history_display.style.applymap(style_status, subset=['Final Status']),
                     use_container_width=True,
                     hide_index=True
                 )
            else:
                 st.info("No completed or cancelled requests found.")

        except requests.exceptions.RequestException as e:
             handle_api_error(e, "load request history")
        except Exception as e:
             st.error(f"An unexpected error occurred while loading request history: {e}")

    # --- Tab 5: Profile ---
    with tab_profile:
        st.subheader("Manage Your Profile")

        try:
            profile_resp = session.get("http://localhost:8000/worker/profile")
            profile_resp.raise_for_status()
            profile_data = profile_resp.json()

            # Get current category IDs and map them to names for display
            current_category_ids = profile_data.get("category_ids", [])
            current_category_names = [category_id_to_name_map.get(cat_id, f"Unknown ID: {cat_id}") for cat_id in current_category_ids]

            with st.form("worker_profile_form"):
                st.text_input("Username", value=profile_data.get("username", "N/A"), disabled=True)
                email = st.text_input("Email", value=profile_data.get("email", ""))
                mobile = st.text_input("Mobile", value=profile_data.get("mobile", ""))
                pincode = st.text_input("Pincode", value=profile_data.get("pincode", ""))
                radius = st.number_input("Service Radius (Pincode +/-)", min_value=1, value=profile_data.get("radius", 10), step=1)

                # Add multiselect for service categories
                if service_categories_map:
                    selected_names = st.multiselect(
                        "Service Categories You Offer",
                        options=list(service_categories_map.keys()),
                        default=current_category_names # Pre-select current categories
                    )
                    # Convert selected names back to IDs for submission
                    updated_category_ids = [service_categories_map[name] for name in selected_names]
                else:
                    st.warning("Could not load service categories. Profile update for categories disabled.")
                    updated_category_ids = current_category_ids # Keep current if load failed

                submitted = st.form_submit_button("Update Profile")
                if submitted:
                    if not pincode or not email or not mobile:
                        st.warning("Email, Mobile, and Pincode cannot be empty.")
                    # Optional: Add check if categories are required
                    # elif not updated_category_ids:
                    #    st.warning("Please select at least one service category.")
                    else:
                        update_payload = {
                            "email": email,
                            "mobile": mobile,
                            "pincode": pincode,
                            "radius": radius,
                            "category_ids": updated_category_ids # Send the list of IDs
                        }
                        try:
                            update_resp = session.put("http://localhost:8000/worker/profile", json=update_payload)
                            update_resp.raise_for_status()
                            st.success("Profile updated successfully!")
                            # Clear cache for categories in case they were updated indirectly? Maybe not needed here.
                            st.rerun() # Rerun to reflect changes and potentially update open requests view
                        except requests.exceptions.RequestException as e:
                            handle_api_error(e, "update profile")
                        except Exception as e:
                            st.error(f"An unexpected error occurred: {e}")

        except requests.exceptions.RequestException as e:
            handle_api_error(e, "load profile")
        except Exception as e:
            st.error(f"An unexpected error occurred while loading profile: {e}")


if __name__ == "__main__":
    # Mock session state for direct execution testing
    if "role" not in st.session_state:
        st.session_state.role = "Worker"
        st.session_state.user_info = {"username": "testworker", "id": 1}
        # No access token needed for worker if using sessions
    show_dashboard()