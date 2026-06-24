from studypdf.db import get_db


def test_note_crud_api_search_and_export(client, app, ready_book):
    book_id = ready_book["id"]
    create_response = client.post(
        "/api/notes",
        json={
            "book_id": book_id,
            "page_number": 2,
            "selected_text": "Chapter 1 text",
            "note_type": "ANOTACAO",
            "note_text": "Important distributed systems note",
            "tags": ["distributed", "systems"],
        },
    )
    assert create_response.status_code == 200
    note_id = create_response.get_json()["id"]

    get_response = client.get(f"/api/notes/{note_id}")
    assert get_response.status_code == 200
    assert get_response.get_json()["note_type"] == "ANOTACAO"

    patch_response = client.patch(f"/api/notes/{note_id}", json={"note_type": "DESTAQUE", "note_text": "Updated note"})
    assert patch_response.status_code == 200

    search_response = client.get("/api/search?q=Updated")
    assert search_response.status_code == 200
    assert search_response.get_json()["results"][0]["id"] == note_id

    export_response = client.get(f"/api/notes/{note_id}/export")
    assert export_response.status_code == 200
    assert "Updated note" in export_response.get_data(as_text=True)

    delete_response = client.delete(f"/api/notes/{note_id}")
    assert delete_response.status_code == 200
    with app.app_context():
        assert get_db().execute("SELECT id FROM notes WHERE id = ?", (note_id,)).fetchone() is None


def test_note_form_flow_redirects_to_detail(client, ready_book):
    response = client.post(
        f"/books/{ready_book['id']}/notes",
        data={
            "page_number": "2",
            "selected_text": "Chapter 1 text",
            "note_type": "DUVIDA",
            "note_text": "What does this imply?",
            "tags": "question",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/notes/")


def test_understanding_check_persists_review_and_updates_same_topic(client, app, ready_book, monkeypatch):
    monkeypatch.setattr("studypdf.routes.books.FEATURE_UNDERSTANDING_CHECKS", True)

    book_id = ready_book["id"]
    first_response = client.post(
        f"/api/books/{book_id}/understanding-checks",
        json={
            "topic_key": "topic-1-page-2",
            "topic_title": "Reliability",
            "page_number": 2,
            "confidence": 2,
            "summary": "short",
            "doubt": "I do not understand failure handling.",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f"/api/books/{book_id}/understanding-checks",
        json={
            "topic_key": "topic-1-page-2",
            "topic_title": "Reliability",
            "page_number": 2,
            "confidence": 5,
            "summary": "The topic explains how reliability depends on handling faults without turning them into user-visible failures.",
            "doubt": "",
        },
    )
    assert second_response.status_code == 200
    assert second_response.get_json()["id"] == first_response.get_json()["id"]

    list_response = client.get(f"/api/books/{book_id}/understanding-checks")
    assert list_response.status_code == 200
    checks = list_response.get_json()["checks"]
    assert len(checks) == 1
    assert checks[0]["status"] == "UNDERSTOOD"

    with app.app_context():
        total = get_db().execute("SELECT COUNT(*) AS total FROM understanding_checks WHERE book_id = ?", (book_id,)).fetchone()["total"]
        assert total == 1


def test_understanding_check_requires_topic_identity(client, ready_book, monkeypatch):
    monkeypatch.setattr("studypdf.routes.books.FEATURE_UNDERSTANDING_CHECKS", True)

    response = client.post(
        f"/api/books/{ready_book['id']}/understanding-checks",
        json={"topic_key": "", "topic_title": "", "page_number": 2, "confidence": 3},
    )

    assert response.status_code == 400


def test_understanding_check_api_is_disabled_by_default(client, ready_book):
    get_response = client.get(f"/api/books/{ready_book['id']}/understanding-checks")
    post_response = client.post(
        f"/api/books/{ready_book['id']}/understanding-checks",
        json={"topic_key": "topic-1", "topic_title": "Topic", "page_number": 2, "confidence": 3},
    )

    assert get_response.status_code == 404
    assert post_response.status_code == 404
