# Future Features Roadmap

This document outlines planned features and enhancements for the SNF Patient Navigator Case Collection App.

---

## High Priority

### 1. Admin Test Mode

**Status**: Planned

**Description**: Allow administrators to quickly test all application features without creating real case data.

**Features**:
- **Quick Test Case Creation**: One-click generation of a test case with pre-filled sample data
- **Test All Workflows**: Automated testing of:
  - Case creation (both Abbreviated and Full intake)
  - Audio recording and playback
  - Transcription functionality
  - Follow-up question generation
  - Draft save/resume functionality
- **Test Data Cleanup**: Easy removal of test cases from the database
- **Feature Verification Checklist**: Visual checklist showing which features are working correctly

**Implementation Notes**:
- Add a "Test Mode" toggle in Admin Settings
- Create sample demographic data and narrative responses
- Test cases should be clearly marked as test data (e.g., `test_admin_1`)
- Include timing metrics for performance testing

---

### 2. Reasoning Steps Annotation

**Status**: Planned

**Description**: Enable detailed annotation of clinical reasoning steps within case narratives to capture the decision-making process.

**Features**:
- **Reasoning Step Markers**: Allow users to mark specific parts of their narrative as reasoning steps
- **Step Categories**:
  - Assessment observations
  - Clinical judgments
  - Decision points
  - Outcome predictions
  - Uncertainty notes
- **Reasoning Chain Visualization**: Visual timeline showing the sequence of reasoning steps
- **Annotation Editor**: Inline annotation tool for highlighting and categorizing text
- **Export with Annotations**: Include reasoning annotations in JSON exports

**Implementation Notes**:
- Add new database table `reasoning_annotations` linked to cases
- Create annotation UI component for intake forms
- Consider using text highlighting with category labels
- Support both typed and audio-transcribed reasoning annotations

**Database Schema Addition**:
```sql
CREATE TABLE reasoning_annotations (
    id VARCHAR(36) PRIMARY KEY,
    case_id VARCHAR(250) REFERENCES cases(case_id),
    question_id VARCHAR(20),
    start_position INTEGER,
    end_position INTEGER,
    annotation_text TEXT,
    category VARCHAR(50),  -- 'assessment', 'judgment', 'decision', 'prediction', 'uncertainty'
    created_at TIMESTAMP,
    user_name VARCHAR(200)
);
```

---

### 3. Patient Demographics Enhancements

**Status**: Planned

**Description**: Add additional date tracking fields to patient demographics for better case documentation and timeline tracking.

**Features**:
- **SNF Admission Date**: Date when the patient was admitted to the Skilled Nursing Facility
- **Patient Navigator Contact Date**: Date when the patient navigator first made contact with the patient

**Implementation Notes**:
- Add `snf_admission_date` and `navigator_contact_date` columns to Case and DraftCase models
- Add date picker widgets to both Abbreviated and Full Intake forms in Patient Demographics section
- Include these dates in Case Viewer display and JSON exports
- Update sample case data to include example dates
- Consider adding date validation (e.g., admission date should be before or on contact date)

**Database Schema Addition**:
```sql
ALTER TABLE cases ADD COLUMN snf_admission_date DATE;
ALTER TABLE cases ADD COLUMN navigator_contact_date DATE;
ALTER TABLE draft_cases ADD COLUMN snf_admission_date DATE;
ALTER TABLE draft_cases ADD COLUMN navigator_contact_date DATE;
```

---

## Medium Priority

### 4. Bulk Transcription

**Status**: Planned

**Description**: Allow admins to transcribe multiple audio recordings at once.

**Features**:
- Select multiple cases or all cases for batch transcription
- Progress indicator showing transcription status
- Background processing to avoid UI blocking
- Email notification when batch transcription completes

---

### 5. Case Search and Filtering

**Status**: Planned

**Description**: Advanced search and filtering capabilities for cases.

**Features**:
- Search by patient demographics (age range, state, etc.)
- Filter by intake type (Abbreviated/Full)
- Filter by date range
- Search within narrative text
- Filter by follow-up question completion status

---

### 6. Data Export Enhancements

**Status**: Planned

**Description**: Additional export formats and options.

**Features**:
- CSV export for spreadsheet analysis
- PDF report generation
- Bulk export (multiple cases at once)
- Custom field selection for exports
- Include audio file references in exports

---

## Low Priority / Future Consideration

### 7. Multi-language Support

**Status**: Future

**Description**: Support for languages other than English.

**Features**:
- UI translation
- Multilingual transcription (Whisper supports multiple languages)
- Language preference per user

---

### 8. Collaborative Features

**Status**: Future

**Description**: Allow multiple users to collaborate on cases.

**Features**:
- Case sharing between users
- Comments and notes on cases
- Assignment of follow-up questions to different users
- Activity log showing case history

---

### 9. Analytics Dashboard

**Status**: Future

**Description**: Visual analytics for case data.

**Features**:
- Case volume over time
- Average completion rates
- Common demographics patterns
- Follow-up question response rates
- Transcription usage statistics

---

### 10. IBM Granite 3.3 Integration

**Status**: Future

**Description**: Alternative AI model for transcription using IBM Granite.

**Features**:
- Model selection between Whisper and Granite
- Comparison metrics between models
- Fallback to alternative model on errors

---

## Completed Features

- [x] Two intake forms (Abbreviated and Full)
- [x] Audio recording with browser microphone
- [x] OpenAI Whisper transcription (admin-only)
- [x] AI-generated follow-up questions
- [x] Draft auto-save with session timeout handling
- [x] Login persistence across page refreshes
- [x] Audio Transcription Manager in Admin Settings
- [x] Session timeout warning auto-dismiss on activity
- [x] Personal case numbering per user
- [x] Follow-on questions displayed in Case Viewer (with section grouping and expandable UI)
- [x] SNF Name field in patient demographics
- [x] Post-discharge services utilization tracking
- [x] Enhanced case dropdown identifiers (age, race, state) with 12-hour time format
- [x] Load Sample Case button for demo purposes (restricted to whitelisted users)

---

## Contributing

If you have feature suggestions or would like to contribute to development, please:

1. Open a GitHub issue describing the feature
2. Include use cases and expected behavior
3. Discuss implementation approach

Repository: https://github.com/hafsaahmed614/DataAnnotation_App
