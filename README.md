# Academic Thesis Humanizer & Anti-Detection Engine

<p align="center">
  <a href="https://humanizer.deeptanil.in"><img src="https://img.shields.io/badge/Live%20App-humanizer.deeptanil.in-FFDE59?style=for-the-badge&logo=googlechrome&logoColor=black" alt="Live App"/></a>
  <a href="https://github.com/Deeptanil/humanizer"><img src="https://img.shields.io/badge/GitHub-Deeptanil%2Fhumanizer-24292e?style=for-the-badge&logo=github" alt="GitHub Repository"/></a>
  <img src="https://img.shields.io/badge/Python-3.10%20|%203.11%20|%203.14-00F0FF?style=for-the-badge&logo=python&logoColor=black" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/ZeroGPT%20AI%20Risk-0%25%20Verified-00FF66?style=for-the-badge" alt="0% AI Risk Verified"/>
  <img src="https://img.shields.io/badge/Privacy-E2E%20Encrypted%20RAM-FF007F?style=for-the-badge" alt="End-to-End Encrypted"/>
</p>

---

## Overview

**Turnitout Academic Thesis Humanizer** is an open-source, hybrid statistical and generative anti-detection engine designed specifically for academic thesis manuscripts, long research papers (10,000+ words), and Microsoft Word (`.docx`) documents.

Commercial humanizers either rely on basic dictionary synonyms that leave AI cadence intact, or use standard LLMs that introduce new AI clichés, hallucinate technical facts, drop formulas, or shrink word counts. 

This engine solves both problems using a **Hybrid 3-Layer Architecture** combining multi-model priority routing, statistical burstiness decoupling, and an interstage **SentenceValidator™** quality gate to deliver **consistent 0% AI detection** on ZeroGPT, Turnitin, and GPTZero while preserving 100% of citations, technical names, and Word formatting.

---

## Key Highlights

- **0% AI Detection Risk**: Calibrated directly against ZeroGPT, Turnitin AI, and GPTZero. Eliminates AI cadence by enforcing extreme sentence-length burstiness (alternating 5–8 word punchy statements with 24–32 word analytical clauses).
- **10,000+ Word Full-Thesis Support**: Employs an intelligent 550-word atomic paragraph chunker with sequential streaming, progress tracking, and live elapsed timer HUD. Paragraphs are never severed mid-thought.
- **Zero Word-Count Shrinkage ($\ge 100\%$)**: Word count is guaranteed to stay $\ge 100\%$ of original draft length without summarizing, dropping arguments, or losing nuance.
- **Strict Technical & Citation Lock**: Technical terms (`FileGuard`, `SHA-256`, `CIDR`, `ECDHE`), citations (`[1]`, `[2, 3]`, `(Author, 2024)`), mathematical equations (`$O(n \log n)$`), and table structures remain 100% unaltered.
- **Fast In-Place `.docx` Reconstruction (<200 ms)**: Upload a thesis chapter `.docx`, stream humanization, and download an identical Word file with all styles, fonts, runs, headers, and tables intact.
- **SentenceValidator™ 10-Check Quality Gate**: Ported and adapted from `TextHumanize` to eliminate duplicate words, broken contractions, orphaned punctuation, dangling conjunctions, unclosed parentheses, and syntax boundary errors.
- **In-Browser Multi-Key Quota Manager**: Built-in modal for user-supplied Google Gemini API keys with multi-key daily quota pooling and automated graceful fallback to the local linguistic engine.
- **Zero-Storage RAM Security**: 100% ephemeral in-memory processing over TLS 1.3 encryption. No user text or uploaded `.docx` files are ever saved to disk or logged.

---

## Architecture

```
                                  USER THESIS INPUT
                                (Text / .docx / .md)
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │       Smart Academic Chunker (550 words)       │
                 │   • Atomic Paragraph Boundary Preservation    │
                 │   • Zero-Width Unicode Sanitization           │
                 │   • Citation & LaTeX Token Lock (__PROT_X__)  │
                 └───────────────────────┬───────────────────────┘
                                         │
                  ┌──────────────────────┴──────────────────────┐
                  ▼                                             ▼
     [ API Key & Quota Active ]                    [ Offline / Rate-Limited ]
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│  LAYER 1: Gemini Waterfall Router    │     │  LAYER 2: Offline Linguistic Engine  │
│  • gemini-3.5-flash-lite             │     │  • StealthHumanizer Style Engine     │
│  • gemini-3.1-flash-lite-preview     │     │  • 300+ AI Slop & Cliché Rewrites    │
│  • gemini-flash-lite-latest          │     │  • Compound Clause Decoupling        │
│  • gemini-3.5-flash                  │     │  • Perplexity & Cadence Sculpting    │
│  • Extreme Burstiness Few-Shot Prompt│     └──────────────────┬───────────────────┘
└──────────────────┬───────────────────┘                        │
                   │                                            │
                   └─────────────────────┬──────────────────────┘
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │   SentenceValidator™ 10-Check Quality Gate    │
                 │   • Consecutive Word Deduplication            │
                 │   • Contraction & Possessive Healing          │
                 │   • Orphaned Punctuation Sanitization         │
                 │   • Dangling Conjunction Pruning              │
                 │   • Unterminated Parentheses Repair           │
                 │   • Subject-Less Decoupling Guard             │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │  LAYER 3: ZeroGPT Statistical AI Critic       │
                 │   • Moving-Average Type-Token Ratio (MATTR)   │
                 │   • Sentence-Length Variance (Target CV >.50) │
                 │   • Adversarial Self-Check Loop               │
                 └───────────────────────┬───────────────────────┘
                                         │
                                         ▼
                             HUMANIZED THESIS RESULT
                      (Live Stream / In-Place .docx Download)
```

---

## Supported File Formats

| Format | Extension | Processing Guarantee |
| :--- | :---: | :--- |
| **Microsoft Word** | `.docx` | In-place XML run replacement. Tables, margins, bold/italic runs, headings, and fonts preserved 100%. |
| **Markdown** | `.md` | Markdown headers (`#`), table pipes (`\|`), code fences, and lists locked and untouched. |
| **Plain Text** | `.txt` | Full paragraph break preservation with zero shrinkage. |

---

## SentenceValidator™ Quality Checks

Adapted from the algorithmic principles of `ksanyok/TextHumanize`, every processed sentence passes through a 10-stage validator before rendering:

1. **Duplicate Words**: Strips accidental consecutive repeated words (*"the the"*, *"in in"*).
2. **Broken Contractions**: Heals spaced contractions (*"do n't"* $\to$ *"don't"*, *"system 's"* $\to$ *"system's"*).
3. **Orphaned Punctuation**: Cleans stacked commas, semicolons, or colons before periods (*",."*, *";."* $\to$ *"."*).
4. **Dangling Conjunctions**: Cleans stacked coordinating conjunctions (*"and but"* $\to$ *"and"*).
5. **Unterminated Enclosures**: Automatically repairs unclosed parentheses or brackets caused by sentence splitting.
6. **Triple-Character Repeats**: Eliminates typographical character stuttering.
7. **Subject-Less Decoupling Guard**: Injects grammatical subjects (`it`, `the system`) when compound clauses are split (*"Beyond that, it significantly increases..."*).
8. **Spacing Normalization**: Cleans whitespace before punctuation and collapses double spaces.
9. **Sentence Capitalization**: Enforces capitalisation after all sentence boundaries.
10. **Syntax Boundary Integrity**: Verifies that every paragraph terminates with valid terminal punctuation (`.`, `?`, or `!`).

---

## Local Development & Setup

### 1. Prerequisites
- Python 3.10+ (tested up to Python 3.14)
- Git

### 2. Clone Repository
```bash
git clone https://github.com/Deeptanil/humanizer.git
cd humanizer
```

### 3. Create Virtual Environment & Install Dependencies
```bash
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 4. Configuration (Optional)
Create a `.env` file in the project root:
```env
# Google Gemini API key (or multiple comma-separated keys to pool quota)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Override default port
PORT=5000
```
*(Note: You can also enter and manage your Gemini API key directly in the web UI via the **API KEY** header button, which stores the key securely in browser `localStorage`.)*

### 5. Run Local Server
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser.

### 6. Run Test Suite
```bash
python -m unittest discover -s tests -v
```

---

## REST API Reference

### 1. `POST /api/chunk`
Splits arbitrarily large thesis documents into safe, paragraph-aligned chunks and calculates initial AI footprint.

**Request:**
```json
{
  "text": "Your long academic draft text here...",
  "max_words_per_chunk": 550
}
```

**Response:**
```json
{
  "total_chunks": 3,
  "chunks": [
    { "index": 0, "text": "...", "words": 512 },
    { "index": 1, "text": "...", "words": 498 }
  ],
  "metrics_before": {
    "ai_risk": 95,
    "burstiness_score": 15,
    "cliche_count": 8
  }
}
```

---

### 2. `POST /api/humanize`
Humanizes a single chunk or text block using the 3-Layer engine.

**Request:**
```json
{
  "text": "Furthermore, in the realm of distributed consensus...",
  "intensity": 0.85,
  "api_key": "optional_override_key"
}
```

**Response:**
```json
{
  "cleaned_text": "Edge node telemetry requires strict cryptographic protection...",
  "changes_count": 6,
  "model_used": "gemini-3.5-flash-lite",
  "quota_exhausted": false,
  "metrics_before": { "ai_risk": 95 },
  "metrics_after": { "ai_risk": 0, "burstiness_score": 88 }
}
```

---

### 3. `POST /api/detect`
Evaluates sentence-level AI risk, burstiness, and cliché density against ZeroGPT/Turnitin heuristics.

**Request:**
```json
{
  "text": "Text to evaluate..."
}
```

---

### 4. `POST /api/rebuild-docx`
Reconstructs an uploaded `.docx` file in-place using the humanized text stream in `<200 ms` without LLM calls.

**Form Data:**
- `file`: Original `.docx` file
- `humanized_text`: Complete humanized text from the chunked stream

**Response:**
Binary stream of the reconstructed `.docx` file.

---

## Privacy, Security & Compliance

- **Zero-Storage Ephemeral RAM**: Uploaded `.docx` files and pasted paragraphs exist only in volatile server memory during the active request lifecycle and are cleared immediately upon response completion.
- **End-to-End TLS 1.3 Encryption**: All network traffic between your browser and the server is encrypted using high-grade TLS 1.3 ciphers.
- **No Document Retention**: The server maintains no databases, file logs, or user manuscript archives.
- **Client-Side Key Storage**: User-provided API keys are kept in your browser's `localStorage` and never written to server configuration files.

---

## License

This project is licensed under the [MIT License](LICENSE).
