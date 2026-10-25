"""
Turnitout DOCX In-Place Processor
Preserves Word styles, runs, formatting, tables, and typography
while humanizing text content in-place.
"""

import os
import re
from typing import Dict, Any, List
from docx import Document
from .engine import HumanizerEngine


def _set_paragraph_text_preserve_style(p, new_text: str) -> None:
    """Replaces paragraph text in-place while keeping the first run's font/style formatting."""
    if len(p.runs) > 0:
        p.runs[0].text = new_text
        for run in p.runs[1:]:
            run.text = ""
    else:
        p.text = new_text


class DocxProcessor:
    def __init__(self, engine: HumanizerEngine):
        self.engine = engine

    def extract_text(self, input_path: str) -> Dict[str, Any]:
        """
        Extracts all paragraph and table text from a .docx file for preview and chunked humanization.
        """
        doc = Document(input_path)
        lines: List[str] = []
        for p in doc.paragraphs:
            t = re.sub(r"\s+", " ", p.text).strip()
            if t:
                lines.append(t)
        for t_idx, table in enumerate(doc.tables):
            lines.append(f"[Table {t_idx + 1}]")
            for row in table.rows:
                # Deduplicate identical adjacent cells caused by merged horizontal cells
                row_texts = []
                for cell in row.cells:
                    ct = re.sub(r"\s+", " ", cell.text).strip()
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

    def rebuild_from_text(self, input_path: str, output_path: str, humanized_text: str) -> Dict[str, Any]:
        """
        Reconstructs the .docx file in-place using the already-humanized text from the chunked stream.
        Executes in <200ms with zero LLM calls (never times out on serverless) while preserving
        all Word styles, runs, tables, headers, and formatting.
        """
        doc = Document(input_path)

        # Split humanized text into main body + optional [Table N] sections
        table_pattern = re.compile(r"^\s*\[Table\s+(\d+)\]\s*$", re.IGNORECASE | re.MULTILINE)
        parts = table_pattern.split(humanized_text or "")
        body_text = parts[0] if parts else (humanized_text or "")

        body_lines = [line.strip() for line in body_text.split("\n") if line.strip()]
        non_empty_paras = [p for p in doc.paragraphs if p.text and p.text.strip()]

        updated_paragraphs = 0
        if non_empty_paras and body_lines:
            if len(body_lines) == len(non_empty_paras):
                for p, new_line in zip(non_empty_paras, body_lines):
                    _set_paragraph_text_preserve_style(p, new_line)
                    updated_paragraphs += 1
            elif len(body_lines) < len(non_empty_paras):
                # Map available lines in order, leaving any trailing structural paragraphs intact
                for idx, new_line in enumerate(body_lines):
                    _set_paragraph_text_preserve_style(non_empty_paras[idx], new_line)
                    updated_paragraphs += 1
            else:
                # More lines in humanized_text than non_empty_paras: assign 1-to-1 up to last paragraph,
                # and join remaining lines into the final paragraph so zero words are ever dropped.
                for idx in range(len(non_empty_paras) - 1):
                    _set_paragraph_text_preserve_style(non_empty_paras[idx], body_lines[idx])
                    updated_paragraphs += 1
                tail_joined = " ".join(body_lines[len(non_empty_paras) - 1 :])
                _set_paragraph_text_preserve_style(non_empty_paras[-1], tail_joined)
                updated_paragraphs += 1

        # Map any [Table N] blocks back into doc.tables in-place
        updated_tables = 0
        # parts[1::2] are table numbers ("1", "2", ...), parts[2::2] are table contents
        for t_num_str, t_content in zip(parts[1::2], parts[2::2]):
            try:
                t_idx = int(t_num_str) - 1
            except ValueError:
                continue
            if 0 <= t_idx < len(doc.tables):
                table = doc.tables[t_idx]
                row_lines = [rl.strip() for rl in t_content.split("\n") if rl.strip()]
                r_line_idx = 0
                for row in table.rows:
                    # Check if row had non-empty cells
                    distinct_cells = []
                    last_cell_text = None
                    for cell in row.cells:
                        ct = cell.text.strip()
                        if ct:
                            if ct != last_cell_text:
                                distinct_cells.append([cell])
                                last_cell_text = ct
                            else:
                                distinct_cells[-1].append(cell)
                    if not distinct_cells or r_line_idx >= len(row_lines):
                        continue
                    new_cells_text = [c.strip() for c in row_lines[r_line_idx].split("|")]
                    r_line_idx += 1
                    for c_group, new_val in zip(distinct_cells, new_cells_text):
                        for cell in c_group:
                            if cell.paragraphs:
                                _set_paragraph_text_preserve_style(cell.paragraphs[0], new_val)
                                for extra_p in cell.paragraphs[1:]:
                                    _set_paragraph_text_preserve_style(extra_p, "")
                            else:
                                cell.text = new_val
                updated_tables += 1

        doc.save(output_path)
        return {
            "total_paragraphs": updated_paragraphs,
            "total_tables": updated_tables,
            "output_path": output_path,
        }

    def process_file(self, input_path: str, output_path: str, intensity: float = 0.6) -> Dict[str, Any]:
        """
        Processes a .docx file in-place, rewriting text while preserving document structure.
        """
        extracted = self.extract_text(input_path)
        full_text = extracted["text"]
        if not full_text.strip():
            doc = Document(input_path)
            doc.save(output_path)
            return {
                "total_paragraphs": 0,
                "total_changes": 0,
                "total_watermarks": 0,
                "output_path": output_path,
            }

        res = self.engine.process(full_text, intensity=intensity)
        rebuild_info = self.rebuild_from_text(input_path, output_path, res["cleaned_text"])
        return {
            "total_paragraphs": rebuild_info["total_paragraphs"],
            "total_changes": res["changes_count"],
            "total_watermarks": res["watermarks_found"],
            "output_path": output_path,
        }

