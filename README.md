# StudyPDF Coach

MVP Flask para estudar PDFs tecnicos no navegador: upload, extracao por pagina com imagens, links para capitulos, leitura em HTML, notas vinculadas a trechos, busca e exportacao de contexto em Markdown para IA.

## Como rodar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Acesse `http://127.0.0.1:5000`.

## Rotas principais

- `GET /`
- `GET /books`
- `POST /books/upload`
- `GET /books/<book_id>/read`
- `POST /books/<book_id>/reprocess`
- `GET /books/<book_id>/notes`
- `GET /notes/<note_id>`
- `POST /api/notes`
- `GET /api/search?q=`
- `GET /api/notes/<note_id>/export`
