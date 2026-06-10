---
name: studypdf-testing
description: Use when adding, changing, or reviewing tests for the StudyPDF Flask application. Applies behavior-first testing principles adapted from Spring boundary/component testing to Flask routes, SQLite persistence, background jobs, PDF processing, and browser JavaScript.
---

# StudyPDF Testing

Use this skill when creating or changing tests in the StudyPDF project. Prefer behavior-focused tests that exercise the application through its real boundaries, while keeping external dependencies controlled and deterministic.

## Project Test Philosophy

Test behavior from the system boundary.

- For request-driven behavior, start from Flask routes using `app.test_client()`.
- Do not write isolated tests for services, repositories, mappers, validators, domain helpers, or persistence code when the behavior is reachable through a route.
- A service should usually be covered by a route test that triggers it through the HTTP boundary.
- SQLite schema, constraints, queries, state transitions, and persistence mappings should be verified as part of boundary tests when reachable from a route.
- Pure domain helpers may have focused unit tests only when they contain meaningful deterministic logic that is hard to cover clearly through HTTP.

## Boundaries By Feature

### HTTP/UI behavior

Start from routes in:

- `studypdf/routes/main.py`
- `studypdf/routes/books.py`
- `studypdf/routes/notes.py`

Use Flask `test_client()` to send realistic requests and assert:

- HTTP status codes.
- Redirect targets.
- JSON response fields.
- Rendered HTML markers that are part of the user contract.
- Database state after the request.

### Background processing and cron

Jobs are not invoked by user-facing controllers, so test from the outermost job entry point:

- `POST /cron/process-books` for cron behavior.
- `process_next_job()` only when testing the worker/service path directly is clearer and no route-level contract is involved.

Assert observable behavior:

- Job status transitions.
- Book status transitions.
- Pages/chapters inserted.
- Processing errors persisted.
- Assets written only when filesystem behavior is the subject of the test.

### Reader JavaScript

For `static/reader.js`, prefer integration-style checks when possible:

- Render `/books/<id>/read`.
- Verify required DOM hooks exist.
- Use browser/Playwright only for behavior that depends on selection, scrolling, dialogs, layout, or localStorage.

For simple syntax safety, always run:

```powershell
node --check static/reader.js
```

## Mocking Policy

Avoid mocking by default.

Do not mock:

- Flask routes.
- Internal services.
- Domain helpers.
- SQLite access.
- The database.
- PDF persistence tables.
- Notes/books repositories implemented as SQL functions.

Mock or fake only dependencies outside the system boundary:

- Real network calls.
- Third-party APIs.
- External services.
- Time, randomness, or ID generation when determinism is required.
- Expensive or brittle PDF extraction when the test is not about extraction.

When faking PyMuPDF/PDF processing, prefer a small real fixture PDF if feasible. Use mocks only at the PDF boundary, not inside business logic.

## Database Testing

Tests that depend on persistence must use an isolated SQLite database.

Preferred setup:

- Override `studypdf.config.DB_PATH` or run the app in a temp working/data directory.
- Call `init_db()` before each test or fixture scope.
- Seed only the rows needed for the behavior.
- Keep each test independent.
- Clean database state between tests by recreating the temp DB or deleting rows.

Do not use the developer's real `data/studypdf.sqlite3` in automated tests.

## What To Assert

Prefer asserting observable behavior:

- Response status and JSON body.
- Redirect location.
- Database rows and field values.
- Book status/progress/checkpoint state.
- Notes created, updated, deleted, or exported.
- Rendered controls for user-visible workflows.
- Files written only when file output is required behavior.

Avoid asserting:

- Private function behavior.
- Internal call order.
- That a service method was called.
- Implementation-specific helper structure.
- Exact HTML formatting unless it is a stable UI contract.

## Boundary Cases To Cover

For new behavior, include relevant boundaries:

- Missing required fields.
- Invalid IDs and not found cases.
- Invalid enum/status values.
- Duplicate or repeated requests when idempotency matters.
- Empty input.
- Minimum and maximum valid values.
- Just below/above valid numeric limits.
- Invalid file type for upload.
- Processing failure paths.
- Reset/cleanup confirmation failures.
- Checkpoint confidence boundaries.
- Progress below page 1 and above total page count.

## Clean Execution Rules

Tests must be deterministic and quiet.

- No dependency on current time unless controlled or asserted loosely.
- No dependency on random UUID values unless injected or pattern-matched.
- No arbitrary sleeps.
- No real network calls.
- No shared mutable state across tests.
- No hidden background exceptions.
- No tests that pass while logging unexpected stack traces.

When async/background behavior is involved, trigger the job synchronously through the route/service under test or wait on a deterministic condition.

## Naming

Use behavior names.

Prefer:

```python
def test_upload_queues_book_when_pdf_is_valid(client):
def test_progress_is_clamped_when_page_is_above_total(client):
def test_reset_requires_confirmation(client):
def test_checkpoint_is_limited_to_real_chapters(client):
```

Avoid:

```python
def test_service():
def test_create():
def test_repository_called():
```

## Validation Commands

Before finishing testing-related work, run the nearest useful checks:

```powershell
python -m py_compile app.py (Get-ChildItem studypdf -Recurse -Filter *.py | ForEach-Object { $_.FullName })
node --check static/reader.js
```

If a pytest suite exists or is added, run:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

If Sonar is configured and relevant, run:

```powershell
$env:SONAR_TOKEN="..."
.\scripts\sonar-scan.ps1
```

Do not commit generated local data such as `data/`, `books/`, `.sonar/`, `.venv/`, or `__pycache__/`.

