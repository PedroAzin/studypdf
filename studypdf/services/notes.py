from flask import abort

from studypdf.config import NOTE_TYPES
from studypdf.db import get_db
from studypdf.domain.notes import note_form_data
from studypdf.time_utils import now_iso


def get_note_or_404(note_id):
    note = get_db().execute(
        """
        SELECT notes.*, books.title AS book_title, books.author AS book_author
        FROM notes
        JOIN books ON books.id = notes.book_id
        WHERE notes.id = ?
        """,
        (note_id,),
    ).fetchone()
    if note is None:
        abort(404)
    return note


def page_for_note(book_id, page_number):
    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        abort(400, "page_number invalido.")

    page = get_db().execute(
        "SELECT * FROM pages WHERE book_id = ? AND page_number = ?",
        (book_id, page_number),
    ).fetchone()
    if page is None:
        abort(404, "Pagina nao encontrada.")
    return page


def validate_note_fields(data):
    if not data["page_number"] or not data["selected_text"]:
        abort(400, "page_number e selected_text sao obrigatorios.")
    if data["note_type"] not in NOTE_TYPES:
        abort(400, "note_type invalido.")


def create_note(book_id, source):
    data = note_form_data(source)
    validate_note_fields(data)
    page = page_for_note(book_id, data["page_number"])
    cursor = get_db().execute(
        """
        INSERT INTO notes
            (book_id, page_id, page_number, selected_text, note_text, note_type, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        note_values(book_id, page, data),
    )
    get_db().commit()
    return cursor.lastrowid


def update_note(note_id, source):
    note = get_note_or_404(note_id)
    data = note_form_data(source)
    validate_note_fields(data)
    page = page_for_note(note["book_id"], data["page_number"])
    get_db().execute(
        """
        UPDATE notes
        SET page_id = ?,
            page_number = ?,
            selected_text = ?,
            note_text = ?,
            note_type = ?,
            tags = ?,
            updated_at = ?
        WHERE id = ?
        """,
        update_values(page, data, note_id),
    )
    get_db().commit()
    return note


def delete_note(note_id):
    note = get_note_or_404(note_id)
    get_db().execute("DELETE FROM notes WHERE id = ?", (note_id,))
    get_db().commit()
    return note


def merge_note_payload(note, payload):
    return {
        "page_number": payload.get("page_number", note["page_number"]),
        "selected_text": payload.get("selected_text", note["selected_text"]),
        "note_type": payload.get("note_type", note["note_type"]),
        "note_text": payload.get("note_text", note["note_text"] or ""),
        "tags": payload.get("tags", note["tags"] or ""),
    }


def note_values(book_id, page, data):
    timestamp = now_iso()
    return (
        book_id,
        page["id"],
        page["page_number"],
        data["selected_text"],
        data["note_text"],
        data["note_type"],
        data["tags"],
        timestamp,
        timestamp,
    )


def update_values(page, data, note_id):
    return (
        page["id"],
        page["page_number"],
        data["selected_text"],
        data["note_text"],
        data["note_type"],
        data["tags"],
        now_iso(),
        note_id,
    )
