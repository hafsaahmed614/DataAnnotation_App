"""
Authentication module for SNF Patient Navigator Case Collection App.
Handles user login, session management, and access control in Streamlit.
Includes login persistence across page refreshes using query params.
"""

import streamlit as st
import hashlib
import secrets
from db import authenticate_user, create_user, get_user_by_username


def generate_session_token(username: str) -> str:
    """Generate a session token for persistent login."""
    # Create a token based on username and a random component
    random_part = secrets.token_hex(16)
    return hashlib.sha256(f"{username}:{random_part}".encode()).hexdigest()[:32]


def init_session_state():
    """Initialize authentication-related session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    if 'auth_checked' not in st.session_state:
        st.session_state.auth_checked = False

    # Check for persistent login via query params (only once per session)
    if not st.session_state.auth_checked and not st.session_state.authenticated:
        st.session_state.auth_checked = True
        try:
            params = st.query_params
            stored_user = params.get("user")
            stored_token = params.get("token")

            if stored_user and stored_token:
                # Validate the user exists
                user = get_user_by_username(stored_user)
                if user:
                    # Auto-login the user
                    st.session_state.authenticated = True
                    st.session_state.current_user = user
                    st.session_state.username = stored_user
                    st.session_state.session_token = stored_token
        except Exception:
            # If anything fails, just continue without auto-login
            pass


def login(username: str, pin: str) -> bool:
    """
    Attempt to log in a user.

    Args:
        username: User's full name (case sensitive)
        pin: 4-digit PIN

    Returns:
        True if login successful, False otherwise
    """
    user = authenticate_user(username, pin)
    if user:
        st.session_state.authenticated = True
        st.session_state.current_user = user
        st.session_state.username = username

        # Generate session token and set query params for persistence
        token = generate_session_token(username)
        st.session_state.session_token = token
        try:
            st.query_params["user"] = username
            st.query_params["token"] = token
        except Exception:
            pass  # Query params might not be available in some contexts

        return True
    return False


def logout():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.username = None
    st.session_state.session_token = None
    st.session_state.auth_checked = False

    # Clear query params
    try:
        st.query_params.clear()
    except Exception:
        pass


def register(username: str, pin: str) -> tuple[bool, str]:
    """
    Register a new user.

    Args:
        username: User's full name (case sensitive)
        pin: 4-digit PIN

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Validate PIN
    if not pin.isdigit() or len(pin) != 4:
        return False, "PIN must be exactly 4 digits"

    # Check if username already exists
    if get_user_by_username(username):
        return False, "Username already exists. Please log in instead."

    # Create user
    user_id = create_user(username, pin)
    if user_id:
        return True, "Account created successfully! You can now log in."
    return False, "Failed to create account. Please try again."


def is_authenticated() -> bool:
    """Check if current session is authenticated."""
    init_session_state()
    return st.session_state.authenticated


def get_current_username() -> str | None:
    """Get the current logged-in username."""
    init_session_state()
    return st.session_state.username


def require_auth():
    """
    Decorator-style function to require authentication.
    Call at the top of pages that require login.
    Returns True if authenticated, False otherwise.
    """
    init_session_state()
    if not st.session_state.authenticated:
        st.warning("Please log in to access this page.")
        st.info("Go to the **Dashboard** to log in or create an account.")
        return False
    return True


def show_login_form():
    """Display the login/register form in the sidebar or main area."""
    init_session_state()

    if st.session_state.authenticated:
        st.success(f"Logged in as: **{st.session_state.username}**")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
        return True

    # Login/Register tabs - Register first for new users
    tab1, tab2 = st.tabs(["Register", "Login"])

    with tab1:
        st.markdown("### Create Account")
        st.markdown("*New user? Create an account to get started.*")
        reg_username = st.text_input(
            "Username (Full Name)",
            key="reg_username",
            placeholder="Enter your full name...",
            help="Use your full name exactly as you want it recorded"
        )
        reg_pin = st.text_input(
            "Create 4-Digit PIN",
            type="password",
            key="reg_pin",
            placeholder="Create a 4-digit PIN...",
            max_chars=4,
            help="Choose a memorable 4-digit number"
        )
        reg_pin_confirm = st.text_input(
            "Confirm PIN",
            type="password",
            key="reg_pin_confirm",
            placeholder="Confirm your PIN...",
            max_chars=4
        )

        if st.button("Create Account", use_container_width=True, type="primary", key="reg_btn"):
            if not reg_username or not reg_pin:
                st.error("Please fill in all fields.")
            elif reg_pin != reg_pin_confirm:
                st.error("PINs do not match.")
            else:
                success, message = register(reg_username.strip(), reg_pin)
                if success:
                    st.success(message)
                    st.info("Switch to the **Login** tab to sign in.")
                else:
                    st.error(message)

    with tab2:
        st.markdown("### Login")
        st.markdown("*Already have an account? Sign in here.*")
        login_username = st.text_input(
            "Username (Full Name)",
            key="login_username",
            placeholder="Enter your full name..."
        )
        login_pin = st.text_input(
            "4-Digit PIN",
            type="password",
            key="login_pin",
            placeholder="Enter your PIN...",
            max_chars=4
        )

        if st.button("Login", use_container_width=True, type="primary", key="login_btn"):
            if not login_username or not login_pin:
                st.error("Please enter both username and PIN.")
            elif login(login_username.strip(), login_pin):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or PIN. Please try again.")

    return False
