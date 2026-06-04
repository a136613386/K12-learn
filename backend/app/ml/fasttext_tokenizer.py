import re


TOKENIZATION_MODE = "char_with_ascii_chunks"


def tokenize_text(text: str) -> str:
    tokens: list[str] = []
    buffer: list[str] = []

    def flush_buffer() -> None:
        if buffer:
            tokens.append("".join(buffer))
            buffer.clear()

    for char in text.strip():
        if char.isspace():
            flush_buffer()
            continue
        if re.match(r"[A-Za-z0-9_+\-*/=<>^:.%]+", char):
            buffer.append(char)
            continue
        flush_buffer()
        if _is_cjk(char):
            tokens.append(char)

    flush_buffer()
    return " ".join(tokens)


def _is_cjk(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"
