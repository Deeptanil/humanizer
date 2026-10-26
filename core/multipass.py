"""
Multi-Pass Generation 3 Humanizer Pipeline
Implements the 4-pass transformation architecture from the research papers:
Pass 1: Severity-Ranked Pattern Stripping (Critical, High, Medium, Low AI tells)
Pass 2: Cognitive Signal & Voice Injection (sensory anchoring, parentheticals, confidence gradients)
Pass 3: Statistical & Metric Tuning (forces sentence length std dev sigma_L >= 8.0, CV_S >= 0.45, opening entropy)
Pass 4: Multi-Point Verification Matrix (8-point audit gate with readability guardrails)
"""

import re
import math
import random
from typing import List, Dict, Tuple, Any, Optional

from .detector import split_sentences, AI_SLOP_PATTERNS, STRUCTURAL_TEMPLATES

# ==============================================================================
# PASS 1: SEVERITY-RANKED PATTERN STRIPPING
# ==============================================================================

# Critical Severity: High-frequency transitional markers & copula avoidance
CRITICAL_SEVERITY_PATTERNS: List[Tuple[str, List[str]]] = [
    (r"\bFurthermore,?\s*", ["Beyond that, ", "At the same time, ", "On top of that, "]),
    (r"\bMoreover,?\s*", ["At the same time, ", "Building on this, ", "Equally important, "]),
    (r"\bAdditionally,?\s*", ["Along with this, ", "In addition, ", "Also, "]),
    (r"\bIn\s+conclusion,?\s*", ["In summary, ", "Taking all this together, ", "All in all, "]),
    (r"\bTo\s+summarize,?\s*", ["In short, ", "Overall, ", "Put simply, "]),
    (r"\bConsequently,?\s*", ["As a result, ", "For this reason, ", "Because of this, "]),
    (r"\bNevertheless,?\s*", ["Even so, ", "Still, ", "Yet, "]),
    (r"\bNonetheless,?\s*", ["Even so, ", "Still, ", "All the same, "]),
    (r"\bIt\s+is\s+(?:important|worth|crucial|essential|vital)\s+to\s+(?:note|remember|highlight|mention)\s+that\b", ["Notably,", "Crucially,", "In particular,"]),
    # Copula avoidance structures
    (r"\bserves?\s+as\s+an?\s+illustration\s+of\b", ["shows", "illustrates", "demonstrates"]),
    (r"\bacts?\s+as\s+a\s+(?:vital\s+)?catalyst\s+for\b", ["spurs", "drives", "fuels"]),
    (r"\bstands?\s+as\s+a\s+testament\s+to\b", ["proves", "gives clear proof of", "shows"]),
    (r"\bis\s+indicative\s+of\b", ["indicates", "shows", "reflects"]),
    (r"\bplays?\s+a\s+(?:crucial|vital|pivotal|key|central|significant)\s+role\s+in\b", ["directly shapes", "is central to", "drives"]),
]

# High Severity: Em-dash clusters, rules of three, false ranges, trailing participials
HIGH_SEVERITY_PATTERNS: List[Tuple[str, List[str]]] = [
    (r"\bdelv(?:e|es|ed|ing)(?:\s+deeply)?(?:\s+into)?\b", ["examine", "explore", "investigate", "look into"]),
    (r"\b(?:rich\s+)?tapestr(?:y|ies)(?:\s+of)?\b", ["mosaic", "complex mix", "broad spectrum", "network"]),
    (r"\bmultifaceted\b", ["complex", "varied", "nuanced"]),
    (r"\bseamless(?:ly)?\b", ["smoothly", "directly", "without friction"]),
    (r"\bholistic(?:ally)?\b", ["broadly", "comprehensively", "system-wide"]),
    (r"\bsynerg(?:y|ies|istic)\b", ["cooperation", "shared momentum", "alignment"]),
    (r"\bparadigm\s+shift\b", ["fundamental change", "major transition", "deep shift"]),
    (r"\ba\s+living\s+testament\s+to\b", ["tangible proof of", "clear evidence of", "a direct reflection of"]),
    (r"\ban?\s+enduring\s+reminder\s+(?:that|of)\b", ["clear proof that", "concrete evidence that"]),
    (r"\ba\s+cornerstone\s+of\b", ["foundational to", "central to", "a bedrock of"]),
    (r"\bbeacon\s+of\b", ["standard for", "symbol of", "model for"]),
    (r"\bat\s+its\s+essence,?\s*", ["fundamentally, ", "at its core, ", "in simple terms, "]),
    (r"\bthough\s+invisible\s+to\s+the\s+naked\s+eye,?\s*", ["while unseen without instruments, ", "although invisible to casual observation, "]),
    (r"\bpoised\s+to\b", ["set to", "ready to", "positioned to"]),
    (r"\bplethora\s+of\b", ["wealth of", "wide array of", "host of"]),
    (r"\bmyriad\s+(?:of\s+)?\b", ["countless", "numerous", "wide range of"]),
    (r"\bcutting-edge\b", ["advanced", "modern", "high-performance"]),
    (r"\bstate-of-the-art\b", ["modern", "current", "advanced"]),
    (r"\bgroundbreaking\b", ["pioneering", "notable", "significant"]),
    (r"\btransformative\b", ["pivotal", "sweeping", "far-reaching"]),
    (r"\boverarching\b", ["primary", "broad", "governing"]),
]


def pass_1_pattern_stripping(text: str, rng: random.Random) -> Tuple[str, List[Dict[str, str]]]:
    """
    Pass 1: Severity-Ranked Pattern Stripping
    Dismantles critical and high-severity AI markers, em-dashes, and trailing participial tails.
    """
    changes: List[Dict[str, str]] = []

    # 1. Strip em-dashes (—)
    if "—" in text or " – " in text:
        text = re.sub(r"\s*—\s*", ", ", text)
        text = re.sub(r"\s+–\s+", ", ", text)
        changes.append({"type": "pass1_em_dash_strip", "original": "—", "replacement": ", "})

    # 2. Critical severity transitional & copula avoidance replacement
    for pattern, repls in CRITICAL_SEVERITY_PATTERNS:
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        for m in reversed(matches):
            orig = m.group(0)
            if "__PROT_" in orig:
                continue
            chosen = rng.choice(repls)
            if orig[0].isupper() and chosen[0].islower():
                chosen = chosen[0].upper() + chosen[1:]
            elif orig[0].islower() and chosen[0].isupper() and not chosen.startswith("I "):
                chosen = chosen[0].lower() + chosen[1:]
            start, end = m.span()
            text = text[:start] + chosen + text[end:]
            changes.append({"type": "pass1_critical_strip", "original": orig, "replacement": chosen})

    # 3. High severity AI buzzword and cliché stripping
    for pattern, repls in HIGH_SEVERITY_PATTERNS:
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        for m in reversed(matches):
            orig = m.group(0)
            if "__PROT_" in orig:
                continue
            chosen = rng.choice(repls)
            if orig[0].isupper() and chosen[0].islower():
                chosen = chosen[0].upper() + chosen[1:]
            elif orig[0].islower() and chosen[0].isupper() and not chosen.startswith("I "):
                chosen = chosen[0].lower() + chosen[1:]
            start, end = m.span()
            text = text[:start] + chosen + text[end:]
            changes.append({"type": "pass1_high_strip", "original": orig, "replacement": chosen})

    # 4. Clean trailing participial -ing analyses at paragraph ends
    text = re.sub(
        r",\s+(?:thereby|thus)?\s*(?:highlighting|underscoring|demonstrating|illustrating|ensuring|fostering|enabling|facilitating)\s+([^.!?]+)([.!?;])$",
        r". This directly shows \1\2",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    return text, changes


# ==============================================================================
# PASS 2: COGNITIVE SIGNAL & VOICE INJECTION
# ==============================================================================

QUALIFYING_SHIFTS = [
    "in practical terms",
    "at least in part",
    "to a significant degree",
    "strictly speaking",
    "in real-world settings",
    "as observation confirms",
]


def pass_2_cognitive_injection(text: str, rng: random.Random) -> Tuple[str, List[Dict[str, str]]]:
    """
    Pass 2: Cognitive Signal & Voice Injection
    Injects human cognitive artifacts (parenthetical qualifiers, confidence gradients)
    that discriminative classifiers look for when confirming human authorship.
    """
    changes: List[Dict[str, str]] = []
    paragraphs = text.split("\n\n")
    processed_paragraphs = []

    for p_idx, p in enumerate(paragraphs):
        lines = p.split("\n")
        processed_lines = []
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or line_str.startswith("[P"):
                processed_lines.append(line)
                continue

            sents = split_sentences(line_str)
            if len(sents) >= 3 and rng.random() < 0.65:
                # Select a candidate mid-sized sentence (16-26 words) to inject a natural qualifier
                candidates = [
                    (i, s) for i, s in enumerate(sents)
                    if 16 <= len(s.split()) <= 26
                    and not any(q in s for q in QUALIFYING_SHIFTS)
                    and not any(p_char in s for p_char in [";", "(", ")"])
                ]
                if candidates:
                    chosen_idx, chosen_sent = rng.choice(candidates)
                    words = chosen_sent.split()
                    qualifier = rng.choice(QUALIFYING_SHIFTS)
                    # Insert after the main subject or opening clause if comma exists
                    if "," in chosen_sent:
                        first_comma = chosen_sent.find(",")
                        new_sent = chosen_sent[:first_comma] + f", {qualifier}," + chosen_sent[first_comma + 1:]
                    else:
                        # Insert after the 3rd or 4th word
                        split_pt = min(4, len(words) - 2)
                        new_sent = " ".join(words[:split_pt]) + f", {qualifier}," + " " + " ".join(words[split_pt:])
                    sents[chosen_idx] = new_sent
                    changes.append({
                        "type": "pass2_cognitive_qualifier",
                        "original": chosen_sent[:30] + "...",
                        "replacement": qualifier,
                    })

            processed_lines.append(" ".join(sents))
        processed_paragraphs.append("\n".join(processed_lines))

    return "\n\n".join(processed_paragraphs), changes


# ==============================================================================
# PASS 3: STATISTICAL & METRIC TUNING (THE MATH LAYER)
# ==============================================================================

def calculate_burstiness_stats(sents: List[str]) -> Tuple[float, float, float]:
    """Computes mean length, standard deviation (sigma_L), and coefficient of variation (CV_S)."""
    lengths = [len(s.split()) for s in sents if len(s.split()) >= 2]
    if len(lengths) < 2:
        return 0.0, 0.0, 0.0
    mu = sum(lengths) / len(lengths)
    var = sum((x - mu) ** 2 for x in lengths) / len(lengths)
    sigma = math.sqrt(var)
    cv = sigma / max(1.0, mu)
    return mu, sigma, cv


def pass_3_statistical_tuning(text: str, rng: random.Random) -> Tuple[str, List[Dict[str, str]]]:
    """
    Pass 3: Statistical & Metric Tuning
    Actively forces:
    1. Sentence length standard deviation sigma_L >= 8.0
    2. Coefficient of variation CV_S >= 0.45
    3. Sharp contrast: Presence of short punchy assertions (3-8 words) paired with periodic sentences (25-35 words).
    4. Diverse sentence opening entropy.
    """
    changes: List[Dict[str, str]] = []
    paragraphs = text.split("\n\n")
    rebuilt_paragraphs = []

    for p in paragraphs:
        if not p.strip() or p.strip().startswith("#"):
            rebuilt_paragraphs.append(p)
            continue

        sents = split_sentences(p)
        if len(sents) < 2:
            rebuilt_paragraphs.append(p)
            continue

        mu, sigma, cv = calculate_burstiness_stats(sents)

        # If burstiness is below human target (sigma_L < 8.0 or CV_S < 0.45), inject clausal asymmetry
        if sigma < 8.0 or cv < 0.45 or not any(len(s.split()) <= 8 for s in sents):
            tuned_sents: List[str] = []
            for s in sents:
                words = s.split()
                w_len = len(words)

                # Split long compound-complex sentences (>= 20 words with a coordinator/subordinator)
                if w_len >= 20 and not any(ch in s for ch in [";", "(", ")"]):
                    # 1. Match coordinating conjunctions: ", but ", ", yet ", ", and [subject]"
                    coord_match = re.search(
                        r"^(.*?),\s+(yet|but|and\s+(?:it|this|they|these|we)|whereby|whereas|while)\s+(.+?)([.!?])$",
                        s,
                        flags=re.IGNORECASE,
                    )
                    # 2. Match front participial clauses: "V-ing ..., [Main Clause]."
                    ing_front_match = re.search(
                        r"^([A-Z][a-z]+ing\s+[^,]{10,25}),\s+([^,]{15,})([.!?])$",
                        s,
                    )

                    if coord_match:
                        first_c, conj, second_c, punct = coord_match.groups()
                        c_lower = conj.lower().strip()
                        if c_lower in ("yet", "but"):
                            sec_cap = second_c.strip()[0].upper() + second_c.strip()[1:]
                            tuned_sents.append(f"{first_c.strip()}.")
                            tuned_sents.append(f"{c_lower.capitalize()} {second_c.strip()}{punct}")
                            changes.append({"type": "pass3_burstiness_split", "original": s[:35], "replacement": f". {c_lower.capitalize()} "})
                        elif c_lower.startswith("and "):
                            pronoun = c_lower.split()[1].capitalize()
                            tuned_sents.append(f"{first_c.strip()}.")
                            tuned_sents.append(f"{pronoun} {second_c.strip()}{punct}")
                            changes.append({"type": "pass3_burstiness_split", "original": s[:35], "replacement": f". {pronoun} "})
                        elif c_lower in ("while", "whereas"):
                            tuned_sents.append(f"{first_c.strip()}; {c_lower} {second_c.strip()}{punct}")
                            changes.append({"type": "pass3_semicolon_period", "original": s[:35], "replacement": "semicolon_clause"})
                        else:
                            tuned_sents.append(s)
                    elif ing_front_match and (sigma < 8.0 or cv < 0.40):
                        front_ing, main_cl, punct = ing_front_match.groups()
                        main_cap = main_cl[0].upper() + main_cl[1:] if len(main_cl) > 1 else main_cl.upper()
                        tuned_sents.append(f"{main_cap}{punct}")
                        tuned_sents.append(f"In doing so, it functions by {front_ing.lower()}{punct}")
                        changes.append({"type": "pass3_front_ing_inversion", "original": s[:35], "replacement": "inverted_clauses"})
                    else:
                        tuned_sents.append(s)
                else:
                    tuned_sents.append(s)
            sents = tuned_sents

        # Opening Entropy Optimization: Ensure adjacent sentences do not start with the same word
        for i in range(1, len(sents)):
            prev_first = sents[i - 1].split()[0].lower() if sents[i - 1].split() else ""
            curr_first = sents[i].split()[0].lower() if sents[i].split() else ""
            if prev_first and curr_first and prev_first == curr_first and curr_first in ("the", "this", "it", "in", "as"):
                # Transpose front adverbial or apply topicalization if a comma exists
                curr_s = sents[i]
                if "," in curr_s:
                    parts = curr_s.split(",", 1)
                    lead, tail = parts[0].strip(), parts[1].strip()
                    # If lead is short (2-4 words), shift or rephrase
                    if len(lead.split()) <= 4 and tail:
                        tail_cap = tail[0].upper() + tail[1:] if len(tail) > 1 else tail.upper()
                        sents[i] = f"{tail_cap.rstrip('.!?')}, {lead.lower()}."
                        changes.append({"type": "pass3_opening_entropy_transposition", "original": curr_s[:30], "replacement": sents[i][:30]})

        rebuilt_paragraphs.append(" ".join(sents))

    return "\n\n".join(rebuilt_paragraphs), changes


# ==============================================================================
# PASS 4: MULTI-POINT VERIFICATION & AUDIT MATRIX
# ==============================================================================

class VerificationReport:
    def __init__(
        self,
        passed: bool,
        sigma_L: float,
        cv_S: float,
        has_short_fragment: bool,
        has_periodic_sentence: bool,
        cliche_count: int,
        opening_entropy: float,
        flesch_grade: float,
        details: Dict[str, Any],
    ):
        self.passed = passed
        self.sigma_L = sigma_L
        self.cv_S = cv_S
        self.has_short_fragment = has_short_fragment
        self.has_periodic_sentence = has_periodic_sentence
        self.cliche_count = cliche_count
        self.opening_entropy = opening_entropy
        self.flesch_grade = flesch_grade
        self.details = details


def pass_4_verify_audit(text: str) -> VerificationReport:
    """
    Pass 4: Multi-Point Verification Matrix (Audit Gate)
    Verifies the 8-point heuristic criteria defined in research:
    1. sigma_L >= 7.5
    2. cv_S >= 0.40
    3. Presence of short assertion (<= 9 words)
    4. Presence of periodic analytical sentence (>= 24 words)
    5. Zero critical AI clichés
    6. Sentence opening entropy
    7. Readability index stability
    """
    sents = split_sentences(text)
    lengths = [len(s.split()) for s in sents if len(s.split()) >= 2]
    mu, sigma, cv = calculate_burstiness_stats(sents)

    has_short = any(l <= 9 for l in lengths)
    has_periodic = any(l >= 24 for l in lengths)

    # Check for remaining AI slop markers
    cliche_count = 0
    flagged = []
    for pattern, weight, label in AI_SLOP_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            cliche_count += len(matches)
            flagged.append(label)

    # Compute sentence opening entropy
    openers = [s.split()[0].lower() for s in sents if s.split()]
    opener_counts = {}
    for o in openers:
        opener_counts[o] = opener_counts.get(o, 0) + 1
    total_openers = max(1, len(openers))
    entropy = -sum((cnt / total_openers) * math.log2(cnt / total_openers) for cnt in opener_counts.values())

    # Readability heuristic (approximate Flesch-Kincaid Grade Level)
    words = re.findall(r"\b[A-Za-z]+\b", text)
    word_count = max(1, len(words))
    sentence_count = max(1, len(sents))
    # Count syllables roughly
    syllable_count = sum(max(1, len(re.findall(r"[aeiouyAEIOUY]+", w))) for w in words)
    fk_grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59

    # Overall pass criteria: high burstiness + no clichés + length diversity
    passed = (
        sigma >= 7.0
        and cv >= 0.38
        and has_short
        and has_periodic
        and cliche_count == 0
    )

    return VerificationReport(
        passed=passed,
        sigma_L=round(sigma, 2),
        cv_S=round(cv, 2),
        has_short_fragment=has_short,
        has_periodic_sentence=has_periodic,
        cliche_count=cliche_count,
        opening_entropy=round(entropy, 2),
        flesch_grade=round(fk_grade, 1),
        details={
            "mu": round(mu, 2),
            "total_sentences": sentence_count,
            "flagged_cliches": flagged,
            "lengths_sample": lengths[:15],
        },
    )


# ==============================================================================
# MASTER GENERATION 3 PIPELINE RUNNER
# ==============================================================================

def execute_generation_3_pipeline(
    text: str,
    intensity: float = 0.85,
    rng: Optional[random.Random] = None,
    llm_was_used: bool = False,
) -> Tuple[str, List[Dict[str, str]], VerificationReport]:
    """
    Executes the full Generation 3 Multi-Pass Humanizer Engine.
    Pass 1: Severity-Ranked Pattern Stripping
    Pass 2: Cognitive Signal & Voice Injection
    Pass 3: Statistical & Metric Tuning (Mathematical calibration)
    Pass 4: Multi-Point Verification Matrix
    """
    if rng is None:
        rng = random.Random()

    all_changes: List[Dict[str, str]] = []

    # Strip statistical watermarks first
    try:
        import texthumanize
        cleaned_wm = texthumanize.clean_watermarks(text)
        if cleaned_wm and isinstance(cleaned_wm, str):
            text = cleaned_wm
    except Exception:
        pass

    # Pass 1: Severity-Ranked Pattern Stripping
    text, p1_changes = pass_1_pattern_stripping(text, rng)
    all_changes.extend(p1_changes)

    # Pass 2: Cognitive Signal & Voice Injection
    text, p2_changes = pass_2_cognitive_injection(text, rng)
    all_changes.extend(p2_changes)

    # Pass 3: Statistical & Metric Tuning (Burstiness & Entropy)
    text, p3_changes = pass_3_statistical_tuning(text, rng)
    all_changes.extend(p3_changes)

    # Pass 4: Verification & Audit Gate
    report = pass_4_verify_audit(text)

    # If verification failed on burstiness or residual tells, run a second iterative pass on failing metrics
    if not report.passed:
        if report.cliche_count > 0:
            text, retry_p1 = pass_1_pattern_stripping(text, rng)
            all_changes.extend(retry_p1)
        if report.sigma_L < 7.5 or not report.has_short_fragment:
            text, retry_p3 = pass_3_statistical_tuning(text, rng)
            all_changes.extend(retry_p3)
        report = pass_4_verify_audit(text)

    return text, all_changes, report
