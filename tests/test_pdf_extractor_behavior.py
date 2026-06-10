from pathlib import Path

import fitz

from studypdf.pdf.extractor import (
    block_kind,
    block_text,
    chapter_candidates,
    clean_pdf_text,
    detect_chapters,
    extract_pdf_pages,
    format_span,
    page_text_to_html,
    render_block,
    render_text_block,
    save_image,
    slugify,
)


def text_block(text, size=11, flags=0, font="Times-Roman"):
    return {
        "type": 0,
        "bbox": [0, 0, 100, 100],
        "lines": [{"spans": [{"text": text, "size": size, "flags": flags, "font": font}]}],
    }


def test_text_cleanup_and_basic_html_rendering():
    assert page_text_to_html("") == '<p class="empty-page">Sem texto extraido nesta pagina.</p>'
    assert page_text_to_html("A&B\n\nNext") == "<p>A&amp;B</p>\n<p>Next</p>"
    assert clean_pdf_text("hy-\n phenated\n text") == "hyphenated text"
    assert slugify("Chapter 1: Reliable Systems!") == "chapter-1-reliable-systems"
    assert slugify("###") == "chapter"


def test_text_blocks_preserve_emphasis_and_semantic_kinds():
    bold = {"text": "Bold", "size": 12, "flags": 16, "font": "Times"}
    italic = {"text": "Italic", "size": 12, "flags": 2, "font": "Times"}

    assert format_span(bold) == "<strong>Bold</strong>"
    assert format_span(italic) == "<em>Italic</em>"
    assert block_kind(text_block("Chapter title", size=20), False) == "heading"
    assert block_kind(text_block("Compact title", size=14, flags=16), False) == "subheading"
    assert block_kind(text_block("Quoted words", size=11, flags=2), False) == "quote"
    assert block_kind(text_block("1. Item", size=11), False) == "list-item"
    assert block_kind(text_block("Lead paragraph", size=11), True) == "lead-paragraph"

    rendered, next_is_lead = render_text_block(text_block("Main Heading", size=20), False)
    assert rendered == '<h2 class="book-heading">Main Heading</h2>'
    assert next_is_lead is True

    rendered, _ = render_text_block(text_block("1. First item", size=11), False)
    assert rendered == '<p class="book-list-item">First item</p>'
    assert block_text(text_block("multi\nline", size=11)) == "multi line"


def test_image_blocks_write_assets_and_render_figures(tmp_path):
    small_image = {"type": 1, "width": 10, "height": 10, "image": b"too-small", "ext": "png"}
    assert save_image(small_image, tmp_path, 1, 1) is None

    image = {"type": 1, "width": 400, "height": 300, "image": b"image-bytes", "ext": "png"}
    filename = save_image(image, tmp_path, 3, 2)

    assert filename.startswith("page-003-img-02-")
    assert (tmp_path / filename).read_bytes() == b"image-bytes"

    html, text, next_index, lead = render_block(image, 3, tmp_path, 42, 2, False)
    assert '/books/42/assets/page-003-img-02-' in html
    assert text == ""
    assert next_index == 3
    assert lead is False


def test_detect_chapters_filters_toc_to_real_book_chapters(tmp_path):
    pdf_path = tmp_path / "toc.pdf"
    doc = fitz.open()
    for label in ["Preface", "Chapter 1. Reliable Systems", "Chapter 2. Data Models"]:
        page = doc.new_page()
        page.insert_text((72, 72), label)
    doc.set_toc([
        [1, "Preface", 1],
        [1, "Chapter 1. Reliable Systems", 2],
        [1, "Appendix", 3],
        [1, "Chapter 2. Data Models", 3],
    ])
    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    try:
        assert [item["title"] for item in chapter_candidates(doc.get_toc())] == [
            "Chapter 1. Reliable Systems",
            "Chapter 2. Data Models",
        ]
        chapters = detect_chapters(doc)
    finally:
        doc.close()

    assert chapters[0]["slug"] == "01-chapter-1-reliable-systems"
    assert chapters[0]["start_page"] == 2
    assert chapters[0]["end_page"] == 2
    assert chapters[1]["end_page"] == 3


def test_extract_pdf_pages_returns_text_html_and_chapters(tmp_path):
    pdf_path = tmp_path / "book.pdf"
    doc = fitz.open()
    first = doc.new_page()
    first.insert_text((72, 72), "Chapter 1. Reliable Systems", fontsize=20)
    first.insert_text((72, 110), "Systems should handle faults.", fontsize=11)
    second = doc.new_page()
    second.insert_text((72, 72), "Chapter 2. Data Models", fontsize=20)
    second.insert_text((72, 110), "Models shape applications.", fontsize=11)
    doc.set_toc([[1, "Chapter 1. Reliable Systems", 1], [1, "Chapter 2. Data Models", 2]])
    doc.save(pdf_path)
    doc.close()

    pages, chapters = extract_pdf_pages(pdf_path, tmp_path / "assets", book_id=7)

    assert len(pages) == 2
    assert "Systems should handle faults." in pages[0]["text_content"]
    assert 'class="book-heading"' in pages[0]["html_content"]
    assert [chapter["title"] for chapter in chapters] == [
        "Chapter 1. Reliable Systems",
        "Chapter 2. Data Models",
    ]
