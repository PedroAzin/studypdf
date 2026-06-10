const reader = document.querySelector(".reader");
const menu = document.querySelector("#selection-menu");
const dialog = document.querySelector("#note-dialog");
const selectedTextField = document.querySelector("#selected-text");
const noteTextField = document.querySelector("#note-text");
const noteTagsField = document.querySelector("#note-tags");
const saveButton = document.querySelector("#save-note");
const dialogTitle = document.querySelector("#dialog-title");
const progressLabel = document.querySelector("[data-progress-label]");
const currentPageLabel = document.querySelector("[data-current-page]");
const progressBar = document.querySelector("[data-progress-bar]");
const readerLayout = document.querySelector(".reader-layout");
const chapterSidebar = document.querySelector("[data-chapter-sidebar]");
const chapterToggle = document.querySelector("[data-chapter-toggle]");
const fontDecrease = document.querySelector("[data-font-decrease]");
const fontIncrease = document.querySelector("[data-font-increase]");
const fontSizeLabel = document.querySelector("[data-font-size-label]");
const checkPanel = document.querySelector("[data-understanding-check]");
const checkTopic = document.querySelector("[data-check-topic]");
const checkSummary = document.querySelector("[data-check-summary]");
const checkDoubt = document.querySelector("[data-check-doubt]");
const checkSave = document.querySelector("[data-check-save]");
const checkLater = document.querySelector("[data-check-later]");
const checkDismiss = document.querySelector("[data-check-dismiss]");
const resetDialog = document.querySelector("#reset-book-dialog");
const resetOpen = document.querySelector("[data-reset-open]");

let currentSelection = null;
let currentNoteType = "DUVIDA";
let lastSavedPage = Number(reader.dataset.lastPageRead || 1);
let saveProgressTimer = null;
let progressReady = false;
let readerFontPercent = Number(window.localStorage.getItem("readerFontPercent") || 100);
let understandingTopics = [];
let savedUnderstandingChecks = new Set();
let dismissedUnderstandingChecks = new Set(JSON.parse(window.localStorage.getItem(checkDismissKey()) || "[]"));
let activeUnderstandingTopic = null;
let selectedConfidence = 3;
let understandingRanges = JSON.parse(reader.dataset.understandingRanges || "[]");

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function applyReaderFontSize(percent) {
  readerFontPercent = clamp(percent, 80, 140);
  reader.style.setProperty("--reader-font-scale", String(readerFontPercent / 100));
  if (fontSizeLabel) fontSizeLabel.textContent = `${readerFontPercent}%`;
  window.localStorage.setItem("readerFontPercent", String(readerFontPercent));
}

applyReaderFontSize(readerFontPercent);

fontDecrease?.addEventListener("click", () => {
  applyReaderFontSize(readerFontPercent - 10);
});

fontIncrease?.addEventListener("click", () => {
  applyReaderFontSize(readerFontPercent + 10);
});

function setChapterNavCollapsed(collapsed) {
  chapterSidebar?.classList.toggle("is-collapsed", collapsed);
  readerLayout?.classList.toggle("chapter-nav-collapsed", collapsed);
  if (chapterToggle) {
    chapterToggle.setAttribute("aria-expanded", String(!collapsed));
    chapterToggle.setAttribute("aria-label", collapsed ? "Expandir capitulos" : "Recolher capitulos");
  }
  window.localStorage.setItem("chapterNavCollapsed", collapsed ? "1" : "0");
}

if (chapterToggle) {
  const savedCollapsed = window.localStorage.getItem("chapterNavCollapsed") === "1";
  setChapterNavCollapsed(savedCollapsed);
  chapterToggle.addEventListener("click", () => {
    setChapterNavCollapsed(!chapterSidebar.classList.contains("is-collapsed"));
  });
}

function pageFromSelection(selection) {
  if (!selection || selection.rangeCount === 0) return null;
  const node = selection.anchorNode?.nodeType === Node.TEXT_NODE
    ? selection.anchorNode.parentElement
    : selection.anchorNode;
  return node?.closest?.(".page") || null;
}

function hideMenu() {
  menu.hidden = true;
}

function selectedTextFromMenu() {
  const text = menu.dataset.selectedText || "";
  const pageNumber = Number(menu.dataset.pageNumber || 0);
  if (!text || !pageNumber) return null;
  return { text, pageNumber };
}

function showMenu(selection, selectedText) {
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();
  const page = pageFromSelection(selection);
  if (!page) return;

  currentSelection = {
    text: selectedText,
    pageNumber: Number(page.dataset.pageNumber),
  };
  menu.dataset.selectedText = currentSelection.text;
  menu.dataset.pageNumber = String(currentSelection.pageNumber);

  menu.style.left = `${Math.max(8, rect.left)}px`;
  menu.style.top = `${Math.max(68, rect.bottom + 8)}px`;
  menu.hidden = false;
}

document.addEventListener("mouseup", (event) => {
  window.setTimeout(() => {
    if (menu.contains(event.target) || dialog.open) return;

    const selection = window.getSelection();
    const selectedText = selection.toString().trim();
    if (selectedText.length > 0 && reader.contains(selection.anchorNode)) {
      showMenu(selection, selectedText);
    }
  }, 0);
});

document.addEventListener("pointerdown", (event) => {
  if (!menu.hidden && !menu.contains(event.target)) {
    hideMenu();
    currentSelection = null;
    delete menu.dataset.selectedText;
    delete menu.dataset.pageNumber;
    window.getSelection()?.removeAllRanges();
  }
}, true);

menu.addEventListener("pointerdown", (event) => {
  event.preventDefault();
});

menu.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-type]");
  const selection = currentSelection || selectedTextFromMenu();
  if (!button || !selection) return;

  currentNoteType = button.dataset.type;
  dialogTitle.textContent = {
    DUVIDA: "Criar duvida",
    ANOTACAO: "Fazer anotacao",
    DESTAQUE: "Destacar trecho",
    TRABALHO: "Relacionar ao trabalho",
  }[currentNoteType] || "Nova nota";

  currentSelection = selection;
  selectedTextField.value = selection.text;
  noteTextField.value = "";
  noteTagsField.value = "";
  hideMenu();
  if (!dialog.open) dialog.showModal();
});

saveButton.addEventListener("click", async (event) => {
  event.preventDefault();
  if (!currentSelection) return;

  saveButton.disabled = true;
  try {
    const response = await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        book_id: Number(reader.dataset.bookId),
        page_number: currentSelection.pageNumber,
        selected_text: currentSelection.text,
        note_type: currentNoteType,
        note_text: noteTextField.value,
        tags: noteTagsField.value.split(",").map((tag) => tag.trim()).filter(Boolean),
      }),
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    dialog.close();
    window.getSelection().removeAllRanges();
  } catch (error) {
    alert(`Nao foi possivel salvar a nota: ${error.message}`);
  } finally {
    saveButton.disabled = false;
  }
});

function visiblePageNumber() {
  const pages = [...document.querySelectorAll(".page")];
  const viewportAnchor = window.innerHeight * 0.38;
  let bestPage = pages[0];
  let bestDistance = Number.POSITIVE_INFINITY;

  for (const page of pages) {
    const rect = page.getBoundingClientRect();
    const distance = Math.abs(rect.top - viewportAnchor);
    if (distance < bestDistance && rect.bottom > 0) {
      bestDistance = distance;
      bestPage = page;
    }
  }

  return Number(bestPage?.dataset.pageNumber || 1);
}

function updateProgressUi(pageNumber, percentRead) {
  const totalPages = Number(reader.dataset.totalPages || 0);
  if (progressLabel) progressLabel.textContent = `${percentRead}% lido`;
  if (currentPageLabel) currentPageLabel.textContent = `pagina ${pageNumber} de ${totalPages}`;
  if (progressBar) progressBar.style.width = `${percentRead}%`;
}

async function saveReadingProgress(pageNumber) {
  if (!pageNumber || pageNumber === lastSavedPage) return;
  lastSavedPage = pageNumber;

  try {
    const response = await fetch(`/api/books/${Number(reader.dataset.bookId)}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ page_number: pageNumber }),
    });
    if (!response.ok) return;
    const payload = await response.json();
    updateProgressUi(payload.page_number, payload.percent_read);
  } catch (_error) {
    // Progress is opportunistic; reading must not be interrupted if it fails.
  }
}

function scheduleProgressSave() {
  if (!progressReady) return;
  window.clearTimeout(saveProgressTimer);
  saveProgressTimer = window.setTimeout(() => {
    saveReadingProgress(visiblePageNumber());
  }, 350);
}

function restoreReadingPosition() {
  if (window.location.hash) {
    progressReady = true;
    return;
  }

  const lastPageRead = Number(reader.dataset.lastPageRead || 1);
  if (lastPageRead > 1) {
    document.querySelector(`#pagina-${lastPageRead}`)?.scrollIntoView({ block: "start" });
  }

  window.setTimeout(() => {
    progressReady = true;
  }, 500);
}

function checkDismissKey() {
  return `understandingDismissed:${reader?.dataset.bookId || "book"}`;
}

function topicElements() {
  const headings = [...reader.querySelectorAll(".book-subheading, .book-heading")];
  const chapterHeadings = headings.filter(headingIsInsideRealChapter);
  if (chapterHeadings.some((heading) => heading.classList.contains("book-subheading"))) {
    return chapterHeadings.filter((heading) => heading.classList.contains("book-subheading"));
  }
  return chapterHeadings;
}

function headingIsInsideRealChapter(heading) {
  const pageNumber = Number(heading.closest(".page")?.dataset.pageNumber || 0);
  return understandingRanges.some((range) => (
    pageNumber >= Number(range.start_page) && pageNumber <= Number(range.end_page)
  ));
}

function collectUnderstandingTopics() {
  const topics = topicElements();
  understandingTopics = topics.map((heading, index) => {
    const page = heading.closest(".page");
    return {
      key: `topic-${index + 1}-page-${page?.dataset.pageNumber || 1}`,
      title: heading.textContent.trim().slice(0, 160),
      pageNumber: Number(page?.dataset.pageNumber || 1),
      heading,
      endElement: topics[index + 1] || null,
    };
  }).filter((topic) => topic.title.length > 0);
}

async function loadUnderstandingChecks() {
  try {
    const response = await fetch(`/api/books/${Number(reader.dataset.bookId)}/understanding-checks`);
    if (!response.ok) return;
    const payload = await response.json();
    savedUnderstandingChecks = new Set((payload.checks || []).map((check) => check.topic_key));
  } catch (_error) {
    savedUnderstandingChecks = new Set();
  }
}

function topicIsDue(topic) {
  if (savedUnderstandingChecks.has(topic.key) || dismissedUnderstandingChecks.has(topic.key)) return false;
  const endTop = topic.endElement
    ? topic.endElement.getBoundingClientRect().top
    : topic.heading.closest(".page").getBoundingClientRect().bottom;
  return endTop < window.innerHeight * 0.42;
}

function maybeShowUnderstandingCheck() {
  if (!progressReady || !checkPanel?.hidden || activeUnderstandingTopic) return;
  const topic = understandingTopics.find(topicIsDue);
  if (topic) showUnderstandingCheck(topic);
}

function showUnderstandingCheck(topic) {
  activeUnderstandingTopic = topic;
  selectedConfidence = 3;
  checkTopic.textContent = topic.title;
  checkSummary.value = "";
  checkDoubt.value = "";
  setConfidence(3);
  checkPanel.hidden = false;
}

function hideUnderstandingCheck() {
  checkPanel.hidden = true;
  activeUnderstandingTopic = null;
}

function setConfidence(value) {
  selectedConfidence = Number(value);
  document.querySelectorAll("[data-confidence]").forEach((button) => {
    button.classList.toggle("active", Number(button.dataset.confidence) === selectedConfidence);
  });
}

function dismissUnderstandingCheck() {
  if (!activeUnderstandingTopic) return;
  dismissedUnderstandingChecks.add(activeUnderstandingTopic.key);
  window.localStorage.setItem(checkDismissKey(), JSON.stringify([...dismissedUnderstandingChecks]));
  hideUnderstandingCheck();
}

async function saveUnderstandingCheck(reviewLater = false) {
  if (!activeUnderstandingTopic) return;
  const topic = activeUnderstandingTopic;
  const confidence = reviewLater ? 1 : selectedConfidence;
  try {
    const response = await fetch(`/api/books/${Number(reader.dataset.bookId)}/understanding-checks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic_key: topic.key,
        topic_title: topic.title,
        page_number: topic.pageNumber,
        confidence,
        summary: checkSummary.value,
        doubt: checkDoubt.value,
      }),
    });
    if (!response.ok) throw new Error(await response.text());
    savedUnderstandingChecks.add(topic.key);
    hideUnderstandingCheck();
  } catch (error) {
    alert(`Nao foi possivel salvar o checkpoint: ${error.message}`);
  }
}

document.querySelectorAll("[data-confidence]").forEach((button) => {
  button.addEventListener("click", () => setConfidence(button.dataset.confidence));
});

checkSave?.addEventListener("click", () => saveUnderstandingCheck(false));
checkLater?.addEventListener("click", () => saveUnderstandingCheck(true));
checkDismiss?.addEventListener("click", dismissUnderstandingCheck);
resetOpen?.addEventListener("click", () => resetDialog?.showModal());
resetDialog?.addEventListener("submit", () => {
  window.localStorage.removeItem(checkDismissKey());
});

document.addEventListener("scroll", scheduleProgressSave, { passive: true });
document.addEventListener("scroll", maybeShowUnderstandingCheck, { passive: true });
window.addEventListener("beforeunload", () => {
  const pageNumber = visiblePageNumber();
  if (navigator.sendBeacon) {
    const payload = new Blob([JSON.stringify({ page_number: pageNumber })], {
      type: "application/json",
    });
    navigator.sendBeacon(`/api/books/${Number(reader.dataset.bookId)}/progress`, payload);
  }
});
restoreReadingPosition();
collectUnderstandingTopics();
loadUnderstandingChecks();
