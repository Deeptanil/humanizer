"""
Smart Academic Document Chunker (10,000+ Word Thesis Support)
Splits arbitrarily large documents (10k-50k+ words) into paragraph-aligned,
token-safe chunks (~250-320 words) while locking section headings, blank lines,
and reference blocks so structure is 100% preserved.
"""

import re
from typing import List, Dict, Any
from .detector import split_sentences

HEADING_REGEX = re.compile(
    r"^(?:"
    r"#{1,6}\s+.+|"                                  # Markdown headings
    r"\[Table\s+\d+\]|"                              # Table markers
    r"(?:chapter|section|part|appendix)\s+[0-9ivxlcdm]+.*|"  # Chapter/Section headers
    r"\d+(?:\.\d+)*\.?\s+[A-Z0-9][^.!?]{1,85}|"      # Numbered headings: "1. Abstract & Problem Statement"
    r"(?:abstract|introduction|literature\s+review|methodology|methods|results|discussion|conclusion|references|bibliography|acknowledgements)"
    r")$",
    re.IGNORECASE,
)


def is_heading_line(line: str) -> bool:
    """Determines whether a line is a section/chapter heading or short data row that must remain untouched."""
    stripped = line.strip()
    if not stripped:
        return False
    # Short pipe-delimited table rows (e.g. "Metric | Value", "Latency | 12ms") are locked;
    # long prose table rows (>14 words) are humanized.
    if "|" in stripped:
        return len(stripped.split()) <= 14
    if stripped.startswith(("-", "*", "•")):
        return False
    if stripped.endswith((".", "!", "?", ";", ":", ",")):
        return False
    words = stripped.split()
    if len(words) > 12:
        return False
    if HEADING_REGEX.match(stripped):
        return True
    # Short title-like line without ending punctuation (e.g., "Architectural Overview & Specs")
    if len(words) <= 8 and stripped[0].isupper():
        return True
    return False


def split_oversized_paragraph(paragraph: str, max_words: int = 280) -> List[str]:
    """
    If a single paragraph exceeds `max_words`, splits it cleanly on sentence boundaries
    into sub-blocks of ~max_words so it never overflows LLM token windows.
    """
    words = paragraph.split()
    if len(words) <= max_words:
        return [paragraph]

    sentences = split_sentences(paragraph)
    if len(sentences) <= 1:
        return [paragraph]

    blocks: List[str] = []
    current_sents: List[str] = []
    current_words = 0

    for sent in sentences:
        sw = len(sent.split())
        if current_sents and (current_words + sw > max_words):
            blocks.append(" ".join(current_sents))
            current_sents = [sent]
            current_words = sw
        else:
            current_sents.append(sent)
            current_words += sw

    if current_sents:
        blocks.append(" ".join(current_sents))

    return blocks


def chunk_document(text: str, max_words_per_chunk: int = 260) -> List[Dict[str, Any]]:
    """
    Splits a full thesis or long document into ordered chunks.
    Each chunk contains a list of line items (either locked headings/blank lines or prose paragraphs)
    totaling up to `max_words_per_chunk` words.
    """
    if not text or not text.strip():
        return []

    raw_lines = text.split("\n")
    chunks: List[Dict[str, Any]] = []
    current_lines: List[str] = []
    current_words = 0

    def _flush():
        nonlocal current_lines, current_words
        if current_lines:
            chunk_text = "\n".join(current_lines)
            chunks.append({
                "index": len(chunks),
                "text": chunk_text,
                "words": current_words,
            })
            current_lines = []
            current_words = 0

    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue

        if is_heading_line(stripped):
            # If we already accumulated substantial prose, flush before starting new section
            if current_words >= 120:
                _flush()
            current_lines.append(stripped)
            continue

        # Prose paragraph
        sub_blocks = split_oversized_paragraph(stripped, max_words=max_words_per_chunk)
        for block in sub_blocks:
            bw = len(block.split())
            if current_words > 0 and (current_words + bw > max_words_per_chunk):
                _flush()
            current_lines.append(block)
            current_words += bw

    _flush()
    return chunks

