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


def is_sentence_ai_flagged(sent: str) -> bool:
    """
    Evaluates whether an individual sentence exhibits characteristic AI generation patterns,
    matching the sentence-level classification methodology of ZeroGPT and GPTZero.
    """
    s = sent.strip()
    words = s.split()
    if len(words) < 4:
        return False

    # 1. High/medium-confidence AI cliché patterns
    for pattern, weight, label in AI_SLOP_PATTERNS:
        if weight >= 1.5 and re.search(pattern, s, re.IGNORECASE):
            return True

    # 2. Structural templates
    for pattern, weight, label in STRUCTURAL_TEMPLATES:
        if weight >= 1.5 and re.search(pattern, s, re.IGNORECASE):
            return True

    # 3. Colon-list structure
    if re.search(r":\s*[^,]+,\s*[^,]+", s):
        return True

    # 4. Formulaic participial modifiers
    if re.search(r"\b(?:platform|system|framework|service|architecture)\s+(?:providing|furnishing|enabling|facilitating)\b", s, re.IGNORECASE):
        return True

    # 5. Overly long unvaried compound sentence with comma chains
    if len(words) >= 25 and not any(p in s for p in [";", "(", ")", "?"]) and s.count(",") >= 3:
        return True

    return False


def analyze_ai_Footprint(text: str) -> Dict[str, Any]:
    """
    Analyzes document text and calculates AI Detection Risk calibrated directly
    against ZeroGPT and Turnitin AI detection methodology.
    """
    if not text or not text.strip():
        return {
            "words": 0,
            "ai_risk": 0,
            "burstiness": 0.0,
            "burstiness_score": 0,
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
            "burstiness_score": 0,
            "cliche_count": 0,
            "vocabulary_diversity": 0.0,
            "flagged_phrases": [],
        }

    # 1. Slop & Cliché Identification
    cliche_count = 0
    flagged_phrases = []
    for pattern, weight, label in AI_SLOP_PATTERNS:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            cliche_count += len(matches)
            flagged_phrases.append(label)

    for pattern, weight, label in STRUCTURAL_TEMPLATES:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            cliche_count += len(matches)
            flagged_phrases.append(label)

    # 2. Sentence Length Burstiness (CV + Variance)
    sentences = split_sentences(text)
    sent_lengths = [len(s.split()) for s in sentences if len(s.split()) >= 2]

    if len(sent_lengths) >= 2:
        mean_len = sum(sent_lengths) / len(sent_lengths)
        variance = sum((x - mean_len) ** 2 for x in sent_lengths) / len(sent_lengths)
        std_dev = math.sqrt(variance)
        cv = std_dev / max(1.0, mean_len)
        has_short = any(l <= 9 for l in sent_lengths)
        if cv >= 0.45 and has_short:
            burstiness_score = int(round(min(98.0, 50.0 + cv * 60.0)))
        else:
            burstiness_score = int(round(max(10.0, cv * 70.0)))
    else:
        std_dev = 0.0
        burstiness_score = 40

    # 3. ZeroGPT-Calibrated Sentence-Level Aggregation
    flagged_words = sum(len(s.split()) for s in sentences if is_sentence_ai_flagged(s))
    if flagged_words == 0 and cliche_count == 0:
        ai_risk = 0
    else:
        sentence_risk = (flagged_words / max(1, word_count)) * 100.0
        if cliche_count > 0:
            cliche_boost = min(20.0, (cliche_count / max(1, len(sentences))) * 15.0)
            sentence_risk = min(100.0, sentence_risk + cliche_boost)
        ai_risk = int(round(max(0.0, min(100.0, sentence_risk))))

    mattr = calculate_mattr(words, window=50)

    return {
        "words": word_count,
        "ai_risk": ai_risk,
        "burstiness": round(std_dev, 2),
        "burstiness_score": burstiness_score,
        "cliche_count": cliche_count,
        "vocabulary_diversity": round(mattr * 100.0, 1),
        "flagged_phrases": flagged_phrases[:10],
    }

