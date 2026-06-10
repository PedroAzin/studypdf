import re


def clean_text(text):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def slugify(value):
    value = clean_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def normalize_tags(value):
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str):
        return value.strip()
    return ""
