import csv
import io
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


SUPPORTED_DOCUMENT_TYPES = {"pdf", "docx", "md", "txt", "html", "htm", "csv"}


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("文本编码不受支持，请使用 UTF-8 或 GB18030")


def extract_text_bytes(data: bytes, file_type: str) -> str:
    if file_type == "pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    if file_type == "docx":
        document = DocxDocument(io.BytesIO(data))
        return "\n\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip())

    text = _decode_text(data)
    if file_type in {"html", "htm"}:
        parser = _TextHTMLParser()
        parser.feed(text)
        return "\n".join(parser.parts)
    if file_type == "csv":
        rows = csv.reader(io.StringIO(text))
        return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
    return text


def extract_text(path: Path, file_type: str) -> str:
    """Compatibility wrapper for local parser tests and one-off utilities."""

    return extract_text_bytes(path.read_bytes(), file_type)


def _group_parts(parts: list[str], size: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if current and current_length + len(part) + 1 > size:
            chunks.append("\n".join(current))
            current = []
            current_length = 0
        if len(part) > size:
            if current:
                chunks.append("\n".join(current))
                current = []
                current_length = 0
            chunks.extend(part[index:index + size] for index in range(0, len(part), size))
        else:
            current.append(part)
            current_length += len(part) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def split_text(text: str, method: str, size: int, overlap: int) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    if method == "paragraph":
        return _group_parts(re.split(r"\n\s*\n+", normalized), size)
    if method == "sentence":
        return _group_parts(re.split(r"(?<=[。！？.!?])\s*", normalized), size)

    chunks = []
    step = size - overlap
    for start in range(0, len(normalized), step):
        chunk = normalized[start:start + size].strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= len(normalized):
            break
    return chunks


def text_terms(text: str) -> list[str]:
    latin = re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())
    chinese_groups = re.findall(r"[\u4e00-\u9fff]+", text)
    chinese = []
    for group in chinese_groups:
        if len(group) == 1:
            chinese.append(group)
        else:
            chinese.extend(group[index:index + 2] for index in range(len(group) - 1))
    return latin + chinese


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    return [term for term, _ in Counter(text_terms(text)).most_common(limit)]


def estimate_tokens(text: str) -> int:
    latin_words = len(re.findall(r"[a-zA-Z0-9_]+", text))
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return max(1, latin_words + (chinese_chars + 1) // 2)
