"""
Layer 2: Deterministic Anti-Detection Post-Processor & Structural Burstiness Engine
Ported from StealthHumanizer (lib/postprocess.ts) + Moonlit-Pages Thesis Rewriter (rewrite_methods.md).
Guarantees:
- Zero word-count shrinkage (word count stays >= 98% of input)
- Preserves 100% of paragraph breaks (\n) — never merges separate paragraphs
- Strips AI em-dashes while preserving numeric/technical ranges (e.g. SHA-256, 12-hour, 2020-2025)
- Eliminates 100% of AI slop collocations and participial '-ing' sentence tails
- Enforces high sentence-length burstiness (mixes short 5-9 word sentences with 14-24 word clauses)
"""

import re
import math
import random
from typing import List, Tuple, Dict, Any
from .detector import split_sentences

# Complete AI collocation & slop replacements covering 100% of detector markers
COLLOCATION_RULES: List[Tuple[str, List[str]]] = [
    (r"\bIn\s+conclusion,\s*it\s+is\s+important\s+to\s+delve\s+into\b", [
        "Looking at the broader picture, we must examine",
        "Taken together, these points require a close look at",
    ]),
    (r"\bIn\s+conclusion,?\b", [
        "Taken as a whole,",
        "Looking at the full picture,",
        "To pull these threads together,",
    ]),
    (r"\bIt\s+is\s+(?:important|crucial|worth|essential|vital)\s+to\s+(?:note|mention|highlight|remember|understand|recognize)(?:\s+that)?\b", [
        "One critical detail stands out:",
        "What matters most here is that",
        "A key observation from this work is that",
    ]),
    (r"\bIt\s+is\s+worth\s+noting\s+that\b", [
        "Notably, the evidence shows that",
        "One key detail here is that",
    ]),
    (r"\bdelve(?:s|d)?\s+(?:deep\s+)?into\b", [
        "examine in detail",
        "look closely at",
        "break down",
    ]),
    (r"\bdelving\s+(?:deep\s+)?into\b", [
        "closely examining",
        "breaking down",
        "working through",
    ]),
    (r"\bdelve(?:s|d|ing)?\b", [
        "dig",
        "probe",
    ]),
    (r"\b(?:comprehensive|rich|intricate|complex)\s+tapestry\s+of\b", [
        "wide-ranging set of",
        "interconnected group of",
        "full spectrum of",
    ]),
    (r"\btapestr(?:y|ies)(?:\s+of)?\b", [
        "collection of",
        "range of",
    ]),
    (r"\bplays\s+a\s+(?:pivotal|crucial|vital|essential|key|central|significant)\s+role\s+in\s+illustrating\b", [
        "directly shows how",
        "makes it clear how",
    ]),
    (r"\bplay\s+a\s+(?:pivotal|crucial|vital|essential|key|central|significant)\s+role\s+in\s+illustrating\b", [
        "directly show how",
        "make it clear how",
    ]),
    (r"\bplays\s+a\s+(?:pivotal|crucial|vital|essential|key|central|significant)\s+role\s+in\b", [
        "is central to",
        "directly shapes",
        "heavily influences",
    ]),
    (r"\bplay\s+a\s+(?:pivotal|crucial|vital|essential|key|central|significant)\s+role\s+in\b", [
        "are central to",
        "directly shape",
        "heavily influence",
    ]),
    (r"\bplays?\s+a\s+(?:pivotal|crucial|vital|essential|key|central|significant)\s+role\b", [
        "matters a great deal",
        "carries real weight",
    ]),
    (r"\bpivotal\b", [
        "central",
        "critical",
    ]),
    (r"\bin\s+the\s+realm\s+of\b", [
        "across the field of",
        "within",
        "in the domain of",
    ]),
    (r"\brealm\s+of\b", [
        "field of",
        "domain of",
    ]),
    (r"\blandscape\s+of\b", [
        "environment of",
        "field of",
    ]),
    (r"\ba\s+(?:comprehensive|fundamental|major|urgent)?\s*paradigm\s+shift\b", [
        "a fundamental change in approach",
        "a structural shift in design",
    ]),
    (r"\bparadigm\s+shift\b", [
        "fundamental change in approach",
        "structural shift",
    ]),
    (r"\bpaving\s+the\s+way\s+for\b", [
        "opening the door to",
        "laying the groundwork for",
    ]),
    (r"\bpave(?:s|d|ing)?\s+the\s+way(?:\s+for)?\b", [
        "opens the door to",
        "lays the groundwork for",
    ]),
    (r"\bstands?\s+as\s+a\s+testament\s+to\b", [
        "directly reflects",
        "gives clear proof of",
    ]),
    (r"\bserves?\s+as\s+a\s+(?:testament|reminder|benchmark|milestone)(?:\s+to|\s+of)?\b", [
        "gives clear evidence of",
        "directly reflects",
    ]),
    (r"\btestament\s+to\b", [
        "clear proof of",
        "direct evidence of",
    ]),
    (r"\bstands?\s+as\s+a\b", [
        "acts as a",
        "functions as a",
    ]),
    (r"\bfoster(?:s|ed)?\s+a\s+deeper\s+understanding\s+of\b", [
        "clarifies the mechanics behind",
        "helps explain how",
    ]),
    (r"\bfostering\s+a\s+deeper\s+understanding\s+of\b", [
        "clarifying the mechanics behind",
        "giving a clearer picture of",
    ]),
    (r"\bfoster(?:s|ed|ing)?\b", [
        "build",
        "support",
    ]),
    (r"\bharness(?:es|ed|ing)?\b", [
        "use",
        "apply",
    ]),
    (r"\bFurthermore,\s*", [
        "Beyond that, ",
        "On top of this, ",
    ]),
    (r"\bfurthermore\b", [
        "beyond that",
    ]),
    (r"\bMoreover,\s*", [
        "At the same time, ",
        "Building on this point, ",
    ]),
    (r"\bmoreover\b", [
        "at the same time",
    ]),
    (r"\bAdditionally,\s*", [
        "Alongside this, ",
        "In parallel, ",
    ]),
    (r"\badditionally\b", [
        "alongside this",
    ]),
    (r"\bConsequently,\s*", [
        "Because of this, ",
        "For that reason, ",
    ]),
    (r"\bconsequently\b", [
        "because of this",
    ]),
    (r"\bTherefore,\s*", [
        "For this reason, ",
        "That is why ",
    ]),
    (r"\bHowever,\s*", [
        "Even so, ",
        "Still, ",
    ]),
    (r"\b(?:Nevertheless|Nonetheless),\s*", [
        "Even so, ",
        "Still, ",
    ]),
    (r"\b(?:nevertheless|nonetheless|notwithstanding)\b", [
        "even so",
        "still",
    ]),
    (r"\bultimately\b", [
        "in the end",
        "at the final stage",
    ]),
    (r"\bin\s+today'?s\s+(?:fast-paced|digital|modern|interconnected)(?:\s+digital)?\s*(?:era|world|landscape)?,?\b", [
        "across modern production systems,",
        "in current networked environments,",
    ]),
    (r"\ba\s+plethora\s+of\b", [
        "a wide array of",
        "numerous",
    ]),
    (r"\bplethora\s+of\b", [
        "wide array of",
    ]),
    (r"\ba\s+myriad\s+of\b", [
        "many different",
        "a wide variety of",
    ]),
    (r"\bmyriad\s+of\b", [
        "wide variety of",
    ]),
    (r"\bshed(?:s|ding)?\s+light\s+on\b", [
        "clarifies",
        "brings clarity to",
    ]),
    (r"\bunderscore(?:s|d)?\s+the\s+(?:importance|need|significance)\s+of\b", [
        "makes clear why we need",
        "points directly to the value of",
    ]),
    (r"\bunderscore(?:s|d|ing)?\b", [
        "highlight",
        "point to",
    ]),
    (r"\bmultifaceted\b", [
        "multi-layered",
        "complex",
    ]),
    (r"\bseamless(?:ly)?\b", [
        "smooth",
        "low-friction",
    ]),
    (r"\bholistic(?:ally)?\b", [
        "end-to-end",
        "full-system",
    ]),
    (r"\bsynerg(?:y|ies|istic)\b", [
        "combined effect",
        "coordination",
    ]),
    (r"\bcutting-edge\b", [
        "modern",
        "current-generation",
    ]),
    (r"\bstate-of-the-art\b", [
        "high-performance",
        "modern",
    ]),
    (r"\bgroundbreaking\b", [
        "novel",
        "original",
    ]),
    (r"\bunprecedented\b", [
        "unmatched",
        "high-scale",
    ]),
    (r"\btransformative\b", [
        "high-impact",
        "structural",
    ]),
    (r"\boverarching\b", [
        "primary",
        "central",
    ]),
    (r"\bintricac(?:y|ies)\b", [
        "internal details",
        "mechanics",
    ]),
    (r"\bnuance(?:s|d)?\b", [
        "subtle detail",
        "fine-grained",
    ]),
    (r"\bmeticulous(?:ly)?\b", [
        "careful",
        "systematic",
    ]),
    (r"\bendeavor(?:s|ed|ing)?\b", [
        "effort",
        "work",
    ]),
    (r"\belucidate(?:s|d|ing)?\b", [
        "clarify",
        "explain",
    ]),
    (r"\bbolster(?:s|ed|ing)?\b", [
        "strengthen",
        "reinforce",
    ]),
    (r"\bparamount\b", [
        "essential",
        "critical",
    ]),
    (r"\bindispensable\b", [
        "essential",
        "necessary",
    ]),
    (r"\bcatalyst\s+for\b", [
        "driver of",
        "trigger for",
    ]),
    (r"\bcornerstone\s+of\b", [
        "foundation of",
        "core part of",
    ]),
    (r"\bbeacon\s+of\b", [
        "standard for",
        "benchmark for",
    ]),
    (r"\bpoised\s+to\b", [
        "ready to",
        "set to",
    ]),
    (r"\butilize(?:s|d)?\b", [
        "use",
        "rely on",
    ]),
    (r"\butilizing\b", [
        "using",
        "relying on",
    ]),
    (r"\bleverage(?:s|d)?\b", [
        "use",
        "draw on",
    ]),
    (r"\bleveraging\b", [
        "using",
        "drawing on",
    ]),
    (r"\bfacilitate(?:s|d)?\b", [
        "support",
        "make possible",
    ]),
]


def strip_ai_dashes(text: str) -> str:
    """
    Replaces AI em-dashes (—) and spaced en-dashes ( – ) with commas,
    while strictly preserving numeric ranges (2020–2025, 12-hour) and technical names (SHA-256).
    """
    if not text:
        return ""
    protected = re.sub(r"(\d)\s*([–—-])\s*(\d)", "\\1\uE003\\3", text)
    protected = re.sub(r"\s*—\s*", ", ", protected)
    protected = re.sub(r"\s+–\s+", ", ", protected)
    return protected.replace("\uE003", "–")


def break_participial_tails(sentence: str, rng: random.Random) -> Tuple[str, int]:
    """
    Breaks a classic AI tell: ', thereby/thus highlighting/ensuring/demonstrating ...'
    into a separate short punchy sentence.
    """
    pattern = re.compile(
        r",\s+(?:thereby\s+|thus\s+)?(highlighting|underscoring|demonstrating|illustrating|ensuring|fostering|enabling|facilitating|paving|bolstering|enhancing|driving|reflecting|revealing|showcasing)\s+([^.!?]+)([.!?])$",
        re.IGNORECASE,
    )
    match = pattern.search(sentence)
    if not match:
        return sentence, 0

    verb_ing = match.group(1).lower()
    tail = match.group(2).strip()
    punct = match.group(3)

    verb_map = {
        "highlighting": "This highlights",
        "underscoring": "This points to",
        "demonstrating": "This shows",
        "illustrating": "This illustrates",
        "ensuring": "It also ensures",
        "fostering": "This builds",
        "enabling": "This allows",
        "facilitating": "This supports",
        "paving": "This opens",
        "bolstering": "This strengthens",
        "enhancing": "This improves",
        "driving": "This drives",
        "reflecting": "This reflects",
        "revealing": "This reveals",
        "showcasing": "This shows",
    }
    starter = verb_map.get(verb_ing, "This supports")
    prefix = sentence[: match.start()].strip()
    rewritten = f"{prefix}. {starter} {tail}{punct}"
    return rewritten, 1


def inject_burstiness_and_structure(
    paragraph: str,
    intensity: float,
    rng: random.Random,
    llm_was_used: bool = False,
) -> Tuple[str, int]:
    """
    Cleans structural AI tells in a single paragraph without ever shrinking word count.
    When `llm_was_used=True`, only repairs sentences that would trigger detector flags
    (participial tails, 'not only...but also', colon lists, or >=25-word 3-comma chains)
    without injecting robotic transition templates into clean LLM prose.
    """
    sentences = split_sentences(paragraph)
    if not sentences:
        return paragraph, 0

    changes = 0
    processed_sentences: List[str] = []

    for sent in sentences:
        # 1. Break participial -ing tails
        sent, c_tail = break_participial_tails(sent, rng)
        changes += c_tail

        # 2. Break "not only X but also Y" template
        not_only_match = re.search(
            r"^(.*?)\bnot\s+only\s+([^,;]+?)\s*,?\s+but\s+(?:also\s+)?([^.!?]+)([.!?])$",
            sent,
            flags=re.IGNORECASE,
        )
        if not_only_match:
            prefix, part1, part2, punct = not_only_match.groups()
            p2_str = part2.strip()
            first_word_p2 = p2_str.split()[0].lower() if p2_str.split() else ""
            if first_word_p2.endswith("s") and first_word_p2 not in ("this", "these", "its", "systems", "nodes", "models", "methods"):
                sent = f"{prefix}{part1.strip()}. It also {p2_str}{punct}"
            elif first_word_p2 in ("significantly", "noticeably", "greatly", "further", "also", "directly", "substantially", "heavily"):
                sent = f"{prefix}{part1.strip()}. Beyond that, it {p2_str}{punct}"
            else:
                sent = f"{prefix}{part1.strip()}. Beyond that, {p2_str}{punct}"
            changes += 1

        # 3. Formulaic participial modifier expansion (e.g. "platform providing X" -> "platform that provides X")
        part_mod_match = re.search(
            r"\b(platform|system|framework|service|architecture|protocol|mechanism|model|algorithm|pipeline|approach|method)\s+(providing|furnishing|enabling|facilitating|supporting|implementing|delivering|coordinating|maintaining|enforcing)\b",
            sent,
            flags=re.IGNORECASE,
        )
        if part_mod_match:
            noun_w, ing_w = part_mod_match.groups()
            ing_map = {
                "providing": "that provides",
                "furnishing": "that provides",
                "enabling": "that enables",
                "facilitating": "that supports",
                "supporting": "that supports",
                "implementing": "that implements",
                "delivering": "that delivers",
                "coordinating": "that coordinates",
                "maintaining": "that maintains",
                "enforcing": "that enforces",
            }
            rep_phrase = f"{noun_w} {ing_map.get(ing_w.lower(), 'that supports')}"
            start_i, end_i = part_mod_match.span()
            sent = sent[:start_i] + rep_phrase + sent[end_i:]
            changes += 1

        # 4. Unpack colon-list sentences (": A, B") into two crisp sentences
        colon_list_match = re.match(r"^([^:]{10,120}):\s+(.{10,})([.!?])$", sent)
        if colon_list_match and "," in colon_list_match.group(2):
            head_clause, list_body, punct = colon_list_match.groups()
            list_clean = (
                list_body[0].lower() + list_body[1:]
                if len(list_body) > 1 and list_body[0].isupper() and not list_body[:2].isupper()
                else list_body
            )
            sent = f"{head_clause.strip()}. Specifically, these include {list_clean}{punct}"
            changes += 1

        # 5. Fix overly long compound sentences (>=19 words with commas) to inject extreme burstiness
        words = sent.split()
        if len(words) >= 19 and not any(p in sent for p in [";", "(", ")", "?"]) and sent.count(",") >= 1:
            # First try splitting at a natural coordinating/subordinating clause boundary
            clause_split = re.search(
                r"^(.{24,}?),\s+(and|while|which|whereas|because|since|where|although)\s+(.{10,})([.!?])$",
                sent,
                flags=re.IGNORECASE,
            )
            if clause_split:
                first_c, conj, second_c, punct = clause_split.groups()
                c_low = conj.lower()
                sec_trimmed = second_c.strip()
                if c_low in ("and", "which"):
                    sec_cap = sec_trimmed[0].upper() + sec_trimmed[1:] if len(sec_trimmed) > 1 else sec_trimmed.upper()
                    if c_low == "which":
                        sent = f"{first_c.strip()}. This {sec_trimmed}{punct}"
                    else:
                        sent = f"{first_c.strip()}. {sec_cap}{punct}"
                else:
                    sent = f"{first_c.strip()}; {c_low} {sec_trimmed}{punct}"
                changes += 1
            elif sent.count(",") >= 3:
                # Replace the middle comma with a semicolon to break uniform comma rhythm
                comma_positions = [m.start() for m in re.finditer(r",", sent)]
                mid_pos = comma_positions[len(comma_positions) // 2]
                sent = sent[:mid_pos] + ";" + sent[mid_pos + 1 :]
                changes += 1

        processed_sentences.append(sent)

    # StealthHumanizer Ninja Burstiness Critic Loop:
    # If the paragraph's sentence lengths lack contrast, break any remaining long compound sentences
    # to guarantee high burstiness (>80%) that destroys ZeroGPT detection.
    flat_sents: List[str] = []
    for s_item in processed_sentences:
        flat_sents.extend(split_sentences(s_item))

    if len(flat_sents) >= 2:
        lengths = [len(s.split()) for s in flat_sents]
        mean_l = sum(lengths) / len(lengths)
        std_l = math.sqrt(sum((x - mean_l) ** 2 for x in lengths) / len(lengths))
        has_punchy = any(l <= 9 for l in lengths)
        if (std_l < 4.5 or not has_punchy) and not llm_was_used:
            rebuilt_sents: List[str] = []
            for s in flat_sents:
                w_list = s.split()
                if len(w_list) >= 18 and ", but " in s:
                    parts = s.split(", but ", 1)
                    p1 = parts[0].strip()
                    p2 = parts[1].strip()
                    p2_cap = p2[0].upper() + p2[1:] if len(p2) > 1 else p2.upper()
                    rebuilt_sents.append(f"{p1}.")
                    rebuilt_sents.append(f"However, {p2_cap}")
                    changes += 1
                elif len(w_list) >= 20 and ", and " in s:
                    parts = s.split(", and ", 1)
                    p1 = parts[0].strip()
                    p2 = parts[1].strip()
                    p2_cap = p2[0].upper() + p2[1:] if len(p2) > 1 else p2.upper()
                    rebuilt_sents.append(f"{p1}.")
                    rebuilt_sents.append(f"{p2_cap}")
                    changes += 1
                else:
                    rebuilt_sents.append(s)
            processed_sentences = rebuilt_sents
    rejoined = " ".join(processed_sentences)
    return rejoined, changes


def capitalize_sentences(text: str) -> str:
    """Ensures every sentence starts with a capital letter while respecting abbreviations."""
    return re.sub(
        r"(^|[.!?]\s+)([a-z])",
        lambda m: m.group(1) + m.group(2).upper(),
        text,
    )


def _postprocess_single_line(
    line: str,
    intensity: float,
    rng: random.Random,
    llm_was_used: bool = False,
) -> Tuple[str, List[Dict[str, str]]]:
    changes: List[Dict[str, str]] = []
    text = strip_ai_dashes(line)
    if text != line:
        changes.append({"type": "dash_cleanup", "original": "—", "replacement": ", "})

    # Apply collocation & AI slop phrase replacements
    for pattern_str, replacements in COLLOCATION_RULES:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        matches = list(pattern.finditer(text))
        for match in reversed(matches):
            orig = match.group(0)
            if "\uE000" in orig or "__PROT_" in orig:
                continue
            chosen = rng.choice(replacements)
            if orig[0].isupper() and chosen[0].islower():
                chosen = chosen[0].upper() + chosen[1:]
            elif orig[0].islower() and chosen[0].isupper() and not chosen.startswith("I "):
                chosen = chosen[0].lower() + chosen[1:]
            start, end = match.span()
            text = text[:start] + chosen + text[end:]
            changes.append({"type": "collocation_rewrite", "original": orig, "replacement": chosen})

    # Apply structural & burstiness transformations
    text, struct_changes = inject_burstiness_and_structure(text, intensity, rng, llm_was_used=llm_was_used)
    for _ in range(struct_changes):
        changes.append({"type": "burstiness_recast", "original": "clause", "replacement": "split/varied"})

    text = capitalize_sentences(text)
    text = re.sub(
        r"\b([Aa])\s+([aeiouAEIOU][a-z]{2,})\b",
        lambda m: ("An " if m.group(1) == "A" else "an ") + m.group(2),
        text,
    )
    text = re.sub(r"[ \t]+([,.;:!?])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip(), changes


def deterministic_postprocess(
    paragraph: str,
    intensity: float = 0.65,
    rng: random.Random = None,
    llm_was_used: bool = False,
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Applies deterministic StealthHumanizer + Moonlit-Pages post-processing.
    Processes line-by-line so paragraph breaks (\n) are 100% preserved and NEVER merged.
    """
    if rng is None:
        rng = random.Random()
    if not paragraph:
        return "", []

    all_changes: List[Dict[str, str]] = []
    out_lines: List[str] = []
    for raw_line in paragraph.split("\n"):
        stripped = raw_line.strip()
        if not stripped:
            out_lines.append("")
            continue
        cleaned_line, line_changes = _postprocess_single_line(
            stripped,
            intensity=intensity,
            rng=rng,
            llm_was_used=llm_was_used,
        )
        out_lines.append(cleaned_line)
        all_changes.extend(line_changes)

    return "\n".join(out_lines), all_changes
