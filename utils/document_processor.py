"""Document extraction, validation, and sanitization for TXT, PDF, and DOCX files.
All processing is performed strictly locally on the user's device.
"""

import io
from typing import Tuple, Dict, Any
from pypdf import PdfReader
from docx import Document

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_TEXT_CHARACTERS = 75_000  # Conservative cutoff for local LLM context budgets
MIN_TEXT_CHARACTERS = 25


class DocumentProcessingError(Exception):
    """Custom exception raised when document parsing fails."""
    pass


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract and decode text from raw TXT bytes using multiple encoding fallbacks."""
    if not file_bytes:
        return ""
    
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
    for enc in encodings:
        try:
            return file_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    # Fallback with replacement of un-decodable characters
    return file_bytes.decode("utf-8", errors="replace")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF pages using pypdf."""
    if not file_bytes:
        return ""
    try:
        stream = io.BytesIO(file_bytes)
        reader = PdfReader(stream)
        pages_text = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages_text.append(f"--- [Page {idx + 1}] ---\n{page_text.strip()}")
        
        extracted = "\n\n".join(pages_text).strip()
        if not extracted:
            raise DocumentProcessingError(
                "No selectable text found in the PDF. It might be a scanned image or protected document."
            )
        return extracted
    except DocumentProcessingError:
        raise
    except Exception as exc:
        raise DocumentProcessingError(f"Failed to read PDF document: {str(exc)}") from exc


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from Microsoft Word (.docx) paragraphs and tables."""
    if not file_bytes:
        return ""
    try:
        stream = io.BytesIO(file_bytes)
        doc = Document(stream)
        paragraphs = []
        
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                paragraphs.append(text)
        
        # Also extract table cells
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
                    
        extracted = "\n\n".join(paragraphs).strip()
        if not extracted:
            raise DocumentProcessingError("The DOCX document does not contain readable text.")
        return extracted
    except DocumentProcessingError:
        raise
    except Exception as exc:
        raise DocumentProcessingError(f"Failed to read DOCX document: {str(exc)}") from exc


def sanitize_text(text: str) -> str:
    """Normalizes whitespace and removes null bytes."""
    if not text:
        return ""
    text = text.replace("\x00", "")
    lines = [line.strip() for line in text.splitlines()]
    # Collapse consecutive blank lines
    collapsed = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                collapsed.append("")
                prev_blank = True
        else:
            collapsed.append(line)
            prev_blank = False
    return "\n".join(collapsed).strip()


def validate_text_content(text: str) -> Tuple[bool, str]:
    """Validates if input text is non-empty and of adequate length."""
    cleaned = text.strip() if text else ""
    if not cleaned:
        return False, "Notes are empty. Please paste text or upload a document."
    if len(cleaned) < MIN_TEXT_CHARACTERS:
        return False, f"Notes are too brief ({len(cleaned)} chars). Please provide at least {MIN_TEXT_CHARACTERS} characters for high-yield study aids."
    return True, ""


def process_uploaded_document(filename: str, file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """
    Validates file size, extracts text by extension, sanitizes, and returns metadata.
    """
    size_bytes = len(file_bytes)
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise DocumentProcessingError(
            f"File exceeds the maximum limit of {MAX_FILE_SIZE_MB} MB (file size: {size_bytes / (1024*1024):.1f} MB)."
        )
    
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "txt":
        raw_text = extract_text_from_txt(file_bytes)
    elif ext == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        if ext == "doc":
            raise DocumentProcessingError("Legacy .doc format is not supported. Please save as modern .docx or .txt.")
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raise DocumentProcessingError(f"Unsupported file format: .{ext}. Supported formats are .txt, .pdf, and .docx.")
    
    clean_text = sanitize_text(raw_text)
    
    is_truncated = False
    original_char_count = len(clean_text)
    if original_char_count > MAX_TEXT_CHARACTERS:
        clean_text = clean_text[:MAX_TEXT_CHARACTERS]
        is_truncated = True

    word_count = len(clean_text.split())
    metadata = {
        "filename": filename,
        "extension": ext,
        "size_kb": round(size_bytes / 1024, 1),
        "character_count": len(clean_text),
        "word_count": word_count,
        "is_truncated": is_truncated,
        "original_char_count": original_char_count,
    }
    return clean_text, metadata
