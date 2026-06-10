# DXC Step Tracker

A Streamlit web application for tracking steps during the Movember campaign, featuring OAuth2 authentication with Microsoft Identity, team challenges, and comprehensive step tracking.

## Features

- **Microsoft OAuth2 Authentication**: Secure login with Microsoft Identity platform
- **Step Tracking**: Log daily steps with screenshot verification for high step counts
- **Activity Conversion**: Convert non-walking activities to steps using MET values
- **AI & Wellbeing Challenges**: Complete challenges and redeem claim codes
- **Team Management**: Join or create teams to compete together
- **Leaderboards**: Individual and team leaderboards
- **Daily Progress**: Track step history, streaks, and statistics
- **Admin Dashboard**: Manage users, generate claim codes, and export data
- **OneDrive Integration**: Upload evidence screenshots to Microsoft OneDrive

## Project Structure

```
MovemberStepTracker/
├── .github/
│   └── workflows/
│       ├── ping-supabase.yml    # Keeps Supabase database alive
│       └── wake-streamlit.yml   # Wakes Streamlit app if sleeping
├── streamlit-app/
│   ├── Home.py                  # Main application entry point
│   ├── pages/                   # Streamlit multipage application
│   │   ├── 1_Leaderboard.py     # Leaderboard page
│   │   └── 2_Admin.py           # Admin dashboard
│   ├── modules/                 # Shared business logic and utilities
│   │   ├── __init__.py          # Package initialization
│   │   ├── auth.py              # OAuth2 authentication and session management
│   │   ├── challenges.py        # Challenge data and claim code logic
│   │   ├── components.py        # Core utility functions (re-exports)
│   │   ├── data_services.py     # Database query functions
│   │   ├── db.py                # Supabase database connection
│   │   ├── excel_export.py      # Excel export functionality
│   │   ├── onedrive_storage.py  # OneDrive API integration
│   │   ├── theme.py             # UI theming and styling
│   │   └── ui_components.py     # Reusable UI components
│   ├── .streamlit/
│   │   ├── config.toml          # Streamlit configuration
│   │   └── static/
│   │       └── assets/
│   │           ├── logo.png     # Application logo
│   │           ├── GT-Standard-L-Extended-Medium.otf  # Custom font
│   │           ├── Challenges.json  # Challenge definitions
│   │           └── MetValues.json    # MET conversion values
│   ├── Dockerfile               # Docker configuration for deployment
│   └── requirements.txt         # Python dependencies
├── runner.py                    # Selenium script for app wake-up
├── runner-req.txt               # Dependencies for runner script
└── README.md
```

## Installation

### Prerequisites

- Python 3.10+
- Supabase account (PostgreSQL database)
- Microsoft Azure AD application (for OAuth2)
- OneDrive app registration (for file uploads)
- Streamlit Cloud account (for deployment)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DWandless/MovemberStepTracker.git
   cd MovemberStepTracker
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   cd streamlit-app
   pip install -r requirements.txt
   ```

4. **Configure secrets:**
   Create a `.streamlit/secrets.toml` file with the following structure:

   ```toml
   [supabase]
   url = "your-supabase-project-url"
   key = "your-supabase-anon-key"

   [azure]
   client_id = "your-azure-ad-client-id"
   client_secret = "your-azure-ad-client-secret"
   tenant_id = "your-azure-tenant-id"  # Optional, defaults to common

   [onedrive]
   client_id = "your-onedrive-app-client-id"
   client_secret = "your-onedrive-app-client-secret"
   tenant_id = "your-onedrive-tenant-id"

   [admin]
   emails = ["admin1@example.com", "admin2@example.com"]
   ```

   **Secrets Configuration Guide:**
   
   - **Supabase**: Get from your Supabase project settings
   - **Azure AD**: Register a web app in Azure AD with redirect URI `http://localhost:8501/_auth/callback` for local development
   - **OneDrive**: Register an app in Azure AD with `Files.ReadWrite` and `Files.ReadWrite.AppFolder` permissions
   - **Admin emails**: Comma-separated list of admin email addresses for access control

5. **Configure static assets:**
   Ensure the following files exist in `.streamlit/static/assets/`:
   - `logo.png` - Application logo image
   - `GT-Standard-L-Extended-Medium.otf` - Custom font file (optional)
   - `Challenges.json` - Challenge definitions with the format:
     ```json
     {
       "challenge_1": {
         "id": 1,
         "title": "Challenge Title",
         "description": "Challenge description",
         "Reward": 5000,
         "Codes": []
       }
     }
     ```
   - `MetValues.json` - MET conversion values with the format:
     ```json
     {
       "Walking": 100,
       "Running": 150,
       "Cycling": 120
     }
     ```

6. **Run the application:**
   ```bash
   streamlit run Home.py
   ```

   The app will be available at `http://localhost:8501`

## Usage

### Authentication

1. Click "Sign in with Microsoft" to authenticate
2. Authorize the app to access your Microsoft account
3. You will be redirected back to the app after successful authentication

### Submitting Steps

1. Navigate to the "Submit Steps" tab
2. Optionally convert non-walking activities to steps using the MET converter
3. Enter the date and step count
4. For submissions 20,000+ steps, upload a screenshot as proof
5. Click "Submit" to log your steps

### Challenges

1. Navigate to the "AI & Wellbeing Challenges" tab
2. View available challenges and their rewards
3. Click "Redeem" on a challenge to enter a claim code
4. Enter the unique claim code provided by an admin
5. Submit to add the reward steps to your total

### Teams

1. Navigate to the "Teams" tab
2. Join an existing team or create your own
3. Teams can have up to 4 members
4. View team member performance and rankings

### Daily Progress

1. Navigate to the "Daily Progress" tab
2. View your step history, streaks, and statistics
3. Delete submissions if needed

### Admin Dashboard

1. Navigate to the Admin page (requires admin email)
2. View and manage user submissions
3. Generate claim codes for challenges
4. Export comprehensive Excel reports

## Deployment

### Streamlit Cloud

1. Push your code to GitHub
2. Connect your repository to Streamlit Cloud
3. Configure secrets in the Streamlit Cloud dashboard
4. Update the Azure AD redirect URI to `https://your-app-url.streamlit.app/_auth/callback`
5. Deploy

### Docker

A Dockerfile is included for containerized deployment:

```bash
cd streamlit-app
docker build -t dxc-step-tracker .
docker run -p 8501:8501 dxc-step-tracker
```

### GitHub Actions

Two automated workflows keep the services alive:

1. **Supabase Ping** - Runs every 3 days to prevent database hibernation
2. **Streamlit Wake** - Runs every 4 hours to wake the app if sleeping

## Database Schema

The application uses Supabase with the following main tables:

- **`users`** - User accounts and team assignments
  - `user_id` (UUID, primary key)
  - `user_name` (text)
  - `user_email` (text)
  - `team_id` (UUID, foreign key to teams, nullable)

- **`teams`** - Team information
  - `team_id` (UUID, primary key)
  - `team_name` (text)
  - `team_leader_id` (UUID, foreign key to users)

- **`forms`** - Step submissions and challenge completions
  - `form_id` (UUID, primary key)
  - `user_id` (UUID, foreign key to users)
  - `form_stepcount` (integer)
  - `form_date` (date)
  - `form_filepath` (text, nullable - OneDrive URL or local path)
  - `form_verified` (boolean)
  - `challenge_code` (text, nullable - hashed claim code)
  - `form_created_at` (timestamp)

## Leaderboard Performance Optimization

The leaderboard page uses custom Supabase SQL functions for optimal performance. Without these functions, the leaderboard would use client-side pagination which is slow (15+ seconds) and subject to Supabase's 1000-record limit.

### Required SQL Functions

Run the following SQL in your Supabase SQL Editor to create the required functions:

```sql
-- Function: Get user step totals with optional date filter
CREATE OR REPLACE FUNCTION get_user_step_totals(p_date DATE DEFAULT NULL)
RETURNS TABLE(user_id BIGINT, total_steps BIGINT) AS $$
BEGIN
    IF p_date IS NULL THEN
        -- All-time aggregation
        RETURN QUERY
        SELECT f.user_id::BIGINT, SUM(f.form_stepcount)::BIGINT as total_steps
        FROM forms f
        GROUP BY f.user_id;
    ELSE
        -- Date-specific aggregation
        RETURN QUERY
        SELECT f.user_id::BIGINT, SUM(f.form_stepcount)::BIGINT as total_steps
        FROM forms f
        WHERE f.form_date = p_date
        GROUP BY f.user_id;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get team step totals with optional date filter
CREATE OR REPLACE FUNCTION get_team_step_totals(p_date DATE DEFAULT NULL)
RETURNS TABLE(team_id BIGINT, total_steps BIGINT) AS $$
BEGIN
    IF p_date IS NULL THEN
        -- All-time aggregation
        RETURN QUERY
        SELECT u.team_id::BIGINT, SUM(f.form_stepcount)::BIGINT as total_steps
        FROM forms f
        JOIN users u ON f.user_id = u.user_id
        WHERE u.team_id IS NOT NULL
        GROUP BY u.team_id;
    ELSE
        -- Date-specific aggregation
        RETURN QUERY
        SELECT u.team_id::BIGINT, SUM(f.form_stepcount)::BIGINT as total_steps
        FROM forms f
        JOIN users u ON f.user_id = u.user_id
        WHERE f.form_date = p_date AND u.team_id IS NOT NULL
        GROUP BY u.team_id;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

After creating the functions, verify they work by running these test queries in Supabase SQL Editor:

```sql
-- Test user function (all-time)
SELECT * FROM get_user_step_totals(NULL);

-- Test user function (specific date)
SELECT * FROM get_user_step_totals('2026-05-20'::DATE);

-- Test team function (all-time)
SELECT * FROM get_team_step_totals(NULL);
```

The leaderboard will automatically use these functions via RPC calls. If the functions don't exist, it will fall back to the slower client-side pagination method.

## Troubleshooting

### Authentication Issues

- Ensure Azure AD redirect URI matches your deployment URL
- Check that client secret is correctly configured
- Verify OAuth2 scopes are properly set

### OneDrive Upload Failures

- Check that OneDrive app has correct permissions
- Verify folder `StepTrackerEvidence` exists in OneDrive
- Ensure access token is valid

### File Not Found Errors

- Ensure static assets are in `.streamlit/static/assets/`
- Check file permissions and paths
- Verify JSON files have correct format

## License

This project is licensed under the MIT License.

