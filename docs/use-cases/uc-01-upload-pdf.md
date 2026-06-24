# UC-01 - Enviar PDF

## Objetivo

Permitir que o usuario envie um arquivo PDF para a aplicacao e receba feedback imediato, sem esperar o processamento completo do livro.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario acessa `/`.
2. Usuario escolhe um arquivo PDF.
3. Opcionalmente informa titulo e autor.
4. Frontend envia `POST /books/upload`.
5. Backend valida se existe arquivo e se a extensao e `.pdf`.
6. Backend envia o arquivo para o Supabase Storage.
7. Backend cria registro em `books` com status `PROCESSING`.
8. Backend cria registro em `processing_jobs` com status `PENDING`.
9. Usuario e redirecionado para `/books`.

## Fluxos alternativos

- Arquivo ausente: retorna erro `400`.
- Extensao diferente de PDF: retorna erro `400`.
- Erro ao salvar arquivo ou criar registros: remove objeto enviado ao Storage quando aplicavel e retorna erro.

## Rotas

- `GET /`
- `POST /books/upload`

## Modulos envolvidos

- `studypdf/routes/main.py`
- `studypdf/routes/books.py`
- `studypdf/config.py`
- `studypdf/db.py`
- `studypdf/storage.py`
- `templates/index.html`
- `static/upload.js`

## Dados gravados

- `books`
- `processing_jobs`
- Objeto `books/<storage_id>/original.pdf` no Supabase Storage
