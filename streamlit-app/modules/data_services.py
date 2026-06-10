"""
Database service module for DXC Step Tracker.
Contains functions for database operations and data fetching.
"""

import pandas as pd
from .db import supabase


def get_user_id(username: str):
    """
    Get user ID from username (email).
    
    Args:
        username: User email to look up
        
    Returns:
        User ID if found, None otherwise
    """
    try:
        res = supabase.table("users").select("user_id").eq("user_email", username).execute()
        if res.data:
            return res.data[0]["user_id"]
    except Exception:
        pass
    return None


def fetch_user_forms(user_id: int):
    """
    Fetch all forms for a specific user.
    
    Args:
        user_id: User ID to fetch forms for
        
    Returns:
        DataFrame of user forms, or empty DataFrame if none found
    """
    try:
        res = supabase.table("forms").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_all_users():
    """
    Fetch all users from the database.
    
    Returns:
        DataFrame of all users, or empty DataFrame if none found
    """
    try:
        res = supabase.table("users").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_all_forms():
    """
    Fetch all forms from the database.
    
    Returns:
        DataFrame of all forms, or empty DataFrame if none found
    """
    try:
        res = supabase.table("forms").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_all_teams():
    """
    Fetch all teams from the database.
    
    Returns:
        DataFrame of all teams, or empty DataFrame if none found
    """
    try:
        res = supabase.table("teams").select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_all_submissions():
    """
    Fetch all unverified submissions with step count > 19999.
    
    Returns:
        DataFrame of submissions merged with user data
    """
    try:
        forms = supabase.table("forms") \
            .select("*") \
            .eq("form_verified", False) \
            .gt("form_stepcount", 19999) \
            .execute().data
        users = supabase.table("users").select("user_id, user_name").execute().data
        if not forms:
            return pd.DataFrame()
        df_forms = pd.DataFrame(forms)
        df_users = pd.DataFrame(users)
        return pd.merge(df_forms, df_users, on="user_id")
    except Exception:
        return pd.DataFrame()
