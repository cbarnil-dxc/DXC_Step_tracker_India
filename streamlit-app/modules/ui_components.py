"""
Reusable UI components for DXC Step Tracker.
Contains functions for rendering headers, footers, and common UI elements.
"""

import streamlit as st
import html


def render_header(title: str, subtitle: str):
    """
    Render the DXC Technology header with blue gradient background.
    
    Args:
        title: Main header title
        subtitle: Subtitle text
    """
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    
    st.markdown(
        f"""
        <div class="header-container">
            <div>
                <div class="header-title">{safe_title}</div>
                <div class="header-subtitle">{safe_subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_footer():
    """Render the DXC Technology footer with blue divider."""
    st.markdown(
        "<div style='margin-top:60px; padding-top:20px; border-top:3px solid #7BA4DB;'></div>",
        unsafe_allow_html=True
    )


def render_sidebar_welcome(display_name=None):
    """
    Render welcome message in sidebar with logout button.
    Uses display_name from session state if not provided.
    
    Args:
        display_name: Display name to show (optional, defaults to session state)
        
    Returns:
        bool: True if logout button was clicked
    """
    if display_name is None:
        display_name = st.session_state.get("display_name", st.session_state.get("username", "User"))
    
    safe_display_name = html.escape(display_name)
    
    st.sidebar.markdown(
        f"<h3 style='color:#7BA4DB;'>Welcome, {safe_display_name}!</h3>",
        unsafe_allow_html=True
    )
    return st.sidebar.button("Logout", type="secondary")
