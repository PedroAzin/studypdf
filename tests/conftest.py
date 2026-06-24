import os

import pytest

from studypdf.db import SCHEMA_TABLES, get_db, init_db


@pytest.fixture
def app(tmp_path, monkeypatch):
    import studypdf.app_factory as app_factory
    import studypdf.db as db_module

    database_url = os.environ.get("STUDYPDF_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("Defina STUDYPDF_TEST_DATABASE_URL para rodar testes com PostgreSQL.")

    monkeypatch.setattr(db_module, "STUDYPDF_DATABASE_URL", database_url)
    monkeypatch.setattr(app_factory, "start_processing_worker", lambda _app: None)

    app = app_factory.create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        init_db()
        clear_database()
    return app


def clear_database():
    db = get_db()
    db.execute(f"TRUNCATE TABLE {', '.join(reversed(SCHEMA_TABLES))} RESTART IDENTITY CASCADE")
    db.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def ready_book(app, tmp_path):
    with app.app_context():
        return seed_ready_book(tmp_path)


def seed_ready_book(tmp_path):
    db = get_db()
    book_dir = tmp_path / "books" / "ready-book"
    book_dir.mkdir(parents=True)
    pdf_path = book_dir / "original.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%test\n")

    cursor = db.execute(
        """
        INSERT INTO books
            (title, author, original_filename, file_path, created_at, status, last_page_read)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("Designing Data-Intensive Applications", "Martin Kleppmann", "book.pdf", str(pdf_path), "2026-01-01T00:00:00+00:00", "READY", 2),
    )
    book_id = cursor.lastrowid
    pages = [
        (book_id, 1, "Preface", "<h3 class='book-subheading'>Preface topic</h3><p>Intro</p>"),
        (book_id, 2, "Chapter 1 text", "<h2 class='book-heading'>Chapter 1</h2><h3 class='book-subheading'>Reliability</h3><p>Text</p>"),
        (book_id, 3, "More chapter 1 text", "<h3 class='book-subheading'>Scalability</h3><p>Text</p>"),
        (book_id, 4, "End chapter 1", "<p>End</p>"),
        (book_id, 5, "Chapter 2 text", "<h2 class='book-heading'>Chapter 2</h2><h3 class='book-subheading'>Data Models</h3><p>Text</p>"),
        (book_id, 6, "Appendix", "<h3 class='book-subheading'>Appendix topic</h3><p>Text</p>"),
    ]
    db.executemany(
        """
        INSERT INTO pages (book_id, page_number, text_content, html_content)
        VALUES (?, ?, ?, ?)
        """,
        pages,
    )
    db.executemany(
        """
        INSERT INTO chapters (book_id, title, slug, level, start_page, end_page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (book_id, "Preface", "preface", 1, 1, 1),
            (book_id, "Chapter 1. Reliable Systems", "chapter-1", 2, 2, 4),
            (book_id, "Chapter 2. Data Models", "chapter-2", 2, 5, 6),
            (book_id, "Glossary", "glossary", 1, 6, 6),
        ],
    )
    db.commit()
    return {"id": book_id, "pdf_path": pdf_path}


def first_page_id(book_id):
    return get_db().execute(
        "SELECT id FROM pages WHERE book_id = ? ORDER BY page_number LIMIT 1",
        (book_id,),
    ).fetchone()["id"]
