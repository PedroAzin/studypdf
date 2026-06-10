from .text import normalize_tags


def note_type_options(note_types):
    preferred = ["DUVIDA", "ANOTACAO", "DESTAQUE", "TRABALHO", "REVISAR"]
    return [note_type for note_type in preferred if note_type in note_types]


def note_form_data(source):
    return {
        "page_number": source.get("page_number"),
        "selected_text": (source.get("selected_text") or "").strip(),
        "note_type": (source.get("note_type") or "").strip().upper(),
        "note_text": (source.get("note_text") or "").strip(),
        "tags": normalize_tags(source.get("tags")),
    }


def selected_context(page_text, selected_text, radius=900):
    if not page_text:
        return "", ""
    index = page_text.lower().find((selected_text or "").lower())
    if index < 0:
        return page_text[:radius].strip(), page_text[-radius:].strip()
    before = page_text[max(0, index - radius) : index].strip()
    after_start = index + len(selected_text or "")
    after = page_text[after_start : after_start + radius].strip()
    return before, after
