from pathlib import Path

from studypdf.db import get_db
from studypdf.services import processing


def test_cron_process_books_reports_zero_when_queue_is_empty(client):
    response = client.post("/cron/process-books")

    assert response.status_code == 200
    assert response.get_json() == {"processed_jobs": 0, "status": "ok"}


def test_original_pdf_and_html_export_are_available(client, ready_book):
    pdf_response = client.get(f"/books/{ready_book['id']}/original")
    html_response = client.get(f"/books/{ready_book['id']}/html")

    assert pdf_response.status_code == 200
    assert pdf_response.mimetype == "application/pdf"
    assert html_response.status_code == 200
    assert "Chapter 1" in html_response.get_data(as_text=True)


def test_delete_book_removes_records_and_files(client, app, ready_book):
    book_id = ready_book["id"]
    pdf_path = Path(ready_book["pdf_path"])

    response = client.delete(f"/api/books/{book_id}")

    assert response.status_code == 200
    assert not pdf_path.parent.exists()
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT id FROM books WHERE id = ?", (book_id,)).fetchone() is None
        assert db.execute("SELECT id FROM pages WHERE book_id = ?", (book_id,)).fetchone() is None


def test_process_next_job_marks_book_ready_and_replaces_content(app, tmp_path, monkeypatch):
    with app.app_context():
        book_dir = tmp_path / "books" / "queued-success"
        book_dir.mkdir(parents=True)
        pdf_path = book_dir / "original.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n")
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO books (title, original_filename, file_path, created_at, status)
            VALUES ('Queued', 'queued.pdf', ?, '2026-01-01T00:00:00+00:00', 'PROCESSING')
            """,
            (str(pdf_path),),
        )
        book_id = cursor.lastrowid
        db.execute(
            "INSERT INTO processing_jobs (book_id, status, created_at) VALUES (?, 'PENDING', '2026-01-01T00:00:00+00:00')",
            (book_id,),
        )
        db.execute(
            """
            INSERT INTO notes (book_id, page_id, page_number, selected_text, note_text, note_type, tags, created_at)
            VALUES (?, 999, 2, 'selected', 'note', 'ANOTACAO', '', '2026-01-01T00:00:00+00:00')
            """,
            (book_id,),
        )
        db.commit()

    monkeypatch.setattr(
        processing,
        "extract_pdf_pages",
        lambda _pdf_path, _assets_dir, _book_id: (
            [
                {"page_number": 1, "text_content": "One", "html_content": "<p>One</p>"},
                {"page_number": 2, "text_content": "Two", "html_content": "<p>Two</p>"},
            ],
            [{"title": "Chapter 1. One", "slug": "chapter-1", "level": 1, "start_page": 1, "end_page": 2}],
        ),
    )

    assert processing.process_next_job() is True
    assert processing.process_next_job() is False

    with app.app_context():
        db = get_db()
        book = db.execute("SELECT status, processed_at FROM books WHERE id = ?", (book_id,)).fetchone()
        job = db.execute("SELECT status, error_message FROM processing_jobs WHERE book_id = ?", (book_id,)).fetchone()
        note = db.execute("SELECT page_id FROM notes WHERE book_id = ?", (book_id,)).fetchone()
        assert book["status"] == "READY"
        assert book["processed_at"] is not None
        assert job["status"] == "DONE"
        assert job["error_message"] is None
        assert db.execute("SELECT COUNT(*) AS total FROM pages WHERE book_id = ?", (book_id,)).fetchone()["total"] == 2
        assert note["page_id"] != 999


def test_process_next_job_marks_book_failed_when_pdf_is_missing(app, tmp_path):
    with app.app_context():
        missing_pdf = tmp_path / "books" / "missing" / "original.pdf"
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO books (title, original_filename, file_path, created_at, status)
            VALUES ('Missing', 'missing.pdf', ?, '2026-01-01T00:00:00+00:00', 'PROCESSING')
            """,
            (str(missing_pdf),),
        )
        book_id = cursor.lastrowid
        db.execute(
            "INSERT INTO processing_jobs (book_id, status, created_at) VALUES (?, 'PENDING', '2026-01-01T00:00:00+00:00')",
            (book_id,),
        )
        db.commit()

    assert processing.process_next_job() is True

    with app.app_context():
        book = get_db().execute("SELECT status, processing_error FROM books WHERE id = ?", (book_id,)).fetchone()
        job = get_db().execute("SELECT status, error_message FROM processing_jobs WHERE book_id = ?", (book_id,)).fetchone()
        assert book["status"] == "FAILED"
        assert "PDF original nao encontrado" in book["processing_error"]
        assert job["status"] == "FAILED"
        assert "PDF original nao encontrado" in job["error_message"]
