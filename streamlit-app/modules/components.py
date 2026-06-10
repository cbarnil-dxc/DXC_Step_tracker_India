"""
Core utility functions for DXC Step Tracker application.
This module contains shared utility functions for logging, validation, and sanitization.

Note: For backward compatibility, this module also re-exports functions from specialized modules:
- Theme functions: see theme.py
- UI components: see ui_components.py
- Authentication: see auth.py
- Database operations: see data_services.py
- Challenge logic: see challenges.py
"""

import streamlit as st
import logging
import os
import re
import unicodedata

# Re-export from specialized modules for backward compatibility
from .theme import apply_dxc_theme, setup_logo, hide_streamlit_branding
from .ui_components import render_header, render_footer, render_sidebar_welcome
from .auth import check_login_required, handle_logout, is_admin
from .data_services import get_user_id, fetch_user_forms
from .challenges import get_all_challenges, get_met_values, generate_claim_code, hash_claim_code, validate_claim_code

# ==================== CORE UTILITY FUNCTIONS ====================

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        filename="app.log",
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def log_audit_event(event_type, user_email, details=None):
    """
    Log audit events for sensitive operations.
    
    Args:
        event_type: Type of event (e.g., "VERIFICATION", "CODE_GENERATION", "ADMIN_ACCESS")
        user_email: Email of the user performing the action
        details: Additional details about the event (optional)
    """
    try:
        # Sanitize email for logging
        safe_email = user_email[:3] + "***@***" if user_email else "unknown"
        
        log_message = f"AUDIT: {event_type} - User: {safe_email}"
        if details:
            log_message += f" - Details: {details}"
        
        logging.info(log_message)
    except Exception:
        logging.error("Failed to log audit event")


def secure_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filenames to prevent directory traversal or injection.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "file"
    filename = os.path.basename(filename)
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("utf-8", "ignore").decode("utf-8")
    filename = re.sub(r"[^A-Za-z0-9.\-_]", "_", filename)
    return filename[:max_length]


def sanitize_username(username: str) -> str:
    """
    Sanitize and validate username.
    
    Args:
        username: Username to sanitize
        
    Returns:
        Sanitized username
        
    Raises:
        ValueError: If username doesn't meet requirements
    """
    username = username.strip()
    if not re.match(r"^[A-Za-z0-9 _.-]{3,50}$", username):
        raise ValueError(
            "Username must be 3–50 characters long and contain only letters, numbers, spaces, dots, underscores, or hyphens."
        )
    return username


def validate_password(password: str) -> bool:
    """
    Validate password strength.
    Requires at least 8 chars, one letter, one digit, one special char.
    
    Args:
        password: Password to validate
        
    Returns:
        True if password meets requirements, False otherwise
    """
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$', password))

