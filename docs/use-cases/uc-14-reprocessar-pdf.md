# UC-14 - Reprocessar PDF

## Objetivo

Executar novamente a extracao do PDF original para atualizar paginas, capitulos e imagens.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario abre o leitor.
2. Usuario clica em `Reprocessar PDF`.
3. Backend baixa o PDF original do Supabase Storage para diretorio temporario.
4. Backend extrai novamente paginas, imagens e capitulos.
5. Backend envia os assets extraidos para o Supabase Storage.
6. Backend substitui paginas e capitulos.
7. Backend atualiza links de pagina das notas.
8. Usuario volta para o leitor.

## Fluxos alternativos

- PDF original ausente: retorna erro `404`.

## Rotas

- `POST /books/<book_id>/reprocess`

## Modulos envolvidos

- `studypdf/routes/books.py`
- `studypdf/services/processing.py`
- `studypdf/pdf/extractor.py`
- `studypdf/storage.py`
