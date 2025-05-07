import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling to the app"""

    # Common CSS for all pages
    st.markdown("""
    <style>
    /* Common styling */
    .main {
        background-color: #f8f9fa;
    }

    /* Panel and card styles */
    div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }

    /* Make headers stand out */
    h1, h2, h3 {
        color: #2c3e50;
        font-weight: 700;
    }

    /* Style dataframes/tables */
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Style status badges */
    .status-pending {
        background-color: #FFF3CD;
        color: #856404;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-negotiating {
        background-color: #CCE5FF;
        color: #004085;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-accepted {
        background-color: #D4EDDA;
        color: #155724;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-inprogress {
        background-color: #D1ECF1;
        color: #0C5460;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-completed {
        background-color: #C3E6CB;
        color: #155724;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .status-cancelled {
        background-color: #F8D7DA;
        color: #721C24;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }

    /* Container styling */
    div.stTabs [data-baseweb="tab-panel"] {
        padding: 15px;
        background-color: white;
        border-radius: 0 15px 15px 15px;
    }

    div.stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px;
        font-weight: 600;
        padding: 0px 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def add_role_based_styles(role):
    """Apply role-specific styling"""

    role_colors = {
        "User": {
            "primary": "#4e73df",  # Blue theme
            "secondary": "#f8f9fc",
            "accent": "#5a5c69",
            "highlight": "#2e59d9",
        },
        "Worker": {
            "primary": "#1cc88a",  # Green theme
            "secondary": "#f8fdfb",
            "accent": "#58665d",
            "highlight": "#13855c",
        },
        "Admin": {
            "primary": "#e74a3b",  # Red theme
            "secondary": "#fdf8f8",
            "accent": "#6e4c49",
            "highlight": "#be3326",
        }
    }

    colors = role_colors.get(role, role_colors["User"])  # Default to User if role not found

    st.markdown(f"""
    <style>
    /* Role-specific styling for {role} */
    div.stButton button[kind="primary"] {{
        background-color: {colors["primary"]};
        color: white;
    }}

    div.stButton button[kind="primary"]:hover {{
        background-color: {colors["highlight"]};
    }}

    div.stTabs [data-baseweb="tab-list"] {{
        background-color: {colors["secondary"]};
        border-radius: 15px 15px 0px 0px;
    }}

    div.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        background-color: {colors["primary"]};
        color: white;
        border-radius: 15px 15px 0px 0px;
    }}

    div.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {{
        color: white;
    }}

    div.stTabs [data-baseweb="tab-list"] button:hover {{
        background-color: {colors["highlight"]};
        color: white;
    }}

    div.stTabs [data-baseweb="tab-list"] button:hover [data-testid="stMarkdownContainer"] p {{
        color: white;
    }}

    h1, h2, h3 {{
        color: {colors["accent"]};
    }}

    .sidebar .sidebar-content {{
        background-color: {colors["primary"]};
    }}

    .stProgress > div > div > div > div {{
        background-color: {colors["primary"]};
    }}
    </style>
    """, unsafe_allow_html=True)

def format_status_with_badge(status):
    """Format a status string as a colored badge"""
    if not status:
        return ""
    status = status.lower()
    return f'<span class="status-{status}">{status.upper()}</span>'

def display_welcome_header(username, role):
    """Display a colorful welcome header with user information"""
    role_icon = {
        "User": "👤",
        "Worker": "👷",
        "Admin": "👑"
    }.get(role, "👋")

    st.markdown(f"""
    <div style="padding: 15px; background-color: white; border-radius: 10px; margin-bottom: 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h2 style="margin-bottom: 5px; display: flex; align-items: center;">
            {role_icon} Welcome, {username}!
        </h2>
        <p style="color: #6c757d; margin-top: 0;">Logged in as: {role}</p>
    </div>
    """, unsafe_allow_html=True)
