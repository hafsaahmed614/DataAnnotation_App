# SNF Patient Navigator Case Collection App

A Streamlit web application for collecting historical SNF (Skilled Nursing Facility) patient navigator cases through a structured, conversational intake process. Features audio recording, AI transcription, and AI-generated follow-up questions.

## Features

### Core Features
- **Two Intake Forms**:
  - **Abbreviated Intake**: Quick 8-question form for essential case information
  - **Full Intake**: Comprehensive 20+ question form for detailed patient journeys
- **Audio Recording**: Record narrative answers via browser microphone (WebM format)
- **AI Transcription**: OpenAI Whisper for automatic audio-to-text transcription (admin-only feature)
- **AI Follow-up Questions**: Automatically generated follow-up questions using OpenAI GPT for deeper case insights
- **Draft Auto-Save**: Automatic draft saving every 2 minutes with session timeout handling (30-minute session limit)

### User Features
- **Secure Authentication**: Username + 4-digit PIN login system
- **Login Persistence**: Stay logged in across page refreshes (session token via URL)
- **Personal Case Numbering**: Cases numbered sequentially per user (e.g., john_doe_1, john_doe_2)
- **Case Viewer**: View and export your saved cases as JSON
- **Resume Drafts**: Resume incomplete forms where you left off with full state restoration
- **Session Timeout Warnings**: Smart warnings that auto-dismiss when you continue working

### Admin Features
- **View All Cases**: Admin password access to view all user cases
- **Transcription Settings**: Configure Whisper model provider and size (tiny/base/small/medium/large)
- **Audio Transcription Manager**:
  - Review audio recordings from any case
  - Play back audio responses
  - Generate transcripts with Whisper
  - Edit and save transcripts
- **User Statistics**: View registered users and case counts

### Follow-On Questions
- **AI-Generated Questions**: GPT generates contextual follow-up questions based on case answers
- **Three Sections**:
  - **Section A**: Reasoning Trace
  - **Section B**: Discharge Timing Dynamics
  - **Section C**: SNF Patient State Transitions, Incentives, and Navigator Time Allocation
- **Audio or Text Answers**: Answer follow-up questions via typing or audio recording
- **Progress Tracking**: See answered/total questions per case

## Project Structure

```
DataAnnotation_App/
├── app.py                              # Dashboard/Home page with login
├── auth.py                             # Authentication module (login, register, session persistence)
├── db.py                               # Database module (SQLAlchemy ORM, all models)
├── session_timer.py                    # Session timeout, auto-save, and activity tracking
├── transcribe.py                       # Audio transcription with OpenAI Whisper
├── openai_integration.py               # OpenAI GPT integration for follow-up questions
├── pages/
│   ├── 1_Abbreviated_Intake.py         # Short 8-question intake form
│   ├── 2_Full_Intake.py                # Comprehensive 20+ question intake form
│   ├── 3_Case_Viewer.py                # View and export saved cases
│   ├── 4_Follow_On_Questions.py        # Answer AI-generated follow-up questions
│   └── 5_Admin_Settings.py             # Admin configuration and audio transcription manager
├── .streamlit/
│   └── config.toml                     # Streamlit server configuration
├── requirements.txt                    # Python dependencies
├── FUTURE_FEATURES.md                  # Planned features and roadmap
├── .gitignore                          # Git ignore patterns
└── README.md                           # This file
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

4. **Set up environment variables** (create `.env` file):
   ```bash
   DATABASE_URL=postgresql://user:password@host:port/database
   OPENAI_API_KEY=your-openai-api-key
   ADMIN_PASSWORD=your-secure-admin-password
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

### Streamlit Cloud Deployment

1. Go to your app's **Settings** → **Secrets**
2. Add the following secrets:

```toml
DATABASE_URL = "postgresql://user:password@host:port/database"
ADMIN_PASSWORD = "your-secure-admin-password"
OPENAI_API_KEY = "your-openai-api-key"
```

## Configuration

### Required Secrets

| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (e.g., Supabase) |
| `ADMIN_PASSWORD` | Password for admin access to view all cases and settings |
| `OPENAI_API_KEY` | OpenAI API key for generating follow-up questions |

### Session Configuration

The app is configured for Streamlit Cloud's 30-minute session timeout:
- Session warnings start at 25 minutes (5 minutes before timeout)
- Warnings auto-dismiss when user continues working (activity detected)
- Auto-save interval: 2 minutes
- Configuration in `.streamlit/config.toml`

## Database Schema

The application uses SQLAlchemy ORM with PostgreSQL (Supabase) for production.

### Tables

#### `cases`
Main case data storage.

| Column | Type | Description |
|--------|------|-------------|
| case_id | VARCHAR(250) | Primary key, format: `{username}_{number}` (e.g., "john_doe_1") |
| created_at | DateTime | UTC timestamp of creation |
| case_start_date | Date | Fixed: 2025-01-01 |
| intake_version | String(10) | "abbrev" or "full" |
| user_name | String(200) | Username of case creator |
| age_at_snf_stay | Integer | Patient's age during SNF stay |
| gender | Text | Patient's gender |
| race | Text | Patient's race |
| state | Text | SNF location state |
| snf_days | Integer | Days in SNF (nullable) |
| services_discussed | Text | Services discussed (nullable) |
| services_accepted | Text | Services accepted (nullable) |
| answers_json | Text | JSON string of narrative responses |

#### `users`
User authentication.

| Column | Type | Description |
|--------|------|-------------|
| id | String(36) | UUID primary key |
| username | String(200) | User's full name (unique) |
| pin_hash | String(64) | SHA-256 hash of 4-digit PIN |
| created_at | DateTime | Account creation timestamp |

#### `follow_up_questions`
AI-generated follow-up questions.

| Column | Type | Description |
|--------|------|-------------|
| id | String(36) | UUID primary key |
| case_id | String(250) | Foreign key to cases |
| user_name | String(200) | User who owns this question |
| section | String(1) | Section: "A", "B", or "C" |
| question_number | Integer | Question number within section |
| question_text | Text | The AI-generated question |
| answer_text | Text | User's answer (nullable) |
| created_at | DateTime | Question creation timestamp |
| answered_at | DateTime | When user answered (nullable) |

#### `audio_responses`
Audio recordings and transcripts with versioning.

| Column | Type | Description |
|--------|------|-------------|
| id | String(36) | UUID primary key |
| case_id | String(250) | Foreign key to cases |
| question_id | String(20) | Question ID (e.g., "aq1", "q6") |
| follow_up_question_id | String(36) | FK to follow_up_questions (nullable) |
| audio_path | Text | Path in storage (nullable) |
| audio_data | LargeBinary | Audio bytes (nullable) |
| auto_transcript | Text | Original Whisper transcription |
| edited_transcript | Text | User-edited version |
| version_number | Integer | Version for edit tracking |
| created_at | DateTime | Recording timestamp |

#### `app_settings`
Application-wide settings.

| Column | Type | Description |
|--------|------|-------------|
| key | String(100) | Setting key (primary) |
| value | Text | Setting value |
| updated_at | DateTime | Last update timestamp |

#### `draft_cases`
Work-in-progress cases for auto-save.

| Column | Type | Description |
|--------|------|-------------|
| id | String(36) | UUID primary key |
| user_name | String(200) | User's name |
| intake_version | String(10) | "abbrev" or "full" |
| age_at_snf_stay | Integer | Demographics (all nullable for drafts) |
| gender | Text | |
| race | Text | |
| state | Text | |
| snf_days | Integer | |
| services_discussed | Text | |
| services_accepted | Text | |
| answers_json | Text | JSON of narrative answers |
| audio_json | Text | JSON of audio flags |
| created_at | DateTime | Draft creation time |
| updated_at | DateTime | Last update time |

## Usage

### For Users

1. **Create an Account**:
   - Go to the Dashboard
   - Enter your full name as username
   - Create a memorable 4-digit PIN

2. **Fill Out an Intake Form**:
   - Choose **Abbreviated Intake** (quick) or **Full Intake** (comprehensive)
   - Fill in patient demographics (age, gender, race, SNF state)
   - Answer narrative questions by **typing** or **recording audio**
   - Drafts auto-save every 2 minutes
   - Click **Save Draft** to manually save progress
   - Click **Save Case** when complete

3. **Answer Follow-up Questions**:
   - After saving a case, AI-generated follow-up questions are created
   - Go to **Follow-On Questions** page to answer them
   - Questions are grouped into three sections (A, B, C)
   - Answer via typing or audio recording
   - Progress is tracked per case

4. **Review Your Cases**:
   - Use **Case Viewer** to see all your saved cases
   - Cases are numbered: Case 1, Case 2, etc.
   - Download cases as JSON for offline review

5. **Session Management**:
   - Sessions timeout after 30 minutes of inactivity
   - Warnings appear at 25 minutes and auto-dismiss when you continue working
   - Your login persists across page refreshes

### For Admins

1. Go to **Admin Settings** page
2. Enter the admin password
3. Available features:
   - **Transcription Settings**: Configure Whisper model size
   - **User Statistics**: View registered users and users with cases
   - **Audio Transcription Manager**:
     - Select any case to view audio recordings
     - Play back audio responses
     - Generate transcripts with Whisper
     - Edit and save transcripts

4. Go to **Case Viewer** and select "View All Cases (Admin)" to view any user's cases

## AI Features

### Follow-up Question Generation
After saving a case, the app uses OpenAI GPT to generate follow-up questions organized into three sections:
- **Section A**: Reasoning Trace - Questions about clinical decision-making
- **Section B**: Discharge Timing Dynamics - Questions about timing and readiness
- **Section C**: SNF Patient State Transitions, Incentives, and Navigator Time Allocation - Questions about transitions and resources

### Audio Transcription
- Uses OpenAI Whisper for speech-to-text
- Configurable model size (tiny to large) via Admin Settings
- Transcription is admin-only (not shown to regular users)
- Supports editing transcripts after generation

## Dependencies

```
streamlit>=1.33.0
sqlalchemy>=2.0.0
pandas>=2.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
openai-whisper>=20231117
ffmpeg-python>=0.2.0
openai>=1.0.0
```

## Version History

- **v1.2** (Current):
  - Session timeout warning auto-dismisses when user continues working
  - Number input fields show placeholder instead of 0 on fresh login
  - Fixed draft detection false positives
  - Added login persistence across page refreshes

- **v1.1**:
  - Audio Transcription Manager in Admin Settings
  - Follow-on questions audio recording support
  - Draft loading properly restores all form fields
  - Fixed case closing after saving follow-on answers

- **v1.0**:
  - Case ID format: `{username}_{number}` (replaces UUID)
  - User tracking via `user_name` column
  - Draft case auto-save functionality
  - Session timeout handling (30 min)
  - AI follow-up question generation
  - Transcription hidden from users (admin-only)

## Support

For questions or issues, please open a GitHub issue at:
https://github.com/hafsaahmed614/DataAnnotation_App/issues
