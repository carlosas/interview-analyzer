# Job Application Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a job application tracking system as the home view, with list/detail views, inline status updates, filtering/sorting, and reverse linking from existing Transcription/Analysis views.

**Architecture:** New `JobApplication` Django model with FKs to Transcription and Analysis. New `JobApplicationService` in the service layer for CRUD + filtering. Home view replaced with a Streamlit table, plus a new detail view page. Reverse linking added to existing Transcription and Analysis views.

**Tech Stack:** Django ORM, PostgreSQL, Streamlit, Python 3.14+ type hints

**PRD:** `tasks/prd-job-application-tracker.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `analyzer/src/models.py` | Add `JobApplication` model |
| Modify | `analyzer/src/services.py` | Add `JobApplicationService` class |
| Modify | `analyzer/src/views/home.py` | Replace landing page with job application list + create form |
| Create | `analyzer/src/views/job_application_detail.py` | Detail/edit view for a single job application |
| Modify | `analyzer/src/streamlit_app.py` | Add detail page to navigation |
| Modify | `analyzer/src/views/transcription.py` | Add "Link to Job Application" dropdown |
| Modify | `analyzer/src/views/analysis.py` | Add "Link to Job Application" dropdown |
| Create | `analyzer/tests/unit/test_job_application_services.py` | Unit tests for `JobApplicationService` |

---

## Task 1: Add JobApplication Model (US-001)

**Files:**
- Modify: `analyzer/src/models.py`

- [ ] **Step 1: Add the JobApplication model**

Add after the `Analysis` class in `analyzer/src/models.py`:

```python
class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        PHONE_SCREEN = "phone_screen", "Phone Screen"
        TECHNICAL_INTERVIEW = "technical_interview", "Technical Interview"
        OFFER = "offer", "Offer"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.APPLIED
    )
    # Deliberate: using default="" instead of null=True per Django TextField convention
    # (avoids two representations of "no data")
    notes = models.TextField(blank=True, default="")
    transcription = models.ForeignKey(
        "Transcription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_applications",
    )
    analysis = models.ForeignKey(
        "Analysis",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_applications",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.company_name} — {self.job_title} ({self.get_status_display()})"
```

- [ ] **Step 2: Generate and run migration**

```bash
make shell
# inside container:
python manage.py makemigrations src
python manage.py migrate
exit
```

Or if running via compose directly:
```bash
docker compose run --rm app python manage.py makemigrations src
make migrate
```

- [ ] **Step 3: Lint**

```bash
make lint
```

- [ ] **Step 4: Commit**

```bash
git add analyzer/src/models.py analyzer/src/migrations/
git commit -m "feat: add JobApplication model with status workflow and FK links"
```

---

## Task 2: Add JobApplicationService (US-002)

**Files:**
- Modify: `analyzer/src/services.py`
- Create: `analyzer/tests/unit/test_job_application_services.py`

- [ ] **Step 1: Write the failing tests**

Create `analyzer/tests/unit/test_job_application_services.py`:

```python
import uuid

from django.test import TestCase

from src.models import JobApplication
from src.services import JobApplicationService


class TestJobApplicationService(TestCase):
    """Unit tests for JobApplicationService."""

    def setUp(self) -> None:
        self.service = JobApplicationService()

    def test_create_job_application(self) -> None:
        """create should persist a new job application with defaults."""
        app = self.service.create(
            company_name="Acme Corp",
            job_title="Backend Engineer",
        )

        self.assertIsNotNone(app.id)
        self.assertEqual(app.company_name, "Acme Corp")
        self.assertEqual(app.job_title, "Backend Engineer")
        self.assertEqual(app.status, JobApplication.Status.APPLIED)
        self.assertEqual(app.notes, "")

    def test_create_with_all_fields(self) -> None:
        """create should accept optional notes and status."""
        app = self.service.create(
            company_name="BigCo",
            job_title="SRE",
            status=JobApplication.Status.PHONE_SCREEN,
            notes="Recruiter reached out on LinkedIn",
        )

        self.assertEqual(app.status, JobApplication.Status.PHONE_SCREEN)
        self.assertEqual(app.notes, "Recruiter reached out on LinkedIn")

    def test_get_all_returns_all(self) -> None:
        """get_all with no filters should return all applications."""
        self.service.create(company_name="A", job_title="X")
        self.service.create(company_name="B", job_title="Y")

        result = self.service.get_all()

        self.assertEqual(result.count(), 2)

    def test_get_all_filter_by_status(self) -> None:
        """get_all should filter by status when provided."""
        self.service.create(company_name="A", job_title="X")
        self.service.create(
            company_name="B", job_title="Y",
            status=JobApplication.Status.OFFER,
        )

        result = self.service.get_all(status=JobApplication.Status.OFFER)

        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().company_name, "B")

    def test_get_all_order_by(self) -> None:
        """get_all should respect order_by parameter."""
        self.service.create(company_name="Zebra", job_title="X")
        self.service.create(company_name="Apple", job_title="Y")

        result = list(self.service.get_all(order_by="company_name"))

        self.assertEqual(result[0].company_name, "Apple")
        self.assertEqual(result[1].company_name, "Zebra")

    def test_get_by_id(self) -> None:
        """get_by_id should return the matching application."""
        app = self.service.create(company_name="Test", job_title="Dev")

        result = self.service.get_by_id(app.id)

        self.assertEqual(result.id, app.id)

    def test_get_by_id_not_found(self) -> None:
        """get_by_id should raise DoesNotExist for invalid UUID."""
        with self.assertRaises(JobApplication.DoesNotExist):
            self.service.get_by_id(uuid.uuid4())

    def test_update(self) -> None:
        """update should modify specified fields."""
        app = self.service.create(company_name="Old", job_title="Dev")

        updated = self.service.update(
            app.id,
            company_name="New",
            status=JobApplication.Status.TECHNICAL_INTERVIEW,
        )

        self.assertEqual(updated.company_name, "New")
        self.assertEqual(updated.status, JobApplication.Status.TECHNICAL_INTERVIEW)
        app.refresh_from_db()
        self.assertEqual(app.company_name, "New")

    def test_create_with_transcription_link(self) -> None:
        """create should link to an existing transcription via FK."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from src.models import Transcription

        transcription = Transcription.objects.create(
            name="Mock Interview",
            audio_filename="mock.mp3",
            audio_file=SimpleUploadedFile("mock.mp3", b"audio", content_type="audio/mpeg"),
            status=Transcription.Status.COMPLETED,
        )

        app = self.service.create(
            company_name="LinkedCo",
            job_title="Dev",
            transcription_id=transcription.id,
        )

        app.refresh_from_db()
        self.assertEqual(app.transcription_id, transcription.id)

    def test_update_sets_fk_fields(self) -> None:
        """update should set and clear FK links."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from src.models import Transcription

        transcription = Transcription.objects.create(
            name="Interview",
            audio_filename="i.mp3",
            audio_file=SimpleUploadedFile("i.mp3", b"audio", content_type="audio/mpeg"),
            status=Transcription.Status.COMPLETED,
        )
        app = self.service.create(company_name="Co", job_title="Dev")

        # Set link
        updated = self.service.update(app.id, transcription_id=transcription.id)
        self.assertEqual(updated.transcription_id, transcription.id)

        # Clear link
        updated = self.service.update(app.id, transcription_id=None)
        self.assertIsNone(updated.transcription_id)

    def test_delete(self) -> None:
        """delete should remove the application from the database."""
        app = self.service.create(company_name="Gone", job_title="Dev")
        app_id = app.id

        self.service.delete(app_id)

        self.assertFalse(JobApplication.objects.filter(pk=app_id).exists())
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
make tests
```
Expected: ImportError — `JobApplicationService` does not exist yet.

- [ ] **Step 3: Implement JobApplicationService**

Add to `analyzer/src/services.py` — import `JobApplication` at the top, then add the class before `LLMService`:

```python
# Add to imports at top:
from src.models import CV, Analysis, JobApplication, Transcription

class JobApplicationService:
    def get_all(
        self,
        status: str | None = None,
        order_by: str = "-created_at",
    ) -> QuerySet[JobApplication]:
        queryset = JobApplication.objects.select_related("transcription", "analysis").all()
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by(order_by)

    def get_by_id(self, job_application_id: uuid.UUID) -> JobApplication:
        return JobApplication.objects.select_related(
            "transcription", "analysis"
        ).get(pk=job_application_id)

    def create(
        self,
        company_name: str,
        job_title: str,
        status: str = JobApplication.Status.APPLIED,
        notes: str = "",
        transcription_id: uuid.UUID | None = None,
        analysis_id: uuid.UUID | None = None,
    ) -> JobApplication:
        return JobApplication.objects.create(
            company_name=company_name,
            job_title=job_title,
            status=status,
            notes=notes,
            transcription_id=transcription_id,
            analysis_id=analysis_id,
        )

    def update(self, job_application_id: uuid.UUID, **kwargs: Any) -> JobApplication:
        app = JobApplication.objects.get(pk=job_application_id)
        for key, value in kwargs.items():
            setattr(app, key, value)
        app.save()
        return app

    def delete(self, job_application_id: uuid.UUID) -> None:
        JobApplication.objects.filter(pk=job_application_id).delete()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
make tests
```
Expected: All `TestJobApplicationService` tests pass.

- [ ] **Step 5: Lint**

```bash
make lint
```

- [ ] **Step 6: Commit**

```bash
git add analyzer/src/services.py analyzer/tests/unit/test_job_application_services.py
git commit -m "feat: add JobApplicationService with CRUD, filtering, and sorting"
```

---

## Task 3: Replace Home View with Job Application List (US-003, US-004, US-005, US-006)

**Files:**
- Modify: `analyzer/src/views/home.py`

This task combines US-003 (list), US-004 (filter/sort), US-005 (inline status), and US-006 (create form) since they all live in the same file and are tightly coupled.

- [ ] **Step 1: Implement the home view**

Replace the entire contents of `analyzer/src/views/home.py`:

```python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import streamlit as st  # noqa: E402

from src.models import JobApplication  # noqa: E402
from src.services import (  # noqa: E402
    AnalysisService,
    JobApplicationService,
    TranscriptionService,
)

job_app_service = JobApplicationService()
transcription_service = TranscriptionService()
analysis_service = AnalysisService()

STATUS_COLORS: dict[str, str] = {
    "applied": "blue",
    "phone_screen": "orange",
    "technical_interview": "violet",
    "offer": "rainbow",
    "accepted": "green",
    "rejected": "red",
}

STATUS_OPTIONS = [s.value for s in JobApplication.Status]
STATUS_LABELS = {s.value: s.label for s in JobApplication.Status}

SORT_OPTIONS: dict[str, str] = {
    "Newest First": "-created_at",
    "Oldest First": "created_at",
    "Company Name (A-Z)": "company_name",
    "Company Name (Z-A)": "-company_name",
}

st.title("💼 Job Applications")

# --- Sidebar: Create + Filter/Sort ---
st.sidebar.header("Job Applications")

if st.sidebar.button("➕ Add Application", key="btn_new_job_app"):
    st.session_state["job_app_mode"] = "new"

st.sidebar.divider()

# Filter
filter_options = ["All"] + [STATUS_LABELS[s] for s in STATUS_OPTIONS]
selected_filter = st.sidebar.selectbox(
    "Filter by Status",
    filter_options,
    key="job_app_filter",
)

# Sort
selected_sort = st.sidebar.selectbox(
    "Sort by",
    list(SORT_OPTIONS.keys()),
    key="job_app_sort",
)

# --- Main content ---

if st.session_state.get("job_app_mode") == "new":
    # Create new job application form
    st.subheader("Add New Application")

    company_name = st.text_input("Company Name *", key="new_company_name")
    job_title = st.text_input("Job Title *", key="new_job_title")

    status = st.selectbox(
        "Status",
        STATUS_OPTIONS,
        format_func=lambda s: STATUS_LABELS[s],
        key="new_status",
    )

    notes = st.text_area("Notes (optional)", key="new_notes")

    # Optional links
    transcriptions = list(transcription_service.get_completed_transcriptions())
    transcription_options = ["None"] + [
        f"{t.name} ({t.created_at:%Y-%m-%d})" for t in transcriptions
    ]
    transcription_choice = st.selectbox(
        "Link Interview (optional)",
        transcription_options,
        key="new_transcription_link",
    )

    analyses = list(analysis_service.get_analyses({}))
    analysis_options = ["None"] + [
        f"{a.transcription.name} ({a.status})" for a in analyses
    ]
    analysis_choice = st.selectbox(
        "Link Analysis (optional)",
        analysis_options,
        key="new_analysis_link",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", key="btn_save_job_app"):
            if not company_name.strip():
                st.error("Company Name is required.")
            elif not job_title.strip():
                st.error("Job Title is required.")
            else:
                transcription_id = (
                    transcriptions[transcription_options.index(transcription_choice) - 1].id
                    if transcription_choice != "None"
                    else None
                )
                analysis_id = (
                    analyses[analysis_options.index(analysis_choice) - 1].id
                    if analysis_choice != "None"
                    else None
                )
                job_app_service.create(
                    company_name=company_name.strip(),
                    job_title=job_title.strip(),
                    status=status,
                    notes=notes,
                    transcription_id=transcription_id,
                    analysis_id=analysis_id,
                )
                st.session_state.pop("job_app_mode", None)
                st.rerun()
    with col2:
        if st.button("Cancel", key="btn_cancel_job_app"):
            st.session_state.pop("job_app_mode", None)
            st.rerun()

else:
    # Build query
    status_filter = None
    if selected_filter != "All":
        # Reverse lookup: label -> value
        label_to_value = {v: k for k, v in STATUS_LABELS.items()}
        status_filter = label_to_value[selected_filter]

    order_by = SORT_OPTIONS[selected_sort]
    applications = list(job_app_service.get_all(status=status_filter, order_by=order_by))

    if not applications:
        st.info("No job applications yet. Click '➕ Add Application' in the sidebar to get started.")
    else:
        for app in applications:
            color = STATUS_COLORS.get(app.status, "gray")
            with st.container(border=True):
                col_company, col_title, col_badge, col_status, col_action = st.columns(
                    [3, 3, 1.5, 2.5, 1]
                )

                with col_company:
                    st.markdown(f"**{app.company_name}**")

                with col_title:
                    st.markdown(app.job_title)

                with col_badge:
                    st.markdown(f":{color}[{STATUS_LABELS[app.status]}]")

                with col_status:
                    new_status = st.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(app.status),
                        format_func=lambda s: STATUS_LABELS[s],
                        key=f"status_{app.id}",
                        label_visibility="collapsed",
                    )
                    if new_status != app.status:
                        job_app_service.update(app.id, status=new_status)
                        st.rerun()

                with col_action:
                    if st.button("→", key=f"detail_{app.id}", help="View details"):
                        st.session_state["selected_job_app_id"] = str(app.id)
                        st.switch_page("views/job_application_detail.py")
```

- [ ] **Step 2: Lint**

```bash
make lint
```

- [ ] **Step 3: Commit**

```bash
git add analyzer/src/views/home.py
git commit -m "feat: replace home view with job application list, filter, sort, and create form"
```

---

## Task 4: Add Job Application Detail View (US-007)

**Files:**
- Create: `analyzer/src/views/job_application_detail.py`

- [ ] **Step 1: Create the detail view**

Create `analyzer/src/views/job_application_detail.py`:

```python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import streamlit as st  # noqa: E402

from src.models import JobApplication  # noqa: E402
from src.services import (  # noqa: E402
    AnalysisService,
    JobApplicationService,
    TranscriptionService,
)

job_app_service = JobApplicationService()
transcription_service = TranscriptionService()
analysis_service = AnalysisService()

STATUS_OPTIONS = [s.value for s in JobApplication.Status]
STATUS_LABELS = {s.value: s.label for s in JobApplication.Status}

st.title("💼 Application Details")

# --- Check for selected application ---
app_id = st.session_state.get("selected_job_app_id")
if not app_id:
    st.warning("No application selected.")
    if st.button("← Back to Applications"):
        st.switch_page("views/home.py")
    st.stop()

try:
    app = job_app_service.get_by_id(app_id)
except JobApplication.DoesNotExist:
    st.error("Application not found.")
    if st.button("← Back to Applications"):
        st.session_state.pop("selected_job_app_id", None)
        st.switch_page("views/home.py")
    st.stop()

# --- Back button ---
if st.button("← Back to Applications", key="btn_back"):
    st.session_state.pop("selected_job_app_id", None)
    st.switch_page("views/home.py")

st.divider()

# --- Editable fields ---
company_name = st.text_input("Company Name", value=app.company_name, key="detail_company")
job_title = st.text_input("Job Title", value=app.job_title, key="detail_job_title")

status = st.selectbox(
    "Status",
    STATUS_OPTIONS,
    index=STATUS_OPTIONS.index(app.status),
    format_func=lambda s: STATUS_LABELS[s],
    key="detail_status",
)

notes = st.text_area("Notes", value=app.notes, height=200, key="detail_notes")

# --- Linked Transcription ---
transcriptions = list(transcription_service.get_completed_transcriptions())
transcription_options = ["None"] + [
    f"{t.name} ({t.created_at:%Y-%m-%d})" for t in transcriptions
]
current_transcription_idx = 0
if app.transcription_id:
    for i, t in enumerate(transcriptions):
        if t.id == app.transcription_id:
            current_transcription_idx = i + 1
            break

transcription_choice = st.selectbox(
    "Linked Interview",
    transcription_options,
    index=current_transcription_idx,
    key="detail_transcription",
)

# --- Linked Analysis ---
analyses = list(analysis_service.get_analyses({}))
analysis_options = ["None"] + [
    f"{a.transcription.name} ({a.status})" for a in analyses
]
current_analysis_idx = 0
if app.analysis_id:
    for i, a in enumerate(analyses):
        if a.id == app.analysis_id:
            current_analysis_idx = i + 1
            break

analysis_choice = st.selectbox(
    "Linked Analysis",
    analysis_options,
    index=current_analysis_idx,
    key="detail_analysis",
)

# --- Timestamps ---
st.caption(
    f"Created: {app.created_at:%Y-%m-%d %H:%M} | "
    f"Updated: {app.updated_at:%Y-%m-%d %H:%M}"
)

# --- Save ---
st.divider()
if st.button("Save Changes", type="primary", key="btn_save_detail"):
    if not company_name.strip():
        st.error("Company Name is required.")
    elif not job_title.strip():
        st.error("Job Title is required.")
    else:
        transcription_id = (
            transcriptions[transcription_options.index(transcription_choice) - 1].id
            if transcription_choice != "None"
            else None
        )
        analysis_id = (
            analyses[analysis_options.index(analysis_choice) - 1].id
            if analysis_choice != "None"
            else None
        )
        job_app_service.update(
            app.id,
            company_name=company_name.strip(),
            job_title=job_title.strip(),
            status=status,
            notes=notes,
            transcription_id=transcription_id,
            analysis_id=analysis_id,
        )
        st.success("Changes saved!")
        st.rerun()

# --- Delete ---
if st.button("Delete Application", type="secondary", key="btn_delete_job_app"):
    st.session_state["confirm_delete_job_app"] = True

if st.session_state.get("confirm_delete_job_app"):
    st.warning("Are you sure you want to delete this application?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, delete", key="btn_confirm_delete_job_app"):
            job_app_service.delete(app.id)
            st.session_state.pop("confirm_delete_job_app", None)
            st.session_state.pop("selected_job_app_id", None)
            st.switch_page("views/home.py")
    with col2:
        if st.button("Cancel", key="btn_cancel_delete_job_app"):
            st.session_state.pop("confirm_delete_job_app", None)
            st.rerun()
```

- [ ] **Step 2: Lint**

```bash
make lint
```

- [ ] **Step 3: Commit**

```bash
git add analyzer/src/views/job_application_detail.py
git commit -m "feat: add job application detail view with edit, link, and delete"
```

---

## Task 5: Update Navigation (US-008)

**Files:**
- Modify: `analyzer/src/streamlit_app.py`

- [ ] **Step 1: Update the navigation config**

In `analyzer/src/streamlit_app.py`, update the `pages` dict:

```python
# Detail page registered separately — must be in the navigation for st.switch_page to work
detail_page = st.Page(
    "views/job_application_detail.py",
    title="Application Details",
    url_path="application-details",
)

pages = {
    "General": [
        st.Page("views/home.py", title="Job Applications", icon="\U0001f4bc"),
    ],
    "Apps": [
        st.Page("views/analysis.py", title="Interview Analyzer", icon="\U0001f916"),
    ],
    "Context": [
        st.Page("views/transcription.py", title="Interviews", icon="\U0001f3a4"),
        st.Page("views/cv.py", title="Curriculum Vitae", icon="\U0001f4c4"),
    ],
}
pg = st.navigation(pages | {"": [detail_page]})
pg.run()
```

Note: The detail page is registered under an empty-string section key. In Streamlit, this creates an unlabeled section in the sidebar. The page will appear in the sidebar but without a section header. This is the simplest approach that keeps the page routable via `st.switch_page`. If sidebar visibility is undesirable, a future improvement could use `st.query_params` to route within the home page instead.

**Important:** This replaces the existing `pg = st.navigation(pages)` / `pg.run()` lines at the bottom of the file — do not duplicate them.

- [ ] **Step 2: Lint**

```bash
make lint
```

- [ ] **Step 3: Commit**

```bash
git add analyzer/src/streamlit_app.py
git commit -m "feat: update navigation — home is now Job Applications, add hidden detail route"
```

---

## Task 6: Reverse Linking from Transcription and Analysis Views (US-009)

**Files:**
- Modify: `analyzer/src/views/transcription.py`
- Modify: `analyzer/src/views/analysis.py`

- [ ] **Step 1: Add reverse linking to transcription view**

In `analyzer/src/views/transcription.py`:

1. Add import for `JobApplicationService` alongside existing imports:
```python
from src.services import JobApplicationService, TranscriptionService  # noqa: E402
```

2. Instantiate the service:
```python
job_app_service = JobApplicationService()
```

3. In the "view existing transcription" block (after the transcription text expander and before the delete divider), add a "Link to Job Application" section.

**Note:** Multiple JobApplications can link to the same Transcription (FK, not OneToOne). The UI shows the first linked application found. This is acceptable for V1 — most transcriptions will have at most one linked application.

```python
    # Link to Job Application
    st.divider()
    st.subheader("Link to Job Application")
    job_applications = list(job_app_service.get_all())
    job_app_options = ["None"] + [
        f"{ja.company_name} — {ja.job_title}" for ja in job_applications
    ]

    # Find first current link (if any — multiple apps could link to this transcription)
    current_link_idx = 0
    for i, ja in enumerate(job_applications):
        if ja.transcription_id == transcription.id:
            current_link_idx = i + 1
            break

    link_choice = st.selectbox(
        "Job Application",
        job_app_options,
        index=current_link_idx,
        key="transcription_job_app_link",
    )

    if st.button("Save Link", key="btn_save_transcription_link"):
        # Clear old link if exists
        if current_link_idx > 0:
            old_app = job_applications[current_link_idx - 1]
            job_app_service.update(old_app.id, transcription_id=None)

        # Set new link
        if link_choice != "None":
            new_app = job_applications[job_app_options.index(link_choice) - 1]
            job_app_service.update(new_app.id, transcription_id=transcription.id)

        st.success("Link updated!")
        st.rerun()
```

- [ ] **Step 2: Add reverse linking to analysis view**

In `analyzer/src/views/analysis.py`:

1. Add import for `JobApplicationService`:
```python
from src.services import AnalysisService, CVService, JobApplicationService, TranscriptionService  # noqa: E402
```

2. Instantiate:
```python
job_app_service = JobApplicationService()
```

3. In the "view existing analysis" block (after the source transcription expander, before the delete divider), add:

```python
    # Link to Job Application
    st.divider()
    st.subheader("Link to Job Application")
    job_applications = list(job_app_service.get_all())
    job_app_options = ["None"] + [
        f"{ja.company_name} — {ja.job_title}" for ja in job_applications
    ]

    current_link_idx = 0
    for i, ja in enumerate(job_applications):
        if ja.analysis_id == analysis.id:
            current_link_idx = i + 1
            break

    link_choice = st.selectbox(
        "Job Application",
        job_app_options,
        index=current_link_idx,
        key="analysis_job_app_link",
    )

    if st.button("Save Link", key="btn_save_analysis_link"):
        if current_link_idx > 0:
            old_app = job_applications[current_link_idx - 1]
            job_app_service.update(old_app.id, analysis_id=None)

        if link_choice != "None":
            new_app = job_applications[job_app_options.index(link_choice) - 1]
            job_app_service.update(new_app.id, analysis_id=analysis.id)

        st.success("Link updated!")
        st.rerun()
```

- [ ] **Step 3: Lint**

```bash
make lint
```

- [ ] **Step 4: Commit**

```bash
git add analyzer/src/views/transcription.py analyzer/src/views/analysis.py
git commit -m "feat: add reverse linking to job applications from transcription and analysis views"
```

---

## Task 7: Final Verification

- [ ] **Step 1: Run full test suite**

```bash
make tests
```
Expected: All tests pass, including new `TestJobApplicationService` tests.

- [ ] **Step 2: Run lint**

```bash
make lint
```
Expected: No errors.

- [ ] **Step 3: Manual smoke test**

Start the app and verify:
```bash
make start
```
Then open http://localhost:8501 and check:
- Home page shows the job application list (empty state initially)
- Can create a new application via sidebar button
- Can filter by status and sort
- Can change status inline from the list
- Can click into detail view and edit all fields
- Can link transcription/analysis from both directions
- Can delete an application with confirmation
- All existing pages still work

- [ ] **Step 4: Final commit if any adjustments needed**
