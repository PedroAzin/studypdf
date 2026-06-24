# UC-16 - Checkpoint de entendimento

## Objetivo

Ajudar o usuario a verificar se entendeu um subtópico antes de avançar na leitura.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario abre o leitor.
2. Backend informa os intervalos de paginas dos capitulos reais.
3. Frontend identifica subtópicos a partir de `.book-subheading` somente dentro desses intervalos.
4. Quando o usuario passa pelo fim de um subtópico, o painel de checkpoint aparece.
5. Usuario registra um resumo em duas frases.
6. Usuario informa o que ficou confuso, se houver.
7. Usuario escolhe nível de confiança de 1 a 5.
8. Frontend envia `POST /api/books/<book_id>/understanding-checks`.
9. Backend calcula status:
   - `UNDERSTOOD` quando confiança é suficiente, há resumo e não há dúvida.
   - `REVIEW` quando confiança é baixa, resumo é curto ou existe dúvida.
10. Checkpoint fica persistido e não é solicitado novamente para o mesmo subtópico.

## Regras de elegibilidade

- Checkpoints so aparecem dentro de capitulos reais, como `Chapter 1`, `Chapter 2`, etc.
- Itens auxiliares como prefacio, sumario, partes, glossario, indice, copyright e colophon nao geram checkpoints.
- Se houver subtitulos antes do primeiro capitulo real, eles sao ignorados.

## Fluxos alternativos

- Usuario clica em `Revisar depois`: checkpoint é salvo com confiança baixa e status `REVIEW`.
- Usuario fecha o painel: subtópico é ignorado apenas na sessao atual da pagina.

## Rotas

- `GET /api/books/<book_id>/understanding-checks`
- `POST /api/books/<book_id>/understanding-checks`

## Modulos envolvidos

- `studypdf/routes/books.py`
- `studypdf/services/understanding.py`
- `studypdf/domain/understanding.py`
- `templates/read.html`
- `static/reader.js`
- `static/styles.css`

## Dados gravados

- `understanding_checks.topic_key`
- `understanding_checks.topic_title`
- `understanding_checks.page_number`
- `understanding_checks.confidence`
- `understanding_checks.summary`
- `understanding_checks.doubt`
- `understanding_checks.status`
