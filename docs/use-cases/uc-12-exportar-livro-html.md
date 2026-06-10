# UC-12 - Exportar livro em HTML

## Objetivo

Permitir visualizar/exportar o livro completo em HTML renderizado.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario clica em `Exportar HTML` no leitor.
2. Backend carrega livro e paginas.
3. Backend sanitiza HTML de leitura.
4. Template `book_export.html` renderiza todas as paginas.

## Rotas

- `GET /books/<book_id>/html`

## Modulos envolvidos

- `studypdf/routes/books.py`
- `studypdf/services/books.py`
- `studypdf/domain/reader.py`
- `templates/book_export.html`

