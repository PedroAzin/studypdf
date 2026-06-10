# Decisoes tecnicas

## Flask com blueprints por feature

As rotas foram separadas por feature para reduzir acoplamento:

- `main`: paginas gerais.
- `books`: upload, estante, leitor e processamento.
- `notes`: notas, destaques, busca e exportacao.

## SQLite com migracoes leves

O projeto usa SQLite direto. A funcao `init_db()` cria tabelas e `ensure_column()` adiciona colunas novas sem exigir ferramenta externa de migracao.

## Processamento em background

O upload nao processa o PDF durante a requisicao. Ele:

1. Salva o PDF original.
2. Cria o livro com status `PROCESSING`.
3. Cria job `PENDING`.
4. Redireciona para a estante.
5. Worker ou cron processa o job.
6. SSE atualiza a estante.

## Conversao de PDF para HTML

PyMuPDF (`fitz`) extrai texto, blocos, imagens e TOC. O HTML gerado usa classes semanticas:

- `book-heading`
- `book-subheading`
- `book-quote`
- `book-list-item`
- `book-paragraph`
- `section-lead`
- `book-image`

## Progresso de leitura

O progresso geral usa pagina atual dividido pelo total de paginas. O progresso por capitulo usa o intervalo entre capitulos reais. Itens auxiliares como `Preface`, `Part`, `Glossary` e `Index` nao recebem progresso de capitulo.

## Traducao pelo Chrome

O leitor marca a pagina como `lang="en"` e o conteudo do livro como `translate="yes"`. A interface do app usa `translate="no"` para evitar que os controles em portugues sejam traduzidos. A traducao final depende da configuracao do Chrome.

## Complexidade

As novas funcoes foram mantidas pequenas e coesas. A excecao consciente e `init_db()`, que e declarativa de schema e nao concentra regras condicionais.

