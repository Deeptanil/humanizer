"""
Turnitout Hybrid 3-Layer Humanizer Engine (v3.0)
Combines:
- Layer 1: Google Gemini Multi-Model Priority Waterfall (structural sentence rewriting)
- Layer 2: StealthHumanizer + Moonlit-Pages Deterministic Post-Processor (collocations, em-dashes, burstiness)
- Layer 3: Multi-Metric Statistical AI Detector + Adversarial Retry Loop
- Smart Chunker: Supports 10,000+ word theses without context shrinkage or timeout
"""

import os
import json
import re
import random
from typing import Dict, List, Tuple, Any, Optional

from .cleaner import WatermarkSanitizer, TokenProtector
from .detector import analyze_ai_Footprint
from .postprocess import deterministic_postprocess
from .chunker import chunk_document, is_heading_line
from .gemini_waterfall import GeminiWaterfallRouter

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

# Protected technical & domain words that should never be blindly swapped by dictionary fallback
PROTECTED_WORDS = {
    "data", "system", "systems", "model", "models", "method", "methods",
    "problem", "problems", "study", "paper", "code", "file", "files",
    "network", "networks", "server", "servers", "token", "tokens",
    "user", "users", "state", "memory", "disk", "web", "lab", "key",
    "keys", "hash", "table", "tables", "figure", "figures", "section",
    "chapter", "abstract", "index", "value", "values", "time", "type",
}


class HumanizerEngine:
    def __init__(
        self,
        seed: Optional[int] = None,
        api_key: Optional[str] = None,
        model_priority: Optional[List[str]] = None,
    ):
        self.rng = random.Random(seed) if seed is not None else random.Random()
        self.sanitizer = WatermarkSanitizer()
        self.protector = TokenProtector()
        self.waterfall = GeminiWaterfallRouter(api_key=api_key, model_priority=model_priority)
        self.used_transitions = set()

    def set_seed(self, seed: int) -> None:
        self.rng = random.Random(seed)

    def set_api_key(self, api_key: str) -> None:
        self.waterfall.set_api_key(api_key)

    def set_model_priority(self, models: List[str]) -> None:
        self.waterfall.set_model_priority(models)

    def _preserve_case(self, original: str, replacement: str) -> str:
        if original.isupper():
            return replacement.upper()
        if original and original[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement.lower()

    def _get_synonyms_for_word(self, word: str) -> List[str]:
        lower = word.lower()
        if lower in PROTECTED_WORDS or len(lower) <= 3:
            return []
        if lower in SYNONYMS:
            return SYNONYMS[lower]

        if lower.endswith("s") and len(lower) > 4:
            root = lower[:-1]
            if root not in PROTECTED_WORDS and root in SYNONYMS:
                return [s + "s" if not s.endswith(("s", "sh", "ch", "x", "z")) else s + "es" for s in SYNONYMS[root]]

        if lower.endswith("ed") and len(lower) > 5:
            root = lower[:-2]
            if root not in PROTECTED_WORDS and root in SYNONYMS:
                return [s + "ed" if not s.endswith("e") else s + "d" for s in SYNONYMS[root]]
            root_e = lower[:-1]
            if root_e not in PROTECTED_WORDS and root_e in SYNONYMS:
                return [s + "ed" if not s.endswith("e") else s + "d" for s in SYNONYMS[root_e]]

        if lower.endswith("ing") and len(lower) > 6:
            root_e = lower[:-3] + "e"
            if root_e not in PROTECTED_WORDS and root_e in SYNONYMS:
                return [s[:-1] + "ing" if s.endswith("e") else s + "ing" for s in SYNONYMS[root_e]]
            root = lower[:-3]
            if root not in PROTECTED_WORDS and root in SYNONYMS:
                return [s[:-1] + "ing" if s.endswith("e") else s + "ing" for s in SYNONYMS[root]]

        return []

    def _apply_phrase_rewrites(self, text: str, intensity: float) -> Tuple[str, List[Dict[str, str]]]:
        changes = []
        fire_rate = min(0.98, 0.78 + (0.22 * intensity))

        for item in PHRASES:
            if not (isinstance(item, list) and len(item) == 2):
                continue
            pattern_str, repl = item[0], item[1]
            if self.rng.random() > fire_rate:
                continue

            pattern = re.compile(pattern_str, re.IGNORECASE)
            matches = list(pattern.finditer(text))
            for match in reversed(matches):
                orig_text = match.group(0)
                if "__PROT_" in orig_text:
                    continue
                chosen_repl = self.rng.choice(repl) if isinstance(repl, list) else repl
                formatted_repl = self._preserve_case(orig_text, chosen_repl)
                start, end = match.span()
                text = text[:start] + formatted_repl + text[end:]
                changes.append({
                    "type": "phrase_cliche",
                    "original": orig_text,
                    "replacement": formatted_repl,
                })
        return text, changes

    def _rotate_transitions(self, text: str, intensity: float) -> Tuple[str, List[Dict[str, str]]]:
        changes = []
        fire_rate = min(0.95, 0.70 + (0.30 * intensity))

        for _, markers in TRANSITIONS.items():
            for marker, alternatives in markers.items():
                pattern = re.compile(r"\b" + re.escape(marker) + r"\b", re.IGNORECASE)
                matches = list(pattern.finditer(text))
                for match in reversed(matches):
                    if self.rng.random() > fire_rate:
                        continue
                    orig = match.group(0)
                    avail = [a for a in alternatives if a not in self.used_transitions] or alternatives
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
                        "replacement": formatted,
                    })
        return text, changes

    def _apply_synonyms(self, text: str, intensity: float, llm_was_used: bool = False) -> Tuple[str, List[Dict[str, str]]]:
        changes = []
        # When Gemini LLM already rewrote the structure, only apply light synonym polishing (12-20%)
        # When running in offline fallback mode, apply stronger synonym disruption (35-65%)
        swap_prob = (0.08 + intensity * 0.14) if llm_was_used else (0.32 + intensity * 0.38)

        def _sub_word(match):
            word = match.group(0)
            # Never touch capitalized mid-sentence proper nouns or acronyms (e.g. FileGuard, CIDR)
            start_pos = match.start()
            if start_pos > 0 and word[0].isupper():
                prev_slice = text[max(0, start_pos - 3) : start_pos]
                if not re.search(r"[.!?]\s*$", prev_slice):
                    return word

            syns = self._get_synonyms_for_word(word)
            if syns and self.rng.random() < swap_prob:
                chosen = self.rng.choice(syns)
                formatted = self._preserve_case(word, chosen)
                changes.append({
                    "type": "synonym_swap",
                    "original": word,
                    "replacement": formatted,
                })
                return formatted
            return word

        parts = re.split(r"(__PROT_\d+__)", text)
        for i in range(len(parts)):
            if not parts[i].startswith("__PROT_"):
                parts[i] = re.sub(r"\b[A-Za-z]+\b", _sub_word, parts[i])

        return "".join(parts), changes

    def calculate_metrics(self, text: str) -> Dict[str, Any]:
        return analyze_ai_Footprint(text)

    def _process_single_paragraph(
        self,
        paragraph: str,
        intensity: float,
        preferred_model_offset: int = 0,
    ) -> Tuple[str, List[Dict[str, str]], Optional[str], List[Dict[str, Any]]]:
        """
        Processes a prose block through Layer 1 (Gemini Waterfall),
        Layer 2 (Deterministic Post-Processor), and Layer 3 (Adversarial Self-Check).
        """
        all_changes: List[Dict[str, str]] = []
        model_used: Optional[str] = None
        attempts_log: List[Dict[str, Any]] = []

        block = paragraph

        # Layer 1: Gemini Multi-Model Priority Waterfall (if API key is configured)
        if self.waterfall.get_api_keys():
            wf_res = self.waterfall.rewrite_with_waterfall(
                block,
                intensity=intensity,
                preferred_model_offset=preferred_model_offset,
            )
            attempts_log.extend(wf_res.get("attempts", []))
            if wf_res.get("success") and wf_res.get("text"):
                block = wf_res["text"]
                model_used = wf_res.get("model_used")
                all_changes.append({
                    "type": "llm_structural_rewrite",
                    "original": f"Chunk ({len(paragraph.split())}w)",
                    "replacement": f"Rewritten via {model_used} ({len(block.split())}w)",
                })

        # Layer 2: Deterministic Post-Processor (StealthHumanizer + Moonlit-Pages)
        block, det_changes = deterministic_postprocess(block, intensity=intensity, rng=self.rng)
        all_changes.extend(det_changes)

        block, phrase_changes = self._apply_phrase_rewrites(block, intensity)
        all_changes.extend(phrase_changes)

        block, trans_changes = self._rotate_transitions(block, intensity)
        all_changes.extend(trans_changes)

        # Only apply dictionary synonym swaps in offline fallback mode;
        # when Gemini rewrote the text, random thesaurus swaps introduce stiff words that detectors flag.
        if model_used is None:
            block, syn_changes = self._apply_synonyms(block, intensity, llm_was_used=False)
            all_changes.extend(syn_changes)

        # Layer 3: Adversarial Self-Check Loop
        # If Gemini is active and the chunk's AI risk is still > 18%, run a targeted 2nd pass
        if model_used is not None:
            post_metrics = self.calculate_metrics(block)
            if post_metrics["ai_risk"] > 18 and len(block.split()) >= 25:
                flagged = ", ".join(post_metrics.get("flagged_phrases", [])) or "uniform sentence cadence"
                extra = (
                    f"The previous draft still scored {post_metrics['ai_risk']}% AI risk due to: {flagged}. "
                    "Rewrite using natural human flow: connect ideas with 'because', 'while', 'since', or 'when', "
                    "use plain everyday verbs (use, run, build, check, keep, show), avoid choppy 7-word staccato "
                    "sentence lists, and keep 100% of the technical facts, __HEADING_X__ and __PROT_X__ tokens, and word count."
                )
                wf_retry = self.waterfall.rewrite_with_waterfall(
                    block,
                    intensity=min(0.95, intensity + 0.12),
                    extra_instructions=extra,
                    preferred_model_offset=preferred_model_offset + 1,
                )
                attempts_log.extend(wf_retry.get("attempts", []))
                if wf_retry.get("success") and wf_retry.get("text"):
                    candidate, cand_changes = deterministic_postprocess(wf_retry["text"], intensity=intensity, rng=self.rng)
                    cand, p_ch = self._apply_phrase_rewrites(candidate, intensity)
                    cand, t_ch = self._rotate_transitions(cand, intensity)
                    cand_metrics = self.calculate_metrics(cand)
                    if cand_metrics["ai_risk"] <= post_metrics["ai_risk"]:
                        block = cand
                        model_used = wf_retry.get("model_used") or model_used
                        all_changes.extend(cand_changes + p_ch + t_ch)
                        all_changes.append({
                            "type": "adversarial_pass_2",
                            "original": f"Risk {post_metrics['ai_risk']}%",
                            "replacement": f"Risk {cand_metrics['ai_risk']}% ({model_used})",
                        })

        return block, all_changes, model_used, attempts_log

    def process(
        self,
        raw_text: str,
        intensity: float = 0.65,
        preferred_model_offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Runs the full 3-layer humanization pipeline across a chunk or document.
        Batches consecutive paragraphs between headings so each chunk uses a single LLM call
        while preserving 100% of line breaks, headings, citations, and technical terms.
        """
        if not raw_text or not raw_text.strip():
            empty_m = self.calculate_metrics("")
            return {
                "cleaned_text": "",
                "watermarks_found": 0,
                "watermark_details": {},
                "changes_count": 0,
                "changes": [],
                "model_used": None,
                "waterfall_attempts": [],
                "metrics_before": empty_m,
                "metrics_after": empty_m,
            }

        metrics_before = self.calculate_metrics(raw_text)

        # Stage 1: Strip invisible zero-width watermarks
        inspect_result = self.sanitizer.inspect(raw_text)
        text = self.sanitizer.strip(raw_text)

        # Stage 2: Protect citations and equations
        text = self.protector.protect(text)

        all_changes: List[Dict[str, str]] = []
        models_used: List[str] = []
        waterfall_attempts: List[Dict[str, Any]] = []

        # Batch consecutive prose lines between headings so each section in a chunk uses
        # a single LLM call while headings stay 100% locked outside the LLM on their exact lines.
        out_lines: List[str] = []
        prose_buffer: List[str] = []

        def _flush_prose_buffer():
            if not prose_buffer:
                return
            combined_prose = "\n".join(prose_buffer)
            rewritten_prose, ch, m_used, att = self._process_single_paragraph(
                combined_prose,
                intensity,
                preferred_model_offset=preferred_model_offset,
            )
            all_changes.extend(ch)
            if m_used:
                models_used.append(m_used)
            waterfall_attempts.extend(att)
            out_lines.append(rewritten_prose.strip())
            prose_buffer.clear()

        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                _flush_prose_buffer()
                out_lines.append("")
            elif is_heading_line(stripped):
                _flush_prose_buffer()
                out_lines.append(line.rstrip())
            else:
                prose_buffer.append(stripped)

        _flush_prose_buffer()
        final_text = "\n".join(out_lines)

        # Restore protected citations and math equations
        final_text = self.protector.restore(final_text)

        metrics_after = self.calculate_metrics(final_text)
        primary_model = models_used[0] if models_used else "deterministic-fallback"

        return {
            "cleaned_text": final_text.strip(),
            "watermarks_found": inspect_result["total_watermarks"],
            "watermark_details": inspect_result["details"],
            "changes_count": len(all_changes),
            "changes": all_changes,
            "model_used": primary_model,
            "waterfall_attempts": waterfall_attempts,
            "metrics_before": metrics_before,
            "metrics_after": metrics_after,
        }
