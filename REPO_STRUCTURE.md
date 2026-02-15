# Repository Structure Analysis

**Project**: SNF Patient Navigator Case Collection App
**Version**: v1.3
**Framework**: Streamlit (Python)
**Analysis Date**: 2026-02-15

---

## Directory Layout

```
DataAnnotation_App/
├── app.py                              # Entry point — Dashboard/Home page
├── auth.py                             # Authentication (login, registration, session tokens)
├── db.py                               # Database layer — SQLAlchemy ORM models & CRUD
├── session_timer.py                    # Session timeout & auto-save
├── transcribe.py                       # OpenAI Whisper audio transcription
├── openai_integration.py               # GPT follow-up question generation
├── pages/
│   ├── 1_Abbreviated_Intake.py         # 8-question intake form (discharged home)
│   ├── 2_Abbreviated_Intake_General.py # 9-question intake form (any SNF outcome)
│   ├── 3_Full_Intake.py               # 20+ question comprehensive form
│   ├── 4_Case_Viewer.py               # View & export saved cases
│   ├── 5_Follow_On_Questions.py        # Answer AI-generated follow-up questions
│   └── 6_Admin_Settings.py            # Admin config & transcription manager
├── .streamlit/
│   └── config.toml                     # Streamlit server configuration
├── .devcontainer/
│   └── devcontainer.json              # GitHub Codespaces dev container
├── README.md                           # Project documentation
├── FUTURE_FEATURES.md                  # Planned features roadmap
├── requirements.txt                    # Python dependencies
├── runtime.txt                         # Python version (3.10)
├── packages.txt                        # System packages (ffmpeg)
└── .gitignore                          # Git ignore rules
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web framework** | Streamlit >=1.33.0 | Multi-page app with forms, widgets, audio |
| **ORM** | SQLAlchemy >=2.0.0 | Database abstraction over SQLite/PostgreSQL |
| **Production DB** | PostgreSQL (Supabase) | Persistent cloud storage |
| **Dev DB** | SQLite | Local development via `snf_cases.db` |
| **Speech-to-text** | OpenAI Whisper >=20231117 | Audio transcription |
| **AI/LLM** | OpenAI GPT API >=1.0.0 | Follow-up question generation |
| **Data processing** | Pandas >=2.0.0 | Data manipulation and export |
| **Media** | ffmpeg-python >=0.2.0 | Audio processing |
| **Config** | python-dotenv >=1.0.0 | Environment variable management |
| **Runtime** | Python 3.10 | Language version |

---

## Core Modules

### `app.py` (169 lines) — Entry Point
- Dashboard and home page
- Login gateway with navigation to intake forms
- Quick-start buttons for each form type
- Launch: `streamlit run app.py`

### `db.py` (1337 lines) — Database Layer
Defines 6 SQLAlchemy models:

| Model | Purpose |
|-------|---------|
| **Case** | Patient case records with demographics, services, narrative answers |
| **User** | Authentication — username + hashed PIN |
| **FollowUpQuestion** | AI-generated questions linked to cases (sections A/B/C) |
| **AudioResponse** | Audio recordings with versioned transcripts |
| **AppSettings** | Key-value application configuration |
| **DraftCase** | Work-in-progress incomplete cases |

Key design decisions:
- Case IDs formatted as `{username}_{number}` (e.g., `john_doe_1`)
- Automatic schema migrations for new columns
- UTC timestamps with CST display conversion
- Session factory pattern for database access

### `auth.py` (229 lines) — Authentication
- Username (full name) + 4-digit PIN login
- SHA-256 PIN hashing
- Session token persistence via query parameters
- Three authorization levels: unauthenticated, user, admin

### `openai_integration.py` (691 lines) — AI Integration
- Generates follow-up questions in 3 sections:
  - **Section A**: Reasoning & decision-making
  - **Section B**: Timing & signals
  - **Section C**: State transitions
- Different prompt templates for abbreviated vs. full intake
- Structured JSON output parsing

### `transcribe.py` (218 lines) — Audio Transcription
- OpenAI Whisper integration
- Configurable model sizes (tiny, base, small, medium, large)
- Audio file processing via ffmpeg

### `session_timer.py` (216 lines) — Session Management
- 30-minute timeout aligned with Streamlit Cloud limits
- Warning at 25 minutes
- Auto-save every 2 minutes
- Auto-dismiss warnings on activity

---

## Pages (Streamlit Multi-Page App)

| Page | File | Questions | Description |
|------|------|-----------|-------------|
| Abbreviated Intake | `1_Abbreviated_Intake.py` | 8 | Quick form for patients discharged home |
| Abbreviated General | `2_Abbreviated_Intake_General.py` | 9 | Quick form for any SNF outcome |
| Full Intake | `3_Full_Intake.py` | 20+ | Comprehensive detailed intake |
| Case Viewer | `4_Case_Viewer.py` | — | Search, view, and export cases as JSON |
| Follow-Up Questions | `5_Follow_On_Questions.py` | — | Answer AI-generated follow-up questions |
| Admin Settings | `6_Admin_Settings.py` | — | Admin config, transcription management |

---

## Database Schema (Key Relationships)

```
User (1) ──── (*) Case
                    │
                    ├── (*) FollowUpQuestion
                    │           │
                    │           └── (0..1) AudioResponse
                    │
                    └── (*) AudioResponse

User (1) ──── (*) DraftCase

AppSettings (standalone key-value store)
```

---

## Configuration & Deployment

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```
Uses SQLite (`snf_cases.db`) by default.

### Streamlit Cloud / Production
- Database: PostgreSQL via `DATABASE_URL` secret
- Required secrets: `DATABASE_URL`, `OPENAI_API_KEY`, `ADMIN_PASSWORD`
- Configured via `.streamlit/secrets.toml` (gitignored)

### Dev Container (GitHub Codespaces)
- Base image: `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm`
- Auto-installs system packages and Python dependencies
- Exposes port 8501
- VSCode extensions: Python, Pylance

---

## Testing

No automated test suite exists. Testing is manual via the Streamlit UI. The future roadmap includes an "Admin Test Mode" feature.

---

## Code Statistics

| Component | Approx. Lines |
|-----------|--------------|
| Core modules (root `.py` files) | ~2,860 |
| Page files (6 pages) | ~5,000+ |
| Documentation (`.md` files) | ~600 |
| **Total Python** | **~9,000+** |
