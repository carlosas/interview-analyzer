# PRD: Job Application Tracker

## Introduction

Add a job application tracking system as the home view of the Interview Analyzer app. Users can track real-life job applications with company name, job title, and a granular status workflow. Applications can be linked to existing interview transcriptions and analyses, connecting the tracking with the app's core interview processing features. The home page becomes a central dashboard for managing the user's job search.

## Goals

- Provide a central home view listing all tracked job applications
- Support a multi-stage status workflow: Applied → Phone Screen → Technical Interview → Offer → Accepted/Rejected
- Allow linking job applications to existing Transcriptions and Analyses
- Enable filtering by status and sorting (newest first, company name, etc.)
- Offer a detail view with editable fields and a notes area

## User Stories

### US-001: Add JobApplication model
**Description:** As a developer, I need a database model to persist job application data so it survives across sessions.

**Acceptance Criteria:**
- [ ] Create `JobApplication` model with: UUID pk, `company_name` (CharField), `job_title` (CharField), `status` (CharField with choices: applied, phone_screen, technical_interview, offer, accepted, rejected), `notes` (TextField, blank/nullable), `created_at`, `updated_at`
- [ ] Add optional FK to `Transcription` (SET_NULL, nullable)
- [ ] Add optional FK to `Analysis` (SET_NULL, nullable)
- [ ] Default status is `applied`
- [ ] Generate and run migration successfully
- [ ] Typecheck/lint passes

### US-002: Add JobApplication service layer
**Description:** As a developer, I need a service class to encapsulate all JobApplication business logic so views remain thin.

**Acceptance Criteria:**
- [ ] Create `JobApplicationService` in `src/services.py`
- [ ] Implement CRUD methods: `get_all()`, `get_by_id()`, `create()`, `update()`, `delete()`
- [ ] `get_all()` supports optional `status` filter parameter
- [ ] `get_all()` supports `order_by` parameter (e.g., `-created_at`, `company_name`)
- [ ] Typecheck/lint passes

### US-003: Replace home view with job application list
**Description:** As a user, I want to see all my job applications in a table on the home page so I can get an overview of my job search at a glance.

**Acceptance Criteria:**
- [ ] Home page (`src/views/home.py`) displays a table/list of all job applications
- [ ] Each row shows: company name, job title, current status (as a colored badge or label)
- [ ] Rows are clickable to navigate to the detail view
- [ ] Empty state message shown when no applications exist (e.g., "No job applications yet. Click 'Add Application' to get started.")
- [ ] "Add Application" button visible to create a new application
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-004: Add status filter and sort controls
**Description:** As a user, I want to filter applications by status and sort the list so I can focus on what matters.

**Acceptance Criteria:**
- [ ] Filter dropdown with options: All, Applied, Phone Screen, Technical Interview, Offer, Accepted, Rejected
- [ ] Sort dropdown with options: Newest First (default), Oldest First, Company Name (A-Z), Company Name (Z-A)
- [ ] Filter and sort apply immediately on change
- [ ] Filter and sort state persists in `st.session_state` during session
- [ ] Results update correctly when both filter and sort are active simultaneously
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-005: Add inline status update from home list
**Description:** As a user, I want to change an application's status directly from the list so I don't have to open the detail view for quick updates.

**Acceptance Criteria:**
- [ ] Each row has a status dropdown/selectbox that reflects the current status
- [ ] Changing the dropdown updates the status in the database immediately
- [ ] The list reflects the new status without full page reload (st.rerun)
- [ ] If a status filter is active and the new status no longer matches, the row disappears from the filtered view on rerun
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-006: Create new job application form
**Description:** As a user, I want to add a new job application so I can start tracking a position I applied to.

**Acceptance Criteria:**
- [ ] Form with fields: Company Name (required), Job Title (required), Status (dropdown, defaults to "Applied"), Notes (optional textarea)
- [ ] Optional dropdowns to link an existing Transcription and/or Analysis
- [ ] Validation: company name and job title are required, show error if empty
- [ ] On successful creation, redirect to the home list with the new entry visible
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-007: Job application detail view
**Description:** As a user, I want to view and edit a job application's details so I can update information and add notes.

**Acceptance Criteria:**
- [ ] Detail view shows: company name, job title, status, notes, linked transcription (if any), linked analysis (if any), created/updated timestamps
- [ ] All fields are editable (company name, job title, status dropdown, notes textarea, transcription link, analysis link)
- [ ] "Save" button persists changes to the database
- [ ] "Delete" button with confirmation dialog (follows existing delete pattern in the app)
- [ ] "Back to list" navigation to return to home
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

### US-008: Update navigation to reflect new home
**Description:** As a developer, I need to update `streamlit_app.py` navigation so the home page is the job tracker.

**Acceptance Criteria:**
- [ ] Home entry in `st.navigation()` points to the job application tracker view
- [ ] Navigation icon and label are appropriate (e.g., 💼 Job Applications or 🏠 Home)
- [ ] All existing pages (Interview Analyzer, Interviews, CV) remain accessible
- [ ] Typecheck/lint passes

### US-009: Reverse linking from Transcription and Analysis views
**Description:** As a user, I want to link an interview transcription or analysis to a job application from within those views, so I can associate data from either direction.

**Acceptance Criteria:**
- [ ] Transcription detail view shows an optional "Link to Job Application" dropdown listing existing applications (formatted as "Company — Job Title")
- [ ] Analysis detail view shows an optional "Link to Job Application" dropdown listing existing applications
- [ ] Selecting an application and saving updates the FK on the JobApplication model
- [ ] Clearing the selection removes the link
- [ ] Typecheck/lint passes
- [ ] Verify in browser using dev-browser skill

## Functional Requirements

- FR-1: Add `JobApplication` model with fields: `id` (UUID), `company_name`, `job_title`, `status` (choices: applied, phone_screen, technical_interview, offer, accepted, rejected), `notes`, `transcription` (FK), `analysis` (FK), `created_at`, `updated_at`
- FR-2: Default status for new applications is `applied`
- FR-3: Status selection is free-form — no enforced ordering between statuses
- FR-4: Home page displays all job applications in a table with columns: company name, job title, status
- FR-5: Each table row includes an inline status dropdown that updates the record on change
- FR-6: Filter dropdown filters the list by status (including an "All" option)
- FR-7: Sort dropdown sorts by: newest first, oldest first, company name A-Z, company name Z-A
- FR-8: Clicking a row navigates to the detail view for that application
- FR-9: Detail view displays all fields and allows inline editing with a Save button
- FR-10: Detail view includes a Delete button with confirmation dialog
- FR-11: New application form requires company name and job title; status defaults to "applied"
- FR-12: New application form allows optionally linking a Transcription and/or Analysis
- FR-13: Transcription and Analysis detail views allow linking to an existing JobApplication
- FR-14: All CRUD operations go through `JobApplicationService` in the service layer

## Non-Goals

- No drag-and-drop Kanban board view (list/table only)
- No email or calendar integration
- No automatic status progression based on interview data
- No bulk operations (bulk delete, bulk status change)
- No export functionality (CSV, PDF)
- No job application reminders or notifications

## Design Considerations

- Follow existing Streamlit view patterns (sidebar controls, session state management, delete confirmation dialogs)
- Status badges should use distinct colors for visual scanning (e.g., blue=applied, yellow=phone screen, orange=technical interview, purple=offer, green=accepted, red=rejected)
- The detail view should follow the same layout patterns as existing views (transcription.py, cv.py)
- Use `st.dataframe` or `st.columns` for the table — prefer a layout that supports clickable rows

## Technical Considerations

- Model follows existing UUID pk pattern used by CV, Transcription, and Analysis models
- Service class follows existing pattern in `src/services.py` (CVService, TranscriptionService, AnalysisService)
- ForeignKeys to Transcription and Analysis use `SET_NULL` to avoid cascading deletes
- Streamlit session state keys should be namespaced (e.g., `job_app_filter`, `job_app_sort`, `selected_job_app_id`)
- Navigation in detail view can use `st.query_params` or session state to pass the selected application ID

## Success Metrics

- Users can add a new job application in under 3 clicks
- Users can update status directly from the home list in 1 click
- Home page loads and displays all applications without noticeable delay
- All existing functionality (transcription, analysis, CV) remains fully accessible

## Resolved Questions

- **Reverse linking:** Yes — Transcription and Analysis detail views should also allow linking to a JobApplication (add an optional dropdown to select an existing application).
- **Status workflow ordering:** No enforcement — users can freely select any status at any time.
- **Status summary on home page:** No — keep the home page focused on the table.
