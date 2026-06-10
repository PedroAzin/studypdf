# UC-04 - Ler livro em HTML

## Objetivo

Renderizar o livro processado como paginas HTML com tipografia de leitura, imagens, capitulos e ferramentas de anotacao.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario clica em `Continuar` ou abre `/books/<book_id>/read`.
2. Backend valida que o livro esta `READY`.
3. Backend carrega paginas e capitulos.
4. Backend monta navegacao lateral e progresso.
5. Template `read.html` renderiza o leitor.
6. JavaScript restaura a ultima pagina lida quando nao ha hash na URL.

## Fluxos alternativos

- Livro ainda em processamento: retorna erro `409`.
- Livro com falha: retorna erro `409`.

## Rotas

- `GET /books/<book_id>/read`
- `GET /books/<book_id>/assets/<filename>`

## Modulos envolvidos

- `studypdf/routes/books.py`
- `studypdf/services/books.py`
- `studypdf/domain/reader.py`
- `templates/read.html`
- `static/reader.js`
- `static/styles.css`

