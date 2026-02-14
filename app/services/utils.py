import re
from unidecode import unidecode


def normalize_text(name: str) -> str:
    """
    Normalize text for internal comparison only.

    Used to match user input against API responses and filter
    duplicates (e.g. exclude_same_artist). Converts accented
    characters to ASCII via unidecode, removes all non-alphanumeric
    characters (spaces, apostrophes, slashes, etc.), and lowercases.

    Examples:
        'Beyoncé' → 'beyonce'
        'AC/DC' → 'acdc'
        'Mötley Crüe' → 'motleycrue'
        'Guns N' Roses' → 'gunsnroses'

    Not used for display or API queries.
    """
    return re.sub(r"[^a-z0-9]", "", unidecode(name).lower())
