import json
import shutil
import time
import uuid
from pathlib import Path

import fitz
from flask import Blueprint, Response, abort, jsonify, redirect, render_template, request, send_file, send_from_directory, url_for

from studypdf.config import (
    ALLOWED_EXTENSIONS,
    BOOKS_DIR,
    BOOK_STATUS_PROCESSING,
    BOOK_STATUS_READY,
    JOB_STATUS_PENDING,
    NOTE_TYPES,
)
from studypdf.db import get_db, open_db, row_to_dict
from studypdf.domain.reader import build_chapter_nav, percent_read, real_chapter_ranges, sanitize_reader_html
from studypdf.pdf.extractor import extract_pdf_pages
from studypdf.services.books import (
    book_chapters,
    book_pages,
    delete_book_record,
    get_book_or_404,
    is_book_ready,
    page_count,
    reset_book_reading_data,
    shelf_books,
)
from studypdf.services.processing import mark_book_ready, process_next_job, refresh_note_page_links, replace_book_content, reset_assets_dir
from studypdf.services.understanding import book_understanding_checks, save_understanding_check
from studypdf.time_utils import now_iso

books_bp = Blueprint("books", __name__)


def wants_json_response():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@books_bp.route("/books")
def books():
    return render_template("books.html", books=shelf_books())


@books_bp.post("/books/upload")
def upload_book():
    uploaded = request.files.get("pdf")
    if not uploaded or uploaded.filename == "":
        abort(400, "Envie um arquivo PDF.")

    original_filename = uploaded.filename
    if Path(original_filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        abort(400, "Apenas arquivos PDF sao aceitos.")

    title = request.form.get("title", "").strip() or Path(original_filename).stem
    author = request.form.get("author", "").strip() or None
    return save_uploaded_book(uploaded, original_filename, title, author)


def save_uploaded_book(uploaded, original_filename, title, author):
    storage_id = uuid.uuid4().hex
    book_dir = BOOKS_DIR / storage_id
    book_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = book_dir / "original.pdf"
    try:
        book_id = create_processing_book(uploaded, original_filename, title, author, pdf_path)
    except (fitz.FileDataError, fitz.EmptyFileError):
        cleanup_failed_upload(book_dir)
        abort(400, "Nao foi possivel abrir o PDF. O arquivo pode estar corrompido, vazio ou protegido por senha.")
    except Exception:
        cleanup_failed_upload(book_dir)
        raise

    redirect_url = url_for("books.books")
    if wants_json_response():
        return jsonify({"status": "queued", "book_id": book_id, "redirect_url": redirect_url})
    return redirect(redirect_url)


def create_processing_book(uploaded, original_filename, title, author, pdf_path):
    db = get_db()
    uploaded.save(pdf_path)
    cursor = db.execute(
        """
        INSERT INTO books
            (title, author, original_filename, file_path, created_at, status, processing_error)
        VALUES (?, ?, ?, ?, ?, ?, NULL)
        """,
        (title, author, original_filename, str(pdf_path), now_iso(), BOOK_STATUS_PROCESSING),
    )
    book_id = cursor.lastrowid
    db.execute(
        """
        INSERT INTO processing_jobs (book_id, status, created_at)
        VALUES (?, ?, ?)
        """,
        (book_id, JOB_STATUS_PENDING, now_iso()),
    )
    db.commit()
    return book_id


def cleanup_failed_upload(book_dir):
    get_db().rollback()
    if book_dir.exists():
        shutil.rmtree(book_dir)


@books_bp.delete("/api/books/<int:book_id>")
def api_delete_book(book_id):
    delete_book_record(book_id)
    return jsonify({"status": "deleted"})


@books_bp.post("/books/<int:book_id>/delete")
def delete_book(book_id):
    delete_book_record(book_id)
    return redirect(url_for("books.books"))


@books_bp.post("/books/<int:book_id>/reset")
def reset_book(book_id):
    if request.form.get("confirmation") != "REINICIAR":
        abort(400, "Digite REINICIAR para confirmar a limpeza do livro.")
    reset_book_reading_data(book_id)
    return redirect(url_for("books.read_book", book_id=book_id))


@books_bp.post("/api/books/<int:book_id>/reset")
def api_reset_book(book_id):
    payload = request.get_json(force=True, silent=True) or {}
    if payload.get("confirmation") != "REINICIAR":
        abort(400, "confirmation deve ser REINICIAR.")
    reset_book_reading_data(book_id)
    return jsonify({"status": "reset", "book_id": book_id})


@books_bp.route("/books/<int:book_id>/read")
def read_book(book_id):
    book = get_book_or_404(book_id)
    if not is_book_ready(book):
        abort(409, book_not_ready_message(book))

    pages = reader_pages(book_id)
    chapters = book_chapters(book_id)
    total_pages = len(pages)
    return render_template(
        "read.html",
        book=book,
        pages=pages,
        chapters=build_chapter_nav(chapters, total_pages, book["last_page_read"]),
        chapter_start_pages={chapter["start_page"] for chapter in chapters},
        understanding_ranges=real_chapter_ranges(chapters, total_pages),
        total_pages=total_pages,
        progress_percent=percent_read(book["last_page_read"], total_pages),
        note_types=sorted(NOTE_TYPES),
    )


def book_not_ready_message(book):
    if book["status"] == BOOK_STATUS_PROCESSING:
        return "Livro ainda esta em processamento."
    return "Livro falhou no processamento."


def reader_pages(book_id):
    return [
        {**row_to_dict(page), "html_content": sanitize_reader_html(page["html_content"])}
        for page in book_pages(book_id)
    ]


@books_bp.post("/api/books/<int:book_id>/progress")
def update_progress(book_id):
    payload = progress_payload()
    total_pages = page_count(book_id)
    if total_pages <= 0:
        abort(404, "Livro sem paginas processadas.")

    page_number = min(total_pages, max(1, int(payload.get("page_number") or 1)))
    get_db().execute(
        """
        UPDATE books
        SET last_page_read = ?, last_read_at = ?
        WHERE id = ?
        """,
        (page_number, now_iso(), book_id),
    )
    get_db().commit()
    return jsonify({
        "status": "saved",
        "page_number": page_number,
        "total_pages": total_pages,
        "percent_read": percent_read(page_number, total_pages),
    })


@books_bp.get("/api/books/<int:book_id>/understanding-checks")
def understanding_checks(book_id):
    get_book_or_404(book_id)
    checks = book_understanding_checks(book_id)
    return jsonify({"checks": checks})


@books_bp.post("/api/books/<int:book_id>/understanding-checks")
def save_understanding(book_id):
    get_book_or_404(book_id)
    check_id = save_understanding_check(book_id, request.get_json(force=True, silent=True) or {})
    return jsonify({"id": check_id, "status": "saved"})


def progress_payload():
    payload = request.get_json(force=True, silent=True)
    if payload is None and request.data:
        try:
            return json.loads(request.data.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
    return payload or {}


@books_bp.route("/api/books/events")
def book_events():
    return Response(book_event_stream(), mimetype="text/event-stream")


def book_event_stream():
    last_snapshot = None
    while True:
        payload = books_event_payload()
        snapshot = json.dumps(payload, sort_keys=True)
        if snapshot != last_snapshot:
            last_snapshot = snapshot
            yield "event: books\n"
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        else:
            yield ": keepalive\n\n"
        time.sleep(2)


def books_event_payload():
    conn = open_db()
    try:
        rows = conn.execute(
            """
            SELECT
                books.id,
                books.title,
                books.status,
                books.processing_error,
                COUNT(pages.id) AS total_pages,
                COUNT(chapters.id) AS total_chapters
            FROM books
            LEFT JOIN pages ON pages.book_id = books.id
            LEFT JOIN chapters ON chapters.book_id = books.id
            GROUP BY books.id
            ORDER BY books.id
            """
        ).fetchall()
        return [book_event_item(row) for row in rows]
    finally:
        conn.close()


def book_event_item(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "status": row["status"] or BOOK_STATUS_READY,
        "processing_error": row["processing_error"],
        "total_pages": row["total_pages"],
        "total_chapters": row["total_chapters"],
    }


@books_bp.post("/cron/process-books")
def cron_process_books():
    processed = 0
    while process_next_job():
        processed += 1
    return jsonify({"status": "ok", "processed_jobs": processed})


@books_bp.post("/books/<int:book_id>/reprocess")
def reprocess_book(book_id):
    book = get_book_or_404(book_id)
    pdf_path = Path(book["file_path"])
    if not pdf_path.exists():
        abort(404, "PDF original nao encontrado.")

    assets_dir = reset_assets_dir(pdf_path)
    pages, chapters = extract_pdf_pages(pdf_path, assets_dir, book_id)
    db = get_db()
    replace_book_content(db, book_id, pages, chapters)
    mark_book_ready(db, book_id)
    refresh_note_page_links(db, book_id)
    db.commit()
    return redirect(url_for("books.read_book", book_id=book_id))


@books_bp.route("/books/<int:book_id>/original")
def original_pdf(book_id):
    book = get_book_or_404(book_id)
    return send_file(book["file_path"], mimetype="application/pdf", download_name=book["original_filename"] or "book.pdf")


@books_bp.route("/books/<int:book_id>/html")
def export_book_html(book_id):
    book = get_book_or_404(book_id)
    pages = [
        {**row_to_dict(page), "html_content": sanitize_reader_html(page["html_content"])}
        for page in book_pages(book_id)
    ]
    return render_template("book_export.html", book=book, pages=pages)


@books_bp.route("/books/<int:book_id>/assets/<path:filename>")
def book_asset(book_id, filename):
    book = get_book_or_404(book_id)
    assets_dir = Path(book["file_path"]).parent / "assets"
    return send_from_directory(assets_dir, filename)
