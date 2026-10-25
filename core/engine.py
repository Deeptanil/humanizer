"""
Turnitout Humanizer Core Engine
Zero-AI, 100% deterministic rule-based evasion engine.
Disrupts Turnitin Winnowing k-grams and AI detector statistical signatures.
"""

import os
import json
import re
import random
import math
from typing import Dict, List, Tuple, Any

from .cleaner import WatermarkSanitizer, TokenProtector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_json(filename: str):
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

PHRASES = _load_json("phrases.json")
SYNONYMS = _load_json("synonyms.json")
TRANSITIONS = _load_json("transitions.json")

class HumanizerEngine:
    def __init__(self, seed: int = None):
        if seed is not None:
            self.rng = random.Random(seed)
        else:
            self.rng = random.Random()
        self.sanitizer = WatermarkSanitizer()
        self.protector = TokenProtector()
        self.used_transitions = set()

    def set_seed(self, seed: int):
        self.rng = random.Random(seed)

    def _preserve_case(self, original: str, replacement: str) -> str:
        """Transfers capitalization pattern from original to replacement."""
        if original.isupper():
            return replacement.upper()
        if original and original[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement.lower()

    def _get_synonyms_for_word(self, word: str) -> List[str]:
        """Looks up synonyms including plural, past tense, and -ing inflections."""
        lower = word.lower()
        if lower in SYNONYMS:
            return SYNONYMS[lower]
        
        # Plural -s
        if lower.endswith('s') and len(lower) > 3:
            root = lower[:-1]
            if root in SYNONYMS:
                return [s + 's' if not s.endswith(('s', 'sh', 'ch', 'x', 'z')) else s + 'es' for s in SYNONYMS[root]]
        
        # Plural -es
        if lower.endswith('es') and len(lower) > 4:
            root = lower[:-2]
            if root in SYNONYMS:
                return [s + 'es' for s in SYNONYMS[root]]
        
        # Past tense -ed
        if lower.endswith('ed') and len(lower) > 4:
            root = lower[:-2]
            if root in SYNONYMS:
                return [s + 'ed' if not s.endswith('e') else s + 'd' for s in SYNONYMS[root]]
            root_e = lower[:-1]  # like 'created' -> 'create'
            if root_e in SYNONYMS:
                return [s + 'ed' if not s.endswith('e') else s + 'd' for s in SYNONYMS[root_e]]

        # Participle -ing
        if lower.endswith('ing') and len(lower) > 5:
            root_e = lower[:-3] + 'e'  # like 'analyzing' -> 'analyze'
            if root_e in SYNONYMS:
                return [s[:-1] + 'ing' if s.endswith('e') else s + 'ing' for s in SYNONYMS[root_e]]
            root = lower[:-3]
            if root in SYNONYMS:
                return [s[:-1] + 'ing' if s.endswith('e') else s + 'ing' for s in SYNONYMS[root]]

        return []

    def _apply_phrase_rewrites(self, text: str, intensity: float) -> Tuple[str, List[Dict[str, str]]]:
        """Replaces known AI cliché phrases and multi-word triggers."""
        changes = []
        # Higher intensity = near 100% replacement rate for cliches
        fire_rate = min(0.98, 0.75 + (0.25 * intensity))

        for item in PHRASES:
            if isinstance(item, list) and len(item) == 2:
                pattern_str, repl = item[0], item[1]
            else:
                continue

            if self.rng.random() > fire_rate:
                continue

            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            if not matches:
                continue

            for match in reversed(matches):
                orig_text = match.group(0)
                if "\uE000" in orig_text or "\uE001" in orig_text:
                    continue
                formatted_repl = self._preserve_case(orig_text, repl)
                start, end = match.span()
                text = text[:start] + formatted_repl + text[end:]
                changes.append({
                    "type": "phrase_cliche",
                    "original": orig_text,
                    "replacement": formatted_repl
                })
        return text, changes

    def _rotate_transitions(self, text: str, intensity: float) -> Tuple[str, List[Dict[str, str]]]:
        """Rotates overused transition markers to increase discourse variety."""
        changes = []
        fire_rate = min(0.95, 0.70 + (0.30 * intensity))

        for category, markers in TRANSITIONS.items():
            for marker, alternatives in markers.items():
                pattern = re.compile(r'\b' + re.escape(marker) + r'\b', re.IGNORECASE)
                matches = list(pattern.finditer(text))
                for match in reversed(matches):
                    if self.rng.random() > fire_rate:
                        continue
                    orig = match.group(0)
                    avail = [a for a in alternatives if a not in self.used_transitions]
                    if not avail:
                        avail = alternatives
                    chosen = self.rng.choice(avail)
                    self.used_transitions.add(chosen)
                    if len(self.used_transitions) > 15:
                        self.used_transitions.clear()

                    formatted = self._preserve_case(orig, chosen)
                    start, end = match.span()
                    text = text[:start] + formatted + text[end:]
                    changes.append({
                        "type": "transition_rotation",
                        "original": orig,
                        "replacement": formatted
                    })
        return text, changes

    def _apply_synonyms(self, text: str, intensity: float) -> Tuple[str, List[Dict[str, str]]]:
        """
        Disrupts Winnowing 5-word k-gram chains by substituting scholarly synonyms
        in-place without altering whitespace, punctuation or protected markers.
        """
        changes = []
        # Swap probability: subtle ~ 0.40, balanced ~ 0.65, aggressive ~ 0.85
        swap_prob = 0.35 + (intensity * 0.50)

        def _sub_word(match):
            word = match.group(0)
            syns = self._get_synonyms_for_word(word)
            if syns and self.rng.random() < swap_prob:
                chosen = self.rng.choice(syns)
                formatted = self._preserve_case(word, chosen)
                changes.append({
                    "type": "synonym_swap",
                    "original": word,
                    "replacement": formatted
                })
                return formatted
            return word

        parts = re.split(r'(\uE000[^\uE001]+\uE001)', text)
        for i in range(len(parts)):
            if not parts[i].startswith('\uE000'):
                parts[i] = re.sub(r'\b[A-Za-z]+\b', _sub_word, parts[i])

        return "".join(parts), changes

    def _tune_burstiness(self, text: str, intensity: float) -> Tuple[str, List[Dict[str, str]]]:
        """
        Adjusts sentence length variance (burstiness).
        Combines adjacent short sentences with academic subordinating conjunctions.
        """
        changes = []
        if intensity < 0.35:
            return text, changes

        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) < 2:
            return text, changes

        conjunctions = [
            ", which consequently ",
            ", thereby ",
            ", ultimately leading to ",
            ", whereas ",
            "; in doing so, it "
        ]

        fused = []
        skip_next = False

        for i in range(len(sentences)):
            if skip_next:
                skip_next = False
                continue

            current_s = sentences[i].strip()
            if i + 1 < len(sentences):
                next_s = sentences[i + 1].strip()
                if "\uE000" in current_s or "\uE000" in next_s:
                    fused.append(current_s)
                    continue

                if len(current_s) < 90 and len(next_s) < 90 and current_s.endswith('.'):
                    if self.rng.random() < (0.35 * intensity):
                        connector = self.rng.choice(conjunctions)
                        trimmed_curr = current_s[:-1]
                        lower_next = next_s[0].lower() + next_s[1:]
                        combined = f"{trimmed_curr}{connector}{lower_next}"
                        fused.append(combined)
                        changes.append({
                            "type": "sentence_fusion",
                            "original": f"{current_s} {next_s}",
                            "replacement": combined
                        })
                        skip_next = True
                        continue

            fused.append(current_s)

        return " ".join(fused), changes

    def calculate_metrics(self, text: str) -> Dict[str, Any]:
        """
        Estimates entropic perplexity, sentence burstiness, and AI detection risk score.
        """
        if not text.strip():
            return {"words": 0, "ai_risk": 0, "burstiness": 0, "cliche_count": 0, "vocabulary_diversity": 0}

        words = re.findall(r'\b[A-Za-z0-9\'-]+\b', text)
        word_count = len(words)
        if word_count == 0:
            return {"words": 0, "ai_risk": 0, "burstiness": 0, "cliche_count": 0, "vocabulary_diversity": 0}

        # 1. Cliché score
        cliche_matches = 0
        for item in PHRASES:
            if isinstance(item, list) and len(item) == 2:
                pattern_str = item[0]
                cliche_matches += len(re.findall(pattern_str, text, re.IGNORECASE))

        # 2. Burstiness (standard deviation of sentence length in words)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        sentence_lens = [len(s.split()) for s in sentences if s.split()]
        if len(sentence_lens) > 1:
            mean_len = sum(sentence_lens) / len(sentence_lens)
            variance = sum((x - mean_len) ** 2 for x in sentence_lens) / (len(sentence_lens) - 1)
            burstiness = math.sqrt(variance)
        else:
            burstiness = 0.0

        # 3. Vocabulary diversity (Type-Token Ratio)
        unique_words = len(set(w.lower() for w in words))
        ttr = unique_words / word_count if word_count > 0 else 0

        # Base risk calculation
        base_risk = 55.0
        base_risk += min(45.0, cliche_matches * 9.0)
        if burstiness < 4.0:
            base_risk += 18.0
        elif burstiness > 8.0:
            base_risk -= 18.0

        if ttr > 0.65:
            base_risk -= 15.0
        elif ttr < 0.40:
            base_risk += 12.0

        ai_risk = max(8, min(96, int(base_risk)))

        return {
            "words": word_count,
            "ai_risk": ai_risk,
            "burstiness": round(burstiness, 2),
            "cliche_count": cliche_matches,
            "vocabulary_diversity": round(ttr * 100, 1)
        }

    def process(self, raw_text: str, intensity: float = 0.6) -> Dict[str, Any]:
        """
        Runs the full 8-stage humanization pipeline.
        Intensity: 0.2 (Subtle) to 1.0 (Maximum Evasion).
        """
        if not raw_text or not raw_text.strip():
            return {
                "cleaned_text": "",
                "watermarks_found": 0,
                "changes_count": 0,
                "changes": [],
                "metrics_before": self.calculate_metrics(""),
                "metrics_after": self.calculate_metrics("")
            }

        metrics_before = self.calculate_metrics(raw_text)

        # Stage 1: Inspect and strip invisible zero-width watermarks
        inspect_result = self.sanitizer.inspect(raw_text)
        text = self.sanitizer.strip(raw_text)

        # Stage 2: Protect citations and equations
        text = self.protector.protect(text)

        # Stage 3: Normalize em-dashes and spacing
        text = text.replace("—", ", ").replace(" - ", ", ")
        text = re.sub(r'[ \t]+', ' ', text)

        all_changes = []

        # Stage 4: AI Clichés & Multi-word phrase rewrites
        text, phrase_changes = self._apply_phrase_rewrites(text, intensity)
        all_changes.extend(phrase_changes)

        # Stage 5: Rotate transition markers
        text, trans_changes = self._rotate_transitions(text, intensity)
        all_changes.extend(trans_changes)

        # Stage 6: Winnowing K-Gram Synonym Disruptor
        text, syn_changes = self._apply_synonyms(text, intensity)
        all_changes.extend(syn_changes)

        # Stage 7: Burstiness & Rhythm adjustment
        text, burst_changes = self._tune_burstiness(text, intensity)
        all_changes.extend(burst_changes)

        # Stage 8: Restore citations and LaTeX equations
        text = self.protector.restore(text)

        # Clean any awkward spacing before punctuation
        text = re.sub(r'\s+([,.:;?!])', r'\1', text)
        text = re.sub(r'\s{2,}', ' ', text)

        metrics_after = self.calculate_metrics(text)

        return {
            "cleaned_text": text.strip(),
            "watermarks_found": inspect_result["total_watermarks"],
            "watermark_details": inspect_result["details"],
            "changes_count": len(all_changes),
            "changes": all_changes,
            "metrics_before": metrics_before,
            "metrics_after": metrics_after
        }
