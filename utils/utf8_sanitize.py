import re

# Remove lone UTF-16 surrogate code points that cannot be encoded to UTF-8
_SURROGATE_RE = re.compile('[\uD800-\uDFFF]')

def sanitize_for_utf8(text: str) -> str:
    """Return a UTF-8-safe string by removing surrogate code points.

    This helps when you have strings containing surrogate characters that
    cannot be encoded with utf-8 and would raise UnicodeEncodeError.
    """
    if not isinstance(text, str):
        return text
    if _SURROGATE_RE.search(text):
        cleaned = _SURROGATE_RE.sub('', text)
        return cleaned
    return text


def to_utf8_bytes(text: str) -> bytes:
    """Encode text to UTF-8, sanitizing surrogates first."""
    safe_text = sanitize_for_utf8(text)
    return safe_text.encode('utf-8', 'replace')
