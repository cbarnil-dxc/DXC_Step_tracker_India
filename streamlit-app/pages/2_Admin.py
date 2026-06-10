import streamlit as st
import os
import shutil
import zipfile
import io
import pandas as pd
import re
import unicodedata
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from modules.db import supabase
from modules.components import (apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome,
                        hide_streamlit_branding, check_login_required, handle_logout, secure_filename, log_audit_event)
from modules.auth import is_admin
from modules.data_services import fetch_all_submissions
from modules.excel_export import generate_comprehensive_export
from modules.onedrive_storage import get_file_download_url, delete_from_onedrive, get_access_token, get_file_id_from_sharing_url

# ------------------ PAGE CONFIG ------------------
logo_path = Path(__file__).resolve().parents[1] / ".streamlit" / "static" / "assets" / "logo.png"
st.set_page_config(page_title="Admin Dashboard", layout="wide", page_icon=logo_path)

# Hide branding early
hide_streamlit_branding()

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo()
render_header("Admin Dashboard", "Manage submissions and verify evidence.")

# ------------------ LOGIN & ROLE CHECK ------------------
username = check_login_required()
user_email = st.session_state.get("user_email", "")

# Check if user email is in admin list from secrets
if not is_admin(user_email):
    log_audit_event("ADMIN_ACCESS_DENIED", user_email, "Attempted to access admin dashboard")
    st.error("Access denied.")
    st.stop()

# ------------------ CONFIG & STATE ------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# replace old confirm state with a simpler pending_delete entry
if "pending_delete" not in st.session_state:
    st.session_state["pending_delete"] = None

# ------------------ FETCH DATA FROM SUPABASE ------------------
df = fetch_all_submissions()

# ------------------ SIDEBAR ------------------
if render_sidebar_welcome():
    handle_logout()

# ------------------ 1. HIGH-STEP SUBMISSIONS (>20,000) ------------------
st.subheader(
    "Unverified Submissions (Steps > 20,000)",
    help="Review and verify step submissions over 20,000 steps. Check the screenshot evidence and click 'Verify' to approve or 'Delete' to remove suspicious entries."
)

if not df.empty:
    for idx, row in df.iterrows():
        col1, col2 = st.columns([3, 1])
        filepath = row.get("form_filepath", "")
        
        # Check if it's a OneDrive URL or local file
        is_onedrive = filepath.startswith("http") or "sharepoint" in filepath.lower() or "onedrive" in filepath.lower()
        
        with col1:
            st.markdown(f"**Name:** {row['user_name']} | **Date:** {row['form_date']} | **Steps:** {row['form_stepcount']}")
            with st.expander("View Full Screenshot"):
                if is_onedrive:
                    st.markdown(f"**Evidence stored in OneDrive:**" + f" [🗁 Open in OneDrive]({filepath})")
                    st.info("Click the link above to view the screenshot in OneDrive.")
                else:
                    safe_name = secure_filename(os.path.basename(str(filepath)))
                    file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                    if os.path.exists(file_path):
                        st.image(file_path, caption=f"Screenshot for {row['user_name']}", width="stretch")
                    else:
                        st.warning("Screenshot not found.")

        with col2:
            if st.button("Verify", key=f"verify_{idx}"):
                try:
                    # Delete from OneDrive if applicable
                    if is_onedrive:
                        access_token = get_access_token()
                        if access_token:
                            file_id = get_file_id_from_sharing_url(filepath, access_token)
                            if file_id:
                                delete_from_onedrive(file_id, access_token)
                    
                    # Delete local file if applicable
                    if not is_onedrive:
                        try:
                            safe_name = secure_filename(os.path.basename(str(filepath)))
                            file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                            os.remove(file_path)
                        except FileNotFoundError:
                            pass

                    # Update database to set form_verified to True
                    supabase.table("forms") \
                        .update({"form_verified": True}) \
                        .eq("form_id", row["form_id"]) \
                        .execute()

                    log_audit_event("VERIFICATION", user_email, f"Form ID: {row['form_id']}, Steps: {row['form_stepcount']}")
                    st.success("Submission verified successfully!")
                except Exception:
                    logging.error("Verification error")
                    st.error("Error verifying form, please try again later.")
                st.rerun()
            if st.button("Delete", key=f"delete_{idx}"):
                # set a small pending_delete dict rather than relying on index
                st.session_state["pending_delete"] = {
                    "form_id": row["form_id"],
                    "user_name": row["user_name"],
                    "form_date": row["form_date"],
                    "form_stepcount": row["form_stepcount"],
                    "file": row.get("form_filepath", "")
                }
                st.rerun()
        
        # Show confirmation dialog inline if this row is being deleted
        if st.session_state["pending_delete"] and st.session_state["pending_delete"]["form_id"] == row["form_id"]:
            pd = st.session_state["pending_delete"]
            st.error("### ⚠ Confirm Deletion")
            st.markdown(f"You are about to permanently delete the submission for:")
            st.markdown(f"- **User:** {pd['user_name']}")
            st.markdown(f"- **Date:** {pd['form_date']}")
            st.markdown(f"- **Steps:** {pd['form_stepcount']}")
            st.markdown("")
            confirm_cb = st.checkbox("I understand this action cannot be undone", key="confirm_delete_cb")
            st.markdown("")
            colA, colB, colC = st.columns([1, 1, 2])
            with colA:
                if st.button("🗙 Delete Permanently", disabled=not confirm_cb, type="secondary", key=f"confirm_delete_{idx}"):
                    try:
                        filepath = pd.get("file", "")
                        is_onedrive = filepath.startswith("http") or "sharepoint" in filepath.lower() or "onedrive" in filepath.lower()
                        
                        # Transaction pattern: Delete from database first, then file
                        # If file deletion fails, we can't rollback, but at least we have the record
                        form_id = pd["form_id"]
                        file_path = pd.get("file", "")
                        
                        # Delete from database
                        supabase.table("forms").delete().eq("form_id", form_id).execute()
                        
                        # Delete file (local or OneDrive)
                        file_deleted = False
                        try:
                            if not is_onedrive:
                                safe_file_path = os.path.join(UPLOAD_FOLDER, secure_filename(os.path.basename(str(file_path))))
                                if os.path.exists(safe_file_path):
                                    os.remove(safe_file_path)
                                    file_deleted = True
                            else:
                                # Delete from OneDrive
                                access_token = get_access_token()
                                if access_token:
                                    file_id = get_file_id_from_sharing_url(file_path, access_token)
                                    if file_id:
                                        delete_from_onedrive(file_id, access_token)
                                        file_deleted = True
                        except Exception:
                            logging.error("File deletion failed but DB record deleted")
                            # File deletion failed but DB record is deleted
                            # This is acceptable - file will be orphaned but not accessible through app
                        
                        st.session_state["pending_delete"] = None
                        
                        if file_deleted:
                            st.success("Submission deleted successfully.")
                        else:
                            st.warning("Submission deleted from database, but file cleanup failed. This will be cleaned up later.")
                        
                        log_audit_event("DELETION", user_email, f"Form ID: {form_id}, File deleted: {file_deleted}")
                        st.rerun()
                    except Exception:
                        logging.error("Deletion error")
                        st.error("Error deleting submission, please try again later.")
            with colB:
                if st.button("Cancel", key=f"cancel_delete_{idx}", type="secondary"):
                    st.session_state["pending_delete"] = None
                    st.rerun()
        
        st.markdown("---")
else:
    st.info("No high-step unverified submissions found.")

# ------------------ 2. DOWNLOAD COMPREHENSIVE DATA ------------------
st.subheader(
    "Download Comprehensive Data",
    help="Export comprehensive user and team statistics as an Excel file with detailed metrics, sorted by total steps."
)

excel_data = generate_comprehensive_export()
if excel_data:
    st.download_button(
        "Download Excel Report",
        excel_data,
        file_name=f"step_tracker_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.caption("Includes user statistics, team statistics, general statistics, and challenge completion data.")
else:
    st.info("Unable to generate report. Please check the data and try again.")

st.divider()

# ------------------ 3. GENERATE CLAIM CODES -------------------
st.subheader(
    "Generate Claim Codes",
    help="Create unique claim codes for verified step submissions."
)
from modules.challenges import get_all_challenges, generate_claim_code, hash_claim_code

# Initialize session state for generated codes
if "generated_codes" not in st.session_state:
    st.session_state.generated_codes = []

Challenges = get_all_challenges()

col_left, col_right = st.columns([1, 1])

with col_left:
    ChallengesDropdown = st.selectbox("Select Challenge", options=[Challenges[ch]["title"] for ch in Challenges])
    num_codes = st.number_input("Number of Claim Codes to Generate", min_value=1, max_value=100, value=5)
    
    # Check if selected challenge has variable reward
    selected_challenge_key = None
    is_variable_reward = False
    for ch in Challenges:
        if Challenges[ch]["title"] == ChallengesDropdown:
            selected_challenge_key = ch
            is_variable_reward = Challenges[ch].get("variable_reward", False)
            break
    
    # Show reward input for variable reward challenges
    if is_variable_reward:
        reward_amount = st.number_input(
            "Reward Amount (steps)",
            min_value=0,
            max_value=50000,
            value=2000,
            step=500,
            help="Enter the number of steps to award for each code generated for this challenge"
        )
    else:
        reward_amount = None
    
    if st.button("Generate Claim Codes"):
        if not ChallengesDropdown:
            st.error("Please select a challenge to generate claim codes for.")
            st.stop()

        # Generate codes with proper duplicate tracking
        generated_codes = []
        existing_codes = set()
        for challenge in Challenges:
            existing_codes.update(Challenges[challenge]["Codes"])
        
        for _ in range(num_codes):
            code = generate_claim_code(Challenges, existing_codes)
            generated_codes.append(code)
            existing_codes.add(hash_claim_code(code))  # Add hash to avoid duplicates

        # Hash codes for storage
        if is_variable_reward:
            # Store as dict with hash and reward for variable reward challenges
            hashed_codes = [{"hash": hash_claim_code(code), "reward": reward_amount} for code in generated_codes]
        else:
            # Store as simple hash string for fixed reward challenges
            hashed_codes = [hash_claim_code(code) for code in generated_codes]

        # Read and update Challenges.json with proper path
        challenges_path = Path(__file__).resolve().parents[1] / ".streamlit" / "static" / "assets" / "Challenges.json"
        try:
            with open(challenges_path, "r", encoding="utf-8") as f:
                challenges_data = json.load(f)
            
            # Add hashed codes to the selected challenge
            for challenge_key in challenges_data:
                if challenges_data[challenge_key]["title"] == ChallengesDropdown:
                    challenges_data[challenge_key]["Codes"].extend(hashed_codes)
                    break
            
            # Write back to file
            with open(challenges_path, "w", encoding="utf-8") as f:
                json.dump(challenges_data, f, indent=4)

            st.session_state.generated_codes = generated_codes
            log_audit_event("CODE_GENERATION", user_email, f"Challenge: {ChallengesDropdown}, Count: {num_codes}, Reward: {reward_amount if is_variable_reward else 'Fixed'}")
        except Exception:
            st.error("Error generating codes.")
            logging.error("Code generation error")

with col_right:
    if st.session_state.generated_codes:
        codes_text = "\n".join(st.session_state.generated_codes)
        st.text_area("Codes", codes_text, height=200, key="generated_codes_display")

# ------------------ FOOTER (ALWAYS RENDER) ------------------
render_footer()
