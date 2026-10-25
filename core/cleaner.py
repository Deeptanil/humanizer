"""
Turnitout Core Sanitizer
Strips hidden zero-width tracking characters, AI watermarks, and protects
academic citations, math environments, and formatting placeholders.
"""

import re

# Invisible zero-width unicode characters commonly injected for AI tracking/watermarking
ZERO_WIDTH_CHARS = [
    '\u200b',  # Zero-width space
    '\u200c',  # Zero-width non-joiner
    '\u200d',  # Zero-width joiner
    '\u2060',  # Word joiner
    '\ufeff',  # Zero-width no-break space / BOM
    '\u00ad',  # Soft hyphen
    '\u200e',  # Left-to-right mark
    '\u200f',  # Right-to-left mark
    '\u202a',  # Left-to-right embedding
    '\u202b',  # Right-to-left embedding
    '\u202c',  # Pop directional formatting
    '\u202d',  # Left-to-right override
    '\u202e',  # Right-to-left override
]

ZERO_WIDTH_REGEX = re.compile('[' + ''.join(re.escape(c) for c in ZERO_WIDTH_CHARS) + ']')

# Citation patterns: IEEE [1], [1-3], [1, 2, 5], APA (Author, 2020), (Author et al., 2021)
IEEE_CITATION_REGEX = re.compile(r'\[(?:\d+(?:[–\-]\d+)?(?:,\s*\d+(?:[–\-]\d+)?)*)\]')
APA_CITATION_REGEX = re.compile(r'\((?:[A-Z][a-zA-Z\s]+(?:,\s*(?:et\s*al\.)?)?,\s*(?:19|20)\d{2}[a-z]?(?:;\s*[A-Z][a-zA-Z\s]+(?:,\s*(?:et\s*al\.)?)?,\s*(?:19|20)\d{2}[a-z]?)*)\)')
LATEX_CITE_REGEX = re.compile(r'\\(?:cite|citep|citet|nocite)\{[^}]+\}')
LATEX_MATH_INLINE = re.compile(r'\$(?:\\\$|[^$])+\$')
LATEX_MATH_BLOCK = re.compile(r'\$\$(?:\\\$|[^$])+\$\$')

class WatermarkSanitizer:
    @staticmethod
    def inspect(text: str) -> dict:
        """Counts and detects hidden zero-width and tracking characters."""
        found = {}
        for c in ZERO_WIDTH_CHARS:
            count = text.count(c)
            if count > 0:
                name = {
                    '\u200b': "Zero-Width Space (U+200B)",
                    '\u200c': "Zero-Width Non-Joiner (U+200C)",
                    '\u200d': "Zero-Width Joiner (U+200D)",
                    '\u2060': "Word Joiner (U+2060)",
                    '\ufeff': "Byte Order Mark (U+FEFF)",
                    '\u00ad': "Soft Hyphen (U+00AD)",
                }.get(c, f"Unicode U+{ord(c):04X}")
                found[name] = count
        return {
            "total_watermarks": sum(found.values()),
            "details": found
        }

    @staticmethod
    def strip(text: str) -> str:
        """Purges all invisible zero-width unicode tracking characters."""
        if not text:
            return ""
        return ZERO_WIDTH_REGEX.sub('', text)

class TokenProtector:
    """Protects citations, LaTeX commands, and equations during text manipulation."""
    def __init__(self):
        self.placeholders = {}
        self.counter = 0

    def protect(self, text: str) -> str:
        self.placeholders.clear()
        self.counter = 0

        def _stash(match):
            token = f"\uE000PROT{self.counter}\uE001"
            self.placeholders[token] = match.group(0)
            self.counter += 1
            return token

        # Protect block math first, then inline math, then citations
        text = LATEX_MATH_BLOCK.sub(_stash, text)
        text = LATEX_MATH_INLINE.sub(_stash, text)
        text = LATEX_CITE_REGEX.sub(_stash, text)
        text = IEEE_CITATION_REGEX.sub(_stash, text)
        text = APA_CITATION_REGEX.sub(_stash, text)

        return text

    def restore(self, text: str) -> str:
        for token, original in self.placeholders.items():
            text = text.replace(token, original)
        return text

