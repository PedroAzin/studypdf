from flask import abort

from studypdf.db import get_db, insert_returning_id, row_to_dict
from studypdf.domain.understanding import normalize_check_payload
from studypdf.time_utils import now_iso


def book_understanding_checks(book_id):
    rows = get_db().execute(
        """
        SELECT *
        FROM understanding_checks
        WHERE book_id = ?
        ORDER BY page_number, topic_title
        """,
        (book_id,),
    ).fetchall()
    return [row_to_dict(row) for row in rows]


def save_understanding_check(book_id, payload):
    data = normalize_check_payload(payload)
    validate_check_data(data)
    existing = check_by_topic(book_id, data["topic_key"])
    if existing:
        update_check(existing["id"], data)
        return existing["id"]
    return insert_check(book_id, data)


def validate_check_data(data):
    if not data["topic_key"] or not data["topic_title"]:
        abort(400, "topic_key e topic_title sao obrigatorios.")


def check_by_topic(book_id, topic_key):
    return get_db().execute(
        """
        SELECT *
        FROM understanding_checks
        WHERE book_id = ? AND topic_key = ?
        """,
        (book_id, topic_key),
    ).fetchone()


def insert_check(book_id, data):
    db = get_db()
    check_id = insert_returning_id(
        db,
        """
        INSERT INTO understanding_checks
            (book_id, topic_key, topic_title, page_number, confidence, summary, doubt, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            book_id,
            data["topic_key"],
            data["topic_title"],
            data["page_number"],
            data["confidence"],
            data["summary"],
            data["doubt"],
            data["status"],
            now_iso(),
            now_iso(),
        ),
    )
    db.commit()
    return check_id


def update_check(check_id, data):
    get_db().execute(
        """
        UPDATE understanding_checks
        SET topic_title = ?,
            page_number = ?,
            confidence = ?,
            summary = ?,
            doubt = ?,
            status = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            data["topic_title"],
            data["page_number"],
            data["confidence"],
            data["summary"],
            data["doubt"],
            data["status"],
            now_iso(),
            check_id,
        ),
    )
    get_db().commit()
