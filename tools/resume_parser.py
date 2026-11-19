"""
Resume parsing tools — extracts text from PDF and DOCX files.
"""
import logging
import re
from pathlib import Path

from tools.validators import validate_file_path

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    import fitz  # PyMuPDF

    try:
        # Validate path
        path = validate_file_path(file_path)
    except ValueError as e:
        logger.error(f"Invalid PDF path: {e}")
        raise FileNotFoundError(f"Resume not found or path invalid: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected PDF file, got: {path.suffix}")

    text_blocks = []
    with fitz.open(str(path)) as doc:
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                text_blocks.append(text)
            logger.debug(f"Page {page_num + 1}: {len(text)} chars extracted")

    full_text = "\n".join(text_blocks)
    logger.info(f"PDF parsed: {len(full_text)} chars from {len(text_blocks)} pages")
    return _clean_text(full_text)


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    from docx import Document

    try:
        # Validate path
        path = validate_file_path(file_path)
    except ValueError as e:
        logger.error(f"Invalid DOCX path: {e}")
        raise FileNotFoundError(f"Resume not found or path invalid: {file_path}")

    if path.suffix.lower() != ".docx":
        raise ValueError(f"Expected DOCX file, got: {path.suffix}")

    doc = Document(str(path))
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text.strip())

    # Also extract from tables (some resumes use tables for layout)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    paragraphs.append(cell.text.strip())

    full_text = "\n".join(paragraphs)
    logger.info(f"DOCX parsed: {len(full_text)} chars from {len(paragraphs)} paragraphs")
    return _clean_text(full_text)


def parse_resume(file_path: str) -> str:
    """Parse a resume file (PDF or DOCX) and return clean text."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".docx":
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use PDF or DOCX.")


def _clean_text(text: str) -> str:
    """Clean extracted text — normalize whitespace, remove artifacts."""
    # Replace multiple spaces/tabs with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace 3+ newlines with 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove common PDF artifacts
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Strip lines
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()
