import re
import os
import docx

TARGET_PATHS = [
    r"C:\Users\deep1\Downloads\thesis_draft_tobehuman_humanized_v2.1.docx",
    r"C:\Users\deep1\Downloads\thesis_draft_tobehuman_humanized.docx"
]

TRAILING_TARGETS = [
    (1, "Research Focus"),
    (2, "Solution"),
    (3, "Evaluation"),
    (4, "Background"),
    (13, "Issues"),
    (14, "Considerations in India"),
    (32, "Research Aim"),
    (33, "Target Audience"),
    (34, "Digital Services Considered"),
    (35, "Research Focus"),
    (39, "Interaction Design Focus")
]

def clean_trailing_words(text: str, target_phrase: str) -> str:
    # Match the phrase at the very end of text optionally preceded by whitespace
    pattern = rf"\s+{re.escape(target_phrase)}\s*$"
    cleaned = re.sub(pattern, "", text).strip()
    return cleaned

def is_title_or_figure_caption(p) -> bool:
    txt = p.text.strip()
    if not txt:
        return False
    # Figure or Table caption
    if re.match(r"^(?:Fig(?:ure)?\.?\s*\d|Table\s*\d)", txt, re.IGNORECASE):
        return True
    # Chapter or main document heading
    if re.match(r"^(?:CHAPTER\s*\d|\bAPPENDICES\b|\bREFERENCES\b|\bABSTRACT\b|\bDECLARATION\b|\bCERTIFICATE\b|\bTABLE OF CONTENTS\b)", txt, re.IGNORECASE):
        return True
    # Section titles like 1.1, 2.3.1, etc.
    if re.match(r"^\d+\.\d+(?:\.\d+)?\s+[A-Za-z]", txt) and len(txt.split()) <= 15 and not txt.endswith((".", "!", "?")):
        return True
    # Style-based headings
    s = p.style.name.lower() if p.style else ""
    if any(h in s for h in ["heading 1", "heading 2", "heading 3", "title", "subtitle"]):
        return True
    return False

def process_file(doc_path: str):
    if not os.path.exists(doc_path):
        print(f"File not found: {doc_path}")
        return
    
    print(f"Processing: {doc_path}")
    doc = docx.Document(doc_path)
    paras = doc.paragraphs

    # 1. Clean all 11 trailing rogue words
    for p_idx, phrase in TRAILING_TARGETS:
        if p_idx < len(paras):
            orig_txt = paras[p_idx].text
            cleaned_txt = clean_trailing_words(orig_txt, phrase)
            if cleaned_txt != orig_txt:
                # Update run text
                if paras[p_idx].runs:
                    paras[p_idx].runs[0].text = cleaned_txt
                    for r in paras[p_idx].runs[1:]:
                        r.text = ""
                else:
                    paras[p_idx].text = cleaned_txt
                print(f"  P{p_idx}: removed trailing '{phrase}'")

    # 2. Remove all bolding except for titles and figure descriptions
    unbolded_count = 0
    for i, p in enumerate(paras):
        if is_title_or_figure_caption(p):
            # This is a valid title or figure caption, keep its bold
            continue
        
        # This is a body paragraph, list item, or general prose
        has_bold = False
        for r in p.runs:
            if r.bold:
                r.bold = False
                has_bold = True
        if has_bold:
            unbolded_count += 1

    print(f"  Unbolded {unbolded_count} body/prose paragraphs across the document.")

    # Save
    try:
        doc.save(doc_path)
        print(f"Successfully saved {doc_path}")
    except PermissionError:
        alt_path = doc_path.replace(".docx", "_cleaned.docx")
        doc.save(alt_path)
        print(f"File was locked by Word. Saved cleanly to {alt_path}")

if __name__ == "__main__":
    for p in TARGET_PATHS:
        process_file(p)
