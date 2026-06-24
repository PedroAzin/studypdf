import os
from pathlib import Path

import pytest

from studypdf.db import SCHEMA_TABLES, get_db, init_db, insert_returning_id


@pytest.fixture
def app(tmp_path, monkeypatch):
    import studypdf.app_factory as app_factory
    import studypdf.db as db_module
    import studypdf.routes.books as books_routes
    import studypdf.services.books as books_service
    import studypdf.services.processing as processing_service

    database_url = os.environ.get("STUDYPDF_TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("Defina STUDYPDF_TEST_DATABASE_URL para rodar testes com PostgreSQL.")

    monkeypatch.setattr(db_module, "STUDYPDF_DATABASE_URL", database_url)
    monkeypatch.setattr(books_routes, "STUDYPDF_CRON_TOKEN", "test-cron-token")
    monkeypatch.setattr(app_factory, "start_processing_worker", lambda _app: None)
    storage_objects = {}
    install_storage_fake(monkeypatch, books_routes, books_service, processing_service, storage_objects)

    app = app_factory.create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    app.config["TEST_STORAGE_OBJECTS"] = storage_objects
    with app.app_context():
        init_db()
        clear_database()
    return app


def install_storage_fake(monkeypatch, books_routes, books_service, processing_service, storage_objects):
    def upload_bytes(key, content, content_type="application/octet-stream"):
        storage_objects[key] = bytes(content)
        return key

    def upload_file(key, path, content_type=None):
        storage_objects[key] = Path(path).read_bytes()
        return key

    def download_bytes(key):
        if key not in storage_objects:
            raise FileNotFoundError("PDF original nao encontrado.")
        return storage_objects[key]

    def download_file(key, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(download_bytes(key))
        return path

    def delete_keys(keys):
        for key in keys:
            storage_objects.pop(key, None)

    def delete_prefix(prefix):
        for key in list(storage_objects):
            if key.startswith(prefix):
                storage_objects.pop(key, None)

    monkeypatch.setattr(books_routes, "upload_bytes", upload_bytes)
    monkeypatch.setattr(books_routes, "upload_file", upload_file)
    monkeypatch.setattr(books_routes, "download_bytes", download_bytes)
    monkeypatch.setattr(books_routes, "download_file", download_file)
    monkeypatch.setattr(books_routes, "delete_keys", delete_keys)
    monkeypatch.setattr(books_service, "delete_prefix", delete_prefix)
    monkeypatch.setattr(processing_service, "download_file", download_file)
    monkeypatch.setattr(processing_service, "upload_file", upload_file)


def clear_database():
    db = get_db()
    db.execute(f"TRUNCATE TABLE {', '.join(reversed(SCHEMA_TABLES))} RESTART IDENTITY CASCADE")
    db.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def ready_book(app):
    with app.app_context():
        return seed_ready_book(app.config["TEST_STORAGE_OBJECTS"])


def seed_ready_book(storage_objects):
    db = get_db()
    storage_key = "books/ready-book/original.pdf"
    storage_objects[storage_key] = b"%PDF-1.4\n%test\n"

    book_id = insert_returning_id(
        db,
        """
        INSERT INTO books
            (title, author, original_filename, file_path, created_at, status, last_page_read)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Designing Data-Intensive Applications",
            "Martin Kleppmann",
            "book.pdf",
            storage_key,
            "2026-01-01T00:00:00+00:00",
            "READY",
            2,
        ),
    )
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
    return {"id": book_id, "storage_key": storage_key}


def first_page_id(book_id):
    return get_db().execute(
        "SELECT id FROM pages WHERE book_id = ? ORDER BY page_number LIMIT 1",
        (book_id,),
    ).fetchone()["id"]
