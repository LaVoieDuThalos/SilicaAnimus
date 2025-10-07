from unidecode import unidecode


def normalize_name(name: str) -> str:
    out = unidecode(name.strip("\"' ").lower())
    return out
