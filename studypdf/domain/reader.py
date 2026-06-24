import re

from .text import clean_text


def sanitize_reader_html(value):
    if not value:
        return value
    return value.replace(" dropcap", "").replace("dropcap ", "").replace("dropcap", "")


def percent_read(last_page, total_pages):
    if not total_pages:
        return 0
    return min(100, max(0, round(((last_page or 1) / total_pages) * 100)))


def nav_progress(start_page, end_page, current_page):
    if not start_page:
        return 0
    current_page = current_page or 1
    if current_page < start_page:
        return 0
    if current_page >= end_page:
        return 100
    span = max(1, end_page - start_page + 1)
    return min(99, max(1, round(((current_page - start_page + 1) / span) * 100)))


def roman_numeral(value):
    pairs = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    number = max(1, int(value or 1))
    result = []
    for decimal, roman in pairs:
        while number >= decimal:
            result.append(roman)
            number -= decimal
    return "".join(result)


def is_book_chapter_title(title):
    text = clean_text(title or "")
    return bool(
        re.match(r"^(chapter|capitulo|capÃ­tulo)\s+(\d+|[ivxlcdm]+)\b", text, flags=re.I)
    )


def visible_book_chapters(chapters, total_pages=None, limit=None):
    rows = [dict(chapter) for chapter in chapters]
    filtered = [chapter for chapter in rows if is_book_chapter_title(chapter["title"])]
    if not filtered:
        filtered = rows

    result = []
    for index, chapter in enumerate(filtered, start=1):
        item = dict(chapter)
        next_start = filtered[index]["start_page"] if index < len(filtered) else None
        item["end_page"] = _chapter_end_page(item["start_page"], next_start, total_pages)
        item["roman"] = roman_numeral(index)
        result.append(item)

    return result[:limit] if limit else result


def build_chapter_nav(chapters, total_pages, last_page_read):
    real_chapters = [chapter for chapter in chapters if is_book_chapter_title(chapter["title"])]
    real_chapter_ids = {chapter["id"] for chapter in real_chapters}
    real_chapter_indexes = {chapter["id"]: index for index, chapter in enumerate(real_chapters)}
    return [
        _chapter_nav_item(index, chapter, real_chapters, real_chapter_ids, real_chapter_indexes, total_pages, last_page_read)
        for index, chapter in enumerate(chapters, start=1)
    ]


def real_chapter_ranges(chapters, total_pages):
    real_chapters = [chapter for chapter in chapters if is_book_chapter_title(chapter["title"])]
    return [
        {
            "title": chapter["title"],
            "start_page": chapter["start_page"],
            "end_page": _chapter_end_page(
                chapter["start_page"],
                real_chapters[index + 1]["start_page"] if index + 1 < len(real_chapters) else None,
                total_pages,
            ),
        }
        for index, chapter in enumerate(real_chapters)
    ]


def _chapter_nav_item(index, chapter, real_chapters, real_chapter_ids, real_chapter_indexes, total_pages, last_page_read):
    item = dict(chapter)
    item["roman"] = roman_numeral(index)
    if chapter["id"] not in real_chapter_ids:
        item["show_progress"] = False
        item["chapter_roman"] = item["roman"]
        item["progress"] = None
        return item

    real_index = real_chapter_indexes[chapter["id"]]
    next_chapter = real_chapters[real_index + 1] if real_index + 1 < len(real_chapters) else None
    item["show_progress"] = True
    item["chapter_roman"] = roman_numeral(real_index + 1)
    item["end_page"] = _chapter_end_page(item["start_page"], next_chapter["start_page"] if next_chapter else None, total_pages)
    item["progress"] = nav_progress(item["start_page"], item["end_page"], last_page_read)
    return item


def _chapter_end_page(start_page, next_start, total_pages):
    if next_start:
        return max(start_page, next_start - 1)
    return total_pages or start_page
