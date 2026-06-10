# UC-11 - Exportar nota para IA

## Objetivo

Gerar um arquivo Markdown com a nota, trecho selecionado e contexto da pagina para uso em IA.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario clica em `Exportar para IA`.
2. Backend busca nota, livro e texto da pagina.
3. Backend calcula contexto anterior e posterior ao trecho.
4. Template `export_note.md` gera Markdown.
5. Resposta baixa arquivo `note-<id>-ia.md`.

## Rotas

- `GET /api/notes/<note_id>/export`

## Modulos envolvidos

- `studypdf/routes/notes.py`
- `studypdf/domain/notes.py`
- `templates/export_note.md`

