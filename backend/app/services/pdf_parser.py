"""
PDF text extraction only — no structural parsing.
Structure parsing is handled by llm_parser.py via LLM calls.
"""
import pdfplumber
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a text-based PDF using pdfplumber.
    Returns the raw concatenated text of all pages.
    Raises ValueError if the file cannot be read or yields no text.
    """
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text(x_tolerance=2, y_tolerance=3)
                if text and text.strip():
                    pages.append(text.strip())
    except Exception as e:
        raise ValueError(
            f"Cannot read PDF: {e}. "
            "Ensure the file is a text-based PDF, not a scanned image."
        )

    if not pages:
        raise ValueError(
            "No text could be extracted from this PDF. "
            "Ensure it is a text-based PDF (you can select/copy text in a PDF viewer), "
            "not a scanned image."
        )

    full_text = "\n\n".join(pages)
    logger.info(
        f"Extracted {len(full_text):,} chars across {len(pages)} pages from {pdf_path}"
    )
    return full_text
