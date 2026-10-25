"""
Turnitout DOCX In-Place Processor
Preserves Word styles, runs, formatting, tables, and typography
while humanizing text content in-place.
"""

import os
from typing import Dict, Any
from docx import Document
from .engine import HumanizerEngine

class DocxProcessor:
    def __init__(self, engine: HumanizerEngine):
        self.engine = engine

    def extract_text(self, input_path: str) -> Dict[str, Any]:
        """
        Extracts all paragraph and table text from a .docx file for preview.
        """
        doc = Document(input_path)
        lines = []
        for p in doc.paragraphs:
            t = p.text.strip()
            if t:
                lines.append(t)
        for t_idx, table in enumerate(doc.tables):
            lines.append(f"\n[Table {t_idx + 1}]")
            for row in table.rows:
                # Deduplicate identical adjacent cells caused by merged horizontal cells
                row_texts = []
                for cell in row.cells:
                    ct = cell.text.strip()
                    if ct and (not row_texts or row_texts[-1] != ct):
                        row_texts.append(ct)
                if row_texts:
                    lines.append(" | ".join(row_texts))

        full_text = "\n\n".join(lines)
        return {
            "text": full_text,
            "paragraphs": len(doc.paragraphs),
            "tables": len(doc.tables),
            "word_count": len(full_text.split()),
        }

    def process_file(self, input_path: str, output_path: str, intensity: float = 0.6) -> Dict[str, Any]:
        """
        Processes a .docx file in-place, rewriting text while preserving document structure.
        """
        doc = Document(input_path)
        total_changes = 0
        total_watermarks = 0
        total_paragraphs = 0

        # Process main document paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            total_paragraphs += 1

            # Process paragraph
            result = self.engine.process(p.text, intensity=intensity)
            total_changes += result["changes_count"]
            total_watermarks += result["watermarks_found"]

            if result["changes_count"] > 0 or result["watermarks_found"] > 0:
                # Update paragraph text while preserving first run style if possible
                if len(p.runs) > 0:
                    # Update first run with new text, clear others to maintain paragraph formatting
                    p.runs[0].text = result["cleaned_text"]
                    for run in p.runs[1:]:
                        run.text = ""
                else:
                    p.text = result["cleaned_text"]

        # Process tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        text = p.text.strip()
                        if not text:
                            continue
                        result = self.engine.process(p.text, intensity=intensity)
                        total_changes += result["changes_count"]
                        total_watermarks += result["watermarks_found"]
                        if result["changes_count"] > 0:
                            if len(p.runs) > 0:
                                p.runs[0].text = result["cleaned_text"]
                                for run in p.runs[1:]:
                                    run.text = ""
                            else:
                                p.text = result["cleaned_text"]

        # Process headers and footers
        for section in doc.sections:
            for header_p in section.header.paragraphs:
                if header_p.text.strip():
                    res = self.engine.process(header_p.text, intensity=intensity)
                    if res["changes_count"] > 0:
                        header_p.text = res["cleaned_text"]
            for footer_p in section.footer.paragraphs:
                if footer_p.text.strip():
                    res = self.engine.process(footer_p.text, intensity=intensity)
                    if res["changes_count"] > 0:
                        footer_p.text = res["cleaned_text"]

        doc.save(output_path)

        return {
            "total_paragraphs": total_paragraphs,
            "total_changes": total_changes,
            "total_watermarks": total_watermarks,
            "output_path": output_path
        }

