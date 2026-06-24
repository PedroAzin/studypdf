from flask import abort

from studypdf.config import BOOK_STATUS_READY, BOOK_STATUS_PROCESSING, BOOK_STATUS_FAILED
from studypdf.db import get_db, row_to_dict
from studypdf.domain.reader import percent_read, visible_book_chapters
from studypdf.storage import delete_prefix


def get_book_or_404(book_id):
    book = get_db().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if book is None:
        abort(404)
    return book


def is_book_ready(book):
    return (book["status"] or BOOK_STATUS_READY) == BOOK_STATUS_READY


def delete_book_files(book):
    storage_prefix = storage_prefix_for_book(book)
    if storage_prefix:
        delete_prefix(storage_prefix)


def storage_prefix_for_book(book):
    parts = (book["file_path"] or "").split("/")
    return "/".join(parts[:2]) if len(parts) >= 2 else ""


def delete_book_record(book_id):
    book = get_book_or_404(book_id)
    db = get_db()
    db.execute("DELETE FROM understanding_checks WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM notes WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM pages WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM processing_jobs WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    delete_book_files(book)


def reset_book_reading_data(book_id):
    get_book_or_404(book_id)
    db = get_db()
    db.execute("DELETE FROM understanding_checks WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM notes WHERE book_id = ?", (book_id,))
    db.execute(
        """
        UPDATE books
        SET last_page_read = 1,
            last_read_at = NULL
        WHERE id = ?
        """,
        (book_id,),
    )
    db.commit()


def shelf_books():
    rows = get_db().execute(
        """
        SELECT
            books.*,
            COUNT(DISTINCT pages.id) AS total_pages,
            COUNT(DISTINCT chapters.id) AS total_chapters,
            COUNT(DISTINCT notes.id) AS total_notes,
            COUNT(DISTINCT CASE WHEN notes.note_type = 'DESTAQUE' THEN notes.id END) AS total_highlights
        FROM books
        LEFT JOIN pages ON pages.book_id = books.id
        LEFT JOIN chapters ON chapters.book_id = books.id
        LEFT JOIN notes ON notes.book_id = books.id
        GROUP BY books.id
        ORDER BY COALESCE(books.last_read_at, books.created_at) DESC
        """
    ).fetchall()
    return [shelf_book(row) for row in rows]


def shelf_book(row):
    item = row_to_dict(row)
    item["status"] = item.get("status") or BOOK_STATUS_READY
    item["is_ready"] = item["status"] == BOOK_STATUS_READY
    item["is_processing"] = item["status"] == BOOK_STATUS_PROCESSING
    item["is_failed"] = item["status"] == BOOK_STATUS_FAILED
    item["percent_read"] = percent_read(item.get("last_page_read"), item.get("total_pages"))
    item["chapters"] = visible_book_chapters(book_chapters(item["id"]), total_pages=item.get("total_pages"), limit=5)
    return item


def book_chapters(book_id):
    return get_db().execute(
        """
        SELECT *
        FROM chapters
        WHERE book_id = ?
        ORDER BY start_page, level
        """,
        (book_id,),
    ).fetchall()


def book_pages(book_id):
    return get_db().execute(
        "SELECT * FROM pages WHERE book_id = ? ORDER BY page_number",
        (book_id,),
    ).fetchall()


def page_count(book_id):
    return get_db().execute(
        "SELECT COUNT(*) AS total FROM pages WHERE book_id = ?",
        (book_id,),
    ).fetchone()["total"]
