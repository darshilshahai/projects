import re
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.config import settings
from app.rag import store as store_module
from app.rag.chunking import chunk_documents

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".md", ".pdf"}


def _is_pdf(data: bytes) -> bool:
    return len(data) >= 5 and data[:5].startswith(b"%PDF-")


def _is_utf8_text(data: bytes) -> bool:
    if b"\x00" in data[:8192]:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def validate_file_content(data: bytes, suffix: str) -> None:
    if suffix == ".pdf":
        if not _is_pdf(data):
            raise ValueError("File content is not a valid PDF")
        return
    if _is_pdf(data):
        raise ValueError("File looks like a PDF — upload it via the PDF tab")
    if not _is_utf8_text(data):
        raise ValueError("Markdown file must be plain UTF-8 text")


def sanitize_filename(name: str, default_ext: str = ".md") -> str:
    name = Path(name).name
    stem = re.sub(r"[^\w.\-]", "_", name).strip("._")
    if not stem:
        raise ValueError("Invalid filename")
    path = Path(stem)
    suffix = path.suffix.lower()
    if suffix in ALLOWED_EXTENSIONS:
        return path.name
    return f"{path.stem}{default_ext}"


def extract_pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    text = "\n\n".join(parts).strip()
    if not text:
        raise ValueError("PDF contains no extractable text")
    return text


def _persist_and_index(source: str, file_bytes: bytes, index_text: str) -> dict:
    store = store_module.store
    if store is None:
        raise RuntimeError("Store not initialized")

    docs_path = Path(settings.docs_folder)
    docs_path.mkdir(parents=True, exist_ok=True)
    (docs_path / source).write_bytes(file_bytes)

    chunks = chunk_documents(
        [{"source": source, "text": index_text}],
        target_size=settings.chunk_size,
    )
    store.delete_source(source)
    chunks_added = store.add_chunks(source, chunks)

    return {
        "source": source,
        "chunks_added": chunks_added,
        "total_chunks": store.count(),
    }


def ingest_text(title: str, text: str) -> dict:
    source = sanitize_filename(title, default_ext=".md")
    content = text.strip()
    if not content:
        raise ValueError("Document text cannot be empty")
    return _persist_and_index(
        source,
        content.encode("utf-8"),
        content,
    )


def ingest_file(filename: str, data: bytes) -> dict:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds 5 MB limit")

    source = sanitize_filename(filename)
    suffix = Path(source).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Only .md and .pdf files are supported")

    validate_file_content(data, suffix)

    if suffix == ".md":
        try:
            index_text = data.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError("Markdown file must be valid UTF-8") from exc
        if not index_text:
            raise ValueError("Markdown file is empty")
    else:
        index_text = extract_pdf_text(data)

    return _persist_and_index(source, data, index_text)
