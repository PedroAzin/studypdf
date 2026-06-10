# Mapa de rotas

## Main

| Metodo | Rota | Endpoint | Descricao |
|---|---|---|---|
| GET | `/` | `main.index` | Tela inicial e upload |
| GET | `/search` | `main.search` | Tela de busca |

## Livros e leitor

| Metodo | Rota | Endpoint | Descricao |
|---|---|---|---|
| GET | `/books` | `books.books` | Estante |
| POST | `/books/upload` | `books.upload_book` | Envia PDF e cria job |
| DELETE | `/api/books/<book_id>` | `books.api_delete_book` | Remove livro via API |
| POST | `/books/<book_id>/delete` | `books.delete_book` | Remove livro via formulario |
| POST | `/books/<book_id>/reset` | `books.reset_book` | Reinicia dados de leitura do livro |
| POST | `/api/books/<book_id>/reset` | `books.api_reset_book` | Reinicia dados de leitura via API |
| GET | `/books/<book_id>/read` | `books.read_book` | Leitor HTML |
| POST | `/api/books/<book_id>/progress` | `books.update_progress` | Salva progresso |
| GET | `/api/books/<book_id>/understanding-checks` | `books.understanding_checks` | Lista checkpoints de entendimento |
| POST | `/api/books/<book_id>/understanding-checks` | `books.save_understanding` | Salva checkpoint de entendimento |
| GET | `/api/books/events` | `books.book_events` | Eventos SSE de processamento |
| POST | `/cron/process-books` | `books.cron_process_books` | Processa jobs pendentes |
| POST | `/books/<book_id>/reprocess` | `books.reprocess_book` | Reprocessa PDF |
| GET | `/books/<book_id>/original` | `books.original_pdf` | Baixa/abre PDF original |
| GET | `/books/<book_id>/html` | `books.export_book_html` | Exporta livro em HTML |
| GET | `/books/<book_id>/assets/<filename>` | `books.book_asset` | Serve imagens extraidas |

## Notas

| Metodo | Rota | Endpoint | Descricao |
|---|---|---|---|
| GET | `/books/<book_id>/notes` | `notes.book_notes` | Lista notas do livro |
| GET | `/books/<book_id>/notes/new` | `notes.new_note` | Formulario de nova nota |
| POST | `/books/<book_id>/notes` | `notes.create_note_form` | Cria nota via formulario |
| GET | `/books/<book_id>/highlights` | `notes.book_highlights` | Lista destaques |
| GET | `/notes/<note_id>` | `notes.note_detail` | Detalhe da nota |
| GET | `/notes/<note_id>/edit` | `notes.edit_note` | Formulario de edicao |
| POST | `/notes/<note_id>/edit` | `notes.update_note_form` | Atualiza nota via formulario |
| POST | `/notes/<note_id>/delete` | `notes.delete_note_form` | Remove nota via formulario |
| POST | `/api/notes` | `notes.create_note` | Cria nota via API |
| GET | `/api/notes/<note_id>` | `notes.api_note` | Consulta nota |
| PATCH | `/api/notes/<note_id>` | `notes.api_note` | Atualiza nota |
| DELETE | `/api/notes/<note_id>` | `notes.api_note` | Remove nota |
| GET | `/api/search?q=` | `notes.api_search` | Busca notas |
| GET | `/api/notes/<note_id>/export` | `notes.export_note` | Exporta nota em Markdown |
