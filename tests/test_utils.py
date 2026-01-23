from app.services.utils import normalize_text


def test_normalize_accented_characters():
    """Accented and non-accented versions normalize to the same string."""
    assert normalize_text("Beyoncé") == normalize_text("Beyonce")


def test_normalize_umlauts():
    """Umlaut characters are converted to ASCII equivalents."""
    assert normalize_text("Mötley Crüe") == normalize_text("Motley Crue")


def test_normalize_special_characters():
    """Special characters are stripped, so 'AC/DC' matches 'acdc'."""
    assert normalize_text("AC/DC") == normalize_text("acdc")


def test_normalize_apostrophes():
    """Apostrophes are stripped during normalization."""
    assert normalize_text("Guns N' Roses") == normalize_text("Guns N Roses")


def test_normalize_case_insensitive():
    """Normalization is case-insensitive."""
    assert normalize_text("RADIOHEAD") == normalize_text("radiohead")
