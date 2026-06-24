# UC-07 - Controlar tamanho da fonte

## Objetivo

Permitir que o usuario aumente ou reduza a fonte do conteudo do leitor.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario abre o leitor.
2. Barra superior mostra controle `A-`, percentual e `A+`.
3. Clique em `A-` reduz a fonte.
4. Clique em `A+` aumenta a fonte.
5. Valor vale apenas para a sessao atual do leitor.

## Regras

- Valor minimo: `80%`.
- Valor maximo: `140%`.
- Escala aplicada via CSS variable `--reader-font-scale`.
- O leitor nao persiste preferencia de fonte no navegador.

## Modulos envolvidos

- `templates/read.html`
- `static/reader.js`
- `static/styles.css`
