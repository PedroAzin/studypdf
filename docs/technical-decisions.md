# Decisoes tecnicas

## Flask com blueprints por feature

As rotas foram separadas por feature para reduzir acoplamento:

- `main`: paginas gerais.
- `books`: upload, estante, leitor e processamento.
- `notes`: notas, destaques, busca e exportacao.

## PostgreSQL/Supabase

O projeto usa PostgreSQL via Supabase. A connection string fica em `STUDYPDF_DATABASE_URL`; sem essa variavel o app nao inicia a camada de banco.

A funcao `init_db()` cria o schema necessario com `CREATE TABLE IF NOT EXISTS`, mantendo a inicializacao simples enquanto o projeto ainda nao usa uma ferramenta externa de migracao.

## Supabase Storage

PDFs originais e imagens extraidas ficam no Supabase Storage. O banco guarda a chave do objeto em `books.file_path`; rotas HTTP do app baixam os bytes do bucket quando precisam servir PDF ou asset ao navegador.

## Processamento em background

O upload nao processa o PDF durante a requisicao. Ele:

1. Salva o PDF original.
2. Cria o livro com status `PROCESSING`.
3. Cria job `PENDING`.
4. Redireciona para a estante.
5. Worker ou cron processa o job usando lock `FOR UPDATE SKIP LOCKED`.
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
