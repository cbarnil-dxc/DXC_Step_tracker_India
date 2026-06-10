"""
Authentication and authorization module for DXC Step Tracker.
Handles Azure OAuth, session management, and user authentication.
"""

import streamlit as st
import logging
from datetime import datetime
from requests_oauthlib import OAuth2Session
from .db import supabase

# ------------------ AZURE OAUTH CONFIG ------------------
azure = st.secrets["azure"]
CLIENT_ID = azure["client_id"]
CLIENT_SECRET = azure["client_secret"]
TENANT_ID = azure.get("tenant_id")
if not TENANT_ID:
    raise RuntimeError("azure.tenant_id must be set in secrets.toml")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
AUTHORIZE_URL = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"
REDIRECT_URI = azure.get("redirect_uri")
if not REDIRECT_URI:
    raise RuntimeError("azure.redirect_uri must be set in secrets.toml")

oauth = OAuth2Session(
    client_id=CLIENT_ID,
    scope=["openid", "profile", "email", "User.Read", "Files.ReadWrite", "Files.ReadWrite.AppFolder"],
    redirect_uri=REDIRECT_URI,
)

# ------------------ SESSION MANAGEMENT ------------------
def init_session_state():
    """Initialize session state defaults."""
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""
    if "display_name" not in st.session_state:
        st.session_state["display_name"] = ""
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = ""


def standardize_name(name):
    """Convert name from 'last, first' format to 'first last' format."""
    if "," in name:
        parts = name.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name


def is_token_expired(token):
    """Check if JWT token is expired."""
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get("exp")
        if exp:
            import time
            return time.time() >= exp
        return False
    except Exception:
        return True


def get_or_create_user(email, display_name):
    """Get existing user or create new user in database, return formatted name."""
    try:
        result = supabase.table("users").select("user_id, user_name").eq("user_email", email).execute()
        
        if result.data:
            return result.data[0]["user_name"]
        else:
            standardized_name = standardize_name(display_name)
            supabase.table("users").insert({
                "user_email": email,
                "user_name": standardized_name,
            }).execute()
            logging.info(f"New user created: {email[:3]}***@*** ({standardized_name})")
            return standardized_name
    except Exception:
        logging.error("Database error in get_or_create_user")
        return standardize_name(display_name)


def handle_oauth_redirect():
    """Handle OAuth redirect from Microsoft."""
    query_params = st.query_params

    if "code" in query_params and st.session_state["token"] is None:
        try:
            token = oauth.fetch_token(
                token_url=TOKEN_URL,
                code=query_params["code"],
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
            )
            st.session_state["token"] = token
            st.query_params.clear()
            st.rerun()
        except Exception:
            logging.error("OAuth redirect handling failed")
            error_str = "authentication_error"
            if "AADSTS70008" in error_str or "expired" in error_str.lower():
                st.error("Session timed out. Please log in again.")
            else:
                st.error("Authentication failed. Please try again.")


def process_token():
    """Process authentication token and set session state."""
    token = st.session_state["token"]

    if token:
        token_to_check = token.get("id_token") or token.get("access_token")
        if token_to_check and is_token_expired(token_to_check):
            st.error("Session expired. Please log in again.")
            if st.button("Log In Again"):
                st.session_state.clear()
                st.rerun()
        
        try:
            import jwt
            token_to_decode = token.get("id_token") or token.get("access_token")
            
            if not token_to_decode:
                st.error("Authentication failed. Please try again.")
                if st.button("Try Again"):
                    st.session_state.clear()
                    st.rerun()
            else:
                decoded = jwt.decode(token_to_decode, options={"verify_signature": False})
                user_email = decoded.get("preferred_username") or decoded.get("email") or decoded.get("upn") or decoded.get("unique_name") or ""
                user_name_raw = decoded.get("name", "Unknown User")
                
                if "," in user_name_raw:
                    last, first = [x.strip() for x in user_name_raw.split(",", 1)]
                    user_name = f"{first} {last}"
                else:
                    user_name = user_name_raw.strip()
                
                if not st.session_state.logged_in:
                    username = get_or_create_user(user_email, user_name)
                    st.session_state.logged_in = True
                    st.session_state.username = user_email
                    st.session_state.display_name = username
                    st.session_state.user_email = user_email
                    st.session_state.login_time = datetime.now().timestamp()
                    logging.info(f"User logged in: {username} ({user_email[:3]}***@***)")
                    st.rerun()
        except Exception:
            logging.error("Error processing authentication token")
            st.error("Error processing authentication. Please log in again.")
            if st.button("Try Again"):
                st.session_state.clear()
                st.rerun()


def check_login_required():
    """
    Check if user is logged in. If not, show warning and stop execution.
    
    Returns:
        str: Username if logged in, otherwise stops execution
    """
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.stop()
    
    # Check session timeout (8 hours)
    login_time = st.session_state.get("login_time")
    if login_time:
        session_timeout = 8 * 3600  # 8 hours in seconds
        if datetime.now().timestamp() - login_time > session_timeout:
            st.warning("Session expired. Please log in again.")
            handle_logout()
            st.stop()
    
    return st.session_state.get("username", "Guest")


def handle_logout():
    """Handle user logout by clearing session state and rerunning."""
    st.session_state.clear()
    st.rerun()


def is_admin(user_email: str) -> bool:
    """
    Check if a user email is in the admin list from secrets.
    
    Args:
        user_email: User email to check
        
    Returns:
        True if user is an admin, False otherwise
    """
    try:
        admin_section = st.secrets.get("admin", {})
        admin_emails = admin_section.get("emails", []) if hasattr(admin_section, "get") else []
        # Backwards compatibility with a flat ADMIN_EMAILS key
        if not admin_emails:
            admin_emails = st.secrets.get("ADMIN_EMAILS", [])
        return user_email.strip().lower() in [e.strip().lower() for e in admin_emails]
    except Exception:
        return False
