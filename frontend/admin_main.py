import streamlit as st
from client import session
import pandas as pd
from datetime import datetime
import json # Import json for better error parsing
import requests

# Helper function for API error handling
def handle_api_error(e, action_msg="perform action"):
    error_detail = "An unknown error occurred."
    status_code = "N/A"
    if isinstance(e, requests.exceptions.RequestException):
        if e.response is not None:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get('detail', e.response.text)
            except json.JSONDecodeError:
                error_detail = e.response.text
        else:
            error_detail = str(e) # Network error, etc.
    else: # Handle other potential exceptions
        error_detail = str(e)

    st.error(f"❌ Failed to {action_msg}: {error_detail} (Status: {status_code})")

# Helper function to format datetime
def format_datetime(dt_str):
    if not dt_str:
        return "N/A"
    try:
        # Parse ISO format string, potentially with timezone info
        dt_obj = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt_obj.strftime('%Y-%m-%d %H:%M:%S') # Format as desired
    except (ValueError, TypeError):
        return str(dt_str) # Return original string if parsing fails

# Function to fetch categories (used in multiple places)
def fetch_categories():
    try:
        response = session.get("http://localhost:8000/admin/service-categories")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        handle_api_error(e, "load service categories")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while loading categories: {e}")
        return []

# Function to display the admin dashboard
def show_dashboard():
    # Get current admin info from session state for checks
    current_admin_info = st.session_state.get("user_info", {})
    current_admin_id = current_admin_info.get("id")

    tab_users, tab_workers, tab_requests, tab_services, tab_categories, tab_admins = st.tabs([ # Added tab_categories
        "👥 Users", "👷 Workers", "📋 Requests", "🛠️ Services", "🏷️ Categories", "👑 Admins" # Added "🏷️ Categories"
    ])

    # --- User Management Tab ---
    with tab_users:
        st.subheader("Manage Users")
        try:
            response = session.get("http://localhost:8000/admin/users") # Requires admin session
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            users = response.json()
            if users:
                df_users = pd.DataFrame(users)
                # Ensure 'created_at' exists before formatting
                if 'created_at' in df_users.columns:
                    df_users['created_at'] = df_users['created_at'].apply(format_datetime)
                else:
                    df_users['created_at'] = "N/A" # Add column if missing
                st.dataframe(df_users[['user_id', 'username', 'email', 'mobile', 'created_at']], use_container_width=True, hide_index=True)

                # Add delete functionality
                user_ids = [user['user_id'] for user in users]
                selected_user_id = st.selectbox("Select User ID to Delete", options=[""] + user_ids, key="delete_user_select")
                if selected_user_id:
                    if st.button(f"Delete User {selected_user_id}", key="delete_user_btn", type="primary"):
                        try:
                            delete_resp = session.delete(f"http://localhost:8000/admin/users/{selected_user_id}")
                            if delete_resp.status_code == 204:
                                st.success(f"User {selected_user_id} deleted successfully!")
                                st.rerun()
                            else:
                                handle_api_error(requests.exceptions.RequestException(response=delete_resp), f"delete user {selected_user_id}")
                        except requests.exceptions.RequestException as e:
                             handle_api_error(e, f"delete user {selected_user_id}")
                        except Exception as e:
                            st.error(f"Error deleting user: {e}")
            else:
                st.info("No users found.")
        except requests.exceptions.RequestException as e:
            handle_api_error(e, "load users")
        except Exception as e:
             st.error(f"An unexpected error occurred while loading users: {e}")

    # --- Worker Management Tab ---
    with tab_workers:
        st.subheader("Manage Workers")
        try:
            response = session.get("http://localhost:8000/admin/workers") # Requires admin session
            response.raise_for_status()
            workers = response.json()
            if workers:
                df_workers = pd.DataFrame(workers)
                # Ensure 'created_at' exists before formatting
                if 'created_at' in df_workers.columns:
                    df_workers['created_at'] = df_workers['created_at'].apply(format_datetime)
                else:
                    df_workers['created_at'] = "N/A"
                st.dataframe(df_workers[['worker_id', 'username', 'email', 'mobile', 'employee_number', 'status', 'created_at']], use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("Approve/Reject Pending Workers")
                pending_workers = [w for w in workers if w['status'] == 'pending']
                if pending_workers:
                    worker_options = {f"{w['username']} (ID: {w['worker_id']})": w['worker_id'] for w in pending_workers}
                    selected_worker_label = st.selectbox("Select Pending Worker", options=[""] + list(worker_options.keys()), key="status_worker_select")
                    if selected_worker_label:
                        selected_worker_id_status = worker_options[selected_worker_label]
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Approve Worker {selected_worker_label}", key="approve_worker_btn"):
                                try:
                                    update_resp = session.patch(f"http://localhost:8000/admin/workers/{selected_worker_id_status}/status", json={"status": "approved"})
                                    if update_resp.status_code == 200:
                                        st.success(f"Worker {selected_worker_label} approved!")
                                        st.rerun()
                                    else:
                                        handle_api_error(requests.exceptions.RequestException(response=update_resp), f"approve worker {selected_worker_label}")
                                except requests.exceptions.RequestException as e:
                                    handle_api_error(e, f"approve worker {selected_worker_label}")
                                except Exception as e:
                                    st.error(f"Error approving worker: {e}")
                        with col2:
                             if st.button(f"Reject Worker {selected_worker_label}", key="reject_worker_btn", type="primary"):
                                try:
                                    update_resp = session.patch(f"http://localhost:8000/admin/workers/{selected_worker_id_status}/status", json={"status": "rejected"})
                                    if update_resp.status_code == 200:
                                        st.success(f"Worker {selected_worker_label} rejected!")
                                        st.rerun()
                                    else:
                                        handle_api_error(requests.exceptions.RequestException(response=update_resp), f"reject worker {selected_worker_label}")
                                except requests.exceptions.RequestException as e:
                                    handle_api_error(e, f"reject worker {selected_worker_label}")
                                except Exception as e:
                                    st.error(f"Error rejecting worker: {e}")
                else:
                    st.info("No pending workers.")

                st.markdown("---")
                st.subheader("Delete Worker")
                all_worker_options = {f"{w['username']} (ID: {w['worker_id']}, Status: {w['status']})": w['worker_id'] for w in workers}
                selected_worker_label_delete = st.selectbox("Select Worker to Delete", options=[""] + list(all_worker_options.keys()), key="delete_worker_select")
                if selected_worker_label_delete:
                    selected_worker_id_delete = all_worker_options[selected_worker_label_delete]
                    if st.button(f"Delete Worker {selected_worker_label_delete}", key="delete_worker_btn", type="primary"):
                         try:
                            delete_resp = session.delete(f"http://localhost:8000/admin/workers/{selected_worker_id_delete}")
                            if delete_resp.status_code == 204:
                                st.success(f"Worker {selected_worker_label_delete} deleted successfully!")
                                st.rerun()
                            else:
                                handle_api_error(requests.exceptions.RequestException(response=delete_resp), f"delete worker {selected_worker_label_delete}")
                         except requests.exceptions.RequestException as e:
                            handle_api_error(e, f"delete worker {selected_worker_label_delete}")
                         except Exception as e:
                            st.error(f"Error deleting worker: {e}")

            else:
                st.info("No workers found.")
        except requests.exceptions.RequestException as e:
            handle_api_error(e, "load workers")
        except Exception as e:
             st.error(f"An unexpected error occurred while loading workers: {e}")

    # --- Request Management Tab ---
    with tab_requests:
        st.subheader("Manage Service Requests")
        try:
            response = session.get("http://localhost:8000/admin/requests") # Requires admin session
            response.raise_for_status()
            requests_data = response.json()
            if requests_data:
                df_requests = pd.DataFrame(requests_data)
                # Ensure datetime columns exist before formatting
                if 'created_at' in df_requests.columns:
                    df_requests['created_at'] = df_requests['created_at'].apply(format_datetime)
                else: df_requests['created_at'] = "N/A"
                if 'updated_at' in df_requests.columns:
                    df_requests['updated_at'] = df_requests['updated_at'].apply(format_datetime)
                else: df_requests['updated_at'] = "N/A"

                # Display relevant columns
                display_cols_req = [
                    'request_id', 'user_id', 'worker_id', 'service_id', 'status',
                    'urgency_level', 'description', 'created_at', 'updated_at'
                ]
                # Ensure all display columns exist
                for col in display_cols_req:
                    if col not in df_requests.columns:
                        df_requests[col] = None # Add missing columns with None

                st.dataframe(df_requests[display_cols_req], use_container_width=True, hide_index=True)

                # Add delete functionality
                request_ids = [req['request_id'] for req in requests_data]
                selected_request_id = st.selectbox("Select Request ID to Delete", options=[""] + request_ids, key="delete_request_select")
                if selected_request_id:
                    if st.button(f"Delete Request {selected_request_id}", key="delete_request_btn", type="primary"):
                        try:
                            delete_resp = session.delete(f"http://localhost:8000/admin/requests/{selected_request_id}")
                            if delete_resp.status_code == 204:
                                st.success(f"Request {selected_request_id} deleted successfully!")
                                st.rerun()
                            else:
                                handle_api_error(requests.exceptions.RequestException(response=delete_resp), f"delete request {selected_request_id}")
                        except requests.exceptions.RequestException as e:
                            handle_api_error(e, f"delete request {selected_request_id}")
                        except Exception as e:
                            st.error(f"Error deleting request: {e}")
            else:
                st.info("No service requests found.")
        except requests.exceptions.RequestException as e:
            handle_api_error(e, "load service requests")
        except Exception as e:
             st.error(f"An unexpected error occurred while loading requests: {e}")

    # --- Service Management Tab ---
    with tab_services:
        st.subheader("Manage Services")

        # Fetch categories needed for adding/editing services
        categories_data_svc = fetch_categories()
        category_options_svc = {cat['name']: cat['category_id'] for cat in categories_data_svc} if categories_data_svc else {}

        # Display existing services
        try:
            response = session.get("http://localhost:8000/admin/services") # Requires admin session
            response.raise_for_status()
            services_data = response.json()
            if services_data:
                df_services = pd.DataFrame(services_data)
                # Add category name by mapping ID
                id_to_name_map = {v: k for k, v in category_options_svc.items()}
                df_services['category_name'] = df_services['category_id'].map(id_to_name_map).fillna("Unknown Category")

                st.dataframe(df_services[['service_id', 'name', 'description', 'category_name', 'category_id']], use_container_width=True, hide_index=True)

                # Add delete functionality
                service_options_del = {f"{srv['name']} (ID: {srv['service_id']})": srv['service_id'] for srv in services_data}
                selected_service_label_del = st.selectbox("Select Service to Delete", options=[""] + list(service_options_del.keys()), key="delete_service_select")
                if selected_service_label_del:
                    selected_service_id_del = service_options_del[selected_service_label_del]
                    if st.button(f"Delete Service {selected_service_label_del}", key="delete_service_btn", type="primary"):
                        try:
                            delete_resp = session.delete(f"http://localhost:8000/admin/services/{selected_service_id_del}")
                            if delete_resp.status_code == 204:
                                st.success(f"Service {selected_service_label_del} deleted successfully!")
                                st.rerun()
                            else:
                                handle_api_error(requests.exceptions.RequestException(response=delete_resp), f"delete service {selected_service_label_del}")
                        except requests.exceptions.RequestException as e:
                            handle_api_error(e, f"delete service {selected_service_label_del}")
                        except Exception as e:
                            st.error(f"Error deleting service: {e}")
            else:
                st.info("No services found.")
        except requests.exceptions.RequestException as e:
            handle_api_error(e, "load services")
        except Exception as e:
             st.error(f"An unexpected error occurred while loading services: {e}")

        st.markdown("---")
        # Add new service form
        st.subheader("Add New Service")
        if not category_options_svc:
            st.warning("Cannot add services: No service categories found. Please add categories first.")
        else:
            with st.form("new_service_form", clear_on_submit=True):
                new_service_name = st.text_input("Service Name")
                new_service_desc = st.text_area("Service Description (Optional)")
                # Add category selection
                selected_category_name_add = st.selectbox(
                    "Select Category",
                    options=list(category_options_svc.keys()),
                    key="add_service_category_select"
                )
                submitted = st.form_submit_button("Add Service")
                if submitted:
                    if not new_service_name:
                        st.warning("Service name is required.")
                    elif not selected_category_name_add:
                        st.warning("Please select a category.") # Should not happen with selectbox unless options are empty
                    else:
                        selected_category_id_add = category_options_svc[selected_category_name_add]
                        service_payload = {
                            "name": new_service_name,
                            "description": new_service_desc,
                            "category_id": selected_category_id_add # Include category_id
                        }
                        try:
                            add_resp = session.post("http://localhost:8000/admin/services", json=service_payload)
                            if add_resp.status_code == 201:
                                st.success(f"Service '{new_service_name}' added successfully!")
                                st.rerun()
                            else:
                                # Use handle_api_error for consistency
                                handle_api_error(requests.exceptions.RequestException(response=add_resp), f"add service '{new_service_name}'")
                        except requests.exceptions.RequestException as e:
                             handle_api_error(e, f"add service '{new_service_name}'")
                        except Exception as e:
                            st.error(f"Error adding service: {e}")

    # --- Service Category Management Tab ---
    with tab_categories:
        st.subheader("Manage Service Categories")

        # Use the already defined fetch_categories function
        categories_data = fetch_categories()

        if categories_data:
            df_categories = pd.DataFrame(categories_data)
            st.dataframe(df_categories[['category_id', 'name']], use_container_width=True, hide_index=True)

            st.divider()

            # --- Update Category ---
            st.subheader("Update Category Name")
            category_options = {cat['name']: cat['category_id'] for cat in categories_data}
            selected_category_name_update = st.selectbox(
                "Select Category to Update",
                options=[""] + list(category_options.keys()),
                key="update_category_select"
            )

            if selected_category_name_update:
                selected_category_id_update = category_options[selected_category_name_update]
                with st.form(f"update_category_form_{selected_category_id_update}", clear_on_submit=True):
                    new_category_name = st.text_input("New Category Name", value=selected_category_name_update)
                    update_submitted = st.form_submit_button("Update Name")
                    if update_submitted:
                        if not new_category_name:
                            st.warning("Category name cannot be empty.")
                        elif new_category_name == selected_category_name_update:
                             st.info("No changes detected.")
                        else:
                            payload = {"name": new_category_name}
                            try:
                                update_resp = session.put(f"http://localhost:8000/admin/service-categories/{selected_category_id_update}", json=payload)
                                update_resp.raise_for_status()
                                st.success(f"Category '{selected_category_name_update}' updated to '{new_category_name}'!")
                                st.rerun()
                            except requests.exceptions.RequestException as e:
                                handle_api_error(e, f"update category '{selected_category_name_update}'")
                            except Exception as e:
                                st.error(f"Error updating category: {e}")

            st.divider()

            # --- Delete Category ---
            st.subheader("Delete Service Category")
            selected_category_name_delete = st.selectbox(
                "Select Category to Delete",
                options=[""] + list(category_options.keys()),
                key="delete_category_select"
            )
            if selected_category_name_delete:
                selected_category_id_delete = category_options[selected_category_name_delete]
                st.warning(f"⚠️ Deleting category '{selected_category_name_delete}' (ID: {selected_category_id_delete}) might fail if it's linked to existing services or workers.")
                if st.button(f"Delete Category '{selected_category_name_delete}'", key="delete_category_btn", type="primary"):
                    try:
                        delete_resp = session.delete(f"http://localhost:8000/admin/service-categories/{selected_category_id_delete}")
                        delete_resp.raise_for_status() # Checks for 204 success or other errors
                        st.success(f"Category '{selected_category_name_delete}' deleted successfully!")
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        # Specific handling for 400 Bad Request (likely due to dependencies)
                        if e.response is not None and e.response.status_code == 400:
                             try:
                                 error_detail = e.response.json().get('detail', e.response.text)
                             except json.JSONDecodeError:
                                 error_detail = e.response.text
                             st.error(f"Failed to delete category: {error_detail}")
                        else:
                            handle_api_error(e, f"delete category '{selected_category_name_delete}'")
                    except Exception as e:
                        st.error(f"Error deleting category: {e}")
        else:
            st.info("No service categories found.")

        st.divider()

        # --- Add New Category ---
        st.subheader("Add New Service Category")
        with st.form("new_category_form", clear_on_submit=True):
            new_category_name_input = st.text_input("New Category Name")
            add_submitted = st.form_submit_button("Add Category")
            if add_submitted:
                if not new_category_name_input:
                    st.warning("Category name is required.")
                else:
                    payload = {"name": new_category_name_input}
                    try:
                        add_resp = session.post("http://localhost:8000/admin/service-categories", json=payload)
                        add_resp.raise_for_status() # Checks for 201 success or other errors
                        st.success(f"Category '{new_category_name_input}' added successfully!")
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                         handle_api_error(e, f"add category '{new_category_name_input}'")
                    except Exception as e:
                        st.error(f"Error adding category: {e}")

    # --- Admin Management Tab ---
    with tab_admins:
        st.subheader("Manage Admin Accounts")

        # --- View Admins ---
        try:
            response = session.get("http://localhost:8000/admin/admins") # Assumed endpoint
            response.raise_for_status()
            admins = response.json()
            if admins:
                df_admins = pd.DataFrame(admins)
                # Assuming backend returns 'admin_id', 'username', 'created_at'
                if 'created_at' in df_admins.columns:
                     df_admins['created_at'] = df_admins['created_at'].apply(format_datetime)
                else: df_admins['created_at'] = "N/A"
                st.dataframe(df_admins[['admin_id', 'username', 'created_at']], use_container_width=True, hide_index=True)
            else:
                st.info("No admin accounts found (besides potentially yourself).")
        except requests.exceptions.RequestException as e:
            handle_api_error(e, "load admin accounts")
        except Exception as e:
             st.error(f"An unexpected error occurred while loading admin accounts: {e}")

        st.divider()

        # --- Create New Admin ---
        st.subheader("Create New Admin")
        with st.form("new_admin_form", clear_on_submit=True):
            new_admin_username = st.text_input("New Admin Username")
            new_admin_password = st.text_input("New Admin Password", type="password")
            create_submitted = st.form_submit_button("Create Admin")
            if create_submitted:
                if not new_admin_username or not new_admin_password:
                    st.warning("Username and Password are required.")
                else:
                    payload = {"username": new_admin_username, "password": new_admin_password}
                    try:
                        # Assumed endpoint, adjust if different
                        create_resp = session.post("http://localhost:8000/admin/create", json=payload)
                        create_resp.raise_for_status() # Check for HTTP errors
                        st.success(f"Admin '{new_admin_username}' created successfully!")
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        handle_api_error(e, f"create admin '{new_admin_username}'")
                    except Exception as e:
                        st.error(f"Error creating admin: {e}")

        st.divider()

        # --- Modify Own Password ---
        st.subheader("Change Your Password")
        with st.form("change_password_form", clear_on_submit=True):
            st.text_input("Your Username", value=current_admin_info.get('username', 'N/A'), disabled=True)
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            password_submitted = st.form_submit_button("Change My Password")
            if password_submitted:
                if not new_password or not confirm_password:
                    st.warning("Please enter and confirm the new password.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    # Assumed endpoint and payload structure, adjust if needed
                    payload = {"password": new_password}
                    try:
                        # Assumes a PUT request to a profile endpoint - ADJUST IF NEEDED
                        update_resp = session.put("http://localhost:8000/admin/profile", json=payload)
                        update_resp.raise_for_status()
                        st.success("Your password has been updated successfully!")
                        # Consider if logout is needed after password change
                    except requests.exceptions.RequestException as e:
                        handle_api_error(e, "update your password")
                    except Exception as e:
                        st.error(f"Error updating password: {e}")

        st.divider()

        # --- Delete Other Admins ---
        st.subheader("Delete Admin Account")
        # Filter out the current admin from the list of deletable admins
        if 'admins' in locals() and current_admin_id is not None:
            other_admins = [admin for admin in admins if admin['admin_id'] != current_admin_id]
            if other_admins:
                other_admin_options = {f"{admin['username']} (ID: {admin['admin_id']})": admin['admin_id'] for admin in other_admins}
                selected_admin_label = st.selectbox(
                    "Select Admin to Delete (Cannot delete yourself)",
                    options=[""] + list(other_admin_options.keys()),
                    key="delete_admin_select"
                )
                if selected_admin_label:
                    selected_admin_id_delete = other_admin_options[selected_admin_label]
                    st.warning(f"⚠️ You are about to delete admin: {selected_admin_label}. This action cannot be undone.")
                    if st.button(f"Confirm Delete Admin {selected_admin_label}", key="delete_admin_btn", type="primary"):
                        try:
                            # Assumed endpoint
                            delete_resp = session.delete(f"http://localhost:8000/admin/admins/{selected_admin_id_delete}")
                            delete_resp.raise_for_status() # Check for HTTP errors (like 204 No Content on success)
                            st.success(f"Admin {selected_admin_label} deleted successfully!")
                            st.rerun()
                        except requests.exceptions.RequestException as e:
                            handle_api_error(e, f"delete admin {selected_admin_label}")
                        except Exception as e:
                            st.error(f"Error deleting admin: {e}")
            else:
                st.info("No other admin accounts to delete.")
        else:
            st.info("Admin list not loaded or cannot identify current admin.")

# This part is usually in main.py or app.py, included here for context if running standalone
if __name__ == "__main__":
    # Mock session state for direct execution testing
    if "access_token" not in st.session_state: # Using access_token loosely here, admin uses session
         st.session_state.access_token = "mock_admin_token_or_flag" # Indicate logged in
         st.session_state.user_info = {"username": "admin_user", "id": 1} # Mock current admin ID
         st.session_state.role = "Admin"
    show_dashboard()