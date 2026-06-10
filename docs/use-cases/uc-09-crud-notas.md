# UC-09 - CRUD de notas

## Objetivo

Permitir criar, consultar, editar e remover notas tanto por telas HTML quanto por API.

## Ator

Usuario leitor.

## Fluxo principal - telas

1. Usuario acessa `/books/<book_id>/notes`.
2. Sistema lista notas do livro.
3. Usuario clica em `Nova nota`, `Abrir`, `Editar` ou `Remover`.
4. Sistema cria, exibe, atualiza ou remove a nota.
5. Remocao redireciona para a lista do livro.

## Fluxo principal - API

1. Cliente cria nota com `POST /api/notes`.
2. Cliente consulta com `GET /api/notes/<note_id>`.
3. Cliente atualiza com `PATCH /api/notes/<note_id>`.
4. Cliente remove com `DELETE /api/notes/<note_id>`.

## Rotas

- `GET /books/<book_id>/notes`
- `GET /books/<book_id>/notes/new`
- `POST /books/<book_id>/notes`
- `GET /notes/<note_id>`
- `GET /notes/<note_id>/edit`
- `POST /notes/<note_id>/edit`
- `POST /notes/<note_id>/delete`
- `POST /api/notes`
- `GET /api/notes/<note_id>`
- `PATCH /api/notes/<note_id>`
- `DELETE /api/notes/<note_id>`

## Modulos envolvidos

- `studypdf/routes/notes.py`
- `studypdf/services/notes.py`
- `studypdf/domain/notes.py`
- `templates/notes.html`
- `templates/note_form.html`
- `templates/note_detail.html`

## Campos

- `book_id`
- `page_id`
- `page_number`
- `selected_text`
- `note_text`
- `note_type`
- `tags`
- `created_at`
- `updated_at`

