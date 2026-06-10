# UC-15 - Traducao pelo Chrome

## Objetivo

Facilitar que o Chrome detecte o conteudo do livro como ingles e ofereca ou aplique traducao para portugues.

## Ator

Usuario leitor.

## Fluxo principal

1. Usuario abre o leitor.
2. HTML da pagina e marcado como `lang="en"`.
3. Conteudo do livro fica `lang="en" translate="yes"`.
4. Interface do app fica `lang="pt-BR" translate="no"`.
5. Chrome pode oferecer traducao do conteudo.
6. Se o usuario marcar `Sempre traduzir ingles`, o Chrome tende a traduzir automaticamente nas proximas aberturas.

## Limitacao

O site nao consegue forcar a traducao automatica do Chrome. A decisao final depende das configuracoes e preferencias do navegador.

## Modulos envolvidos

- `templates/base.html`
- `templates/read.html`

