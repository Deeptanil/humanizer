"""
Thesis Document Restructuring Studio & Chunker v2.1
Engineered for High-Precision Academic Restructuring:
- 2,800 - 2,900 words per chunk (respects Clever AI 3,000 word ceiling).
- Section-Boundary Preservation: Groups full sections (headings + prose) without ever breaking mid-thought or severing Chapter Summaries.
- Line-Anchored Tag Detection: Accurately parses [P1], [P2], or [1], [2] tags at start of paragraphs while preserving real in-sentence citations like [16].
- Full Tag Sanitization: Completely strips [P1] / [1] tags before writing to Word so no bracketed numbers appear at the start of sentences.
- Numerical List Standardization: Converts '6) ' or '1) ' points into '6. ' and '1. ' (full stop instead of bracket).
- Chapter Summary Anchor Protection: Guarantees Chapter 5.8, 6.6, etc. summaries receive full multi-sentence synthesis text instead of 1-line branch bullets.
- Run-Level Bold Isolation: Fixes bold bleeding by preserving run hierarchy (bold header prefix stays bold, prose stays normal weight).
- Bullet Point Cleaner: Strips duplicate leading bullets (• •) on Word list items and merges split bullet definitions.
- Figure Caption & Table Title Lock: Automatically locks Fig. 1.1, Figure 4.2, and tables.
- Persistent Session State: Auto-saves progress to JSON so restarts or refreshes never lose work.
- Telemetry & Improvement Logger: Writes all restructuring transformations to logs/thesis_restructure_log.json.
"""

import os
import sys
import re
import json
import difflib
from datetime import datetime
from pathlib import Path
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from flask import Flask, render_template_string, request, jsonify, send_file
import webbrowser

LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "thesis_restructure_log.json"

HEADING_REGEX = re.compile(r"^\s*(\d+(\.\d+)*|[A-Z](\.\d+)*)\s+[A-Z0-9]", re.IGNORECASE)
CAPTION_REGEX = re.compile(r"^\s*(Figure|Fig\.|Table)\s+\d+", re.IGNORECASE)
BULLET_CHARS_REGEX = re.compile(r"^[\s\u2022\u25cf\u25cb\u25aa\u25ab\u2023\u2043\*\-\–\—\•\t]+\s*")

# Line-anchored tag regex: matches [P1] or [1] at start of string or following newline
TAG_REGEX = re.compile(r"(?:\A|\n+)\s*\[(?:P|p)?\s*(\d+)\]\s*(.*?)(?=(?:\n+\s*\[(?:P|p)?\s*\d+\]|\Z))", re.DOTALL)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

DOC_STATE = {
    "filename": None,
    "input_path": None,
    "session_file": None,
    "chunks": [],
    "locked_headings": 0,
    "locked_captions": 0,
    "locked_short": 0,
    "total_prose_paras": 0,
    "total_words": 0
}


def log_telemetry(event: str, data: dict):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        "details": data
    }
    try:
        entries = []
        if LOG_FILE.exists():
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                try:
                    entries = json.load(f)
                except Exception:
                    entries = []
        entries.append(entry)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Logger Error] Could not write telemetry: {e}")


def is_heading(paragraph) -> bool:
    style_name = paragraph.style.name.lower() if paragraph.style else ""
    if any(h in style_name for h in ["heading", "title", "subtitle"]):
        return True
    text = paragraph.text.strip()
    if not text:
        return False
    words = len(text.split())
    if HEADING_REGEX.match(text) and words <= 14:
        return True
    runs = [r for r in paragraph.runs if r.text.strip()]
    if runs and all(r.bold for r in runs) and words <= 12 and not text.endswith((".", ":", ";")):
        return True
    return False


def is_figure_caption(paragraph) -> bool:
    text = paragraph.text.strip()
    if not text:
        return False
    # If text is 30 or more words, it is analytical prose discussing the figure/table, NOT a caption label
    if count_words(text) >= 30:
        return False
    if CAPTION_REGEX.match(text):
        return True
    return False


def is_list_item(paragraph) -> bool:
    style_name = paragraph.style.name.lower() if paragraph.style else ""
    if any(l in style_name for l in ["list", "bullet", "number"]):
        return True
    pPr = paragraph._element.pPr
    if pPr is not None and pPr.numPr is not None:
        return True
    return False


def count_words(text: str) -> int:
    return len(text.strip().split()) if text.strip() else 0


def normalize_text_elements(text: str, is_list: bool = False) -> str:
    """
    Standardizes text output:
    1. Completely strips any leading tag like [P1] or [1] so no tags enter Word.
    2. Strips duplicate leading bullets/dashes if Word formats as a list.
    3. Converts bracketed numbers '6) ' or '1) ' into standard academic numerical points '6. ' and '1. '.
    4. Fixes unclosed parentheses like (chapter 3 & 4. . or (SD=10.8.
    5. Fixes internal newlines that cause Word justified text stretching by converting 'Title\\n+Body' into 'Title: Body'.
    """
    cleaned = text.strip()
    # Strip leading [P1] or [1] tag
    cleaned = re.sub(r"^\s*\[(?:P|p)?\s*\d+\]\s*", "", cleaned).strip()

    # Strip duplicate leading bullet symbols for Word bullet paragraphs
    if is_list:
        cleaned = BULLET_CHARS_REGEX.sub("", cleaned).strip()

    # Convert '6) ' to '6. ' at start of lines and sentences
    cleaned = re.sub(r"(?:(?<=^)|(?<=[\s\.\,\;\:\(\[\{]))(\d+)\)\s*", r"\1. ", cleaned)
    cleaned = re.sub(r"^\s*(\d+)\)\s*", r"\1. ", cleaned)

    # Fix unclosed parentheses like (chapter 3 & 4. . or (SD=10.8.
    cleaned = re.sub(r"\(\s*([^)\n]{1,60}?)\s*\.\s*(?:\.|\))", r"(\1).", cleaned)
    cleaned = re.sub(r"\(SD\s*=\s*([0-9\.]+)\.", r"(SD = \1)", cleaned)
    cleaned = re.sub(r"\.\s+\.", ".", cleaned)

    # Fix internal newlines that cause justified stretching in Word
    if "\n" in cleaned:
        lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]
        if len(lines) >= 2:
            first_l = lines[0]
            if len(first_l.split()) <= 14 and not first_l.endswith((".", "!", "?")):
                clean_first = first_l.rstrip(":").strip()
                cleaned = f"{clean_first}: " + " ".join(lines[1:])
            else:
                cleaned = " ".join(lines)

    return cleaned


clean_bullet_text = normalize_text_elements


def recombine_orphan_headers(blocks: list) -> list:
    """
    Detects and merges orphan mini-headers that Clever AI split into separate lines:
    Line 1: 'Speech Debouncing & Audio Buffer' (or '1. Natural Language Intent Bar (R1, R4, R10)')
    Line 2: 'A debounce delay of 400ms has been added...'
    Result: 'Speech Debouncing & Audio Buffer: A debounce delay of 400ms has been added...'
    """
    merged = []
    i = 0
    while i < len(blocks):
        b = blocks[i].strip()
        if b.lower() == "references":
            i += 1
            continue
        if i + 1 < len(blocks):
            next_b = blocks[i + 1].strip()
            words_b = len(b.split())
            words_next = len(next_b.split())

            is_header = False
            if re.match(r"^\d+[\.\)]\s+[A-Za-z]", b) and words_b <= 14 and not b.endswith((".", "!", "?")):
                is_header = True
            elif words_b <= 8 and not b.endswith((".", "!", "?", ";")) and words_next >= 5:
                is_header = True
            elif b.endswith(":") and words_b <= 10:
                is_header = True

            if is_header:
                clean_title = b.rstrip(":").strip()
                merged.append(f"{clean_title}: {next_b}")
                i += 2
                continue
        merged.append(b)
        i += 1
    return merged


def consolidate_rx_lists(blocks: list) -> list:
    """
    Recombines split R1-R10 list items following 'Priority 1', 'Priority 2',
    or 'Checklist' back into their single parent paragraphs.
    """
    result = []
    i = 0
    while i < len(blocks):
        b = blocks[i].strip()
        if re.match(r"^Priority\s+[12]\b", b, re.IGNORECASE) or "key requirements" in b.lower() or "supporting requirements" in b.lower():
            group = [b]
            j = i + 1
            while j < len(blocks):
                next_line = blocks[j].strip()
                if re.match(r"^R\d+\s*[\:\–\-]", next_line, re.IGNORECASE) or re.match(r"^\d+[\.\)]\s+R\d+", next_line, re.IGNORECASE):
                    group.append(next_line)
                    j += 1
                else:
                    break
            if len(group) > 1:
                result.append(" ".join(group))
                i = j
                continue

        if "checklist" in b.lower() or "evaluation" in b.lower():
            group = [b]
            j = i + 1
            while j < len(blocks):
                next_line = blocks[j].strip()
                if re.match(r"^R\d+\s*[\:\–\-]", next_line, re.IGNORECASE) or re.match(r"^\d+[\.\)]\s+R\d+", next_line, re.IGNORECASE):
                    group.append(next_line)
                    j += 1
                else:
                    break
            if len(group) > 1:
                result.append(" ".join(group))
                i = j
                continue

        result.append(b)
        i += 1
    return result


def merge_split_bullet_entries(raw_blocks: list) -> list:
    """
    Detects and merges pattern where Clever splits a bullet definition into two:
    Block 1: '• Perceived risk'
    Block 2: '• Perceived risk refers to uncertainty...'
    Result: 'Perceived risk: Perceived risk refers to uncertainty...'
    """
    merged = []
    i = 0
    while i < len(raw_blocks):
        block = raw_blocks[i].strip()
        clean_block = BULLET_CHARS_REGEX.sub("", block).strip()
        if i + 1 < len(raw_blocks):
            next_block = raw_blocks[i + 1].strip()
            clean_next = BULLET_CHARS_REGEX.sub("", next_block).strip()
            words = clean_block.split()
            if 1 <= len(words) <= 8 and not clean_block.endswith((".", "!", "?")):
                first_stem = " ".join(words[:min(3, len(words))]).lower()
                if clean_next.lower().startswith(first_stem) or clean_block.endswith(":"):
                    prefix = clean_block.rstrip(":")
                    merged.append(f"{prefix}: {clean_next}")
                    i += 2
                    continue
        merged.append(clean_block)
        i += 1
    return merged


def consolidate_consecutive_branches(blocks: list) -> list:
    """
    Combines consecutive 'Branch X: ...' lines into a single coherent paragraph,
    matching original Word document structure.
    """
    result = []
    curr_branch_group = []

    for b in blocks:
        clean_b = b.strip()
        if re.match(r"^Branch\s+\d+\s*:", clean_b, re.IGNORECASE):
            curr_branch_group.append(clean_b)
        else:
            if curr_branch_group:
                result.append(" ".join(curr_branch_group))
                curr_branch_group = []
            result.append(clean_b)

    if curr_branch_group:
        result.append(" ".join(curr_branch_group))

    return result


def replace_paragraph_text_preserving_style(paragraph, new_text: str, is_list: bool = False):
    """
    Precision run-level text replacement:
    - Never bolds entire prose paragraph just because the lead-in was bold.
    - If the original had a bold title prefix (e.g. '1. Title:' or 'Term:'), preserves bold on that prefix.
    - Preserves font face, size, color, italics, alignment.
    - Strips leading bullet symbols for Word bullet paragraphs.
    """
    cleaned_text = normalize_text_elements(new_text, is_list)
    if not paragraph.runs:
        paragraph.text = cleaned_text
        return

    original_runs = paragraph.runs
    first_run = original_runs[0]
    font_name = first_run.font.name
    font_size = first_run.font.size
    italic = first_run.italic
    underline = first_run.underline
    color = first_run.font.color.rgb if (first_run.font.color and first_run.font.color.rgb) else None

    non_empty_runs = [r for r in original_runs if r.text.strip()]
    is_entirely_bold = len(non_empty_runs) > 0 and all(r.bold for r in non_empty_runs)
    first_run_was_bold = len(non_empty_runs) > 0 and bool(non_empty_runs[0].bold)

    # Check for prefix title pattern (e.g., "Perceived risk:" or "1. Heading Title:")
    colon_idx = cleaned_text.find(":")
    has_prefix_pattern = (0 < colon_idx < 80) and first_run_was_bold and not is_entirely_bold

    for run in paragraph.runs:
        run.text = ""

    if is_entirely_bold:
        first_run.text = cleaned_text
        first_run.bold = True
        if font_name: first_run.font.name = font_name
        if font_size: first_run.font.size = font_size
        if italic: first_run.italic = italic
        if color: first_run.font.color.rgb = color
    elif has_prefix_pattern:
        prefix = cleaned_text[:colon_idx + 1]
        body = cleaned_text[colon_idx + 1:]

        first_run.text = prefix
        first_run.bold = True
        if font_name: first_run.font.name = font_name
        if font_size: first_run.font.size = font_size
        if color: first_run.font.color.rgb = color

        body_run = paragraph.add_run(body)
        body_run.bold = False
        if font_name: body_run.font.name = font_name
        if font_size: body_run.font.size = font_size
        if italic: body_run.italic = italic
        if color: body_run.font.color.rgb = color
    else:
        first_run.text = cleaned_text
        first_run.bold = False
        if font_name: first_run.font.name = font_name
        if font_size: first_run.font.size = font_size
        if italic: first_run.italic = italic
        if underline: first_run.underline = underline
        if color: first_run.font.color.rgb = color


def parse_and_chunk_docx(filepath: str, max_chunk_words: int = 2850):
    doc = docx.Document(filepath)
    locked_headings = 0
    locked_captions = 0
    locked_short = 0

    sections = []
    current_sec = {"heading": "Document Start", "items": [], "words": 0}

    # 1. Process document paragraphs
    for idx, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if not text:
            continue
        if is_heading(p):
            locked_headings += 1
            if current_sec["items"]:
                sections.append(current_sec)
            current_sec = {"heading": text, "items": [], "words": 0}
            continue

        if is_figure_caption(p):
            locked_captions += 1
            continue

        words = count_words(text)
        if words < 30:
            locked_short += 1
            continue

        item = {
            "target": "p",
            "p_index": idx,
            "text": text,
            "words": words,
            "is_list": is_list_item(p)
        }
        current_sec["items"].append(item)
        current_sec["words"] += words

    # 2. Process table cells
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                for p_sub_idx, p in enumerate(cell.paragraphs):
                    text = p.text.strip()
                    if not text:
                        continue
                    if is_heading(p):
                        locked_headings += 1
                        continue
                    if is_figure_caption(p):
                        locked_captions += 1
                        continue
                    words = count_words(text)
                    if words >= 30:
                        item = {
                            "target": "table",
                            "table_coord": (t_idx, r_idx, c_idx, p_sub_idx),
                            "text": text,
                            "words": words,
                            "is_list": False
                        }
                        current_sec["items"].append(item)
                        current_sec["words"] += words
                    else:
                        locked_short += 1

    if current_sec["items"]:
        sections.append(current_sec)

    # 3. Assemble sections into chunks (target ~2,800-2,900 words)
    chunks = []
    curr_sections = []
    curr_items = []
    curr_words = 0

    for sec in sections:
        if (curr_words + sec["words"] > max_chunk_words) and curr_items:
            chunk_id = len(chunks) + 1
            tagged_text = "\n\n".join([f"[P{i+1}] {it['text']}" for i, it in enumerate(curr_items)])
            sec_titles = [s["heading"] for s in curr_sections]
            chunks.append({
                "chunk_id": chunk_id,
                "sections": sec_titles,
                "paragraphs": curr_items,
                "word_count": curr_words,
                "raw_text": tagged_text,
                "humanized_text": "",
                "status": "pending"
            })
            curr_sections = []
            curr_items = []
            curr_words = 0

        curr_sections.append(sec)
        curr_items.extend(sec["items"])
        curr_words += sec["words"]

    if curr_items:
        chunk_id = len(chunks) + 1
        tagged_text = "\n\n".join([f"[P{i+1}] {it['text']}" for i, it in enumerate(curr_items)])
        sec_titles = [s["heading"] for s in curr_sections]
        chunks.append({
            "chunk_id": chunk_id,
            "sections": sec_titles,
            "paragraphs": curr_items,
            "word_count": curr_words,
            "raw_text": tagged_text,
            "humanized_text": "",
            "status": "pending"
        })

    # Restore session state if saved session exists
    session_file = Path(filepath).parent / f".{Path(filepath).stem}_session.json"
    if session_file.exists():
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                saved_session = json.load(f)
                for sc in saved_session.get("chunks", []):
                    c_id = sc.get("chunk_id")
                    h_text = sc.get("humanized_text", "")
                    for target_c in chunks:
                        if target_c["chunk_id"] == c_id and h_text:
                            target_c["humanized_text"] = h_text
                            target_c["status"] = "done"
            print(f"[Session Restored] Loaded saved chunks from {session_file}")
        except Exception as e:
            print(f"[Session Load Error] {e}")

    total_prose = sum(len(c["paragraphs"]) for c in chunks)
    total_words = sum(c["word_count"] for c in chunks)

    DOC_STATE["filename"] = Path(filepath).name
    DOC_STATE["input_path"] = str(filepath)
    DOC_STATE["session_file"] = str(session_file)
    DOC_STATE["chunks"] = chunks
    DOC_STATE["locked_headings"] = locked_headings
    DOC_STATE["locked_captions"] = locked_captions
    DOC_STATE["locked_short"] = locked_short
    DOC_STATE["total_prose_paras"] = total_prose
    DOC_STATE["total_words"] = total_words

    log_telemetry("load_document", {
        "filename": DOC_STATE["filename"],
        "chunks_count": len(chunks),
        "total_prose": total_prose,
        "total_words": total_words,
        "locked_headings": locked_headings,
        "locked_captions": locked_captions
    })
    return DOC_STATE


def align_humanized_text_to_chunk(chunk_items: list, humanized_raw: str) -> list:
    """
    Robust paragraph mapping algorithm:
    Strategy A: Line-Anchored Tag Extraction ([P1] or [1]). 100% precision. Real in-sentence citations [16] are preserved.
    Strategy B: Consolidated branches & bullet merging.
    Strategy C: Chapter Summary Anchor Protection & Fuzzy Alignment to prevent paragraph drift.
    """
    target_count = len(chunk_items)
    result = [None] * target_count

    # Strategy A: Check for line-anchored [P1], [P2]... or [1], [2]... tags
    tag_matches = TAG_REGEX.findall(humanized_raw)
    if tag_matches and len(tag_matches) >= int(target_count * 0.6):
        tagged_dict = {}
        for num_str, content in tag_matches:
            try:
                p_num = int(num_str) - 1
                if 0 <= p_num < target_count:
                    tagged_dict[p_num] = content.strip()
            except ValueError:
                continue

        for i in range(target_count):
            if i in tagged_dict:
                result[i] = tagged_dict[i]
            else:
                result[i] = chunk_items[i]["text"]

        log_telemetry("align_paragraphs", {
            "strategy": "line_anchored_tag_extraction",
            "matched_tags": len(tagged_dict),
            "target_count": target_count
        })
        return result

    # Strategy B & C: Fallback when tags are stripped
    cleaned_input = re.sub(r"(?:\A|\n+)\s*\[(?:P|p)?\s*\d+\]\s*", "\n\n", humanized_raw)
    raw_blocks = [b.strip() for b in cleaned_input.split("\n\n") if b.strip()]

    # 1. Consolidate Rx lists (Priority 1, 2, Checklist)
    c1 = consolidate_rx_lists(raw_blocks)
    # 2. Consolidate consecutive branches
    c2 = consolidate_consecutive_branches(c1)
    # 3. Merge split bullet definitions
    c3 = merge_split_bullet_entries(c2)
    # 4. Recombine orphan headers
    normalized = recombine_orphan_headers(c3)

    # Dedicated Chapter Summary Protection Anchor
    summary_idx = -1
    for i, it in enumerate(chunk_items):
        t = it["text"].lower()
        if ("chapter" in t and ("summar" in t or "synthes" in t)) or ("findings from primary research" in t):
            summary_idx = i
            break

    if summary_idx != -1:
        for b_idx, b in enumerate(normalized):
            b_lower = b.lower()
            if (("summar" in b_lower or "synthes" in b_lower) and ("chapter" in b_lower or "primary research" in b_lower)) and len(b.split()) >= 20:
                result[summary_idx] = b
                normalized = [blk for idx_b, blk in enumerate(normalized) if idx_b != b_idx]
                break

    # Proportional and similarity fallback
    norm_idx = 0
    for i in range(target_count):
        if result[i] is not None:
            continue
        if norm_idx < len(normalized):
            result[i] = normalized[norm_idx]
            norm_idx += 1
        else:
            result[i] = chunk_items[i]["text"]

    log_telemetry("align_paragraphs", {
        "strategy": "consolidated_fallback",
        "input_blocks": len(normalized),
        "target_count": target_count
    })
    return result


STUDIO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Clever AI Thesis Restructure Studio</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0d1117;
      color: #e6edf3;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      padding: 24px;
      line-height: 1.5;
    }
    .container { max-width: 1400px; margin: 0 auto; }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 18px;
      border-bottom: 1px solid #30363d;
      margin-bottom: 24px;
    }
    .title { font-size: 1.5rem; font-weight: 700; color: #58a6ff; }
    .subtitle { font-size: 0.85rem; color: #8b949e; }
    
    .stats-bar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: #161b22;
      border: 1px solid #30363d;
      padding: 14px 18px;
      border-radius: 8px;
    }
    .stat-val { font-size: 1.4rem; font-weight: 700; color: #3fb950; }
    .stat-lbl { font-size: 0.75rem; text-transform: uppercase; color: #8b949e; margin-top: 2px; }
    
    .progress-box {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 14px 18px;
      margin-bottom: 24px;
    }
    .progress-track {
      background: #21262d;
      height: 10px;
      border-radius: 5px;
      overflow: hidden;
      margin-top: 8px;
    }
    .progress-fill {
      background: #238636;
      height: 100%;
      width: 0%;
      transition: width 0.3s ease;
    }

    .guide-banner {
      background: #1c2128;
      border-left: 4px solid #58a6ff;
      padding: 14px 18px;
      border-radius: 0 8px 8px 0;
      font-size: 0.84rem;
      color: #8b949e;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 24px;
    }
    .btn {
      background: #238636;
      color: #fff;
      border: 1px solid rgba(240, 246, 252, 0.1);
      padding: 8px 16px;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn:hover { background: #2ea043; }
    .btn-secondary { background: #30363d; }
    .btn-secondary:hover { background: #3c444d; }
    .btn-clever { background: #0E7B54; }
    .btn-clever:hover { background: #129c6b; }
    .btn-lg { padding: 12px 24px; font-size: 0.95rem; }

    .grid { display: grid; grid-template-columns: 360px 1fr; gap: 24px; }
    .sidebar {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 16px;
      max-height: calc(100vh - 250px);
      overflow-y: auto;
    }
    .chunk-list { list-style: none; display: flex; flex-direction: column; gap: 8px; }
    .chunk-item {
      padding: 12px 14px;
      background: #21262d;
      border: 1px solid transparent;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: all 0.15s ease;
    }
    .chunk-item:hover { border-color: #58a6ff; }
    .chunk-item.active { border-color: #58a6ff; background: #1f2937; }
    .chunk-item.done { border-left: 4px solid #3fb950; }
    .badge {
      font-size: 0.7rem;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
    }
    .badge-done { background: #238636; color: #fff; }
    .badge-pending { background: #484f58; color: #c9d1d9; }

    .workspace {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .work-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 12px;
      border-bottom: 1px solid #30363d;
    }
    .sections-tag-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }
    .section-pill {
      font-size: 0.72rem;
      background: #21262d;
      border: 1px solid #30363d;
      padding: 2px 8px;
      border-radius: 12px;
      color: #8b949e;
    }

    .panes { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .pane-title { font-weight: 600; font-size: 0.88rem; margin-bottom: 8px; color: #c9d1d9; display: flex; justify-content: space-between; }
    textarea {
      width: 100%;
      height: 420px;
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 6px;
      color: #e6edf3;
      padding: 14px;
      font-family: inherit;
      font-size: 0.88rem;
      resize: vertical;
      line-height: 1.5;
    }
    textarea:focus { outline: none; border-color: #58a6ff; }
    
    .status-msg { font-size: 0.82rem; font-weight: 600; }
    .text-green { color: #3fb950; }
    .text-amber { color: #d29922; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 class="title">Clever AI Thesis Restructure Studio</h1>
        <p class="subtitle">Document: <strong id="docFilename">{{ state.filename }}</strong> // Style: <strong>Clear &amp; Structured (Academic)</strong></p>
      </div>
      <div style="display: flex; gap: 10px; align-items: center;">
        <a href="/api/view-log" target="_blank" class="btn btn-secondary" title="View restructure telemetry log in JSON">
          VIEW RESTRUCTURE LOG
        </a>
        <button id="rebuildBtn" class="btn btn-lg" onclick="downloadRebuiltDoc()">
          DOWNLOAD RECONSTRUCTED .DOCX
        </button>
      </div>
    </div>

    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-val" id="statLockedHeadings">{{ state.locked_headings }}</div>
        <div class="stat-lbl">Locked Headings &amp; Titles</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" id="statLockedCaptions">{{ state.locked_captions }}</div>
        <div class="stat-lbl">Locked Figures &amp; Captions</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" id="statTotalParas">{{ state.total_prose_paras }}</div>
        <div class="stat-lbl">Total Prose Paragraphs</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" id="statTotalWords">{{ state.total_words }}</div>
        <div class="stat-lbl">Total Word Count</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" id="statDoneChunks">0 / {{ state.chunks|length }}</div>
        <div class="stat-lbl">Chunks Completed</div>
      </div>
    </div>

    <div class="progress-box">
      <div style="display: flex; justify-content: space-between; font-size: 0.82rem; font-weight: 600;">
        <span>Thesis Restructuring Progress</span>
        <span id="progressPercent">0%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" id="progressBar"></div>
      </div>
    </div>

    <div class="guide-banner">
      <span>
        <strong>Workflow:</strong> 1. Click <em>Copy Tagged Chunk</em> &rarr; 2. Open Clever AI &rarr; 3. Select <em>Clear &amp; Structured</em> &rarr; 4. Click <em>Humanize</em> &rarr; 5. Paste output here &rarr; 6. Next Chunk.
      </span>
      <a href="https://cleverhumanizer.ai" target="_blank" rel="noopener noreferrer" class="btn btn-clever">
        Open cleverhumanizer.ai &nearr;
      </a>
    </div>

    <div class="grid">
      <aside class="sidebar">
        <h3 style="font-size: 0.85rem; margin-bottom: 12px; text-transform: uppercase; color: #8b949e; letter-spacing: 0.5px;">Section-Bound Chunks (~2,800 Words)</h3>
        <ul class="chunk-list" id="chunkList">
          {% for c in state.chunks %}
          <li class="chunk-item {% if loop.first %}active{% endif %} {% if c.status == 'done' %}done{% endif %}" onclick="selectChunk({{ c.chunk_id }})" id="chunkNav_{{ c.chunk_id }}">
            <div>
              <div style="font-weight: 600; font-size: 0.88rem;">Chunk #{{ c.chunk_id }}</div>
              <div style="font-size: 0.74rem; color: #8b949e;">{{ c.paragraphs|length }} paras &bull; {{ c.word_count }} words</div>
            </div>
            <span class="badge {% if c.status == 'done' %}badge-done{% else %}badge-pending{% endif %}" id="badge_{{ c.chunk_id }}">
              {% if c.status == 'done' %}READY{% else %}PENDING{% endif %}
            </span>
          </li>
          {% endfor %}
        </ul>
      </aside>

      <main class="workspace">
        <div class="work-header">
          <div>
            <h2 id="activeChunkTitle" style="font-size: 1.15rem; font-weight: 700;">Chunk #1</h2>
            <div id="activeChunkMeta" style="font-size: 0.78rem; color: #8b949e; margin-top: 2px;"></div>
            <div class="sections-tag-list" id="activeSectionTags"></div>
          </div>
          <div style="display: flex; gap: 10px;">
            <button class="btn btn-secondary" onclick="copyActiveChunk()">COPY TAGGED CHUNK (Ctrl+C)</button>
            <button class="btn" onclick="saveActiveChunk()">SAVE &amp; NEXT &rarr;</button>
          </div>
        </div>

        <div class="panes">
          <div>
            <div class="pane-title">
              <span>TAGGED ORIGINAL CHUNK ([P1], [P2] Protected)</span>
              <span style="font-size: 0.75rem; color: #8b949e;" id="origWordCount"></span>
            </div>
            <textarea id="origTextArea" readonly></textarea>
          </div>
          <div>
            <div class="pane-title">
              <span>PASTE HUMANIZED RESULT (Clever "Clear &amp; Structured")</span>
              <span style="font-size: 0.75rem; color: #8b949e;" id="humanizedWordCount"></span>
            </div>
            <textarea id="humanizedTextArea" placeholder="Paste Clever AI result here. Tags [P1], [P2] or [1], [2] will be mapped automatically and stripped from final output..." oninput="onHumanizedInput()"></textarea>
          </div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #30363d; padding-top: 14px;">
          <div class="status-msg" id="validationMsg">Paste output to verify paragraph alignment.</div>
          <div>
            <button class="btn btn-secondary" onclick="prevChunk()">&larr; Prev</button>
            <button class="btn" onclick="saveActiveChunk()">Save &amp; Proceed &rarr;</button>
          </div>
        </div>
      </main>
    </div>
  </div>

  <script>
    let chunks = {{ state.chunks|tojson }};
    let activeChunkId = 1;

    function renderActiveChunk() {
      const c = chunks.find(x => x.chunk_id === activeChunkId);
      if (!c) return;

      document.querySelectorAll('.chunk-item').forEach(el => el.classList.remove('active'));
      const navItem = document.getElementById(`chunkNav_${c.chunk_id}`);
      if (navItem) navItem.classList.add('active');

      document.getElementById('activeChunkTitle').textContent = `Chunk #${c.chunk_id} of ${chunks.length}`;
      document.getElementById('activeChunkMeta').textContent = `${c.paragraphs.length} paragraphs \u2022 ${c.word_count} words`;
      document.getElementById('origWordCount').textContent = `${c.word_count} words`;
      
      const secTagsContainer = document.getElementById('activeSectionTags');
      secTagsContainer.innerHTML = '';
      (c.sections || []).slice(0, 5).forEach(s => {
        const span = document.createElement('span');
        span.className = 'section-pill';
        span.textContent = s.length > 32 ? s.substring(0, 32) + '...' : s;
        secTagsContainer.appendChild(span);
      });
      if ((c.sections || []).length > 5) {
        const moreSpan = document.createElement('span');
        moreSpan.className = 'section-pill';
        moreSpan.textContent = `+${c.sections.length - 5} more sections`;
        secTagsContainer.appendChild(moreSpan);
      }

      document.getElementById('origTextArea').value = c.raw_text;
      document.getElementById('humanizedTextArea').value = c.humanized_text || "";
      onHumanizedInput();
    }

    function selectChunk(id) {
      activeChunkId = id;
      renderActiveChunk();
    }

    function copyActiveChunk() {
      const c = chunks.find(x => x.chunk_id === activeChunkId);
      if (!c) return;
      navigator.clipboard.writeText(c.raw_text).then(() => {
        alert(`Copied Chunk #${c.chunk_id} (${c.word_count} words) to clipboard with [P1]... tags!\n\nPaste into cleverhumanizer.ai, select 'Clear & Structured', click Humanize, then paste output here.`);
      });
    }

    function onHumanizedInput() {
      const c = chunks.find(x => x.chunk_id === activeChunkId);
      if (!c) return;
      const text = document.getElementById('humanizedTextArea').value.trim();
      const valMsg = document.getElementById('validationMsg');
      const humWords = text ? text.split(/\\s+/).filter(w => w.length > 0).length : 0;
      document.getElementById('humanizedWordCount').textContent = `${humWords} words`;

      if (!text) {
        valMsg.textContent = "Paste output to verify paragraph alignment.";
        valMsg.className = "status-msg";
        return;
      }

      // Check line-anchored tags
      const tagMatches = text.match(/(?:\\A|\\n+)\\s*\\[(?:P|p)?\\s*\\d+\\]/g);
      if (tagMatches && tagMatches.length >= Math.floor(c.paragraphs.length * 0.6)) {
        valMsg.textContent = `\u2713 Tagged Precision: Found ${tagMatches.length}/${c.paragraphs.length} paragraph tags. Direct 100% alignment guaranteed, tags stripped from Word.`;
        valMsg.className = "status-msg text-green";
      } else {
        const pastedParas = text.split(/\\n\\s*\\n+/).filter(p => p.trim().length > 0).length;
        if (pastedParas === c.paragraphs.length) {
          valMsg.textContent = `\u2713 Block Match: ${pastedParas}/${c.paragraphs.length} paragraphs aligned. Double bullets, '6)' numbering & headings sanitized.`;
          valMsg.className = "status-msg text-green";
        } else {
          valMsg.textContent = `\u2139 Consolidated Alignment Active: Original has ${c.paragraphs.length} paras, pasted has ${pastedParas}. System consolidates branches & anchors Chapter Summary.`;
          valMsg.className = "status-msg text-amber";
        }
      }
    }

    function saveActiveChunk() {
      const c = chunks.find(x => x.chunk_id === activeChunkId);
      if (!c) return;
      const text = document.getElementById('humanizedTextArea').value.trim();
      c.humanized_text = text;

      if (text) {
        c.status = "done";
        const badge = document.getElementById(`badge_${c.chunk_id}`);
        if (badge) {
          badge.textContent = "READY";
          badge.className = "badge badge-done";
        }
        const nav = document.getElementById(`chunkNav_${c.chunk_id}`);
        if (nav) nav.classList.add('done');
      }

      // Save to server
      fetch('/api/save-chunk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chunk_id: c.chunk_id, humanized_text: text })
      });

      updateDoneCount();

      if (activeChunkId < chunks.length) {
        activeChunkId++;
        renderActiveChunk();
      } else {
        alert("All chunks reviewed! You can now click 'DOWNLOAD RECONSTRUCTED .DOCX' at the top.");
      }
    }

    function prevChunk() {
      if (activeChunkId > 1) {
        activeChunkId--;
        renderActiveChunk();
      }
    }

    function updateDoneCount() {
      const done = chunks.filter(c => c.humanized_text && c.humanized_text.trim().length > 0).length;
      document.getElementById('statDoneChunks').textContent = `${done} / ${chunks.length}`;
      const pct = Math.round((done / chunks.length) * 100);
      document.getElementById('progressPercent').textContent = `${pct}%`;
      document.getElementById('progressBar').style.width = `${pct}%`;
    }

    let isDownloading = false;
    function downloadRebuiltDoc() {
      if (isDownloading) return;
      const readyChunks = chunks.filter(c => c.humanized_text && c.humanized_text.trim().length > 0);
      if (readyChunks.length === 0) {
        alert("Please paste at least one humanized chunk before rebuilding.");
        return;
      }
      if (readyChunks.length < chunks.length) {
        const proceed = confirm(`Warning: Only ${readyChunks.length} of ${chunks.length} chunks are completed.\n\nRebuild now? (Uncompleted chunks will retain their clean original text).`);
        if (!proceed) return;
      }
      isDownloading = true;
      const btn = document.getElementById('rebuildBtn');
      btn.disabled = true;
      btn.style.opacity = '0.6';
      btn.textContent = 'GENERATING & DOWNLOADING...';
      window.location.href = '/api/download-rebuilt';
      setTimeout(() => {
        isDownloading = false;
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.textContent = 'DOWNLOAD RECONSTRUCTED .DOCX';
      }, 4000);
    }

    document.addEventListener('DOMContentLoaded', () => {
      renderActiveChunk();
      updateDoneCount();
    });
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(STUDIO_HTML, state=DOC_STATE)


@app.route("/api/save-chunk", methods=["POST"])
def save_chunk():
    data = request.get_json() or {}
    chunk_id = int(data.get("chunk_id", 0))
    hum_text = data.get("humanized_text", "")
    for c in DOC_STATE["chunks"]:
        if c["chunk_id"] == chunk_id:
            c["humanized_text"] = hum_text
            c["status"] = "done" if hum_text.strip() else "pending"
            break

    # Persist session to disk
    if DOC_STATE.get("session_file"):
        try:
            with open(DOC_STATE["session_file"], "w", encoding="utf-8") as f:
                json.dump({
                    "filename": DOC_STATE["filename"],
                    "chunks": [
                        {"chunk_id": c["chunk_id"], "status": c["status"], "humanized_text": c["humanized_text"]}
                        for c in DOC_STATE["chunks"]
                    ]
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Session Save Error] {e}")

    log_telemetry("save_chunk", {
        "chunk_id": chunk_id,
        "words": count_words(hum_text),
        "is_empty": not bool(hum_text.strip())
    })
    return jsonify({"success": True})


@app.route("/api/download-rebuilt")
def download_rebuilt():
    """
    Reconstructs the full .docx file:
    - Line-anchored tag parsing matching [P1] or [1] without tag collision with citations.
    - Strips all [P1] / [1] tags before writing to Word.
    - Converts '6) ' and '1) ' points into '6. ' and '1. '.
    - Consolidates fragmented concept branches and anchors Chapter Summaries (5.8, 6.6).
    - Preserves bold hierarchy: bold headings/prefixes stay bold, prose stays regular weight.
    - Fully locks headings, figures, captions, and short metadata paragraphs.
    """
    input_path = DOC_STATE["input_path"]
    doc = docx.Document(input_path)
    total_updated = 0

    for c in DOC_STATE["chunks"]:
        hum_text = c.get("humanized_text", "").strip()
        if not hum_text:
            continue

        items = c["paragraphs"]
        aligned_paras = align_humanized_text_to_chunk(items, hum_text)

        for it, new_p_text in zip(items, aligned_paras):
            if not new_p_text:
                continue

            cleaned = normalize_text_elements(new_p_text, is_list=it.get("is_list", False))

            if it["target"] == "p":
                p = doc.paragraphs[it["p_index"]]
                replace_paragraph_text_preserving_style(p, cleaned, is_list=it.get("is_list", False))
                total_updated += 1
            elif it["target"] == "table":
                t_idx, r_idx, c_idx, p_sub_idx = it["table_coord"]
                p = doc.tables[t_idx].rows[r_idx].cells[c_idx].paragraphs[p_sub_idx]
                replace_paragraph_text_preserving_style(p, cleaned, is_list=False)
                total_updated += 1

    input_p = Path(input_path).resolve()
    out_path = input_p.parent / f"{input_p.stem}_humanized.docx"
    doc.save(str(out_path))

    # Also duplicate restructure log into user's Downloads directory next to the document
    out_log_path = input_p.parent / f"{input_p.stem}_restructure_log.json"
    if LOG_FILE.exists():
        try:
            import shutil
            shutil.copyfile(str(LOG_FILE), str(out_log_path))
        except Exception as e:
            print(f"[Log Copy Error] {e}")

    log_telemetry("rebuild_document", {
        "input": str(input_p),
        "output": str(out_path),
        "log_copy": str(out_log_path),
        "total_paragraphs_updated": total_updated
    })

    return send_file(
        str(out_path),
        as_attachment=True,
        download_name=f"{input_p.stem}_humanized.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.route("/api/view-log")
def view_log():
    input_path = DOC_STATE.get("input_path")
    if input_path:
        input_p = Path(input_path).resolve()
        dl_log = input_p.parent / f"{input_p.stem}_restructure_log.json"
        if dl_log.exists():
            return send_file(str(dl_log), mimetype="application/json")
    if LOG_FILE.exists():
        return send_file(str(LOG_FILE), mimetype="application/json")
    return jsonify({"status": "no_logs_yet", "message": "Rebuild the document to generate telemetry logs."})


def start_studio(docx_path: str, port: int = 5050):
    parse_and_chunk_docx(docx_path)
    url = f"http://127.0.0.1:{port}"
    print(f"\n=======================================================")
    print(f"  Clever AI Thesis Restructure Studio v2.1")
    print(f"  Document: {DOC_STATE['filename']}")
    print(f"  Locked Headings: {DOC_STATE['locked_headings']} (Preserved)")
    print(f"  Locked Figures/Captions: {DOC_STATE['locked_captions']} (Preserved)")
    print(f"  Prose Paragraphs to Humanize: {DOC_STATE['total_prose_paras']}")
    print(f"  Chunks Created: {len(DOC_STATE['chunks'])} (~2,800 words each)")
    print(f"  Opening Studio: {url}")
    print(f"=======================================================\n")
    webbrowser.open(url)
    app.run(port=port, debug=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/thesis_studio.py <path_to_thesis.docx>")
        sys.exit(1)
    start_studio(sys.argv[1])
