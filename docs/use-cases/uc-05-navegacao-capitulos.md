# UC-05 - Navegar por capitulos

## Objetivo

Permitir navegacao pelo sumario lateral e mostrar progresso por capitulo real.

## Ator

Usuario leitor.

## Fluxo principal

1. Backend busca capitulos em `chapters`.
2. Dominio identifica capitulos reais com titulos como `Chapter 1`.
3. Menu expandido mostra todos os itens do sumario.
4. Apenas capitulos reais exibem progresso.
5. Menu colapsado mostra somente capitulos reais.
6. Cada capitulo colapsado aparece como circulo de progresso com numeral romano no centro.
7. Clique em qualquer item navega para `#pagina-<start_page>`.

## Regras

- Itens como `Copyright`, `Preface`, `Part`, `Glossary`, `Index` e `Colophon` nao recebem progresso.
- O progresso do capitulo usa o intervalo ate o proximo capitulo real.
- O menu colapsado nao mostra itens auxiliares.

## Modulos envolvidos

- `studypdf/domain/reader.py`
- `studypdf/routes/books.py`
- `templates/read.html`
- `static/reader.js`
- `static/styles.css`

