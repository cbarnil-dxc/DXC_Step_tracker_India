import streamlit as st
import pandas as pd
from modules.db import supabase
from pathlib import Path
from modules.components import apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome, hide_streamlit_branding, check_login_required, handle_logout

# ------------------ PAGE CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / ".streamlit" / "static" / "assets" / "logo.png"
st.set_page_config(page_title="Leaderboard", layout="wide", page_icon=logo_path2)

# Hide branding early
hide_streamlit_branding()

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo()
render_header("DXC Step Leaderboard", "Keep a Track of Leaders & Your Friends!")

# ------------------ SECURITY: LOGIN CHECK ------------------
username = check_login_required()

# ------------------ SIDEBAR ------------------
if render_sidebar_welcome():
    handle_logout()

# ------------------ TABS ------------------
tab1, tab2 = st.tabs(["Individual Leaderboard", "Team Leaderboard"])

# ------------------ TAB 1: INDIVIDUAL LEADERBOARD ------------------
with tab1:
    st.subheader("Filter Leaderboard")

    col1, col2 = st.columns(2)
    with col1:
        selected_date = st.date_input(
            "Select a date (leave empty for all-time)",
            value=None,
            key="individual_date"
        )
    with col2:
        view_option = st.selectbox(
            "Show:",
            ["All", "Top 10", "Bottom 10"],
            key="individual_view"
        )

    # ------------------ FETCH DATA FROM SUPABASE ------------------
    try:
        # Try to use database-level aggregation for performance
        try:
            if selected_date:
                response = supabase.rpc('get_user_step_totals', {'p_date': str(selected_date)}).execute()
            else:
                response = supabase.rpc('get_user_step_totals', {'p_date': None}).execute()
            
            if response.data:
                step_summary = pd.DataFrame(response.data)
            else:
                raise Exception("RPC returned no data")
        except Exception:
            # Fallback to per-user aggregation if RPC not available
            # Get unique user_ids first
            if selected_date:
                response = supabase.table("forms").select("user_id").eq("form_date", str(selected_date)).execute()
                user_ids = list(set(r["user_id"] for r in response.data))
            else:
                response = supabase.table("forms").select("user_id").execute()
                user_ids = list(set(r["user_id"] for r in response.data))
            
            step_summary_data = []
            for uid in user_ids:
                # Fetch all records for this user with pagination
                total = 0
                offset = 0
                batch_size = 1000
                
                while True:
                    if selected_date:
                        user_batch = supabase.table("forms").select("form_stepcount").eq("user_id", uid).eq("form_date", str(selected_date)).range(offset, offset + batch_size - 1).execute()
                    else:
                        user_batch = supabase.table("forms").select("form_stepcount").eq("user_id", uid).range(offset, offset + batch_size - 1).execute()
                    
                    batch_total = sum(r["form_stepcount"] for r in user_batch.data)
                    total += batch_total
                    
                    if len(user_batch.data) < batch_size:
                        break
                    
                    offset += batch_size
                
                step_summary_data.append({"user_id": uid, "total_steps": total})
            
            step_summary = pd.DataFrame(step_summary_data)
    except Exception:
        st.error("Database error while fetching forms.")
        st.stop()

    if step_summary.empty:
        st.info("No step data available for the selected date." if selected_date else "No step data available.")
        st.stop()

    # ------------------ GET USERNAMES ------------------
    try:
        users = supabase.table("users").select("user_id, user_name").execute().data
        users_df = pd.DataFrame(users)
    except Exception as e:
        st.error(f"Error fetching user data, please try again later.")
        st.stop()

    # Merge steps with usernames
    leaderboard = pd.merge(step_summary, users_df, on="user_id", how="inner")
    leaderboard = leaderboard[["user_name", "total_steps"]]

    leaderboard.rename(columns={
        "user_name": "Username",
        "total_steps": "Step Count"
    }, inplace=True)

    # ------------------ SORTING OPTIONS ------------------
    if view_option == "Top 10":
        leaderboard = leaderboard.sort_values("Step Count", ascending=False).head(10)
    elif view_option == "Bottom 10":
        leaderboard = leaderboard.sort_values("Step Count", ascending=True).head(10)
    else:  # All
        leaderboard = leaderboard.sort_values("Step Count", ascending=False)

    leaderboard.reset_index(drop=True, inplace=True)
    leaderboard.index += 1  # Start rank from 1

    # ------------------ DISPLAY ------------------
    st.subheader("Individual Leaderboard")
    if selected_date:
        st.caption(f"Showing results for **{selected_date}**")
    else:
        st.caption("Showing **all-time** results")

    if leaderboard.empty:
        st.info("No data available to display.")
    else:
        st.dataframe(leaderboard, width='stretch')

        # Highlight top performer (only for All or Top 10 views)
        if view_option != "Bottom 10" and not leaderboard.empty:
            top_user = leaderboard.iloc[0]
            st.success(f"✪ {top_user['Username']} is leading with {int(top_user['Step Count'])} steps!")

# ------------------ TAB 2: TEAM LEADERBOARD ------------------
with tab2:
    st.subheader("Filter Team Leaderboard")
    
    col1, col2 = st.columns(2)
    with col1:
        team_selected_date = st.date_input(
            "Select a date (leave empty for all-time)",
            value=None,
            key="team_date"
        )
    with col2:
        team_view_option = st.selectbox(
            "Show:",
            ["All", "Top 10", "Bottom 10"],
            key="team_view"
        )
    
    # ------------------ FETCH TEAM DATA ------------------
    try:
        # Get all teams
        teams = supabase.table("teams").select("team_id, team_name").execute().data
        
        if not teams:
            st.info("No teams have been created yet.")
            st.stop()
        
        # Get all users with team assignments
        users_with_teams = supabase.table("users").select("user_id, team_id").execute().data
        
        # Create dataframes
        teams_df = pd.DataFrame(teams)
        users_teams_df = pd.DataFrame(users_with_teams)
        
        # Try to use database-level aggregation for performance
        try:
            if team_selected_date:
                response = supabase.rpc('get_team_step_totals', {'p_date': str(team_selected_date)}).execute()
            else:
                response = supabase.rpc('get_team_step_totals', {'p_date': None}).execute()
            
            if response.data:
                team_steps = pd.DataFrame(response.data)
                # Merge with team names
                team_leaderboard = pd.merge(team_steps, teams_df, on="team_id", how="inner")
                rpc_success = True
            else:
                raise Exception("RPC returned no data")
        except Exception:
            # Fallback to per-user aggregation if RPC not available
            rpc_success = False
            
            # Get unique user_ids first
            if team_selected_date:
                response = supabase.table("forms").select("user_id").eq("form_date", str(team_selected_date)).execute()
                user_ids = list(set(r["user_id"] for r in response.data))
            else:
                response = supabase.table("forms").select("user_id").execute()
                user_ids = list(set(r["user_id"] for r in response.data))
            
            # Fetch all forms with pagination for each user
            all_forms = []
            for uid in user_ids:
                offset = 0
                batch_size = 1000
                
                while True:
                    if team_selected_date:
                        user_batch = supabase.table("forms").select("user_id, form_stepcount, form_date").eq("user_id", uid).eq("form_date", str(team_selected_date)).range(offset, offset + batch_size - 1).execute()
                    else:
                        user_batch = supabase.table("forms").select("user_id, form_stepcount, form_date").eq("user_id", uid).range(offset, offset + batch_size - 1).execute()
                    
                    all_forms.extend(user_batch.data)
                    
                    if len(user_batch.data) < batch_size:
                        break
                    
                    offset += batch_size
            
            forms_data = all_forms
            
            if not forms_data:
                st.info("No step data available for the selected date." if team_selected_date else "No step data available.")
                st.stop()
            
            forms_df = pd.DataFrame(forms_data)
            
            # Merge forms with user team assignments
            merged = pd.merge(forms_df, users_teams_df, on="user_id", how="inner")
            
            # Filter out users without teams
            merged = merged[merged["team_id"].notna()]
            
            if merged.empty:
                st.info("No team members have submitted steps yet.")
                st.stop()
            
            # Aggregate steps by team
            team_steps = merged.groupby("team_id")["form_stepcount"].sum().reset_index()
            team_steps.rename(columns={"form_stepcount": "total_steps"}, inplace=True)
            
            # Merge with team names
            team_leaderboard = pd.merge(team_steps, teams_df, on="team_id", how="inner")
        
        # Get member names for each team
        users_with_names = supabase.table("users").select("user_id, user_name, team_id").execute().data
        users_names_df = pd.DataFrame(users_with_names)
        
        # Group by team_id and join member names
        member_names = users_names_df[users_names_df["team_id"].notna()].groupby("team_id")["user_name"].apply(lambda x: ", ".join(sorted(x))).reset_index(name="member_names")
        team_leaderboard = pd.merge(team_leaderboard, member_names, on="team_id", how="left")
        team_leaderboard["member_names"] = team_leaderboard["member_names"].fillna("No members")
        
        # Select and rename columns
        team_leaderboard = team_leaderboard[["team_name", "total_steps", "member_names"]]
        team_leaderboard.rename(columns={
            "team_name": "Team Name",
            "total_steps": "Total Steps",
            "member_names": "Members"
        }, inplace=True)
        
        # ------------------ SORTING OPTIONS ------------------
        if team_view_option == "Top 10":
            team_leaderboard = team_leaderboard.sort_values("Total Steps", ascending=False).head(10)
        elif team_view_option == "Bottom 10":
            team_leaderboard = team_leaderboard.sort_values("Total Steps", ascending=True).head(10)
        else:  # All
            team_leaderboard = team_leaderboard.sort_values("Total Steps", ascending=False)
        
        team_leaderboard.reset_index(drop=True, inplace=True)
        team_leaderboard.index += 1  # Start rank from 1
        
        # ------------------ DISPLAY ------------------
        st.subheader("Team Leaderboard")
        if team_selected_date:
            st.caption(f"Showing results for **{team_selected_date}**")
        else:
            st.caption("Showing **all-time** results")
        
        if team_leaderboard.empty:
            st.info("No data available to display.")
        else:
            st.dataframe(team_leaderboard, width='stretch')
            
            # Highlight top team (only for All or Top 10 views)
            if team_view_option != "Bottom 10" and not team_leaderboard.empty:
                top_team = team_leaderboard.iloc[0]
                st.success(f"✪ {top_team['Team Name']} is leading with {int(top_team['Total Steps'])} steps!")
        
    except Exception:
        st.error("Error loading team leaderboard.")

# ------------------ FOOTER (ALWAYS RENDER) ------------------
render_footer()