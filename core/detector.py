"""
Multi-Metric Statistical AI Detection Engine
Ported & adapted from StealthHumanizer + Moonlit-Pages academic thesis detector principles.
Evaluates:
1. Sentence Length Burstiness (Coefficient of Variation & adjacent diffs)
2. Vocabulary Diversity (Moving-Average Type-Token Ratio - MATTR, length-invariant)
3. AI Slop & Cliché Density (85+ high-frequency LLM markers)
4. Structural Templates (Participial -ing tails, 'not only... but also', triadic lists)
5. Sentence Opening Entropy (repetitive 'The', 'This', 'Furthermore' starts)
6. Punctuation & Rhythm Uniformity (em-dashes, uniform paragraph lengths)
"""

import re
import math
from typing import Dict, List, Any

# High-severity AI slop words & phrases (weighted by statistical tell strength)
AI_SLOP_PATTERNS = [
    (r"\bdelve(?:s|d|ing)?(?:\s+into)?\b", 4, "delve"),
    (r"\btapestr(?:y|ies)\b", 4, "tapestry"),
    (r"\btestament\s+to\b", 4, "testament to"),
    (r"\bpivotal(?:\s+role)?\b", 3, "pivotal"),
    (r"\bunderscore(?:s|d|ing)?\b", 3, "underscore"),
    (r"\bmultifaceted\b", 3, "multifaceted"),
    (r"\bin\s+today'?s\s+(?:fast-paced|digital|modern|interconnected)\b", 4, "in today's ..."),
    (r"\bit\s+is\s+(?:important|worth|crucial|essential|vital)\s+to\s+(?:note|mention|highlight|remember|understand)\b", 4, "it is important to note"),
    (r"\bplays?\s+a\s+(?:crucial|vital|pivotal|key|significant|central|essential)\s+role\b", 3, "plays a crucial role"),
    (r"\bpave(?:s|d|ing)?\s+the\s+way\b", 3, "paves the way"),
    (r"\bshed(?:s|ding)?\s+light\s+on\b", 3, "sheds light on"),
    (r"\bfoster(?:s|ed|ing)?\b", 2, "foster"),
    (r"\bharness(?:es|ed|ing)?\b", 2, "harness"),
    (r"\brealm\s+of\b", 3, "realm of"),
    (r"\blandscape\s+of\b", 2, "landscape of"),
    (r"\bparadigm\s+shift\b", 3, "paradigm shift"),
    (r"\bplethora\s+of\b", 3, "plethora of"),
    (r"\bmyriad\s+of\b", 3, "myriad of"),
    (r"\bseamless(?:ly)?\b", 2, "seamless"),
    (r"\bholistic(?:ally)?\b", 2, "holistic"),
    (r"\bsynerg(?:y|ies|istic)\b", 3, "synergy"),
    (r"\bcutting-edge\b", 2, "cutting-edge"),
    (r"\bstate-of-the-art\b", 2, "state-of-the-art"),
    (r"\bgroundbreaking\b", 2, "groundbreaking"),
    (r"\bunprecedented\b", 2, "unprecedented"),
    (r"\btransformative\b", 2, "transformative"),
    (r"\boverarching\b", 2, "overarching"),
    (r"\bintricac(?:y|ies)\b", 3, "intricacies"),
    (r"\bnuance(?:s|d)?\b", 2, "nuanced"),
    (r"\bfurthermore\b", 2, "furthermore"),
    (r"\bmoreover\b", 2, "moreover"),
    (r"\badditionally\b", 1.5, "additionally"),
    (r"\bin\s+conclusion\b", 2, "in conclusion"),
    (r"\bultimately\b", 1.5, "ultimately"),
    (r"\bconsequently\b", 1.5, "consequently"),
    (r"\bnevertheless\b", 1.5, "nevertheless"),
    (r"\bnonetheless\b", 1.5, "nonetheless"),
    (r"\bnotwithstanding\b", 2, "notwithstanding"),
    (r"\bmeticulous(?:ly)?\b", 2, "meticulous"),
    (r"\bendeavor(?:s|ed|ing)?\b", 2, "endeavor"),
    (r"\belucidate(?:s|d|ing)?\b", 2, "elucidate"),
    (r"\bbolster(?:s|ed|ing)?\b", 2, "bolster"),
    (r"\bparamount\b", 2, "paramount"),
    (r"\bindispensable\b", 2, "indispensable"),
    (r"\bcatalyst\s+for\b", 2, "catalyst for"),
    (r"\bcornerstone\s+of\b", 2, "cornerstone of"),
    (r"\bbeacon\s+of\b", 3, "beacon of"),
    (r"\bpoised\s+to\b", 2, "poised to"),
    (r"\bstands?\s+as\s+a\b", 2, "stands as a"),
    (r"\bserves?\s+as\s+a\s+(?:testament|reminder|benchmark|milestone)\b", 3, "serves as a milestone"),
]

# Structural AI templates (Wikipedia Signs of AI Writing + Turnitin AI structural signals)
STRUCTURAL_TEMPLATES = [
    # Participial "-ing" clause tacked onto the end of a sentence after a comma
    (r",\s+(?:thereby\s+|thus\s+)?(?:highlighting|underscoring|demonstrating|illustrating|ensuring|fostering|enabling|facilitating|paving|bolstering|enhancing|driving|reflecting|showcasing)\s+[^.!?]{5,}[.!?]", 3.5, "participial -ing tail"),
    # "Not only ... but also ..."
    (r"\bnot\s+only\b[^.!?]{3,60}\bbut\s+(?:also\b)?", 2.5, "not only...but also"),
    # "It is not just X; it is Y" / "more than just"
    (r"\b(?:not\s+just|more\s+than\s+just|not\s+merely)\b[^.!?]{2,50}\b(?:it\s+is|it's|but\s+rather|but\s+a)\b", 3.5, "not just X, it's Y"),
    # Em-dash overuse
    (r"\s*—\s*", 2.0, "em-dash"),
]


def split_sentences(text: str) -> List[str]:
    """Splits text into sentences while protecting decimals, versions, IPs, and abbreviations."""
    if not text or not text.strip():
        return []
    # Protect alnum.alnum (e.g., 3.14, v2.6, 192.168.1.1)
    protected = re.sub(r"([A-Za-z0-9])\.(?=[A-Za-z0-9])", "\\1\uE002", text)
    # Protect common abbreviations
    protected = re.sub(
        r"\b(e\.g|i\.e|et\s+al|Fig|Eq|Dr|Prof|Mr|Mrs|Ms|vs|etc|cf|Inc|Ltd|Jr|Sr|No)\.",
        lambda m: m.group(0).replace(".", "\uE002"),
        protected,
        flags=re.IGNORECASE,
    )
    raw_parts = re.findall(r"[^.!?]+[.!?]+|\S[^.!?]*$", protected)
    sentences = []
    for part in raw_parts:
        restored = part.replace("\uE002", ".").strip()
        # Ignore tiny heading numbers like "1." or "2."
        if len(restored.split()) >= 2:
            sentences.append(restored)
    return sentences


def calculate_mattr(words: List[str], window: int = 50) -> float:
    """
    Moving-Average Type-Token Ratio (MATTR).
    Unlike raw TTR (which drops artificially on 10,000-word texts),
    MATTR is completely length-invariant.
    """
    if not words:
        return 0.0
    lower_words = [w.lower() for w in words]
    if len(lower_words) <= window:
        return len(set(lower_words)) / len(lower_words)

    ratios = []
    # Step by 10 words for speed on 10k-word inputs
    step = max(1, min(10, (len(lower_words) - window) // 50 + 1))
    for i in range(0, len(lower_words) - window + 1, step):
        chunk = lower_words[i : i + window]
        ratios.append(len(set(chunk)) / window)
    return sum(ratios) / len(ratios) if ratios else 0.65


def analyze_ai_Footprint(text: str) -> Dict[str, Any]:
    """
    Computes a realistic, multi-signal AI detection risk score (0-100%)
    and returns granular breakdown metrics.
    """
    if not text or not text.strip():
        return {
            "words": 0,
            "ai_risk": 0,
            "burstiness": 0.0,
            "cliche_count": 0,
            "vocabulary_diversity": 0.0,
            "flagged_phrases": [],
        }

    words = re.findall(r"\b[A-Za-z0-9'-]+\b", text)
    word_count = len(words)
    if word_count == 0:
        return {
            "words": 0,
            "ai_risk": 0,
            "burstiness": 0.0,
            "cliche_count": 0,
            "vocabulary_diversity": 0.0,
            "flagged_phrases": [],
        }

    # 1. Slop & Cliché Density
    slop_weight = 0.0
    cliche_count = 0
    flagged_phrases = []
    for pattern, weight, label in AI_SLOP_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            count = len(matches)
            cliche_count += count
            slop_weight += count * weight
            flagged_phrases.append(label)

    for pattern, weight, label in STRUCTURAL_TEMPLATES:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            count = len(matches)
            cliche_count += count
            slop_weight += count * weight
            flagged_phrases.append(label)

    # Normalize slop per 100 words
    slop_per_100 = (slop_weight / max(25, word_count)) * 100.0
    slop_risk = min(100.0, slop_per_100 * 9.5)

    # 2. Sentence Length Burstiness (CV + Adjacent Jump Variance)
    sentences = split_sentences(text)
    sent_lengths = [len(s.split()) for s in sentences if len(s.split()) >= 2]

    if len(sent_lengths) >= 2:
        mean_len = sum(sent_lengths) / len(sent_lengths)
        variance = sum((x - mean_len) ** 2 for x in sent_lengths) / len(sent_lengths)
        std_dev = math.sqrt(variance)
        cv = std_dev / max(1.0, mean_len)  # Coefficient of variation (Human >= 0.45, AI ~ 0.20-0.32)

        # Adjacent sentence length jumps
        jumps = [abs(sent_lengths[i] - sent_lengths[i - 1]) for i in range(1, len(sent_lengths))]
        avg_jump = sum(jumps) / len(jumps)

        # Check for short punchy sentences (<= 9 words) and long sentences (>= 26 words)
        has_short = any(l <= 9 for l in sent_lengths)
        has_long = any(l >= 24 for l in sent_lengths)

        # Convert CV + jump to burstiness risk (lower CV = higher AI risk)
        if cv >= 0.52 and avg_jump >= 8.5 and has_short:
            burstiness_risk = max(5.0, 28.0 - (cv - 0.52) * 40.0)
        elif cv >= 0.40 and avg_jump >= 6.5:
            burstiness_risk = 38.0 - (cv - 0.40) * 80.0
        else:
            # Uniform sentence lengths -> strong AI signal
            burstiness_risk = min(92.0, 58.0 + (0.40 - cv) * 110.0)
            if not has_short:
                burstiness_risk = min(95.0, burstiness_risk + 12.0)
    else:
        std_dev = 0.0
        burstiness_risk = 45.0

    # 3. Sentence Opening Diversity & Contractions / Human Markers
    if len(sentences) >= 3:
        starters = []
        for s in sentences:
            toks = re.findall(r"\b[A-Za-z']+\b", s)
            if toks:
                starters.append(toks[0].lower())
        starter_diversity = len(set(starters)) / max(1, len(starters))
        # AI often starts >35% of sentences with "The", "This", "It", "In", "These"
        ai_determiner_starts = sum(1 for st in starters if st in ("the", "this", "these", "it", "in"))
        det_ratio = ai_determiner_starts / max(1, len(starters))
        opening_risk = max(10.0, min(85.0, (1.0 - starter_diversity) * 60.0 + det_ratio * 45.0))
    else:
        opening_risk = 35.0

    # 4. MATTR Vocabulary Diversity
    mattr = calculate_mattr(words, window=50)
    # Human MATTR on 50-word window is typically 0.72 - 0.84; repetitive AI templates drop or over-pack
    if mattr >= 0.74:
        vocab_risk = 20.0
    elif mattr >= 0.66:
        vocab_risk = 38.0
    else:
        vocab_risk = 65.0

    # 5. Human Rhythm & Punctuation Variety Bonus (semicolons, parentheses, questions, contractions, colons)
    human_markers = 0
    if re.search(r"\b(?:don't|doesn't|isn't|aren't|can't|won't|it's|that's|there's|we're|they're)\b", text, re.I):
        human_markers += 2
    if ";" in text:
        human_markers += 1
    if "?" in text:
        human_markers += 1
    if len(sent_lengths) >= 3 and any(l <= 7 for l in sent_lengths):
        human_markers += 2

    human_bonus = min(22.0, human_markers * 4.5)

    # Combine weighted signals
    combined = (
        0.38 * burstiness_risk
        + 0.34 * slop_risk
        + 0.16 * opening_risk
        + 0.12 * vocab_risk
        - human_bonus
    )

    # If slop_weight is very high (>= 3 major AI clichés in a short passage), floor the risk
    if slop_per_100 >= 6.0:
        combined = max(combined, min(95.0, 62.0 + slop_per_100 * 2.5))

    ai_risk = int(round(max(4.0, min(98.0, combined))))
    burstiness_score = int(round(max(5.0, min(99.0, 100.0 - burstiness_risk))))

    return {
        "words": word_count,
        "ai_risk": ai_risk,
        "burstiness": round(std_dev, 2),
        "burstiness_score": burstiness_score,
        "cliche_count": cliche_count,
        "vocabulary_diversity": round(mattr * 100.0, 1),
        "flagged_phrases": flagged_phrases[:10],
    }

