"""
Clever AI Document Humanizer (Automated DOCX Engine)
Uses Playwright to automate cleverhumanizer.ai in 'Clear & Structured' mode
Preserves:
- Headings & subheadings (detects Heading styles, bold titles, numbering like '1.2 Problem Area')
- Paragraph alignments (justified, centered, left)
- Font styles (family, size, bold, italic, color)
- Bullet points & numbered lists (Word list XML properties preserved)
- Tables (processes cell paragraphs with >= 30 words, keeps short labels/data intact)
- Enforces >= 30 words rule required by Clever
"""

import os
import sys
import time
import re
from pathlib import Path
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Patterns that indicate headings/titles to preserve as-is
HEADING_REGEX = re.compile(
    r"^\s*(\d+(\.\d+)*|[A-Z](\.\d+)*)\s+[A-Z0-9]", re.IGNORECASE
)


def is_heading(paragraph) -> bool:
    """Detect if a paragraph is a title or heading that must not be altered."""
    style_name = paragraph.style.name.lower() if paragraph.style else ""
    if any(h in style_name for h in ["heading", "title", "subtitle"]):
        return True

    text = paragraph.text.strip()
    if not text:
        return False

    word_count = len(text.split())

    # Numbered heading pattern like "1.2 Problem Area" or "Chapter 2"
    if HEADING_REGEX.match(text) and word_count <= 14:
        return True

    # Short bold phrase with no ending period
    runs = [r for r in paragraph.runs if r.text.strip()]
    if runs and all(r.bold for r in runs) and word_count <= 10 and not text.endswith((".", ":", ";")):
        return True

    return False


def is_list_item(paragraph) -> bool:
    """Detect if paragraph is a bullet point or numbered list."""
    style_name = paragraph.style.name.lower() if paragraph.style else ""
    if any(l in style_name for l in ["list", "bullet", "number"]):
        return True
    pPr = paragraph._element.pPr
    if pPr is not None and pPr.numPr is not None:
        return True
    return False


def count_words(text: str) -> int:
    return len(text.strip().split()) if text.strip() else 0


def replace_paragraph_text_preserving_style(paragraph, new_text: str):
    """
    Replaces the text of a paragraph while preserving font family,
    size, bold/italic properties, and paragraph alignment.
    """
    if not paragraph.runs:
        paragraph.text = new_text
        return

    # Capture style metadata from the primary run
    first_run = paragraph.runs[0]
    font_name = first_run.font.name
    font_size = first_run.font.size
    bold = first_run.bold
    italic = first_run.italic
    underline = first_run.underline
    color = first_run.font.color.rgb if (first_run.font.color and first_run.font.color.rgb) else None

    # Clear all runs
    for run in paragraph.runs:
        run.text = ""

    # Re-inject the humanized text into the first run
    first_run.text = new_text
    if font_name:
        first_run.font.name = font_name
    if font_size:
        first_run.font.size = font_size
    first_run.bold = bold
    first_run.italic = italic
    first_run.underline = underline
    if color:
        first_run.font.color.rgb = color


class CleverAutomator:
    """Manages the Playwright browser session for cleverhumanizer.ai."""

    def __init__(self, headless: bool = False):
        from playwright.sync_api import sync_playwright

        self.playwright = sync_playwright().start()
        # Launch using installed Google Chrome or Edge to avoid downloading extra binaries
        browser = None
        for channel in ["chrome", "msedge", None]:
            try:
                kwargs = {
                    "headless": headless,
                    "args": ["--disable-blink-features=AutomationControlled", "--start-maximized"]
                }
                if channel:
                    kwargs["channel"] = channel
                browser = self.playwright.chromium.launch(**kwargs)
                break
            except Exception:
                continue

        if not browser:
            import subprocess
            print("[Playwright] Installing browser binaries...")
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            browser = self.playwright.chromium.launch(headless=headless)

        self.browser = browser
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()

    def initialize_session(self):
        """Navigate to Clever AI Humanizer and select 'Clear & Structured' mode."""
        print("[Clever] Navigating to https://cleverhumanizer.ai/...")
        self.page.goto("https://cleverhumanizer.ai/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(2)

        # Ensure Clear & Structured mode is activated
        try:
            structured_btn = self.page.locator('button[data-humanize-style="academic"]')
            if structured_btn.count() > 0:
                structured_btn.click()
                print("[Clever] Writing Style set to: Clear & Structured (Academic)")
            else:
                fallback_btn = self.page.locator('button:has-text("Clear & Structured")')
                if fallback_btn.count() > 0:
                    fallback_btn.click()
                    print("[Clever] Writing Style set to: Clear & Structured")
        except Exception as e:
            print(f"[Clever] Warning selecting style: {e}")

        time.sleep(1)

    def humanize_text(self, text: str) -> str:
        """Sends text to Clever and waits for humanized response."""
        word_count = count_words(text)
        if word_count < 30:
            print(f"  [Skip] Text has {word_count} words (< 30 words minimum required by Clever). Keeping intact.")
            return text

        print(f"  [Humanizing] Sending {word_count} words...")

        # Locate Quill input editor
        editor = self.page.locator("#quillEditor .ql-editor")
        if editor.count() == 0:
            editor = self.page.locator(".ql-editor").first

        # Clear and fill text
        editor.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        time.sleep(0.3)

        # Fill via javascript for fast insertion
        self.page.evaluate(
            """({text}) => {
                const ed = document.querySelector('#quillEditor .ql-editor') || document.querySelector('.ql-editor');
                if (ed) {
                    ed.innerText = text;
                    ed.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }""",
            {"text": text}
        )
        time.sleep(0.6)

        # Re-verify 'Clear & Structured' is active
        try:
            self.page.evaluate("""() => {
                const btn = document.querySelector('button[data-humanize-style="academic"]');
                if (btn && !btn.classList.contains('active')) btn.click();
            }""")
        except Exception:
            pass

        # Click Humanize button
        submit_btn = self.page.locator("button.submitQuill, button:has-text('Humanize AI')").first
        submit_btn.click()

        # Wait for processing to finish
        print("  [Processing] Waiting for output...", end="", flush=True)
        start_time = time.time()
        timeout = 45  # seconds

        output_text = ""
        while time.time() - start_time < timeout:
            time.sleep(1)
            print(".", end="", flush=True)

            # Check if output is rendered
            res = self.page.evaluate("""() => {
                const out = document.querySelector('.quillOutput') || document.querySelector('#quillOutput .ql-editor');
                if (!out) return null;
                const text = out.innerText ? out.innerText.trim() : '';
                return text.length > 20 ? text : null;
            }""")

            if res:
                output_text = res
                break

        print()
        if output_text and count_words(output_text) >= 15:
            print(f"  [Success] Received {count_words(output_text)} humanized words.")
            time.sleep(1)  # small cooldown
            return output_text
        else:
            print("  [Warning] Timeout or empty output returned; retaining original paragraph.")
            return text

    def close(self):
        try:
            self.browser.close()
            self.playwright.stop()
        except Exception:
            pass


def process_document(input_docx_path: str, output_docx_path: str = None, headless: bool = False):
    """
    Main driver to process an entire .docx file:
    - Skips headings (preserves styles)
    - Processes body paragraphs >= 30 words
    - Processes bullet/numbered points >= 30 words
    - Processes table cell paragraphs >= 30 words
    """
    input_path = Path(input_docx_path)
    if not input_path.exists():
        print(f"Error: File '{input_docx_path}' not found.")
        sys.exit(1)

    if not output_docx_path:
        output_docx_path = input_path.parent / f"{input_path.stem}_humanized.docx"

    print(f"\n=======================================================")
    print(f"  Clever AI DOCX Humanizer")
    print(f"  Input Document:  {input_path.name}")
    print(f"  Output Document: {Path(output_docx_path).name}")
    print(f"  Writing Style:   Clear & Structured (Academic)")
    print(f"=======================================================\n")

    doc = docx.Document(str(input_path))

    # Phase 1: Survey and count paragraphs
    work_items = []

    # Check normal paragraphs
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if not text:
            continue
        if is_heading(p):
            print(f"[Heading Preserved] '{text[:50]}...'")
            continue

        words = count_words(text)
        is_list = is_list_item(p)
        label = "List Item" if is_list else "Body Paragraph"

        if words >= 30:
            work_items.append({"type": "paragraph", "obj": p, "words": words, "desc": f"{label} #{i+1}: {text[:45]}..."})
        else:
            print(f"[{label} Kept (short)] '{text[:45]}...' ({words} words < 30)")

    # Check tables
    for t_idx, table in enumerate(doc.tables):
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                for p in cell.paragraphs:
                    text = p.text.strip()
                    if not text:
                        continue
                    words = count_words(text)
                    if words >= 30:
                        work_items.append({
                            "type": "table_cell",
                            "obj": p,
                            "words": words,
                            "desc": f"Table {t_idx+1} [R{r_idx+1}:C{c_idx+1}]: {text[:40]}..."
                        })

    total_items = len(work_items)
    print(f"\nFound {total_items} eligible prose sections (>= 30 words) to humanize.\n")

    if total_items == 0:
        print("No paragraphs >= 30 words found to humanize.")
        return

    # Phase 2: Launch Clever session
    automator = CleverAutomator(headless=headless)
    try:
        automator.initialize_session()

        for idx, item in enumerate(work_items, start=1):
            p = item["obj"]
            orig_text = p.text.strip()
            print(f"\n[{idx}/{total_items}] {item['desc']}")

            humanized_text = automator.humanize_text(orig_text)

            if humanized_text and humanized_text != orig_text:
                replace_paragraph_text_preserving_style(p, humanized_text)

            # Periodic auto-save
            doc.save(str(output_docx_path))

    finally:
        automator.close()

    # Final save
    doc.save(str(output_docx_path))
    print(f"\nCompleted! Humanized document saved to:\n👉 {output_docx_path}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/humanize_docx_clever.py <path_to_document.docx> [output_path.docx]")
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    process_document(in_file, out_file)
