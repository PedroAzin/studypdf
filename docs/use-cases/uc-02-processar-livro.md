# UC-02 - Processar livro em background

## Objetivo

Converter o PDF enviado em paginas HTML, imagens extraidas e capitulos navegaveis sem bloquear a requisicao de upload.

## Ator

Worker interno ou cron job.

## Fluxo principal

1. Worker chama `process_next_job()`.
2. Servico busca o primeiro job `PENDING`.
3. Job muda para `RUNNING`.
4. Livro muda para `PROCESSING`.
5. PDF original e aberto com PyMuPDF.
6. Imagens sao extraidas para `books/<storage_id>/assets`.
7. Texto e blocos sao convertidos em HTML semantico.
8. Capitulos reais sao detectados a partir do TOC.
9. Paginas antigas e capitulos antigos sao substituidos.
10. Livro muda para `READY`.
11. Job muda para `DONE`.

## Fluxos alternativos

- Livro nao encontrado: job falha.
- PDF original ausente: job falha.
- Erro de extracao: livro muda para `FAILED` e `processing_error` recebe a mensagem.

## Rotas

- `POST /cron/process-books`
- Worker iniciado por `create_app()`

## Modulos envolvidos

- `studypdf/services/processing.py`
- `studypdf/pdf/extractor.py`
- `studypdf/db.py`
- `studypdf/config.py`

## Dados gravados

- `pages`
- `chapters`
- `books.status`
- `books.processed_at`
- `processing_jobs.status`
- Imagens em `books/<storage_id>/assets`

