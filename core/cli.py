"""
Turnitout CLI Interface
Processes .docx or .txt / .md files directly from command line.
"""

import sys
import argparse
import os
from core.engine import HumanizerEngine
from core.docx_handler import DocxProcessor

def main():
    parser = argparse.ArgumentParser(description="Turnitout Humanizer CLI")
    parser.add_argument("input_file", help="Input file path (.docx, .txt, .md, .tex)")
    parser.add_argument("-o", "--output", help="Output file path (default: Humanized_<input>)")
    parser.add_argument("-i", "--intensity", type=float, default=0.6, help="Intensity between 0.2 and 0.95 (default: 0.6)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)

    engine = HumanizerEngine(seed=args.seed)

    input_ext = os.path.splitext(args.input_file)[1].lower()
    default_out = f"Humanized_{os.path.basename(args.input_file)}"
    output_path = args.output or default_out

    print(f"\n⚡ Processing '{args.input_file}' with intensity {args.intensity}...")

    if input_ext == ".docx":
        proc = DocxProcessor(engine)
        res = proc.process_file(args.input_file, output_path, intensity=args.intensity)
        print(f"✅ Finished! Saved to '{output_path}'")
        print(f"   Paragraphs: {res['total_paragraphs']}")
        print(f"   Modifications: {res['total_changes']}")
        print(f"   Watermarks purged: {res['total_watermarks']}\n")
    else:
        with open(args.input_file, "r", encoding="utf-8") as f:
            content = f.read()
        res = engine.process(content, intensity=args.intensity)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(res["cleaned_text"])
        print(f"✅ Finished! Saved to '{output_path}'")
        print(f"   Words: {res['metrics_after']['words']}")
        print(f"   AI Risk Estimate: {res['metrics_after']['ai_risk']}% (was {res['metrics_before']['ai_risk']}%)")
        print(f"   Watermarks purged: {res['watermarks_found']}")
        print(f"   Modifications: {res['changes_count']}\n")

if __name__ == "__main__":
    main()

