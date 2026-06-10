# UC-17 - Reiniciar livro

## Objetivo

Limpar os dados de estudo de um livro sem apagar o PDF processado.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario clica em `Reiniciar livro` no leitor ou `Reiniciar` na estante.
2. Sistema exige confirmacao textual.
3. Usuario digita `REINICIAR`.
4. Backend remove notas, destaques e checkpoints de entendimento.
5. Backend redefine progresso para pagina 1.
6. Usuario volta ao leitor com o livro limpo.

## Confirmacao

A limpeza so acontece quando a confirmacao enviada e exatamente:

```text
REINICIAR
```

## O que e limpo

- `notes`
- Destaques, porque sao notas do tipo `DESTAQUE`
- `understanding_checks`
- `books.last_page_read`
- `books.last_read_at`

## O que e mantido

- PDF original.
- Paginas processadas.
- Capitulos.
- Imagens extraidas.
- Dados do livro na estante.

## Rotas

- `POST /books/<book_id>/reset`
- `POST /api/books/<book_id>/reset`

## Modulos envolvidos

- `studypdf/routes/books.py`
- `studypdf/services/books.py`
- `templates/books.html`
- `templates/read.html`
- `static/reader.js`

