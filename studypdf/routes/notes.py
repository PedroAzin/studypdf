from flask import Blueprint, Response, abort, jsonify, redirect, render_template, request, url_for

from studypdf.config import NOTE_TYPES
from studypdf.db import get_db, row_to_dict
from studypdf.domain.notes import note_type_options, selected_context
from studypdf.services.books import get_book_or_404
from studypdf.services.notes import create_note as create_note_record
from studypdf.services.notes import delete_note, get_note_or_404, merge_note_payload, update_note

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/books/<int:book_id>/notes", methods=["GET"])
def book_notes(book_id):
    book = get_book_or_404(book_id)
    notes = get_db().execute(
        """
        SELECT * FROM notes
        WHERE book_id = ?
        ORDER BY created_at DESC
        """,
        (book_id,),
    ).fetchall()
    return render_template("notes.html", book=book, notes=notes)


@notes_bp.route("/books/<int:book_id>/notes/new", methods=["GET"])
def new_note(book_id):
    book = get_book_or_404(book_id)
    return render_template(
        "note_form.html",
        mode="create",
        book=book,
        note=empty_note(book),
        pages=book_page_options(book_id),
        note_types=note_type_options(NOTE_TYPES),
    )


def empty_note(book):
    return {
        "id": None,
        "book_id": book["id"],
        "page_number": request.args.get("page", book["last_page_read"] or 1),
        "selected_text": "",
        "note_text": "",
        "note_type": "ANOTACAO",
        "tags": "",
    }


def book_page_options(book_id):
    return get_db().execute(
        "SELECT page_number FROM pages WHERE book_id = ? ORDER BY page_number",
        (book_id,),
    ).fetchall()


@notes_bp.post("/books/<int:book_id>/notes")
def create_note_form(book_id):
    get_book_or_404(book_id)
    note_id = create_note_record(book_id, request.form)
    return redirect(url_for("notes.note_detail", note_id=note_id))


@notes_bp.route("/books/<int:book_id>/highlights", methods=["GET"])
def book_highlights(book_id):
    book = get_book_or_404(book_id)
    highlights = get_db().execute(
        """
        SELECT * FROM notes
        WHERE book_id = ? AND note_type = 'DESTAQUE'
        ORDER BY page_number, created_at
        """,
        (book_id,),
    ).fetchall()
    return render_template("highlights.html", book=book, highlights=highlights)


@notes_bp.route("/notes/<int:note_id>", methods=["GET"])
def note_detail(note_id):
    return render_template("note_detail.html", note=get_note_or_404(note_id))


@notes_bp.route("/notes/<int:note_id>/edit", methods=["GET"])
def edit_note(note_id):
    note = get_note_or_404(note_id)
    book = get_book_or_404(note["book_id"])
    return render_template(
        "note_form.html",
        mode="edit",
        book=book,
        note=note,
        pages=book_page_options(note["book_id"]),
        note_types=note_type_options(NOTE_TYPES),
    )


@notes_bp.post("/notes/<int:note_id>/edit")
def update_note_form(note_id):
    update_note(note_id, request.form)
    return redirect(url_for("notes.note_detail", note_id=note_id))


@notes_bp.post("/notes/<int:note_id>/delete")
def delete_note_form(note_id):
    note = delete_note(note_id)
    return redirect(url_for("notes.book_notes", book_id=note["book_id"]))


@notes_bp.post("/api/notes")
def create_note():
    payload = request.get_json(force=True, silent=True) or {}
    book_id = payload.get("book_id")
    if not book_id:
        abort(400, "book_id, page_number e selected_text sao obrigatorios.")
    note_id = create_note_record(book_id, payload)
    return jsonify({"id": note_id, "status": "saved"})


@notes_bp.get("/api/notes/<int:note_id>")
def api_note(note_id):
    return jsonify(row_to_dict(get_note_or_404(note_id)))


@notes_bp.patch("/api/notes/<int:note_id>")
def patch_note(note_id):
    note = get_note_or_404(note_id)
    update_note(note_id, merge_note_payload(note, request.get_json(force=True, silent=True) or {}))
    return jsonify({"id": note_id, "status": "updated"})


@notes_bp.delete("/api/notes/<int:note_id>")
def delete_api_note(note_id):
    delete_note(note_id)
    return jsonify({"id": note_id, "status": "deleted"})


@notes_bp.route("/api/search", methods=["GET"])
def api_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"query": query, "results": []})
    return jsonify({"query": query, "results": search_notes(query)})


def search_notes(query):
    pattern = f"%{query}%"
    rows = get_db().execute(
        """
        SELECT
            notes.id,
            notes.book_id,
            notes.page_number,
            notes.selected_text,
            notes.note_text,
            notes.note_type,
            notes.tags,
            notes.created_at,
            books.title AS book_title
        FROM notes
        JOIN books ON books.id = notes.book_id
        WHERE notes.selected_text LIKE ?
           OR notes.note_text LIKE ?
           OR notes.tags LIKE ?
           OR books.title LIKE ?
        ORDER BY notes.created_at DESC
        LIMIT 100
        """,
        (pattern, pattern, pattern, pattern),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


@notes_bp.route("/api/notes/<int:note_id>/export", methods=["GET"])
def export_note(note_id):
    note = export_note_record(note_id)
    before, after = selected_context(note["text_content"], note["selected_text"])
    markdown = render_template("export_note.md", note=note, before=before, after=after)
    return Response(markdown, mimetype="text/markdown; charset=utf-8", headers=export_headers(note_id))


def export_note_record(note_id):
    note = get_db().execute(
        """
        SELECT notes.*, books.title AS book_title, books.author AS book_author, pages.text_content
        FROM notes
        JOIN books ON books.id = notes.book_id
        JOIN pages ON pages.id = notes.page_id
        WHERE notes.id = ?
        """,
        (note_id,),
    ).fetchone()
    if note is None:
        abort(404)
    return note


def export_headers(note_id):
    return {"Content-Disposition": f"attachment; filename=note-{note_id}-ia.md"}
