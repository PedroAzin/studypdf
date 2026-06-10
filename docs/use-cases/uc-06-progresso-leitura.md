# UC-06 - Salvar e restaurar progresso de leitura

## Objetivo

Guardar a pagina atual do usuario e permitir que ele continue a leitura do ponto onde parou.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario rola o leitor.
2. JavaScript identifica a pagina mais proxima do ponto de leitura.
3. JavaScript envia `POST /api/books/<book_id>/progress`.
4. Backend limita a pagina ao intervalo valido.
5. Backend atualiza `books.last_page_read` e `books.last_read_at`.
6. Estante passa a apontar `Continuar` para a ultima pagina.
7. Ao abrir o leitor sem hash, JavaScript rola para a ultima pagina persistida.

## Rotas

- `POST /api/books/<book_id>/progress`
- `GET /books/<book_id>/read`

## Modulos envolvidos

- `studypdf/routes/books.py`
- `studypdf/domain/reader.py`
- `static/reader.js`
- `templates/books.html`
- `templates/read.html`

## Dados gravados

- `books.last_page_read`
- `books.last_read_at`

