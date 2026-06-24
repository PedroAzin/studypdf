import hashlib
import html
import re

import fitz

from studypdf.config import MIN_IMAGE_HEIGHT, MIN_IMAGE_WIDTH, SOFT_HYPHENS
from studypdf.domain.reader import is_book_chapter_title


def page_text_to_html(text):
    paragraphs = [part.strip() for part in (text or "").splitlines() if part.strip()]
    if not paragraphs:
        return '<p class="empty-page">Sem texto extraido nesta pagina.</p>'
    return "\n".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in paragraphs)


def clean_pdf_text(text):
    text = text.strip()
    text = re.sub(rf"[{SOFT_HYPHENS}][ \t\r\f\v]*\n[ \t\r\f\v]*", "", text)
    text = re.sub(rf"(?<=[A-Za-z])[{SOFT_HYPHENS}]\s+(?=[a-z])", "", text)
    text = " ".join(part.strip() for part in text.splitlines())
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def slugify(value):
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "chapter"


def is_bold(span):
    font = (span.get("font") or "").lower()
    return bool(span.get("flags", 0) & 16) or "bold" in font or "semibold" in font


def is_italic(span):
    font = (span.get("font") or "").lower()
    return bool(span.get("flags", 0) & 2) or "italic" in font or "oblique" in font or font.endswith("-it")


def format_span(span):
    text = html.escape(span.get("text", ""))
    if not text.strip():
        return text
    if is_bold(span):
        text = f"<strong>{text}</strong>"
    if is_italic(span):
        text = f"<em>{text}</em>"
    return text


def block_stats(block):
    spans = text_spans(block)
    if not spans:
        return {"avg_size": 0, "bold_ratio": 0, "italic_ratio": 0, "text": ""}
    return {
        "avg_size": sum(span.get("size", 0) for span in spans) / len(spans),
        "bold_ratio": sum(1 for span in spans if is_bold(span)) / len(spans),
        "italic_ratio": sum(1 for span in spans if is_italic(span)) / len(spans),
        "text": clean_pdf_text("".join(span.get("text", "") for span in spans)),
    }


def text_spans(block):
    return [
        span
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span.get("text", "").strip()
    ]


def block_text(block):
    parts = []
    for line in block.get("lines", []):
        line_text = "".join(span.get("text", "") for span in line.get("spans", []))
        if line_text.strip():
            parts.append(line_text.strip())
    return clean_pdf_text(" ".join(parts))


def block_text_html(block):
    lines = []
    for line in block.get("lines", []):
        spans = [format_span(span) for span in line.get("spans", []) if span.get("text", "").strip()]
        rendered = "".join(spans).strip()
        if rendered:
            lines.append(rendered)
    return clean_rendered_text("\n".join(lines).strip())


def clean_rendered_text(text):
    text = re.sub(rf"[{SOFT_HYPHENS}][ \t\r\f\v]*\n[ \t\r\f\v]*", "", text)
    text = re.sub(rf"(?<=[A-Za-z])[{SOFT_HYPHENS}]\s+(?=[a-z])", "", text)
    text = " ".join(part.strip() for part in text.splitlines())
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def block_kind(block, is_section_lead):
    stats = block_stats(block)
    text = stats["text"]
    if not text:
        return "empty"
    if stats["avg_size"] >= 18:
        return "heading"
    if stats["avg_size"] >= 13.5 and (stats["bold_ratio"] >= 0.45 or len(text) <= 90):
        return "subheading"
    if stats["italic_ratio"] >= 0.35 and stats["avg_size"] <= 12:
        return "quote"
    if re.match(r"^(\u2022|[?â€¢\-*]|\d+\.|[a-zA-Z]\.)\s+", text):
        return "list-item"
    if is_section_lead:
        return "lead-paragraph"
    return "paragraph"


def render_text_block(block, is_section_lead):
    rendered = block_text_html(block)
    if not rendered:
        return "", is_section_lead

    kind = block_kind(block, is_section_lead)
    if kind == "heading":
        return f'<h2 class="book-heading">{rendered}</h2>', True
    if kind == "subheading":
        return f'<h3 class="book-subheading">{rendered}</h3>', True
    if kind == "quote":
        return f'<blockquote class="book-quote">{rendered}</blockquote>', is_section_lead
    if kind == "list-item":
        cleaned = re.sub(r"^(\u2022|[?â€¢\-*]|\d+\.|[a-zA-Z]\.)\s+", "", rendered)
        return f'<p class="book-list-item">{cleaned}</p>', is_section_lead
    if kind == "lead-paragraph":
        return f'<p class="book-paragraph section-lead">{rendered}</p>', False
    return f'<p class="book-paragraph">{rendered}</p>', is_section_lead


def save_image(block, assets_dir, page_number, image_index):
    width = block.get("width", 0)
    height = block.get("height", 0)
    image_bytes = block.get("image")
    if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT or not image_bytes:
        return None

    ext = block.get("ext") or "png"
    digest = hashlib.sha256(image_bytes).hexdigest()[:12]
    filename = f"page-{page_number:03}-img-{image_index:02}-{digest}.{ext}"
    assets_dir.mkdir(parents=True, exist_ok=True)
    path = assets_dir / filename
    if not path.exists():
        path.write_bytes(image_bytes)
    return filename


def detect_chapters(doc):
    candidates = toc_candidates(doc.get_toc())
    if not candidates:
        return []

    total_pages = len(doc)
    return [
        chapter_record(index, chapter, candidates, total_pages)
        for index, chapter in enumerate(candidates)
    ]


def chapter_candidates(toc):
    return [
        {"level": level, "title": title.strip(), "start_page": start_page}
        for level, title, start_page, *_rest in toc
        if (title or "").strip() and is_book_chapter_title(title)
    ]


def toc_candidates(toc):
    return [
        {"level": level, "title": title.strip(), "start_page": start_page}
        for level, title, start_page, *_rest in toc
        if (title or "").strip()
    ]


def chapter_record(index, chapter, candidates, total_pages):
    next_start = candidates[index + 1]["start_page"] if index < len(candidates) - 1 else None
    end_page = next_start - 1 if next_start else total_pages
    return {
        "title": chapter["title"],
        "slug": f"{index + 1:02d}-{slugify(chapter['title'])}",
        "level": chapter["level"],
        "start_page": chapter["start_page"],
        "end_page": max(chapter["start_page"], end_page),
    }


def extract_pdf_pages(pdf_path, assets_dir, book_id):
    doc = fitz.open(pdf_path)
    try:
        return extract_document(doc, assets_dir, book_id)
    finally:
        doc.close()


def extract_document(doc, assets_dir, book_id):
    chapters = detect_chapters(doc)
    pages = [
        extract_page(page, page_number, assets_dir, book_id)
        for page_number, page in enumerate(doc, start=1)
    ]
    return pages, chapters


def extract_page(page, page_number, assets_dir, book_id):
    blocks = sorted_page_blocks(page)
    html_parts = []
    text_parts = []
    image_index = 1
    is_section_lead = False

    for block in blocks:
        rendered, text, image_index, is_section_lead = render_block(
            block, page_number, assets_dir, book_id, image_index, is_section_lead
        )
        if rendered:
            html_parts.append(rendered)
        if text:
            text_parts.append(text)

    text_content = "\n".join(text_parts)
    return {
        "page_number": page_number,
        "text_content": text_content,
        "html_content": "\n".join(html_parts) or page_text_to_html(text_content),
    }


def sorted_page_blocks(page):
    blocks = page.get_text("dict").get("blocks", [])
    return sorted(blocks, key=lambda block: (block.get("bbox", [0, 0])[1], block.get("bbox", [0, 0])[0]))


def render_block(block, page_number, assets_dir, book_id, image_index, is_section_lead):
    if block.get("type") == 0:
        return render_text_content(block, is_section_lead, image_index)
    if block.get("type") == 1:
        return render_image_content(block, page_number, assets_dir, book_id, image_index, is_section_lead)
    return "", "", image_index, is_section_lead


def render_text_content(block, is_section_lead, image_index):
    text = block_text(block)
    rendered, is_section_lead = render_text_block(block, is_section_lead)
    if not text or not rendered:
        return "", "", image_index, is_section_lead
    return rendered, text, image_index, is_section_lead


def render_image_content(block, page_number, assets_dir, book_id, image_index, is_section_lead):
    filename = save_image(block, assets_dir, page_number, image_index)
    image_index += 1
    if not filename:
        return "", "", image_index, is_section_lead
    src = f"/books/{book_id}/assets/{filename}"
    html_content = (
        '<figure class="book-image">'
        f'<img src="{src}" alt="Imagem da pagina {page_number}" loading="lazy">'
        f'<figcaption>Imagem da pagina {page_number}</figcaption>'
        "</figure>"
    )
    return html_content, "", image_index, is_section_lead
