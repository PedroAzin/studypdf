import io
import json

from bs4 import BeautifulSoup

from studypdf.db import get_db


def test_books_page_lists_ready_book_with_progress(client, ready_book):
    response = client.get("/books")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Designing Data-Intensive Applications" in html
    assert "Continuar" in html


def test_upload_rejects_non_pdf_file(client):
    response = client.post(
        "/books/upload",
        data={"pdf": (io.BytesIO(b"not a pdf"), "book.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "Apenas arquivos PDF" in response.get_data(as_text=True)


def test_upload_queues_pdf_and_redirects_to_shelf(client, app):
    response = client.post(
        "/books/upload",
        data={"title": "Queued Book", "author": "Author", "pdf": (io.BytesIO(b"%PDF-1.4"), "book.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/books"
    with app.app_context():
        book = get_db().execute("SELECT * FROM books WHERE title = ?", ("Queued Book",)).fetchone()
        job = get_db().execute("SELECT * FROM processing_jobs WHERE book_id = ?", (book["id"],)).fetchone()
        assert book["status"] == "PROCESSING"
        assert job["status"] == "PENDING"


def test_reader_hides_understanding_checks_when_feature_is_disabled(client, ready_book):
    response = client.get(f"/books/{ready_book['id']}/read")

    assert response.status_code == 200
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    reader = soup.select_one(".reader")
    assert reader["data-understanding-enabled"] == "0"
    assert json.loads(reader["data-understanding-ranges"]) == []
    assert soup.select_one("[data-understanding-check]") is None


def test_reader_exposes_only_real_chapter_ranges_for_understanding_checks(client, ready_book, monkeypatch):
    monkeypatch.setattr("studypdf.routes.books.FEATURE_UNDERSTANDING_CHECKS", True)

    response = client.get(f"/books/{ready_book['id']}/read")

    assert response.status_code == 200
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    reader = soup.select_one(".reader")
    assert reader["data-understanding-enabled"] == "1"
    ranges = json.loads(reader["data-understanding-ranges"])
    assert [item["title"] for item in ranges] == [
        "Chapter 1. Reliable Systems",
        "Chapter 2. Data Models",
    ]
    assert ranges[0]["start_page"] == 2
    assert ranges[0]["end_page"] == 4


def test_progress_is_clamped_when_page_is_above_total(client, app, ready_book):
    response = client.post(f"/api/books/{ready_book['id']}/progress", json={"page_number": 999})

    assert response.status_code == 200
    assert response.get_json()["page_number"] == 6
    with app.app_context():
        book = get_db().execute("SELECT last_page_read FROM books WHERE id = ?", (ready_book["id"],)).fetchone()
        assert book["last_page_read"] == 6


def test_reset_requires_confirmation_and_cleans_study_data(client, app, ready_book):
    book_id = ready_book["id"]
    with app.app_context():
        page_id = get_db().execute("SELECT id FROM pages WHERE book_id = ? LIMIT 1", (book_id,)).fetchone()["id"]
        get_db().execute(
            """
            INSERT INTO notes (book_id, page_id, page_number, selected_text, note_text, note_type, tags, created_at)
            VALUES (?, ?, 1, 'selected', 'note', 'ANOTACAO', '', '2026-01-01T00:00:00+00:00')
            """,
            (book_id, page_id),
        )
        get_db().execute(
            """
            INSERT INTO understanding_checks
                (book_id, topic_key, topic_title, page_number, confidence, summary, doubt, status, created_at)
            VALUES (?, 'topic-1', 'Topic', 2, 2, 'short', 'doubt', 'REVIEW', '2026-01-01T00:00:00+00:00')
            """,
            (book_id,),
        )
        get_db().execute("UPDATE books SET last_page_read = 4, last_read_at = '2026-01-01T00:00:00+00:00' WHERE id = ?", (book_id,))
        get_db().commit()

    bad_response = client.post(f"/api/books/{book_id}/reset", json={"confirmation": "SIM"})
    assert bad_response.status_code == 400

    response = client.post(f"/api/books/{book_id}/reset", json={"confirmation": "REINICIAR"})
    assert response.status_code == 200
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) AS total FROM notes WHERE book_id = ?", (book_id,)).fetchone()["total"] == 0
        assert db.execute("SELECT COUNT(*) AS total FROM understanding_checks WHERE book_id = ?", (book_id,)).fetchone()["total"] == 0
        book = db.execute("SELECT last_page_read, last_read_at FROM books WHERE id = ?", (book_id,)).fetchone()
        assert book["last_page_read"] == 1
        assert book["last_read_at"] is None
