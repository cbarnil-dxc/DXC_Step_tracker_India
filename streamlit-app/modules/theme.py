"""
UI theming and styling module for DXC Step Tracker.
Contains functions for applying the DXC theme, fonts, and visual styling.
"""

import streamlit as st
import base64
from pathlib import Path

# ------------------ PATHS + STATIC ASSETS ------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # Go up to streamlit-app root
ASSETS_DIR = BASE_DIR / ".streamlit" / "static" / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
HEADER_FONT_PATH = ASSETS_DIR / "GT-Standard-L-Extended-Medium.otf"


def apply_header_font():
    """Apply the GT-Standard font to headers using base64 encoding."""
    if not HEADER_FONT_PATH.exists():
        return

    try:
        font_b64 = base64.b64encode(HEADER_FONT_PATH.read_bytes()).decode("utf-8")
    except Exception:
        return

    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'GTStandardHeader';
            src: url(data:font/otf;base64,{font_b64}) format('opentype');
            font-weight: 500;
            font-style: normal;
        }}

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6,
        .header-title, .header-subtitle {{
            font-family: 'GTStandardHeader', sans-serif !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_dxc_theme():
    """Apply the DXC gradient theme and styling to the page."""
    apply_header_font()
    
    st.markdown("""
    <style>
        /* White to Blue to Orange Gradient Background */
        .stApp {
            background: linear-gradient(135deg, 
                #FFFFFF 0%,     /* White */
                #F8FBFF 25%,    /* Light blue */
                #E3F2FD 50%,    /* Soft blue */
                #FFF3E0 75%,    /* Light orange */
                #FFE0B2 100%    /* Soft orange */
            );
            min-height: 100vh;
        }
        
        /* Make Streamlit header transparent */
        .stApp header {
            background: rgba(255, 255, 255, 0) !important;
            box-shadow: none !important;
            border: none !important;
        }
        
        .header-container {
            display: flex;
            justify-content: flex-start;
            align-items: center;
            background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
            color: white;
            padding: 20px 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .header-title { font-size: 42px; font-weight: bold; }
        .header-subtitle { font-size: 18px; margin-top: 5px; }
        
        /* Custom gradient buttons - exclude Logout and Submit */
        .stButton>button:not([kind="secondary"]) {
            background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
            color: white;
            border-radius: 8px;
            font-weight: bold;
            transition: 0.3s;
            border: none;
        }
        .stButton>button:not([kind="secondary"]):hover {
            background: linear-gradient(90deg, #6B94CB, #EF8A5C);
            transform: scale(1.05);
        }
        
        /* Secondary buttons and form submit buttons - white background, blue border */
        .stButton>button[kind="secondary"],
        .stFormSubmitButton>button {
            background-color: #FFFFFF !important;
            border: 1px solid #7BA4DB !important;
            color: #31333F !important;
            border-radius: 8px;
            font-weight: bold;
        }
        .stButton>button[kind="secondary"]:hover,
        .stFormSubmitButton>button:hover {
            background-color: #F8FBFF !important;
            border: 1px solid #6B94CB !important;
        }
        
        /* Sidebar border - creates visible divider */
        [data-testid="stSidebar"] {
            border-right: 2px solid #7BA4DB !important;
        }
        
        .footer-branding {
            text-align: center;
            font-size: 14px;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #7BA4DB;
        }
    </style>
    """, unsafe_allow_html=True)


def setup_logo():
    """Setup the logo in the sidebar."""
    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), icon_image=str(LOGO_PATH), size="large")
    else:
        st.warning(f"Logo not found at: {LOGO_PATH}")


def hide_streamlit_branding():
    """Hide Streamlit's default branding elements."""
    st.html(
        """
        <script>
        window.addEventListener('load', () => {
            window.top.document.querySelectorAll(`[href*="streamlit.io"]`)
                .forEach(e => e.style.display = 'none');
        });
        </script>
        """
    )
