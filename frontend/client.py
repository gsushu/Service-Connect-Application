# filepath: d:\Other\adbms\Service-Connect-Application-main\frontend\client.py
import requests
import streamlit as st # Import streamlit to access session_state

class AuthenticatedSession(requests.Session):
    def request(self, method, url, **kwargs):
        # Check if token exists in session state
        token = st.session_state.get("access_token")
        if token:
            # Add Authorization header if token exists
            headers = kwargs.get("headers", {})
            headers["Authorization"] = f"Bearer {token}"
            kwargs["headers"] = headers
        # Call the original request method
        return super().request(method, url, **kwargs)

# Use the custom session class
session = AuthenticatedSession()
