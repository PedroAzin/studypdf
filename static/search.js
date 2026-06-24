const form = document.querySelector(".search-form");
const input = document.querySelector("#search-query");
const results = document.querySelector("#search-results");

function clearResults() {
  results.replaceChildren();
}

function appendMutedMessage(message) {
  const paragraph = document.createElement("p");
  paragraph.className = "muted";
  paragraph.textContent = message;
  results.append(paragraph);
}

function noteMetaItem(text) {
  const span = document.createElement("span");
  span.textContent = text;
  return span;
}

function noteLink(href, label, className = "button") {
  const link = document.createElement("a");
  link.className = className;
  link.href = href;
  link.textContent = label;
  return link;
}

function renderNote(item) {
  const article = document.createElement("article");
  article.className = "note-card";

  const meta = document.createElement("div");
  meta.className = "note-meta";
  meta.append(
    noteMetaItem(item.book_title),
    noteMetaItem(item.note_type),
    noteMetaItem(`Pagina ${item.page_number}`),
  );
  if (item.tags) {
    meta.append(noteMetaItem(item.tags));
  }

  const quote = document.createElement("blockquote");
  quote.textContent = item.selected_text;

  const actions = document.createElement("div");
  actions.className = "actions";
  actions.append(
    noteLink(`/notes/${item.id}`, "Abrir", "button secondary"),
    noteLink(`/api/notes/${item.id}/export`, "Exportar para IA"),
  );

  article.append(meta, quote);
  if (item.note_text) {
    const noteText = document.createElement("p");
    noteText.textContent = item.note_text;
    article.append(noteText);
  }
  article.append(actions);
  return article;
}

function render(items) {
  clearResults();
  if (items.length === 0) {
    appendMutedMessage("Nenhum resultado encontrado.");
    return;
  }
  results.append(...items.map(renderNote));
}

function runSearch(query) {
  if (!query) {
    clearResults();
    appendMutedMessage("Digite um termo para pesquisar.");
    return Promise.resolve();
  }
  return fetch(`/api/search?q=${encodeURIComponent(query)}`)
    .then((response) => response.json())
    .then((data) => render(data.results));
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = input.value.trim();
  const params = new URLSearchParams({ q: query });
  history.replaceState(null, "", `/search?${params.toString()}`);
  runSearch(query);
});

runSearch(input.value.trim());
