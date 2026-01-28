# SNF Patient Navigator Case Collection App

A Streamlit web application for collecting historical SNF (Skilled Nursing Facility) patient navigator cases through a conversational intake process.

## Features

- **Two Intake Forms**: 
  - Abbreviated Intake: Quick entry with essential questions
  - Full Intake: Comprehensive form with 20+ detailed questions
- **User ID System**: Users create their own ID to track their cases
- **Case Viewer**: 
  - Users can view only their own cases (using their ID)
  - Admin can view all cases (with password)
- **Database Support**: SQLite for development, PostgreSQL for production

## Project Structure

```
DataAnnotation_App/
├── app.py                          # Home page with instructions
├── db.py                           # Database module (SQLAlchemy ORM)
├── pages/
│   ├── 1_Abbreviated_Intake.py     # Short intake form
│   ├── 2_Full_Intake.py            # Comprehensive intake form
│   └── 3_Case_Viewer.py            # Case search and display
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore patterns
└── README.md                       # This file
```

## Setup

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hafsaahmed614/DataAnnotation_App.git
   cd DataAnnotation_App
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   
   # On Mac/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

### Streamlit Cloud Deployment

The app is deployed on Streamlit Cloud. To configure secrets:

1. Go to your app's **Settings** → **Secrets**
2. Add the following:

```toml
DATABASE_URL = "postgresql://user:password@host:port/database"
ADMIN_PASSWORD = "your-secure-admin-password"
```

## Configuration

### Required Secrets

| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | PostgreSQL connection string for production database |
| `ADMIN_PASSWORD` | Password for admin access to view all cases |

### Database Schema

Table: `cases`

| Column | Type | Description |
|--------|------|-------------|
| case_id | UUID | Primary key |
| created_at | DateTime | UTC timestamp |
| case_start_date | Date | Fixed: 2025-01-01 |
| intake_version | String | "abbrev" or "full" |
| user_id | String | ID of user who created the case |
| age_at_snf_stay | Integer | Patient's age |
| gender | Text | Patient's gender |
| race | Text | Patient's race |
| state | Text | SNF location state |
| snf_days | Integer | Days in SNF (nullable) |
| services_discussed | Text | Free text (nullable) |
| services_accepted | Text | Free text (nullable) |
| answers_json | Text | JSON string of narrative responses |

## Usage

### For Users

1. Go to **Abbreviated Intake** or **Full Intake**
2. Enter your **ID number** (remember this!)
3. Fill in patient demographics and narrative questions
4. Click **Save Case**
5. To view your cases later, go to **Case Viewer** and enter your ID

### For Admins

1. Go to **Case Viewer**
2. Select **"View All Cases (Admin)"**
3. Enter the admin password
4. View and export any case

## Support

For questions or issues, please open a GitHub issue.
