import re
from unidecode import unidecode


def normalize_text(name: str) -> str:
    """
    Normalize text for comparison.

    Converts accented characters to ASCII equivalents, removes
    non-alphanumeric characters, and lowercases. This ensures
    user input like 'Beyonce' matches API responses like 'Beyoncé'.
    """
    return re.sub(r"[^a-z0-9]", "", unidecode(name).lower())
