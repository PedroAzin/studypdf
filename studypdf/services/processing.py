import shutil
import threading
import time
from pathlib import Path

from studypdf.config import (
    BOOK_STATUS_FAILED,
    BOOK_STATUS_PROCESSING,
    BOOK_STATUS_READY,
    JOB_POLL_SECONDS,
    JOB_STATUS_DONE,
    JOB_STATUS_FAILED,
    JOB_STATUS_PENDING,
    JOB_STATUS_RUNNING,
)
from studypdf.db import open_db
from studypdf.pdf.extractor import extract_pdf_pages
from studypdf.time_utils import now_iso

worker_started = False


def process_book_with_connection(conn, book_id):
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if book is None:
        raise RuntimeError(f"Livro nao encontrado: {book_id}")

    pdf_path = Path(book["file_path"])
    if not pdf_path.exists():
        raise FileNotFoundError("PDF original nao encontrado.")

    assets_dir = reset_assets_dir(pdf_path)
    pages, chapters = extract_pdf_pages(pdf_path, assets_dir, book_id)
    replace_book_content(conn, book_id, pages, chapters)
    mark_book_ready(conn, book_id)
    refresh_note_page_links(conn, book_id)


def reset_assets_dir(pdf_path):
    assets_dir = pdf_path.parent / "assets"
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    return assets_dir


def replace_book_content(conn, book_id, pages, chapters):
    conn.execute("DELETE FROM pages WHERE book_id = ?", (book_id,))
    conn.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))
    conn.execute("DELETE FROM understanding_checks WHERE book_id = ?", (book_id,))
    conn.executemany(
        """
        INSERT INTO pages (book_id, page_number, text_content, html_content)
        VALUES (?, ?, ?, ?)
        """,
        [(book_id, page["page_number"], page["text_content"], page["html_content"]) for page in pages],
    )
    conn.executemany(
        """
        INSERT INTO chapters (book_id, title, slug, level, start_page, end_page)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (book_id, chapter["title"], chapter["slug"], chapter["level"], chapter["start_page"], chapter["end_page"])
            for chapter in chapters
        ],
    )


def mark_book_ready(conn, book_id):
    conn.execute(
        """
        UPDATE books
        SET status = ?, processing_error = NULL, processed_at = ?, last_page_read = COALESCE(last_page_read, 1)
        WHERE id = ?
        """,
        (BOOK_STATUS_READY, now_iso(), book_id),
    )


def refresh_note_page_links(conn, book_id):
    conn.execute(
        """
        UPDATE notes
        SET page_id = (
            SELECT pages.id
            FROM pages
            WHERE pages.book_id = notes.book_id
              AND pages.page_number = notes.page_number
        ),
        updated_at = ?
        WHERE book_id = ?
        """,
        (now_iso(), book_id),
    )


def process_next_job():
    conn = open_db()
    try:
        job = claim_next_job(conn)
        if job is None:
            return False
        run_claimed_job(conn, job)
        return True
    finally:
        conn.close()


def claim_next_job(conn):
    conn.execute("BEGIN IMMEDIATE")
    job = conn.execute(
        """
        SELECT * FROM processing_jobs
        WHERE status = ?
        ORDER BY created_at
        LIMIT 1
        """,
        (JOB_STATUS_PENDING,),
    ).fetchone()
    if job is None:
        conn.commit()
        return None

    conn.execute(
        """
        UPDATE processing_jobs
        SET status = ?, started_at = ?
        WHERE id = ?
        """,
        (JOB_STATUS_RUNNING, now_iso(), job["id"]),
    )
    conn.execute(
        "UPDATE books SET status = ?, processing_error = NULL WHERE id = ?",
        (BOOK_STATUS_PROCESSING, job["book_id"]),
    )
    conn.commit()
    return job


def run_claimed_job(conn, job):
    try:
        process_book_with_connection(conn, job["book_id"])
        mark_job_done(conn, job["id"])
    except Exception as exc:
        conn.rollback()
        mark_job_failed(conn, job, str(exc)[:500])


def mark_job_done(conn, job_id):
    conn.execute(
        """
        UPDATE processing_jobs
        SET status = ?, finished_at = ?, error_message = NULL
        WHERE id = ?
        """,
        (JOB_STATUS_DONE, now_iso(), job_id),
    )
    conn.commit()


def mark_job_failed(conn, job, message):
    conn.execute(
        """
        UPDATE books
        SET status = ?, processing_error = ?
        WHERE id = ?
        """,
        (BOOK_STATUS_FAILED, message, job["book_id"]),
    )
    conn.execute(
        """
        UPDATE processing_jobs
        SET status = ?, finished_at = ?, error_message = ?
        WHERE id = ?
        """,
        (JOB_STATUS_FAILED, now_iso(), message, job["id"]),
    )
    conn.commit()


def processing_worker(app):
    while True:
        try:
            processed = process_next_job()
        except Exception:
            app.logger.exception("Erro no worker de processamento")
            processed = False
        if not processed:
            time.sleep(JOB_POLL_SECONDS)


def start_processing_worker(app):
    global worker_started
    if worker_started:
        return
    worker_started = True
    thread = threading.Thread(target=processing_worker, args=(app,), daemon=True)
    thread.start()
