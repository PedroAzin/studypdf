# UC-18 - Régua de foco para leitura

## Objetivo

Exibir uma régua horizontal semi-transparente que acompanha o cursor do mouse (ou é controlada pelo teclado) dentro da área de leitura, destacando a linha atual e escurecendo o restante do conteúdo. Auxilia leitores com TDAH a manterem o foco em uma única linha de texto.

## Ator

Usuário leitor.

## Pré-condição

Livro com status `READY`, leitor aberto em `/books/<book_id>/read`.

## Fluxo principal

1. Usuário ativa a régua clicando no botão **"Régua"** na barra superior do leitor.
2. A régua aparece na posição vertical do cursor do mouse dentro da área `.reader`.
3. A régua segue o movimento vertical do mouse em tempo real.
4. O restante do conteúdo fora da régua recebe overlay de escurecimento.
5. Usuário desativa clicando novamente no botão; a régua e o overlay somem.

## Fluxos alternativos

### 4a. Controle por teclado
- Com a régua ativa, `↑` e `↓` movem a régua em incrementos de `4px`.
- Permite uso sem mouse (ex.: leitura com touchpad ou tablet).

### 4b. Scroll da página
- Ao rolar a página, a régua mantém sua posição relativa à viewport (não ao documento), acompanhando o scroll naturalmente por ser `position: fixed` dentro do `.reader-layout`.

### 5a. Troca de página
- Ao navegar entre páginas, a régua permanece ativa se já estava ativa; posição é resetada para o centro da viewport.

## Regras

- A régua só funciona enquanto o leitor está visível — fora da rota `/books/<book_id>/read` o estado é descartado.
- Altura da régua: `3em` (equivale a ~1,5 linhas de texto, absorvendo variação de line-height).
- Cor da régua: faixa colorida semitransparente (`--reader-ruler-color`, default `rgba(255, 230, 100, 0.35)`).
- Overlay fora da régua: `rgba(0, 0, 0, 0.35)`, implementado com dois `div` (acima e abaixo da régua), não com `backdrop-filter` para evitar impacto em performance de scroll.
- O overlay não intercepta eventos de mouse — `pointer-events: none` em todos os elementos da régua para não bloquear seleção de texto e cliques em notas.
- Preferência (ligado/desligado) é persistida no `localStorage` com a chave `studypdf_ruler_enabled`.
- A posição vertical **não** é persistida — reseta sempre que a régua é ativada.
- O botão da barra superior recebe a classe `active` enquanto a régua está ligada, seguindo o padrão dos demais `.reader-tool`.

## Comportamento de acessibilidade

- Botão com `aria-label="Ativar régua de foco"` / `"Desativar régua de foco"` alternando conforme estado.
- Botão com `aria-pressed="true|false"`.
- A régua em si tem `aria-hidden="true"` (elemento decorativo).

## Estrutura HTML injetada pelo JavaScript

```html
<!-- Injetado dentro de .reader-layout quando a régua é ativada -->
<div class="reader-ruler" aria-hidden="true">
  <div class="reader-ruler-overlay reader-ruler-overlay--top"></div>
  <div class="reader-ruler-band"></div>
  <div class="reader-ruler-overlay reader-ruler-overlay--bottom"></div>
</div>
```

## CSS (variáveis e classes novas em styles.css)

```css
--reader-ruler-color: rgba(255, 230, 100, 0.35);
--reader-ruler-height: 3em;

.reader-ruler { ... }          /* position: fixed, cobre toda a viewport */
.reader-ruler-band { ... }     /* a faixa colorida */
.reader-ruler-overlay { ... }  /* os dois painéis escuros */
```

## Módulos envolvidos

- `templates/read.html` — botão de toggle na `topbar_actions`
- `static/reader.js` — lógica de ativação, rastreamento do mouse, controle por teclado, persistência em `localStorage`
- `static/styles.css` — variáveis CSS e classes da régua

## Módulos não envolvidos

- Nenhuma alteração em backend, rotas, serviços, domínio ou banco de dados.

## Critérios de aceite

| # | Cenário | Resultado esperado |
|---|---------|-------------------|
| 1 | Clicar no botão "Régua" com régua desativada | Régua aparece na posição do cursor; botão fica `active`; `localStorage` salva `"1"` |
| 2 | Mover mouse verticalmente com régua ativa | Faixa e overlays seguem o cursor sem flickering |
| 3 | Clicar no botão novamente | Régua some; botão volta ao estado normal; `localStorage` salva `"0"` |
| 4 | Pressionar `↑` / `↓` com régua ativa | Régua se move `4px` por tecla |
| 5 | Selecionar texto sobre a régua | Seleção funciona normalmente (pointer-events: none) |
| 6 | Reabrir o leitor com `localStorage` = `"1"` | Régua inicia ativa |
| 7 | Navegar para outra página com régua ativa | Régua permanece ativa; posição reseta para centro da viewport |
| 8 | Ativar a régua | Topbar e sidebar somem; apenas o conteúdo do leitor fica visível |
| 9 | Desativar a régua | Topbar e sidebar voltam a aparecer normalmente |
