import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<![\d-])(?!\d{4}-\d{2}-\d{2})\+?\d[\d\s-]{8,}\d")


def mask(text: str) -> str:
    return _PHONE.sub("[PHONE]", _EMAIL.sub("[EMAIL]", text or ""))
