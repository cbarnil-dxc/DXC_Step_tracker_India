# db.py
from supabase import create_client, ClientOptions
import streamlit as st

# Load credentials from Streamlit secrets
supabase_secrets = st.secrets["supabase"]
url = supabase_secrets["url"]
key = supabase_secrets["key"]

if not url or not key:
    raise RuntimeError("supabase.url or supabase.key not set in secrets.toml")

# Client options for Supabase v2.24.0
options = ClientOptions(
    auto_refresh_token=True,
    persist_session=False,
)

supabase = create_client(url, key, options)
