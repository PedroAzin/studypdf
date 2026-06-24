const shelfCards = new Map(
  [...document.querySelectorAll("[data-book-id]")].map((card) => [
    Number(card.dataset.bookId),
    card.dataset.bookStatus,
  ]),
);

if (globalThis.EventSource && shelfCards.size > 0) {
  const events = new EventSource("/api/books/events");

  events.addEventListener("books", (event) => {
    const books = JSON.parse(event.data);
    let shouldReload = false;

    for (const book of books) {
      if (!shelfCards.has(book.id)) continue;
      const previous = shelfCards.get(book.id);
      if (previous !== book.status) {
        shouldReload = true;
        break;
      }
    }

    if (shouldReload) {
      globalThis.location.reload();
    }
  });
}
