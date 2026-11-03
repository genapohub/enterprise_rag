"""Document text extraction: txt/md (+ optional pdf/docx)."""
from pathlib import Path


def extract_text(path: str, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    raw = Path(path).read_bytes()
    if suffix in {".txt", ".md"}:
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("gb18030", errors="replace")
    if suffix == ".pdf":
        try:
            import fitz  # pymupdf
        except ImportError as exc:
            raise RuntimeError("PyMuPDF 未安装，无法解析 PDF") from exc
        doc = fitz.open(stream=raw, filetype="pdf")
        parts = []
        for i, page in enumerate(doc):
            parts.append(page.get_text() or "")
        doc.close()
        text = "\n".join(parts).strip()
        if not text:
            raise RuntimeError("PDF 未抽出文本（可能是扫描件，本期不做 OCR）")
        return text
    if suffix == ".docx":
        try:
            import io
            from docx import Document as Docx
        except ImportError as exc:
            raise RuntimeError("python-docx 未安装，无法解析 Word") from exc
        d = Docx(io.BytesIO(raw))
        text = "\n".join(p.text for p in d.paragraphs if p.text).strip()
        if not text:
            raise RuntimeError("Word 文档无有效段落文本")
        return text
    raise RuntimeError(f"不支持的文件类型: {suffix}")
