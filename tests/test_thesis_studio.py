import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import docx
from scripts.thesis_studio import (
    parse_and_chunk_docx, align_humanized_text_to_chunk,
    replace_paragraph_text_preserving_style, clean_bullet_text,
    merge_split_bullet_entries, app, DOC_STATE
)

def test_chunker_thesis_draft():
    thesis_path = r'c:\Users\deep1\Downloads\thesis_draft.docx'
    if not Path(thesis_path).exists():
        return
    state = parse_and_chunk_docx(thesis_path, max_chunk_words=2850)
    print(f"Total chunks: {len(state['chunks'])}")
    assert len(state['chunks']) in [7, 8, 9]
    for c in state['chunks']:
        print(f"Chunk {c['chunk_id']}: {c['word_count']} words, {len(c['paragraphs'])} paragraphs, {len(c['sections'])} sections")
        assert c['word_count'] <= 3000

def test_split_bullet_merger():
    blocks = [
        "• Perceived risk",
        "• Perceived risk refers to uncertainty about the outcome of performing an action [20].",
        "• Normal item"
    ]
    merged = merge_split_bullet_entries(blocks)
    assert len(merged) == 2
    assert merged[0].startswith("Perceived risk: Perceived risk refers to")

def test_list_cleaning_and_numbering():
    assert clean_bullet_text("• • 71.5% Avoidance", is_list=True) == "71.5% Avoidance"
    assert clean_bullet_text("2) Next step", is_list=True) == "2. Next step"
    assert clean_bullet_text("6) Recommendations for future research", is_list=False) == "6. Recommendations for future research"
    # Unclosed parenthesis and double dot fixing
    assert clean_bullet_text("(chapters 3 & 4. .", is_list=False) == "(chapters 3 & 4)."
    assert clean_bullet_text("(SD=10.8.", is_list=False) == "(SD = 10.8)"
    # Internal newline title un-stretching
    assert clean_bullet_text("1. Natural Language Intent Bar (R1, R4, R10)\n\nA large natural language input field...", is_list=False) == "1. Natural Language Intent Bar (R1, R4, R10): A large natural language input field..."


def test_recombine_orphan_headers():
    from scripts.thesis_studio import recombine_orphan_headers
    blocks = [
        "1. Natural Language Intent Bar (R1, R4, R10)",
        "A large natural language input field is shown at the top of the screen.",
        "References",
        "Tian, Y. and Mi, X., 2025. A Study of the Deconstruction..."
    ]
    recomb = recombine_orphan_headers(blocks)
    assert len(recomb) == 2
    assert recomb[0].startswith("1. Natural Language Intent Bar (R1, R4, R10): A large natural language")
    assert recomb[1].startswith("Tian, Y. and Mi, X., 2025.")

def test_bold_bleed_protection():
    doc = docx.Document()
    p = doc.add_paragraph()
    r1 = p.add_run("1. Operating System Modes: ")
    r1.bold = True
    r2 = p.add_run("Apple Assistive Access simplifies the home launcher.")
    r2.bold = False

    replace_paragraph_text_preserving_style(p, "1. Operating System Modes: Apple Assistive Access simplifies the launcher.")
    assert p.runs[0].bold == True, "Prefix should be bold"
    assert p.runs[1].bold == False, "Body should NOT be bold"

def test_align_humanized_text():
    sample_items = [
        {"text": "First paragraph regarding older adults and digital technology adoption [7].", "words": 35},
        {"text": "Second paragraph discussing quantitative survey methodology with 130 participants.", "words": 40}
    ]
    tagged_input = "[P1] New first paragraph on senior technology.\n\n[P2] New second paragraph on 130 survey respondents."
    res = align_humanized_text_to_chunk(sample_items, tagged_input)
    assert len(res) == 2
    assert "New first paragraph" in res[0]
    assert "New second paragraph" in res[1]

if __name__ == "__main__":
    test_chunker_thesis_draft()
    test_split_bullet_merger()
    test_list_cleaning_and_numbering()
    test_recombine_orphan_headers()
    test_bold_bleed_protection()
    test_align_humanized_text()
    print("ALL TESTS PASSED SUCCESSFULLY!")
