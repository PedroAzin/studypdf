# UC-13 - Remover livro

## Objetivo

Excluir um livro e todos os dados relacionados.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario clica em `Remover` na estante.
2. Sistema confirma a intencao no navegador.
3. Backend remove notas, paginas, capitulos, jobs e livro.
4. Backend remove objetos do livro no Supabase Storage.
5. Usuario retorna para `/books`.

## Rotas

- `POST /books/<book_id>/delete`
- `DELETE /api/books/<book_id>`

## Modulos envolvidos

- `studypdf/routes/books.py`
- `studypdf/services/books.py`
- `studypdf/storage.py`
- `templates/books.html`

## Dados removidos

- `notes`
- `pages`
- `chapters`
- `processing_jobs`
- `books`
- Objetos `books/<storage_id>/*` no Supabase Storage
