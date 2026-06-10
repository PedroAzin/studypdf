# UC-08 - Criar nota pelo leitor

## Objetivo

Criar notas a partir de um trecho selecionado no texto do livro.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario seleciona um trecho dentro de uma pagina.
2. Menu contextual aparece proximo a selecao.
3. Usuario escolhe tipo: duvida, anotacao, destaque ou trabalho.
4. Dialog abre com trecho selecionado.
5. Usuario escreve nota e tags.
6. Frontend envia `POST /api/notes`.
7. Backend valida livro, pagina, tipo e trecho.
8. Nota e gravada.

## Regras

- O menu fecha ao clicar fora.
- O menu guarda trecho e pagina no proprio elemento para evitar perda da selecao antes do clique.
- Tipos validos ficam em `NOTE_TYPES`.

## Rotas

- `POST /api/notes`

## Modulos envolvidos

- `static/reader.js`
- `templates/read.html`
- `studypdf/routes/notes.py`
- `studypdf/services/notes.py`
- `studypdf/domain/notes.py`

## Dados gravados

- `notes`

