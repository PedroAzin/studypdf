const form = document.querySelector(".search-form");
const input = document.querySelector("#search-query");
const results = document.querySelector("#search-results");

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function render(items) {
  if (items.length === 0) {
    results.innerHTML = '<p class="muted">Nenhum resultado encontrado.</p>';
    return;
  }

  results.innerHTML = items.map((item) => `
    <article class="note-card">
      <div class="note-meta">
        <span>${escapeHtml(item.book_title)}</span>
        <span>${escapeHtml(item.note_type)}</span>
        <span>Pagina ${item.page_number}</span>
        ${item.tags ? `<span>${escapeHtml(item.tags)}</span>` : ""}
      </div>
      <blockquote>${escapeHtml(item.selected_text)}</blockquote>
      ${item.note_text ? `<p>${escapeHtml(item.note_text)}</p>` : ""}
      <div class="actions">
        <a class="button secondary" href="/notes/${item.id}">Abrir</a>
        <a class="button" href="/api/notes/${item.id}/export">Exportar para IA</a>
      </div>
    </article>
  `).join("");
}

async function runSearch(query) {
  if (!query) {
    results.innerHTML = '<p class="muted">Digite um termo para pesquisar.</p>';
    return;
  }
  const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  const data = await response.json();
  render(data.results);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = input.value.trim();
  const params = new URLSearchParams({ q: query });
  history.replaceState(null, "", `/search?${params.toString()}`);
  runSearch(query);
});

runSearch(input.value.trim());
