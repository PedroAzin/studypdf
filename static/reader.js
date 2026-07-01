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
const rulerToggle = document.querySelector("[data-ruler-toggle]");
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
const chapterLinks = [...document.querySelectorAll(".chapter-link.is-book-chapter")];
const understandingEnabled = reader.dataset.understandingEnabled === "1";

let currentSelection = null;
let currentNoteType = "DUVIDA";
let lastSavedPage = Number(reader.dataset.lastPageRead || 1);
let saveProgressTimer = null;
let progressReady = false;
let readerFontPercent = 100;
let understandingTopics = [];
let savedUnderstandingChecks = new Set();
let dismissedUnderstandingChecks = new Set();
let activeUnderstandingTopic = null;
let selectedConfidence = 3;
let understandingRanges = understandingEnabled ? JSON.parse(reader.dataset.understandingRanges || "[]") : [];

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function applyReaderFontSize(percent) {
  readerFontPercent = clamp(percent, 80, 140);
  reader.style.setProperty("--reader-font-scale", String(readerFontPercent / 100));
  if (fontSizeLabel) fontSizeLabel.textContent = `${readerFontPercent}%`;
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
}

if (chapterToggle) {
  setChapterNavCollapsed(false);
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
  globalThis.setTimeout(() => {
    if (menu.contains(event.target) || dialog.open) return;

    const selection = globalThis.getSelection();
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
    globalThis.getSelection()?.removeAllRanges();
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
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      credentials: "same-origin",
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
    globalThis.getSelection().removeAllRanges();
  } catch (error) {
    alert(`Nao foi possivel salvar a nota: ${error.message}`);
  } finally {
    saveButton.disabled = false;
  }
});

function visiblePageNumber() {
  const pages = [...document.querySelectorAll(".page")];
  const viewportHeight = document.documentElement.clientHeight || 720;
  const viewportAnchor = viewportHeight * 0.38;
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

function chapterProgress(startPage, endPage, pageNumber) {
  if (!startPage || pageNumber < startPage) return 0;
  if (pageNumber >= endPage) return 100;
  const span = Math.max(1, endPage - startPage + 1);
  return clamp(Math.round(((pageNumber - startPage + 1) / span) * 100), 1, 99);
}

function updateChapterProgressUi(pageNumber) {
  for (const link of chapterLinks) {
    const startPage = Number(link.dataset.startPage || 0);
    const endPage = Number(link.dataset.endPage || startPage);
    const progress = chapterProgress(startPage, endPage, pageNumber);
    const ring = link.querySelector(".chapter-progress-ring");
    const label = link.querySelector("[data-chapter-progress-label]");
    const bar = link.querySelector("[data-chapter-progress-bar]");

    link.classList.toggle("is-current", pageNumber >= startPage && pageNumber <= endPage);
    ring?.style.setProperty("--chapter-progress", `${progress}%`);
    if (ring) ring.setAttribute("aria-label", `${progress}% lido neste capitulo`);
    if (label) label.textContent = `${progress}%`;
    if (bar) bar.style.width = `${progress}%`;
  }
}

async function saveReadingProgress(pageNumber) {
  if (!pageNumber || pageNumber === lastSavedPage) return;
  lastSavedPage = pageNumber;

  try {
    const response = await fetch(`/api/books/${Number(reader.dataset.bookId)}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      credentials: "same-origin",
      body: JSON.stringify({ page_number: pageNumber }),
    });
    if (!response.ok) return;
    const payload = await response.json();
    updateProgressUi(payload.page_number, payload.percent_read);
  } catch (error) {
    console.debug("Nao foi possivel salvar o progresso de leitura.", error);
    // Progress is opportunistic; reading must not be interrupted if it fails.
  }
}

function scheduleProgressSave() {
  if (!progressReady) return;
  updateChapterProgressUi(visiblePageNumber());
  globalThis.clearTimeout(saveProgressTimer);
  saveProgressTimer = globalThis.setTimeout(() => {
    saveReadingProgress(visiblePageNumber());
  }, 350);
}

function restoreReadingPosition() {
  if (globalThis.location.hash) {
    progressReady = true;
    globalThis.setTimeout(() => updateChapterProgressUi(visiblePageNumber()), 100);
    return;
  }

  const lastPageRead = Number(reader.dataset.lastPageRead || 1);
  if (lastPageRead > 1) {
    document.querySelector(`#pagina-${lastPageRead}`)?.scrollIntoView({ block: "start" });
  }

  globalThis.setTimeout(() => {
    progressReady = true;
  }, 500);
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

function loadUnderstandingChecks() {
  return fetch(`/api/books/${Number(reader.dataset.bookId)}/understanding-checks`)
    .then((response) => (response.ok ? response.json() : { checks: [] }))
    .then((payload) => {
      savedUnderstandingChecks = new Set((payload.checks || []).map((check) => check.topic_key));
    })
    .catch((error) => {
      console.debug("Nao foi possivel carregar checkpoints de entendimento.", error);
      savedUnderstandingChecks = new Set();
    });
}

function topicIsDue(topic) {
  if (savedUnderstandingChecks.has(topic.key) || dismissedUnderstandingChecks.has(topic.key)) return false;
  const endTop = topic.endElement
    ? topic.endElement.getBoundingClientRect().top
    : topic.heading.closest(".page").getBoundingClientRect().bottom;
  const viewportHeight = document.documentElement.clientHeight || 720;
  return endTop < viewportHeight * 0.42;
}

function maybeShowUnderstandingCheck() {
  if (!understandingEnabled || !progressReady || !checkPanel?.hidden || activeUnderstandingTopic) return;
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
  hideUnderstandingCheck();
}

async function saveUnderstandingCheck(reviewLater = false) {
  if (!activeUnderstandingTopic) return;
  const topic = activeUnderstandingTopic;
  const confidence = reviewLater ? 1 : selectedConfidence;
  try {
    const response = await fetch(`/api/books/${Number(reader.dataset.bookId)}/understanding-checks`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      credentials: "same-origin",
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

if (understandingEnabled) {
  document.querySelectorAll("[data-confidence]").forEach((button) => {
    button.addEventListener("click", () => setConfidence(button.dataset.confidence));
  });

  checkSave?.addEventListener("click", () => saveUnderstandingCheck(false));
  checkLater?.addEventListener("click", () => saveUnderstandingCheck(true));
  checkDismiss?.addEventListener("click", dismissUnderstandingCheck);
}
resetOpen?.addEventListener("click", () => resetDialog?.showModal());

document.addEventListener("scroll", scheduleProgressSave, { passive: true });
document.addEventListener("scroll", maybeShowUnderstandingCheck, { passive: true });
globalThis.addEventListener("hashchange", () => {
  globalThis.setTimeout(() => updateChapterProgressUi(visiblePageNumber()), 100);
});
globalThis.addEventListener("load", () => {
  updateChapterProgressUi(visiblePageNumber());
});
globalThis.addEventListener("beforeunload", () => {
  const pageNumber = visiblePageNumber();
  if (navigator.sendBeacon) {
    const payload = new FormData();
    payload.append("csrf_token", csrfToken);
    payload.append("page_number", String(pageNumber));
    navigator.sendBeacon(`/api/books/${Number(reader.dataset.bookId)}/progress`, payload);
  }
});
restoreReadingPosition();
if (understandingEnabled) {
  collectUnderstandingTopics();
  loadUnderstandingChecks();
}
updateChapterProgressUi(visiblePageNumber());

// --- Regua de foco (UC-18) ---
let rulerEnabled = false;
let rulerY = Math.round(globalThis.innerHeight / 2);
let rulerEl = null;
let rulerBand = null;
let rulerTop = null;
let rulerBottom = null;
let rulerHud = null;
let rulerTimerEl = null;
let rulerInterval = null;
let rulerSeconds = 0;

function formatRulerTime(seconds) {
  const m = String(Math.floor(seconds / 60)).padStart(2, "0");
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function createRulerElement() {
  const el = document.createElement("div");
  el.className = "reader-ruler";
  el.setAttribute("aria-hidden", "true");
  rulerTop = document.createElement("div");
  rulerTop.className = "reader-ruler-overlay reader-ruler-overlay--top";
  rulerBand = document.createElement("div");
  rulerBand.className = "reader-ruler-band";
  rulerBottom = document.createElement("div");
  rulerBottom.className = "reader-ruler-overlay reader-ruler-overlay--bottom";
  el.appendChild(rulerTop);
  el.appendChild(rulerBand);
  el.appendChild(rulerBottom);
  return el;
}

function createHud() {
  const hud = document.createElement("div");
  hud.className = "ruler-hud";
  hud.setAttribute("aria-live", "off");

  rulerTimerEl = document.createElement("span");
  rulerTimerEl.className = "ruler-hud-timer";
  rulerTimerEl.setAttribute("aria-label", "Tempo em modo foco");
  rulerTimerEl.textContent = "00:00";

  const closeBtn = document.createElement("button");
  closeBtn.className = "ruler-hud-close";
  closeBtn.setAttribute("aria-label", "Sair do modo foco");
  closeBtn.textContent = "x";
  closeBtn.addEventListener("click", disableRuler);

  hud.appendChild(rulerTimerEl);
  hud.appendChild(closeBtn);
  return hud;
}

function updateRulerPosition() {
  if (!rulerEl || !rulerBand || !rulerTop || !rulerBottom) return;
  const bandHeight = rulerBand.offsetHeight || 48;
  const half = Math.round(bandHeight / 2);
  const topY = Math.max(0, rulerY - half);
  const bottomY = Math.min(globalThis.innerHeight, rulerY + half);
  rulerBand.style.top = `${topY}px`;
  rulerTop.style.height = `${topY}px`;
  rulerBottom.style.top = `${bottomY}px`;
  rulerBottom.style.height = `${Math.max(0, globalThis.innerHeight - bottomY)}px`;
}

function setRulerToggleState(active) {
  if (!rulerToggle) return;
  rulerToggle.classList.toggle("active", active);
  rulerToggle.setAttribute("aria-pressed", String(active));
  rulerToggle.setAttribute("aria-label", active ? "Desativar regua de foco" : "Ativar regua de foco");
}

function enableRuler() {
  rulerEnabled = true;
  rulerY = Math.round(globalThis.innerHeight / 2);
  rulerEl = createRulerElement();
  document.body.appendChild(rulerEl);
  document.body.classList.add("ruler-active");
  updateRulerPosition();

  rulerSeconds = 0;
  rulerHud = createHud();
  document.body.appendChild(rulerHud);
  rulerInterval = globalThis.setInterval(() => {
    rulerSeconds += 1;
    if (rulerTimerEl) rulerTimerEl.textContent = formatRulerTime(rulerSeconds);
  }, 1000);

  try { localStorage.setItem("studypdf_ruler_enabled", "1"); } catch (_) { /* ignore */ }
  setRulerToggleState(true);
}

function disableRuler() {
  rulerEnabled = false;
  rulerEl?.remove();
  rulerEl = null;
  rulerBand = null;
  rulerTop = null;
  rulerBottom = null;
  rulerHud?.remove();
  rulerHud = null;
  rulerTimerEl = null;
  globalThis.clearInterval(rulerInterval);
  rulerInterval = null;
  rulerSeconds = 0;
  document.body.classList.remove("ruler-active");
  try { localStorage.setItem("studypdf_ruler_enabled", "0"); } catch (_) { /* ignore */ }
  setRulerToggleState(false);
}

rulerToggle?.addEventListener("click", () => {
  if (rulerEnabled) disableRuler();
  else enableRuler();
});

document.addEventListener("mousemove", (event) => {
  if (!rulerEnabled) return;
  rulerY = event.clientY;
  updateRulerPosition();
}, { passive: true });

document.addEventListener("keydown", (event) => {
  if (!rulerEnabled) return;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    const step = rulerBand?.offsetHeight || 48;
    rulerY = event.key === "ArrowDown"
      ? Math.min(globalThis.innerHeight, rulerY + step)
      : Math.max(0, rulerY - step);
    updateRulerPosition();
  }
});

try {
  if (localStorage.getItem("studypdf_ruler_enabled") === "1") enableRuler();
} catch (_) { /* ignore */ }
