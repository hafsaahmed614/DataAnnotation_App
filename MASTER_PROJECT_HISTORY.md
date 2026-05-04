# MASTER PROJECT HISTORY

**Project**: SNF Patient Navigator Case Collection App
**Repository**: `DataAnnotation_App`
**Owner**: hafsaahmed614 (github.com/hafsaahmed614/DataAnnotation_App)
**Framework**: Streamlit (Python 3.10)
**Status**: Active — v1.3
**Development Window**: 2026-01-27 → 2026-02-16 (≈3 weeks, 89 commits)
**Document Generated**: 2026-04-21

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Purpose & Domain Context](#2-purpose--domain-context)
3. [Technology Stack](#3-technology-stack)
4. [Repository Layout](#4-repository-layout)
5. [Core Modules — Detailed Breakdown](#5-core-modules--detailed-breakdown)
6. [Pages (Streamlit Multi-Page App)](#6-pages-streamlit-multi-page-app)
7. [Database Schema](#7-database-schema)
8. [Authentication & Session Model](#8-authentication--session-model)
9. [AI / OpenAI Integration](#9-ai--openai-integration)
10. [Audio Pipeline & Transcription](#10-audio-pipeline--transcription)
11. [Draft & Auto-Save System](#11-draft--auto-save-system)
12. [Configuration, Deployment & Environment](#12-configuration-deployment--environment)
13. [Version History — v1.0 → v1.3](#13-version-history--v10--v13)
14. [Full Chronological Git History](#14-full-chronological-git-history)
15. [Themes & Lessons from Development](#15-themes--lessons-from-development)
16. [Data Pedigree & Seed Case Evolution](#16-data-pedigree--seed-case-evolution)
17. [Roadmap — Planned & Future Features](#17-roadmap--planned--future-features)
18. [Code Statistics](#18-code-statistics)

---

## 1. Executive Summary

The **SNF Patient Navigator Case Collection App** is a Streamlit-based web application that allows patient navigators to document historical Skilled Nursing Facility (SNF) cases through a structured, conversational intake process. It combines:

- **Three structured intake forms** (Abbreviated, Abbreviated General, Full) with 8, 9, and 20+ narrative questions respectively.
- **Browser-based audio recording** for each narrative answer, with **OpenAI Whisper** transcription (admin-only).
- **AI-generated follow-up questions** (OpenAI GPT) grouped into three sections per case for deeper reasoning capture.
- **Per-user authentication** (username + 4-digit PIN), **per-user case numbering**, and an **admin panel** for reviewing all users' cases and managing transcription.
- **Draft auto-save** and **session-timeout handling** tuned for Streamlit Cloud's ≈30-minute session cap.
- **SQLAlchemy** over SQLite (dev) / PostgreSQL-Supabase (prod).

The project went from a bare Streamlit skeleton on 2026-01-27 to a feature-complete v1.3 by 2026-02-16 — roughly three weeks of intense iteration covering six database tables, six multi-page forms, ≈6,600 lines of Python, and ≈600 lines of docs.

---

## 2. Purpose & Domain Context

The application is built for **patient navigators** — clinicians/operators who help patients transition between hospital, SNF, home, and other care settings. The tool supports:

- **Historical case collection**: Navigators describe real past cases (all timestamps fixed with `case_start_date = 2025-01-01` and prompts written in past tense).
- **SNF outcome tracking**: The three forms support the full spectrum of outcomes — discharged home, long-term SNF stay, return to hospital, death in SNF, or other.
- **Reasoning capture**: The AI-generated follow-up questions specifically probe clinical reasoning, discharge timing dynamics, and state-transition decisions.
- **Downstream use (implied)**: Data annotation / training-data generation (the repo name `DataAnnotation_App` suggests the end goal is a corpus of annotated clinical reasoning traces).

Domain terms that shape the schema and prompts:
- **SNF** — Skilled Nursing Facility
- **HHA** — Home Health Agency
- **CHC waiver** — (Pennsylvania) Community HealthChoices waiver, appearing in sample case data
- **Discharge home / Long-term SNF / Hospital return / Death in SNF** — the five modeled state transitions

---

## 3. Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | 3.10 (pinned via `runtime.txt`) | Whisper compatibility |
| Web framework | Streamlit | ≥1.33.0 | Multi-page app, forms, widgets, `st.audio_input` |
| ORM | SQLAlchemy | ≥2.0.0 | DB abstraction |
| Prod DB | PostgreSQL (Supabase) | — | Persistent cloud storage |
| Dev DB | SQLite | — | `snf_cases.db` (gitignored) |
| Speech-to-text | OpenAI Whisper | ≥20231117 | Local audio transcription |
| LLM | OpenAI GPT | ≥1.0.0 SDK, model `gpt-5-mini-2025-08-07` | Follow-up question generation |
| Data | Pandas | ≥2.0.0 | Export helpers |
| DB driver | psycopg2-binary | ≥2.9.0 | Postgres connector |
| Media | ffmpeg (system) + ffmpeg-python | ≥0.2.0 | Audio decoding |
| Secrets | python-dotenv | ≥1.0.0 | Local `.env` loading |
| Dev container | `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm` | — | Codespaces |

---

## 4. Repository Layout

```
DataAnnotation_App/
├── app.py                              # Dashboard / home page (169 lines)
├── auth.py                             # Login, register, session persistence (229 lines)
├── db.py                               # SQLAlchemy ORM + CRUD + migrations (≈1,337 lines)
├── session_timer.py                    # Timeout, auto-save, JS injection (≈295 lines)
├── transcribe.py                       # Whisper singleton + audio widget (≈219 lines)
├── openai_integration.py               # GPT prompts + response parsing (≈692 lines)
├── pages/
│   ├── 1_Abbreviated_Intake.py         # 8-question form (discharged home)  (≈727 lines)
│   ├── 2_Abbreviated_Intake_General.py # 9-question form (any outcome)      (≈687 lines)
│   ├── 3_Full_Intake.py                # 20+ question comprehensive form    (≈780 lines)
│   ├── 4_Case_Viewer.py                # View, search, export cases          (≈534 lines)
│   ├── 5_Follow_On_Questions.py        # Answer AI-generated questions       (≈594 lines)
│   └── 6_Admin_Settings.py             # Admin config + transcription mgr    (≈406 lines)
├── .streamlit/config.toml              # Streamlit server/browser/theme config
├── .devcontainer/devcontainer.json     # Codespaces (Python 3.11 base image)
├── requirements.txt                    # Python deps
├── runtime.txt                         # python-3.10
├── packages.txt                        # ffmpeg
├── README.md                           # User + dev documentation
├── REPO_STRUCTURE.md                   # Architecture analysis
├── FUTURE_FEATURES.md                  # Roadmap
├── MASTER_PROJECT_HISTORY.md           # This file
└── .gitignore                          # Python/Streamlit/.db/secrets
```

---

## 5. Core Modules — Detailed Breakdown

### 5.1 `app.py` — Dashboard / Home Page
- Page config with `🏥` icon, wide layout, expanded sidebar.
- Custom CSS trick that hides Streamlit's default "app" sidebar label and injects "Dashboard" via `::before` — this was iterated 6+ times across commits (see git history around 2026-01-28 → 2026-02-12).
- Logged-out state shows inline `Register`/`Login` tabs (Register intentionally first to lower friction for new users).
- Logged-in state shows a 4-column "Quick Start" grid linking to each intake form + case viewer.
- Sidebar repeats login status, navigation, and a feature list.
- Emphasizes that all cases use a **fixed start date of Jan 1, 2025** and all answers should be in **past tense**.

### 5.2 `auth.py` — Authentication
- Username (full name, case-insensitive at the DB layer) + 4-digit PIN, SHA-256 hashed.
- Session state flags: `authenticated`, `current_user`, `username`, `session_token`, `auth_checked`.
- **Login persistence** via `st.query_params` — login stores `?user=<name>&token=<hex>` in the URL, and on subsequent loads the auth module auto-rehydrates the session if the user still exists. This was added in `d5cea40` (2026-01-29) to fix the "refresh logs me out" problem.
- `generate_session_token` uses `secrets.token_hex(16)` + a SHA-256 truncation.
- `register()` validates the PIN is exactly 4 digits and rejects duplicate usernames (case-insensitive).
- `show_login_form()` renders the tabbed Register / Login UI on the dashboard.
- `require_auth()` is a decorator-style guard called at the top of every protected page.

### 5.3 `db.py` — Database Layer
- Detects `DATABASE_URL` env var; defaults to `sqlite:///snf_cases.db`.
- Normalizes `postgres://` → `postgresql://` (Heroku-style URLs).
- Uses `StaticPool` + `check_same_thread=False` for SQLite to work with Streamlit's threading.
- Defines **six SQLAlchemy models** (see §7): `Case`, `User`, `FollowUpQuestion`, `AudioResponse`, `AppSettings`, `DraftCase`.
- Provides **automatic migrations** via `_run_migrations()` — on every `init_db()` call, it inspects the schema and issues `ALTER TABLE ADD COLUMN` for `snf_name` and `services_utilized_after_discharge` on `cases` and `draft_cases`, and attempts to widen `intake_version` from VARCHAR(10) → VARCHAR(50) for Postgres (no-op on SQLite). Added in `544c044`.
- **Case ID format**: `{normalized_username}_{seq}` where `normalized_username = username.lower().replace(" ", "_")`. Per-user sequence starts at 1. Replaced the earlier UUID scheme in `928c3a6` (2026-01-29).
- Rich helper API: `create_case`, `save_audio_response`, `save_transcript_version` (with version auto-increment), `save_draft_case` (upsert one draft per user per intake type), `create_follow_up_questions`, `update_follow_up_answer`, `get_cases_with_pending_follow_ups`, etc.
- Settings defaults: `whisper_model_size="base"`, `whisper_model_version="openai-whisper"` (with `granite-3.3` reserved for future).

### 5.4 `session_timer.py` — Session & Auto-Save
- Constants: `SESSION_TIMEOUT_SECONDS=1800` (30 min), `WARNING_THRESHOLD_SECONDS=1500` (25 min), `AUTO_SAVE_INTERVAL_SECONDS=120` (2 min).
- `should_show_warning()` suppresses the timeout banner if the user has been active within the last 60 seconds — **this was a deliberate UX fix** (commit `4a74b68`, 2026-01-30) so active typers don't get nagged.
- Three-tier warning visuals: >3 min = yellow info, 1–3 min = orange warning, <1 min = red critical.
- `render_resume_draft_banner()` shows "You have an unfinished draft" with Resume / Start Fresh buttons and a relative timestamp.
- `inject_periodic_save_js()` is the signature workaround (`10837db` + `c71926d`): Streamlit's `text_area` only fires `on_change` on blur, so if a user types into the last question and refreshes, the value is never sent. The JS injects three safeguards:
  1. **Debounced input save** — 3 s after the user stops typing, briefly blur/refocus the textarea to flush the value.
  2. **Periodic interval** — every 30 s, blur the active textarea as a safety net.
  3. **beforeunload** — best-effort blur on page unload.

### 5.5 `transcribe.py` — Whisper Integration
- Singleton pattern for the Whisper model (`_whisper_model`, `_current_model_name`) so it's loaded once per Streamlit process.
- Reloads if the admin changes the model size via `get_configured_model_size()`.
- `transcribe_audio(audio_bytes)` writes bytes to a temp WAV file, runs `model.transcribe(..., language="en")`, returns the stripped text.
- `show_audio_input_with_transcription()` provides the reusable UI component used (originally) on intake pages with a radio toggle (Type / Record Audio / Both), inline audio playback, and an editable transcript area. Transcription was later hidden from regular users — it now runs only in the admin page (`de2cbdd`, 2026-01-29).

### 5.6 `openai_integration.py` — GPT Follow-Up Generation
- Three long system prompts tuned per intake type:
  - **`ABBREVIATED_SYSTEM_PROMPT`** — 12 questions max, min 4 per section (Reasoning Trace / Discharge Timing / State Transitions & Time Allocation).
  - **`ABBREVIATED_GENERAL_SYSTEM_PROMPT`** — 9 questions max, 3 per section (Reasoning Trace / Early Warning Signals LT vs Hospital / Decision Points & Triggers).
  - **`FULL_INTAKE_SYSTEM_PROMPT`** — long-form expert interviewer prompt, 6–10 questions per section, with explicit counterfactual requirements.
- All prompts enforce past tense, require every question to reference a specific case detail, and forbid PHI requests, AI self-references, solutions, and medical advice.
- `format_case_for_prompt()` assembles demographics + services + narrative answers into the user message.
- `parse_follow_up_response()` regex-parses `A) …`, `B) …`, `C) …` section headers and numbered questions. The regex was extended (`1043405`, 2026-02-12) to handle Abbreviated General's different section titles ("Early Warning Signals", "Decision Points").
- Model: `gpt-5-mini-2025-08-07`, `max_completion_tokens=4000`, no `temperature` param (removed in `06dd1e3` — `gpt-5-mini` rejects it).
- `log_api_error()` appends errors into `st.session_state.api_errors` (capped at 100) for admin visibility.

---

## 6. Pages (Streamlit Multi-Page App)

All six pages share a common pattern:
1. `st.set_page_config(...)` with page-specific title/icon.
2. The "Dashboard" sidebar-rename CSS block.
3. `init_db()` + `init_session_state()` + `require_auth()`.
4. `init_session_timer()` + `update_activity_time()` + `inject_periodic_save_js()` (on intake pages).

### 6.1 `1_Abbreviated_Intake.py` — 8-question form for patients discharged home
- Questions `aq1`–`aq8`: Case Summary, SNF Team Discharge Timing, Requirements for Safe Discharge, Estimated Discharge Date, Alignment Across Stakeholders, SNF Discharge Conditions, HHA Involvement, Information Shared with HHA.
- Contains a hard-coded `SAMPLE_CASE_DATA` demo (a 65-year-old male amputation patient in Pennsylvania with a CHC waiver ramp installation delay) loadable via a whitelisted "Load Sample Case" button (`DEMO_ALLOWED_USERS = ["Hafsa Ahmed", "Mohsin Ansari"]`).
- Per-section "Save Draft" buttons + `on_change` auto-save hooks.

### 6.2 `2_Abbreviated_Intake_General.py` — 9-question form for any SNF outcome
- Added in v1.3 (`6de16a4`, 2026-02-12).
- Questions `gq1`–`gq9`: gq1–gq6 mirror the abbreviated form at a higher level ("Requirements for Safe Next Step" instead of "Safe Discharge"), plus three outcome-focused questions: `gq7` Outcome, `gq8` Early Signs, `gq9` Learning.
- Feeds the `ABBREVIATED_GENERAL_SYSTEM_PROMPT` → different Section B/C titles on follow-ups.

### 6.3 `3_Full_Intake.py` — Comprehensive 20+ question form
- Questions `q6`–`q28` (intentional numbering, skips `q24` for historical reasons) grouped into seven sections: Case Overview, Admission & Assessment, Care Planning, Discharge Planning, HHA Coordination, Transition Home, Follow-up.
- Supports all the same draft / auto-save / audio features as the shorter forms.

### 6.4 `4_Case_Viewer.py` — Search, View, Export
- Admin toggle (gated by `ADMIN_PASSWORD` secret) unlocks "View All Cases (Admin)".
- Dropdown labels show intake-type prefix (`Abbreviated Case 1 — 72yo White Pennsylvania — Feb 2 03:45 PM`).
- Per-case view shows demographics, services, narrative answers with original prompts (`d8fa42c`), follow-up questions grouped by section, and a JSON download button.
- All timestamps converted to US Central Time (`CST = timezone(timedelta(hours=-6))`), formatted as `Feb 2, 2026 03:45 PM`.

### 6.5 `5_Follow_On_Questions.py` — AI-generated question answering
- Dropdown lists the user's cases with pending follow-ups, with intake-type prefix (`732353f`).
- Section labels adapt by intake type: abbreviated/full use `Reasoning Trace / Discharge Timing Dynamics / SNF Patient State Transitions…`, while abbreviated_gen uses `Reasoning Trace / Early Warning Signals / Decision Points & Triggers`.
- Each question supports typing or audio recording; admin-only transcription flows through `AudioResponse` with `follow_up_question_id` FK.
- Progress bar + "Case complete" message when all answered (`1e5e6b7`, `973de69`).
- Draft system auto-saves follow-on answers when switching between cases (`0e54e63`).

### 6.6 `6_Admin_Settings.py` — Admin Configuration
- Password-gated via `st.secrets["ADMIN_PASSWORD"]` (default `"admin123"` in dev).
- **Transcription Settings**: Model provider (OpenAI Whisper / IBM Granite 3.3 — coming soon) + model size (tiny / base / small / medium / large) with parameter counts shown.
- **User Statistics**: registered user count, users with cases.
- **Audio Transcription Manager** (`8b28665`, 2026-01-29): Select any case → list audio recordings → play back → generate / edit / save transcripts with automatic version bumping.

---

## 7. Database Schema

All timestamps stored in UTC; converted to CST at display time.

### `cases`
| Column | Type | Notes |
|---|---|---|
| `case_id` | VARCHAR(250) PK | `{username}_{n}` |
| `created_at` | DateTime | UTC |
| `case_start_date` | Date | Fixed 2025-01-01 |
| `intake_version` | VARCHAR(50) | `abbrev` / `abbrev_gen` / `full` / `follow_on_*` |
| `user_name` | VARCHAR(200) | Full name (case-insensitive matching) |
| `age_at_snf_stay` | Integer | Required |
| `gender`, `race`, `state` | Text | Required |
| `snf_name` | Text | Added via migration |
| `snf_days`, `services_discussed`, `services_accepted` | Text / Int | Nullable |
| `services_utilized_after_discharge` | Text | Added via migration |
| `answers_json` | Text | JSON of `{question_id: answer_text}` |

### `users`
| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR(36) PK | UUID |
| `username` | VARCHAR(200) UNIQUE | Full name |
| `pin_hash` | VARCHAR(64) | SHA-256 of 4-digit PIN |
| `created_at` | DateTime | — |

### `follow_up_questions`
| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR(36) PK | UUID |
| `case_id` | FK → cases | |
| `user_name` | VARCHAR(200) | Denormalized for easier queries |
| `section` | VARCHAR(1) | `A` / `B` / `C` |
| `question_number` | Integer | Within section |
| `question_text` | Text | AI-generated |
| `answer_text` | Text | Nullable |
| `created_at`, `answered_at` | DateTime | — |

### `audio_responses`
| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR(36) PK | UUID |
| `case_id` | FK → cases | |
| `question_id` | VARCHAR(20) | `aq1`, `q6`, or `fu_<12-char-prefix>` for follow-up |
| `follow_up_question_id` | FK → follow_up_questions | Nullable |
| `audio_path` | Text | Supabase Storage path (optional) |
| `audio_data` | LargeBinary | Bytes fallback |
| `auto_transcript` | Text | Original Whisper output |
| `edited_transcript` | Text | Admin-edited |
| `version_number` | Integer | Auto-incrementing per (case_id, question_id) |
| `created_at` | DateTime | — |

### `app_settings`
Key-value store keyed by `key` (VARCHAR(100)), seeded with `whisper_model_size` and `whisper_model_version`.

### `draft_cases`
Identical shape to `cases` but with all demographic fields nullable, plus an extra `audio_json` column for per-question audio flags, and `created_at`/`updated_at` for staleness display. One row per (user, intake_version).

### Key Relationships
```
User ──< Case ──< FollowUpQuestion ──< (optional) AudioResponse
                 └──< AudioResponse
User ──< DraftCase
AppSettings (standalone)
```

---

## 8. Authentication & Session Model

- **Login method**: username (full name) + 4-digit PIN, SHA-256 hashed.
- **Username matching**: case-insensitive (`func.lower(User.username) == username.lower()`), enforced for both login and duplicate-registration checks (`78da746`, 2026-01-28).
- **Admin access**: a separate password stored in `st.secrets["ADMIN_PASSWORD"]`. Granted per-session via the Admin Settings page; unlocks "View All Cases" in Case Viewer too.
- **Session persistence**: login injects `?user=<name>&token=<hex>` into `st.query_params`; `auth_checked` guards against repeated validation. On any subsequent page load, if the query params are present and the user still exists in the DB, the session is re-authenticated transparently.
- **Logout**: clears session state + `st.query_params.clear()`.

---

## 9. AI / OpenAI Integration

- **Model**: `gpt-5-mini-2025-08-07` (switched from gpt-4-class models in `864724a`).
- **Prompt strategy**: three very long system prompts (~100–200 lines each) that encode domain constraints:
  - Enforce **past tense**, **case-anchored** questions.
  - Forbid PHI requests, AI self-references, medical advice, new hypotheticals.
  - Impose strict section/question counts and specific section titles.
- **User message format**: demographics + service info + all narrative answers labeled with their question IDs and human-readable labels.
- **Output parsing**: regex matches section headers `A)` / `B)` / `C)` with alternate titles for Abbreviated General, then numbered questions `1.` or `1)`. Multi-line question text is concatenated.
- **Error handling**: failures log into `st.session_state.api_errors` (capped at 100) and return `(False, [], error_msg)` so the UI can show a graceful fallback.
- **Historical count change** (`c4d78f8`, 2026-02-02): the abbreviated prompt was tightened from looser counts to a minimum of 4 questions per section (12 total).

---

## 10. Audio Pipeline & Transcription

1. **Capture**: `st.audio_input` records via browser microphone, producing WebM (not WAV, despite the widget's suffix). The code explicitly uses the file's MIME type for playback (`c103b29`, 2026-01-29) to avoid the "unsupported format" error.
2. **Storage**: raw bytes saved into `audio_responses.audio_data` (LargeBinary); an optional `audio_path` field supports future Supabase Storage migration.
3. **Transcription** (admin-only since `de2cbdd` on 2026-01-29): Whisper is loaded as a singleton; the configured model size (from `app_settings`) drives `whisper.load_model()`. A temp WAV file is used because Whisper's Python API needs a file path.
4. **Versioning**: `save_transcript_version()` reads the latest `AudioResponse` for the `(case_id, question_id)` pair, copies forward missing fields, and creates a new row with `version_number = latest + 1`. This preserves edit history.
5. **Follow-up audio**: uses `question_id = f"fu_{follow_up_question_id[:12]}"` (because `question_id` is `VARCHAR(20)`) plus the `follow_up_question_id` FK for correct linkage (`b176799` fixed a NotNullViolation here).

---

## 11. Draft & Auto-Save System

Multiple layers combine to prevent data loss in Streamlit's cooperative session model:

1. **DB-level drafts** (`DraftCase`): one row per user per intake type; updated on every save. Added in `aa0378c` (2026-01-29).
2. **`on_change` auto-save callbacks** on every text area — saves the entire form state to the DB immediately on any interaction (`5ea32a5`, 2026-02-16). Previously only saved every 2 min (`0eaab20`).
3. **Periodic JS safety net** (`inject_periodic_save_js`): blur/refocus the active textarea every 30 s so Streamlit's `on_change` fires.
4. **Debounced JS save** (`c71926d`, 2026-02-16): 3 s after the user stops typing, blur/refocus the current textarea to flush the last value before refresh/close.
5. **`beforeunload` hook**: best-effort blur on tab close.
6. **Widget-key sync before save** (`5ab7264`): reads from `st.session_state[f"text_{qid}"]` directly before building the save payload, ensuring the most recent keystroke lands in the saved record.
7. **Resume banner**: on page load, if a draft exists, shows "You have an unfinished draft (last saved N minutes ago) — X question(s) answered" with Resume / Start Fresh buttons.
8. **Follow-on draft support**: `0fde8cd` extended `DraftCase` to handle `follow_on_*` intake versions, requiring the `intake_version` column to be widened from VARCHAR(10) to VARCHAR(50).

---

## 12. Configuration, Deployment & Environment

### Required secrets (via `.streamlit/secrets.toml` or env vars)
| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL URL (Supabase). Falls back to `sqlite:///snf_cases.db`. |
| `OPENAI_API_KEY` | GPT + Whisper |
| `ADMIN_PASSWORD` | Admin panel gate (defaults to `"admin123"` if missing — dev only) |

### Streamlit config (`.streamlit/config.toml`)
- `server.maxMessageSize = 200`
- `server.enableStaticServing = true`
- `browser.gatherUsageStats = false`

### Python / system
- `runtime.txt` pins Python 3.10 (Whisper compatibility — `b0af605`).
- `packages.txt` installs `ffmpeg` on Streamlit Cloud (`5bd112e`).

### Dev Container (GitHub Codespaces)
- Base image `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm`.
- `updateContentCommand` installs apt packages from `packages.txt` + pip from `requirements.txt`.
- `postAttachCommand` auto-launches `streamlit run app.py` with CORS / XSRF disabled.
- Forwards port 8501 with auto-preview.

### Git hygiene
- `.gitignore` excludes `__pycache__`, venvs, `.streamlit/secrets.toml`, `*.db`, `.env*`, IDE folders, and OS files.
- Local SQLite DB (`snf_cases.db`, 12 KB) is tracked in git even though `*.db` is ignored — it was added in the initial commit and never removed.

---

## 13. Version History — v1.0 → v1.3

### v1.0 — Foundations (2026-01-27 → 2026-01-29)
- Initial Streamlit skeleton with Abbreviated + Full intake forms.
- Audio recording with browser microphone.
- OpenAI Whisper transcription added (later hidden from regular users).
- AI follow-up question generation via OpenAI GPT, three sections (A/B/C).
- **Major refactor** (`928c3a6`): `case_id` format changed from UUID to `{username}_{n}`; `user_name` column added; transcription hidden from regular users.
- Draft auto-save + 30-min session-timeout handling added (`aa0378c`).
- Admin Settings page + Audio Transcription Manager.
- Login persistence and case-insensitive usernames.

### v1.1 — UX Polish (late Jan 2026)
- Audio Transcription Manager moved into Admin Settings.
- Follow-on questions gain audio recording support.
- Draft loading properly restores all form fields.
- Fixed case closing after saving follow-on answers.

### v1.2 — Reliability Pass (2026-01-30)
- Session timeout warning auto-dismisses when the user keeps typing (60-second activity window).
- Number input fields show placeholder instead of `0` on fresh login.
- Draft-detection false positives fixed.
- Login persistence across page refreshes confirmed.

### v1.3 — Current (2026-02-02 → 2026-02-16)
- **New form**: Abbreviated Intake General (for any SNF outcome, not just discharge home) with a dedicated GPT system prompt and different follow-up sections (Early Warning Signals, Decision Points & Triggers).
- **Per-intake-type case numbering**: cases numbered separately per type; dropdowns show type prefix.
- **US Central Time**: all timestamps display in CST.
- **Completion message**: clear "Case complete" when all follow-ups answered.
- **Database migrations**: automatic column additions for `snf_name`, `services_utilized_after_discharge`.
- **Dashboard CSS fix**: sidebar shows "Dashboard" rather than default "app" (after 6+ iterations).
- **Load Sample Case** button restricted to whitelisted demo users.
- **Draft resilience**: `on_change` callbacks, per-section Save Draft buttons, JS-level debounced / periodic / unload save hooks.
- **Repository documentation**: `REPO_STRUCTURE.md`, `FUTURE_FEATURES.md` added.

---

## 14. Full Chronological Git History

Total commits: **89** (main branch), across 20 unique calendar days from **2026-01-27** to **2026-02-16**. Several merge commits from `claude/*` branches indicate Claude-assisted development via pull request.

### Phase 1 — Bootstrap (2026-01-27, 4 commits)
| Commit | Summary |
|---|---|
| `5f14cdc` | Add SNF Patient Navigator Case Collection App (initial) |
| `6eb4466` | Added Dev Container Folder |
| `3e4e192` | Add user ID system and admin access controls |
| `12dece4` | Rename back to app.py |

### Phase 2 — Core Feature Build-Out (2026-01-28, 13 commits)
- `2748356` Replace user ID with full name, add case numbering per person
- `090b5a4` Merge PR #1 (claude/setup-snf-navigator-app-n8pez)
- `7e3c56e` Rename sidebar 'app' to 'Dashboard', fix Case Viewer state bug
- `3d154af` Add audio recording, transcription, and user authentication
- `df9aa6f` Add .gitignore
- `58db84d` Update Streamlit ≥1.33.0 (for `st.audio_input`)
- `a7e938a` Add admin settings for Whisper model configuration
- `4510b70` Fix sidebar label and swap Register/Login tab order
- `78da746` Make usernames case-insensitive
- `cc93d64` Fix sidebar Dashboard label flicker
- `5bd112e` Add `packages.txt` (ffmpeg) for Streamlit Cloud
- `b0af605` Add `runtime.txt` (Python 3.10) for Whisper compat
- `737c75d` **Add AI-generated follow-up questions feature**
- `864724a` Change default model to `gpt-5-mini-2025-08-07`
- `2ebd94a` Fix: use `max_completion_tokens` for gpt-5-mini
- `06dd1e3` Fix: remove `temperature` parameter for gpt-5-mini

### Phase 3 — Follow-On Questions UX (2026-01-29, 22 commits)
- `7c793e1`, `d91c082`, `bd6494b` — polishing Save All / messaging on Follow-On page
- `f51d41b`, `de2cbdd` — hide transcription from regular users
- `b176799` — fix NotNullViolation on follow-up question audio
- `30d8fcd` — update abbreviated case system prompt
- `928c3a6` — **Major refactor**: case_id format, user tracking, transcription control
- `aa0378c` — **Add incremental saving with draft cases + session timeout handling**
- `cb154ac` — remove transcript UI from Case Viewer, show full details in Follow-On
- `f49d97a` — reorder pages: Follow-On (4th), Admin Settings (5th)
- `20c9ccc` — update README comprehensively
- `7735f88`, `c103b29` — widget-warning + audio-format fixes
- `e3a233c` — improve Save All feedback
- `8b28665` — **Add Audio Transcription Manager to Admin Settings**
- `c00a4be` — fix case closing after saving follow-on answer
- `d5cea40` — **Fix draft loading and add login persistence**
- PR merges: #2, #3, #4, #5 (all `claude/extract-repo-structure-*`)

### Phase 4 — Reliability & Small UX (2026-01-30, 4 commits)
- `54a0825` fix widget session state warnings
- `acc05cc` fix number inputs showing 0 on fresh login
- `4a74b68` **Fix session timeout warning to dismiss when user continues working**
- `e04b480` Update README.md + create `FUTURE_FEATURES.md`

### Phase 5 — Demo & New Fields (2026-02-02, 7 commits)
- `c4d78f8` Increase follow-up questions: min 4 per section (12 total)
- `0d47d61`, `5bdc05e`, `0ae853c`, `6dcb1e2` Load Sample Case button + whitelisting
- `8c2b5f8` Add new form fields (SNF name, post-discharge services), follow-up display, case identifiers
- `eca782f` Update `FUTURE_FEATURES.md`
- `544c044` **Add database migration logic for new columns**

### Phase 6 — Abbreviated General + Dashboard CSS Saga (2026-02-11 → 2026-02-13, 18 commits)
- `5ad17a1` Fix case selection on Follow-On Questions
- `6de16a4` **Add Abbreviated Intake General page for any SNF outcome**
- `783de3a` Fix multiple issues with Abbreviated Intake General
- `b85a047`, `8cb2aa5`, `bdd0f6f` — Dashboard CSS fights
- `732353f`, `1e5e6b7` — intake-type prefix + completion messages
- `3edfcda` Update Abbreviated General system prompt + section labels
- `1043405` **Fix section parsing for Abbreviated General** + improve Dashboard CSS
- `6c859fe`, `900b962`, `b37fe9a`, `ac23225` — more Dashboard CSS attempts
- `6c9993e`, `70bc308` — intake-type identifier + Abbreviated General section labels in Case Viewer
- `eaee10d` **Convert times to US Central timezone (CST)**
- `ebb502c` Update README for v1.3

### Phase 7 — Draft-Save Hardening (2026-02-15 → 2026-02-16, 15 commits)
- `bbec2e1` **Add comprehensive repository structure analysis** (`REPO_STRUCTURE.md`)
- `0eaab20` **Fix draft auto-save to persist on every interaction**
- `3a9782a` Add Save Draft buttons after each section
- `05a5877` Update repo structure analysis with architecture patterns
- `5ea32a5` **Add on_change auto-save and per-question Save Draft buttons**
- `5ab7264` Fix last answer not saved on draft resume by syncing widget keys
- `0fde8cd` **Add draft-saving system to Follow-On Questions page**
- `698243b` Fix widget key conflict on Follow-On Questions text areas
- `d8fa42c` Show question prompts for original case in Case Viewer
- `e4de73a` Remove per-question Save button from Follow-On Questions
- `10837db` **Add periodic JS auto-save to prevent data loss on refresh/navigation**
- `36d064a` Remove "Discharged home" from Abbreviated Intake General descriptions
- `973de69` Fix progress bar not updating after saving follow-on answers
- `50dd4c3` Fix case selector reverting to first case on Follow-On Questions
- `0e54e63` **Auto-save follow-on draft when switching between cases**
- `c71926d` **Add debounced auto-save for textarea content on all intake pages** (latest)

---

## 15. Themes & Lessons from Development

Reading the commit history chronologically, several patterns emerge:

1. **Streamlit's blur-to-save behavior is the single biggest source of bugs.** Commits `10837db`, `5ea32a5`, `5ab7264`, `0eaab20`, `c71926d` all tackle different facets of "the user's last keystrokes weren't saved." The final solution layers DB drafts + `on_change` callbacks + per-section buttons + JS blur/refocus (debounced + periodic + beforeunload).
2. **Sidebar "Dashboard" rename is shockingly hard.** At least 8 commits (`cc93d64`, `b85a047`, `8cb2aa5`, `6c859fe`, `900b962`, `b37fe9a`, `ac23225`, plus the original in `7e3c56e`) iterate on CSS tricks because Streamlit's multipage app derives sidebar labels from file names.
3. **Widget state management requires discipline.** Commits `54a0825`, `acc05cc`, `0ae853c`, `5bdc05e`, `7735f88`, `698243b` all address Streamlit widget warnings arising from passing `value=` while also using `key=`, or from duplicate keys.
4. **GPT-5-mini API has strict constraints.** `2ebd94a`, `06dd1e3` — `max_completion_tokens` must replace `max_tokens`, `temperature` must be omitted.
5. **Iterative schema growth → need migrations.** Rather than pre-designing the schema, fields were added as needs emerged (`snf_name`, `services_utilized_after_discharge`, wider `intake_version`). `544c044` introduced self-healing ALTER-TABLE migrations rather than requiring manual DB reset.
6. **Per-intake-type parallelism.** Each time a new form type was added, parallel changes cascaded across: DB `intake_version` enum, GPT system prompt, section-label maps, Case Viewer dropdown formatters, Follow-On Questions section labels, completion messages.
7. **Claude-assisted PR workflow.** Multiple merge commits reference `claude/*` branches (e.g., `claude/setup-snf-navigator-app-n8pez`, `claude/extract-repo-structure-PqdRM`, `claude/fix-case-closing-PqdRM`) — the project was developed with Claude Code assistance across a small number of focused branches.

---

## 16. Data Pedigree & Seed Case Evolution

This section documents the source files supplied by the user, the iteration path they shaped, and the seed-case methodology that produced the current v11 Patient Navigator (PN) prompt. The Streamlit app captures cases; this section captures how the **AI logic that consumes those cases** was trained and constrained.

### 16.1 File Inventory

**Taxonomy Files (JSON)** — the source of the controlled "Liaison" vocabulary:
- **Action taxonomy** — the constrained verb set the PN is permitted to use (anchored to **Verify / Flag / Educate** and adjacent neutral verbs).
- **Friction taxonomy** — the categorized set of obstacles a case can surface (insurance, transport, communication, caregiver capacity, etc.).
- **Outcome taxonomy** — the discrete outcome states a case can resolve to.

Together, these three JSON files define the bounded vocabulary that prevents the PN from drifting into freeform clinical, advocacy, or vendor-recommendation language.

**Evaluation Files (CSV)** — the ground-truth corpus used to grade model output:
- **`synthetic_cases_v10_rows.csv`** — synthetic case records each carrying a veteran-navigator ranking on a **1–5 scale** plus per-case improvement notes.
- **`evaluation_sessions_v10_rows.csv`** — session-level evaluations pairing model responses with critique on tone, scope, and clinical fidelity.

These two CSVs are the source of truth for both regression detection and forward improvement targets.

### 16.2 Iteration Log (Learning Path)

**Iterations 1–4 — Foundational.** Established the PN role and surfaced the central lesson that generic AI "helpfulness" produces **political overstepping** — the model rewrote clinical plans, advocated for specific vendors, and inserted opinion into adjudication-bound situations. The role definition was hardened in response.

**Iterations 5–7 — Taxonomy Hardening.** The JSON taxonomies were imposed as hard constraints. Output verbs were locked to **Verify / Flag / Educate**, and the **No-Vendor Rule** was enforced — the PN cannot name, rank, or recommend specific vendors, agencies, or providers. Eval rejected any response that breached either rule.

**Iterations 8–10 — Evaluation Refinement.** The V10 CSV files exposed two recurring failure modes that taxonomy alone did not catch:
- **"Bot-Speak"** — overly templated, clinical-customer-service phrasing that veteran navigators flagged as unusable in real workflows.
- **"Atlantis Illusion"** — the false assumption that the portal is a **live clinical feed**, leading the PN to behave as if it had real-time visibility into facility events.

Both were addressed by tightening prompt scope and explicitly grounding the PN in **asynchronous, partial-information** context.

**Iteration 11 — Manual Context.** Implemented **Manual SW Inquiry** logic in response to navigator feedback that PNs routinely work from information gathered **verbally** — phone calls, hallway conversations, case-conference notes. The PN now treats those verbal inputs as first-class evidence rather than discounting anything not present in a structured record.

### 16.3 Seed Case Collection Strategy

"Seed cases" — the high-signal reference cases that anchor the v11 prompt — were collected through a three-step pipeline:

1. **Generate** synthetic case variations across demographic, friction, and outcome axes.
2. **Grade** each variation with veteran navigators on the 1–5 scale, capturing per-case improvement suggestions.
3. **Extract** the **"Logic DNA"** — reasoning patterns, framing choices, and verb usage — from the **Rank-5** cases and codify those patterns into the v11 system prompt.

The v11 prompt is therefore derived from observed expert judgment rather than abstract design. Each subsequent iteration starts from the Rank-5 logic and is re-evaluated against the V10 corpus to prevent regression on prior fixes (Bot-Speak, Atlantis Illusion, vendor leakage).

---

## 17. Roadmap — Planned & Future Features

### Active Workstream — v11 Prototype & DPO Preparation

- [ ] **Hand off v11 Prototype** — deliver the three full-format edge cases to the navigators for final validation.
- [ ] **Coding Agent Update** — run the documentation-update prompt to finalize project history (this section).
- [ ] **Batch 11 Production** — once navigators approve the "Manual Inquiry" logic, generate the first full batch of **25 "Stress Test"** cases.
- [ ] **DPO Dataset Preparation** — pair v6 "Overstep" failures with v11 "Masterful Moves" to seed AI fine-tuning.

### From `FUTURE_FEATURES.md`

**High priority**
1. **Admin Test Mode** — one-click test case creation, workflow verification checklist, easy cleanup (test cases marked `test_admin_1`).
2. **Reasoning Steps Annotation** — inline markers on narrative text categorizing reasoning (assessment, judgment, decision, prediction, uncertainty), with a visual timeline and a new `reasoning_annotations` table.
3. **Patient Demographics Enhancements** — `snf_admission_date` and `navigator_contact_date` columns with date pickers and validation.

**Medium priority**
4. **Bulk Transcription** — batch-process multiple cases with progress indicator.
5. **Case Search and Filtering** — demographics, intake type, date range, narrative text search, completion status.
6. **Data Export Enhancements** — CSV, PDF, bulk export, custom field selection, audio references.

**Low priority / future**
7. Multi-language support (UI + Whisper multilingual).
8. Collaborative features (case sharing, comments, assignment).
9. Analytics dashboard (volume, completion rates, demographics patterns).
10. IBM Granite 3.3 transcription as alternative to Whisper (already stubbed in settings).

**Completed milestones** (from FUTURE_FEATURES.md's Done list)
- [x] Two intake forms (Abbreviated + Full)
- [x] Audio recording, Whisper transcription, AI follow-ups
- [x] Draft auto-save + session-timeout handling
- [x] Login persistence
- [x] Audio Transcription Manager
- [x] Per-user case numbering
- [x] Follow-on questions in Case Viewer
- [x] SNF Name field, post-discharge services field
- [x] Case-dropdown identifiers with CST 12-hour format
- [x] Load Sample Case (whitelisted)

---

## 18. Code Statistics

| Component | Approx. Lines |
|-----------|--------------|
| `app.py` | 169 |
| `auth.py` | 229 |
| `db.py` | 1,337 |
| `session_timer.py` | 295 |
| `transcribe.py` | 219 |
| `openai_integration.py` | 692 |
| **Core modules subtotal** | **≈2,941** |
| `pages/1_Abbreviated_Intake.py` | 727 |
| `pages/2_Abbreviated_Intake_General.py` | 687 |
| `pages/3_Full_Intake.py` | 780 |
| `pages/4_Case_Viewer.py` | 534 |
| `pages/5_Follow_On_Questions.py` | 594 |
| `pages/6_Admin_Settings.py` | 406 |
| **Pages subtotal** | **≈3,728** |
| **Total Python** | **≈6,669** |
| Documentation (`README.md`, `REPO_STRUCTURE.md`, `FUTURE_FEATURES.md`, this file) | ≈1,400+ |

Commit total: **89**. Active development window: **21 days** (2026-01-27 through 2026-02-16). Pull requests merged from Claude-assisted branches: **5** (#1–#5).

---

*End of document. Generated 2026-04-21.*
