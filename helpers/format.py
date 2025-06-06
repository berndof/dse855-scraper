import re


def to_snake_case(text: str) -> str:
    text = text.replace("/", " ")  # Substitui barras por espaço
    text = re.sub(r"[\s\-]+", "_", text.strip())  # Espaços ou hífens viram underscore
    return text.lower()