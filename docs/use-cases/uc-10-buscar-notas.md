# UC-10 - Buscar notas

## Objetivo

Buscar notas por trecho, texto da nota, tags ou titulo do livro.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario acessa `/search`.
2. Usuario digita termo de busca.
3. Frontend chama `/api/search?q=<termo>`.
4. Backend consulta notas e livros com `LIKE`.
5. Frontend renderiza resultados com link para detalhe e exportacao.

## Rotas

- `GET /search`
- `GET /api/search?q=`

## Modulos envolvidos

- `studypdf/routes/main.py`
- `studypdf/routes/notes.py`
- `templates/search.html`
- `static/search.js`

## Dados lidos

- `notes`
- `books`

