"""
Google Gemini Multi-Model Priority Waterfall Router
Executes LLM humanization across an ordered priority list of Gemini models.
If Model #1 fails (429 rate limit, 503 overload, 404 not found, timeout, or quality gate failure),
it immediately falls back to Model #2, then Model #3, and so on down the priority chain.
"""

import os
import re
import time
import requests
from typing import List, Dict, Optional, Tuple, Any

# Default ordered priority list configured per user specification:
# 1. Gemini 3.5 Flash Lite -> 2. Gemini 3.1 Flash Lite -> 3. Gemini 2.5 Flash Lite
# -> 4. Gemini 3.6 Flash -> 5. Gemini 3.8 Flash
DEFAULT_MODEL_PRIORITY: List[str] = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]


def _load_dotenv_if_present() -> None:
    """Loads key=value pairs from .env in project root if not already in os.environ."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


_load_dotenv_if_present()

# Anti-Detection Academic Thesis System Prompt
# Combines StealthHumanizer (burstiness + banned slop) + Moonlit-Pages (minimal-edit + >=100% word count)
ACADEMIC_STEALTH_SYSTEM_PROMPT = """You are an elite academic thesis editor and statistical anti-detection rewriter.
Your task is to rewrite the provided passage so it reads as authentic, natural human scholarship that passes Turnitin AI, GPTZero, and CopyLeaks as 100% human-written.

STRICT NON-NEGOTIABLE RULES:

1. ZERO WORD-COUNT SHRINKAGE (CRITICAL FOR THESES):
   - Never summarize, condense, shorten, or drop any sentence or detail.
   - Your output word count MUST be between 100% and 112% of the input word count.
   - Every single claim, technical detail, and step from the input must remain present.

2. TECHNICAL & CITATION LOCK:
   - Preserve ALL technical terms, system names, algorithms, protocols, acronyms, numbers, units, and identifiers EXACTLY (e.g., FileGuard, SHA-256, CIDR, ZIP, __PROT_0__).
   - Preserve all citations ([1], [2, 3], (Author, 2024)) and protected tokens (__PROT_X__) in their exact form.
   - Never alter section headings or merge separate paragraphs together.

3. EXTREME BURSTINESS (SENTENCE LENGTH VARIANCE):
   - AI detectors flag uniform sentence lengths (where every sentence is 18-24 words).
   - Deliberately vary sentence lengths: mix crisp, direct declarative sentences (5 to 9 words) with longer, analytical multi-clause sentences (24 to 36 words).
   - NEVER write three sentences in a row of similar length.

4. BAN ALL AI SLOP & PREDICTABLE TEMPLATES:
   - NEVER use any of these words or phrases: delve, tapestry, pivotal, paramount, underscore, multifaceted, seamless, holistic, synergy, paradigm shift, testament to, realm of, landscape of, foster, harness, plethora, myriad, cutting-edge, state-of-the-art, groundbreaking, unprecedented, transformative, overarching, meticulous, elucidate, bolster, catalyst, cornerstone, beacon, poised to, in conclusion, furthermore, moreover, additionally, it is important to note, it is worth noting, plays a crucial role, shed light on, pave the way.
   - NEVER use participial "-ing" tails tacked onto the end of sentences after a comma (e.g., ", thereby highlighting...", ", ensuring that...", ", demonstrating..."). Turn those into separate direct sentences instead.
   - NEVER use "not only X, but also Y" or "it is not just X; it is Y" constructions.
   - NEVER use em-dashes (—). Use commas, semicolons, parentheses, or separate sentences.

5. NATURAL SCHOLARLY VOICE:
   - Write in direct, concrete, active academic prose.
   - Vary how sentences open—avoid starting consecutive sentences with "The", "This", or "It".
   - Output ONLY the rewritten text. Do NOT include any intro, preamble, markdown fences, or explanations."""


class GeminiWaterfallRouter:
    """
    Routes rewrite requests through a strict priority-ordered list of Gemini models
    with automatic failover and per-model rate-limit cooldown tracking.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_priority: Optional[List[str]] = None,
        cooldown_seconds: float = 35.0,
        request_timeout: float = 25.0,
    ):
        self._explicit_api_key = api_key
        self._explicit_models = model_priority
        self.cooldown_seconds = cooldown_seconds
        self.request_timeout = request_timeout
        # Tracks model -> timestamp until which the model is cooling down after a 429/503
        self.cooldown_until: Dict[str, float] = {}
        # Tracks models that returned 404/invalid so we don't retry them endlessly
        self.dead_models: set = set()

    def get_api_keys(self) -> List[str]:
        """Returns configured Gemini API key(s) from explicit config or environment (.env / Vercel env)."""
        if self._explicit_api_key is not None:
            raw = self._explicit_api_key
        else:
            _load_dotenv_if_present()
            raw = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        return keys

    def set_api_key(self, api_key: str) -> None:
        self._explicit_api_key = api_key.strip()
        self.dead_models.clear()
        self.cooldown_until.clear()

    def get_model_priority(self) -> List[str]:
        """Returns the ordered list of models to try."""
        if self._explicit_models and len(self._explicit_models) > 0:
            return [self._normalize_model_name(m) for m in self._explicit_models if m.strip()]
        env_models = os.environ.get("GEMINI_MODELS", "").strip()
        if env_models:
            return [self._normalize_model_name(m) for m in env_models.split(",") if m.strip()]
        return list(DEFAULT_MODEL_PRIORITY)

    def set_model_priority(self, models: List[str]) -> None:
        cleaned = [self._normalize_model_name(m) for m in models if m and m.strip()]
        if cleaned:
            self._explicit_models = cleaned
            self.dead_models.clear()
            self.cooldown_until.clear()

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        name = name.strip()
        if name.startswith("models/"):
            name = name[len("models/") :]
        # Convert human-readable display names like "Gemini 3.5 Flash Lite" -> "gemini-3.5-flash-lite"
        if " " in name:
            name = re.sub(r"\s+", "-", name.lower())
        return name

    @staticmethod
    def _clean_llm_output(text: str) -> str:
        """Strips accidental LLM preambles, markdown code fences, or surrounding quotes."""
        text = text.strip()
        # Strip markdown code blocks if model wrapped output
        text = re.sub(r"^```(?:markdown|text)?\s*\n?", "", text, flags=re.I)
        text = re.sub(r"\n?```\s*$", "", text)
        # Strip common conversational preambles
        text = re.sub(
            r"^(?:Here\s+is\s+the\s+(?:rewritten|humanized|revised)\s+(?:text|passage|paragraph|version)\s*[:\-—]\s*\n*)",
            "",
            text,
            flags=re.I,
        )
        return text.strip()

    def call_single_model(
        self,
        model: str,
        api_key: str,
        user_text: str,
        system_prompt: str = ACADEMIC_STEALTH_SYSTEM_PROMPT,
        temperature: float = 1.05,
    ) -> Tuple[Optional[str], Optional[str], int]:
        """
        Calls a single Gemini model via the v1beta REST endpoint.
        Returns (output_text, error_reason, http_status).
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload: Dict[str, Any] = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Rewrite the following academic text according to all system rules. "
                                "Keep the word count >= 100% of the original, preserve all technical terms "
                                "and protected tokens (__PROT_X__), and vary sentence lengths sharply:\n\n"
                                f"{user_text}"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.92,
                "maxOutputTokens": 4096,
            },
        }

        try:
            resp = requests.post(
                url,
                params={"key": api_key},
                json=payload,
                timeout=self.request_timeout,
            )
        except requests.RequestException as exc:
            return None, f"Network/timeout error: {exc}", 0

        if resp.status_code != 200:
            err_msg = f"HTTP {resp.status_code}"
            try:
                err_json = resp.json()
                detail = err_json.get("error", {}).get("message", "")
                if detail:
                    err_msg = f"HTTP {resp.status_code}: {detail[:120]}"
            except Exception:
                pass
            return None, err_msg, resp.status_code

        try:
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return None, "Empty candidates (safety/filter block)", 200
            parts = candidates[0].get("content", {}).get("parts", [])
            output = "".join(p.get("text", "") for p in parts if "text" in p)
            cleaned = self._clean_llm_output(output)
            if not cleaned:
                return None, "Empty text in candidate", 200
            return cleaned, None, 200
        except Exception as exc:
            return None, f"Parse error: {exc}", 200

    def rewrite_with_waterfall(
        self,
        text: str,
        intensity: float = 0.65,
        extra_instructions: str = "",
    ) -> Dict[str, Any]:
        """
        Attempts to rewrite `text` by iterating through `get_model_priority()` in strict order.
        If Model 1 fails or violates word-count preservation, automatically tries Model 2, etc.
        """
        api_keys = self.get_api_keys()
        models = self.get_model_priority()
        attempts: List[Dict[str, Any]] = []

        if not api_keys:
            return {
                "success": False,
                "text": text,
                "model_used": None,
                "attempts": [{"model": "none", "status": "no_api_key", "error": "No GEMINI_API_KEY configured"}],
            }

        input_words = len(text.split())
        min_allowed_words = max(1, int(input_words * 0.84))
        temp = round(0.95 + (0.25 * intensity), 2)
        sys_prompt = ACADEMIC_STEALTH_SYSTEM_PROMPT
        if extra_instructions:
            sys_prompt += f"\n\nADDITIONAL PASS INSTRUCTION:\n{extra_instructions}"

        now = time.time()

        # Pass 1: Try active models in priority order (skipping models currently in cooldown)
        # Pass 2 (if all active models are cooling down): Try cooling-down models in priority order
        ordered_candidates: List[str] = []
        cooling_candidates: List[str] = []
        for m in models:
            if m in self.dead_models:
                continue
            if self.cooldown_until.get(m, 0.0) > now:
                cooling_candidates.append(m)
            else:
                ordered_candidates.append(m)

        full_try_order = ordered_candidates + cooling_candidates

        for model in full_try_order:
            for key_idx, api_key in enumerate(api_keys):
                out_text, err, status = self.call_single_model(
                    model=model,
                    api_key=api_key,
                    user_text=text,
                    system_prompt=sys_prompt,
                    temperature=temp,
                )

                if out_text is not None:
                    out_words = len(out_text.split())
                    if out_words < min_allowed_words and input_words >= 15:
                        attempts.append({
                            "model": model,
                            "status": "rejected_shrinkage",
                            "error": f"Output shrank too much ({out_words} vs {input_words} words)",
                        })
                        continue

                    # Clear any cooldown on success
                    self.cooldown_until.pop(model, None)
                    attempts.append({"model": model, "status": "success", "words": out_words})
                    return {
                        "success": True,
                        "text": out_text,
                        "model_used": model,
                        "attempts": attempts,
                    }

                # Handle error codes intelligently
                attempts.append({"model": model, "status": f"failed_{status}", "error": err})
                if status in (429, 503):
                    # Rate limit or overloaded -> put model on short cooldown
                    self.cooldown_until[model] = time.time() + self.cooldown_seconds
                elif status == 404:
                    # Model name does not exist on this endpoint -> mark dead for session
                    self.dead_models.add(model)
                    break

        return {
            "success": False,
            "text": text,
            "model_used": None,
            "attempts": attempts,
        }

