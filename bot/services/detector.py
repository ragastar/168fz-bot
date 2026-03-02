import re

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


def detect_input_type(text: str | None, has_photo: bool) -> str:
    """Determine input type: photo, url, or text."""
    if has_photo:
        return "photo"
    if text and URL_PATTERN.search(text):
        return "url"
    return "text"
