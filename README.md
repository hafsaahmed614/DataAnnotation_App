# SNF Patient Navigator Case Collection App

A Streamlit web application for collecting historical SNF (Skilled Nursing Facility) patient navigator cases through a conversational intake process.

## Features

- **Two Intake Forms**: 
  - Abbreviated Intake: Quick entry with essential questions
  - Full Intake: Comprehensive form with 20+ detailed questions
- **Case Viewer**: Search and review saved cases by Case ID
- **Database Support**: SQLite for development, PostgreSQL for production
- **JSON Export**: Download individual cases as JSON files
- **PHI-Conscious Design**: Narrative text hidden from summary tables

## Project Structure

```
snf_navigator_app/
├── app.py                          # Home page with instructions & recent cases
├── db.py                           # Database module (SQLAlchemy ORM)
├── pages/
│   ├── 1_Abbreviated_Intake.py     # Short intake form
│   ├── 2_Full_Intake.py            # Comprehensive intake form
│   └── 3_Case_Viewer.py            # Case search and display
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore patterns
└── README.md                       # This file
```

## Database Schema

Single table `cases` with the following columns:

| Column | Type | Description |
|--------|------|-------------|
| case_id | UUID (string) | Primary key |
| created_at | DateTime | UTC timestamp |
| case_start_date | Date | Fixed: 2025-01-01 |
| intake_version | String | "abbrev" or "full" |
| age_at_snf_stay | Integer | Patient's age |
| gender | Text | Patient's gender |
| race | Text | Patient's race |
| state | Text | SNF location state |
| snf_days | Integer | Days in SNF (nullable) |
| services_discussed | Text | Free text (nullable) |
| services_accepted | Text | Free text (nullable) |
| answers_json | Text | JSON string of narrative responses |

## Local Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/hafsaahmed614/DataAnnotation_App.git
   cd DataAnnotation_App
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

5. **Open in browser**:
   The app will automatically open at `http://localhost:8501`

### Local Database

By default, the app creates a SQLite database file (`snf_cases.db`) in the project directory. This is ideal for development and testing.

## Production Deployment

### Using PostgreSQL

To use PostgreSQL instead of SQLite, set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://username:password@host:port/database_name"
```

Or in Windows:
```cmd
set DATABASE_URL=postgresql://username:password@host:port/database_name
```

### Streamlit Cloud Deployment

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Add secrets in Streamlit Cloud dashboard:
   - Go to App Settings → Secrets
   - Add: `DATABASE_URL = "your-postgres-connection-string"`

### Heroku Deployment

1. Create a `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. Add PostgreSQL addon:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

3. Deploy:
   ```bash
   git push heroku main
   ```

## Usage Guide

### Creating a New Case

1. Navigate to **Abbreviated Intake** or **Full Intake** from the sidebar
2. Fill in required demographics (age, gender, race, state)
3. Answer narrative questions in past tense
4. Enter services discussed/accepted and SNF days
5. Click **Save Case**
6. Copy the generated Case ID for future reference

### Viewing a Case

1. Navigate to **Case Viewer** from the sidebar
2. Enter the Case ID (UUID format)
3. Click **Search**
4. Review demographics, services, and narrative responses
5. Optionally download the case as JSON

## Question IDs Reference

### Abbreviated Intake (aq1-aq8)
- aq1: Case Summary
- aq2: SNF Team Discharge Timing
- aq3: Requirements for Safe Discharge
- aq4: Estimated Discharge Date
- aq5: Alignment Across Stakeholders
- aq6: SNF Discharge Conditions
- aq7: HHA Involvement
- aq8: Information Shared with HHA

### Full Intake (q6-q28)
- q6: Case Summary
- q7: Referral Source and Expectation
- q8: Upstream Path to SNF
- q9: Expected Length of Stay at Admission
- q10: Initial Assessment
- q11: Early Home Feasibility
- q12: Key SNF Roles and People
- q13: Patient Response
- q14: Patient/Family Goals
- q15: SNF Discharge Timing Over Time
- q16: Requirements for Safe Discharge
- q17: Services Discussion and Agreement
- q18: HHA Involvement and Handoff
- q19: Information Shared with HHA
- q20: Estimated Discharge Date and Reasoning
- q21: Alignment Across Stakeholders
- q22: SNF Discharge Conditions
- q23: Plan for First 24-48 Hours
- q25: Transition SNF to Home Overall
- q26: Handoff Completion and Gaps
- q27: 24-Hour Follow-up Contact
- q28: Initial At-Home Status

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError"**: Ensure you've activated the virtual environment and installed requirements
   ```bash
   pip install -r requirements.txt
   ```

2. **Database connection errors**: Check that `DATABASE_URL` is correctly formatted for PostgreSQL

3. **Port already in use**: Specify a different port:
   ```bash
   streamlit run app.py --server.port=8502
   ```

## License

This project is for internal use. Please contact the repository owner for licensing information.

## Support

For questions or issues, please open a GitHub issue or contact the development team.
