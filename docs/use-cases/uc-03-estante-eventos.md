# UC-03 - Acompanhar processamento na estante

## Objetivo

Mostrar livros em processamento esmaecidos na estante e atualizar automaticamente quando o processamento terminar.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario acessa `/books`.
2. Backend lista livros com paginas, capitulos, notas, destaques e progresso.
3. Livros `PROCESSING` aparecem desabilitados/esmaecidos.
4. Frontend abre conexao com `/api/books/events`.
5. Backend envia snapshots via Server-Sent Events.
6. Quando status ou estatisticas mudam, frontend recarrega a estante.
7. Livro `READY` passa a exibir a acao `Continuar`.

## Rotas

- `GET /books`
- `GET /api/books/events`

## Modulos envolvidos

- `studypdf/routes/books.py`
- `studypdf/services/books.py`
- `static/shelf.js`
- `templates/books.html`

## Dados lidos

- `books`
- `pages`
- `chapters`
- `notes`

