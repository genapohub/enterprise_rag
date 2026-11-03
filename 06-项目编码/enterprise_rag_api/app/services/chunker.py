"""Recursive character chunking: size 800 / overlap 120."""
from typing import List


def split_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    separators = ["\n\n", "\n", "。", "！", "？", "；", " ", ""]
    return _split(text, separators, chunk_size, overlap)


def _split(text: str, separators: List[str], chunk_size: int, overlap: int) -> List[str]:
    if len(text) <= chunk_size:
        return [text]
    sep = separators[0] if separators else ""
    rest_seps = separators[1:] if separators else []
    if sep == "":
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = max(0, end - overlap)
        return chunks
    parts = text.split(sep) if sep else [text]
    chunks: List[str] = []
    buf = ""
    for i, part in enumerate(parts):
        piece = part if i == len(parts) - 1 else part + sep
        if len(piece) > chunk_size:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_split(piece, rest_seps, chunk_size, overlap))
            continue
        if len(buf) + len(piece) <= chunk_size:
            buf += piece
        else:
            if buf:
                chunks.append(buf)
            # overlap from previous
            if overlap > 0 and chunks:
                tail = chunks[-1][-overlap:]
                buf = tail + piece
                if len(buf) > chunk_size:
                    buf = piece
            else:
                buf = piece
    if buf:
        chunks.append(buf)
    # hard cap
    final: List[str] = []
    for c in chunks:
        if len(c) <= 1200:
            final.append(c)
        else:
            final.extend(_split(c, [""], chunk_size, overlap))
    return final
