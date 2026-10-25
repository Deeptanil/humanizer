# Graph Report - Humanizer  (2026-10-25)

## Corpus Check
- 76 files · ~54,698 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 233 nodes · 344 edges · 15 communities (14 shown, 1 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Chunker, Detector & Postprocessor
- SVG Badges & Brand Assets
- Core Humanizer Engine & DOCX
- Flask API & Token Cleaner
- System Architecture & Evasion Docs
- Automated Unit Test Suite
- Project Governance & Studio UI
- Gemini Priority Waterfall Router
- Public Documentation & Comparisons
- Spatial Desk Interactive Scripts
- Multi-Cluster Agent Runbook
- Client-Side Cluster Load Balancer
- Vercel Serverless Routing Config
- Test HTTP Response Mocks

## God Nodes (most connected - your core abstractions)
1. `HumanizerEngine` - 25 edges
2. `GeminiWaterfallRouter` - 17 edges
3. `TiniX Documentation & Trending Badge System` - 12 edges
4. `analyze_ai_Footprint()` - 11 edges
5. `TURNITOUT Main Landing Page (Scrapbook Manifesto & Spatial Study Desk)` - 11 edges
6. `chunk_document()` - 10 edges
7. `WatermarkSanitizer` - 9 edges
8. `TokenProtector` - 8 edges
9. `deterministic_postprocess()` - 8 edges
10. `split_sentences()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `TiniX History of Achievements SVG Badges Snippet` --semantically_similar_to--> `TiniX Achievement Badges Light & Dark Preview Page`  [INFERRED] [semantically similar]
  achievements.html → badge-preview.html
- `Google Site Verification Token` --conceptually_related_to--> `Turnitout Plagiarism & AI Footprint Removal Engine`  [INFERRED]
  googled1934658a17ddea1.html → README.md
- `Turnitout Plagiarism & AI Footprint Removal Engine` --shares_data_with--> `TiniX History of Achievements SVG Badges Snippet`  [INFERRED]
  README.md → achievements.html
- `chunk_endpoint()` --calls--> `chunk_document()`  [EXTRACTED]
  app.py → core/chunker.py
- `chunk_endpoint()` --uses--> `WatermarkSanitizer`  [INFERRED]
  app.py → core/cleaner.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three-Layer Plagiarism & AI Footprint Evasion Architecture** — readme_15_stage_pipeline, similarity_evasion_analysis_three_layer_vector, similarity_evasion_analysis_winnowing_lsh, architecture_rules_asset_decoupling [EXTRACTED 1.00]
- **Local Flask Academic Thesis Humanizer Studio Stack** — user_guide_thesis_humanizer, web_templates_index_thesis_studio_ui, web_static_favicon_icon, requirements_python_dependencies [INFERRED 0.85]
- **Turnitout Brand Logos, Favicons, and UI Showcase Assets** — docs_assets_logo_image, docs_assets_logo_banner_image, docs_assets_favicon_icon, docs_favicon_icon, docs_assets_turnitout_ui_screenshot [INFERRED 0.85]
- **TiniX Light and Dark Theme Documentation Badges** — docs_assets_badges_tinix_badge_badge, docs_assets_badges_tinix_badge_dark_badge, docs_assets_badges_tinix_ai_remover_badge, docs_assets_badges_tinix_plagerism_remover_badge, docs_assets_badges_tinix_turnitin_bypass_badge, docs_assets_badges_tinix_latex_badge, docs_assets_badges_tinix_academic_writing_badge [INFERRED 0.85]

## Communities (15 total, 1 thin omitted)

### Community 0 - "Chunker, Detector & Postprocessor"
Cohesion: 0.10
Nodes (30): chunk_document(), is_heading_line(), Any, Smart Academic Document Chunker (10,000+ Word Thesis Support) Splits…, Determines whether a line is a section/chapter heading that must remain…, If a single paragraph exceeds `max_words`, splits it cleanly on sentence…, Splits a full thesis or long document into ordered chunks. Each chunk contains…, split_oversized_paragraph() (+22 more)

### Community 1 - "SVG Badges & Brand Assets"
Cohesion: 0.07
Nodes (29): TiniX Academic Writing Light Badge, TiniX Academic Writing Dark Badge, TiniX AI Remover Light Badge, TiniX AI Remover Dark Badge, TiniX Trending #1 Repo of the Week Light Badge, TiniX Trending #1 Repo of the Week Dark Badge, TiniX Documentation & Trending Badge System, TiniX LaTeX Light Badge (+21 more)

### Community 2 - "Core Humanizer Engine & DOCX"
Cohesion: 0.13
Nodes (10): main(), Turnitout CLI Interface Processes .docx or .txt / .md files directly from…, DocxProcessor, Any, Turnitout DOCX In-Place Processor Preserves Word styles, runs, formatting,…, Processes a .docx file in-place, rewriting text while preserving document…, HumanizerEngine, Any (+2 more)

### Community 3 - "Flask API & Token Cleaner"
Cohesion: 0.13
Nodes (15): chunk_endpoint(), config_endpoint(), detect_endpoint(), humanize(), index(), inspect_watermark(), Turnitout Web Application (v3.0 — 3-Layer Hybrid + Multi-Model Priority…, upload_docx() (+7 more)

### Community 4 - "System Architecture & Evasion Docs"
Cohesion: 0.13
Nodes (20): Decoupled Citation Engine (turnitout.core.citation_engine), Multi-File Stream Processor & ZIP Bundling (turnitout.core.doc_processor), System Architecture: Turnitout Core (v1.6.0), Hierarchical Rules & Taxonomy Loader (turnitout.core.rules), Text Modifier & Transformer Pipeline (turnitout.core.modifier), Turnitout Markdown Changelog (v1.0.0-beta to v1.6.0), ZipPy Compression Perplexity Engine (zlib/lzma), Getting Started Guide: Turnitout Core & Cluster Mirrors (+12 more)

### Community 5 - "Automated Unit Test Suite"
Cohesion: 0.11
Nodes (13): Verify that a 10,500+ word multi-section thesis is cleanly split into ~260-word…, Test the exact FileGuard technical text from the user's screenshot: 1. Line…, Verify that an AI-generated paragraph full of slop words, em-dashes, and…, Verify that GeminiWaterfallRouter tries models in strict priority order: Model…, Test /, /api/config, /api/chunk, /api/humanize, and /api/detect endpoints., Verify that if Model #1 summarizes/shrinks a paragraph below 84% of its word…, test_10k_word_chunker_and_heading_preservation(), test_ai_slop_heavy_text_risk_reduction() (+5 more)

### Community 6 - "Project Governance & Studio UI"
Cohesion: 0.12
Nodes (17): TiniX History of Achievements SVG Badges Snippet, Hierarchical Academic Discipline Taxonomy (rules/academic/taxonomy/), Asset Decoupling of Linguistic & Topic Dictionaries, UI & Citation Engine Decoupling, TiniX Achievement Badges Light & Dark Preview Page, Google Site Verification Token, Privacy Policy: In-Memory Zero Permanent Storage, 15-Stage Deterministic Transformation Pipeline & ZipPy Perplexity (+9 more)

### Community 7 - "Gemini Priority Waterfall Router"
Cohesion: 0.16
Nodes (8): GeminiWaterfallRouter, Any, Strips accidental LLM preambles, markdown code fences, or surrounding quotes., Calls a single Gemini model via the v1beta REST endpoint. Returns (output_text,…, Attempts to rewrite `text` by iterating through `get_model_priority()` in…, Routes rewrite requests through a strict priority-ordered list of Gemini models…, Returns configured Gemini API key(s) from explicit config or environment., Returns the ordered list of models to try.

### Community 8 - "Public Documentation & Comparisons"
Cohesion: 0.18
Nodes (16): TiniX History of Achievements Section, v2.0.0 Master 38-Pattern AI Tell Scrubber & Invariant Gates, Empirical Voice Matching Engine (Beta), Turnitout Changelog & Release Notes HTML (v2.0.0), Turnitout vs QuillBot Comparison Page, Turnitout vs StealthGPT & Undetectable AI Comparison Page, Turnitout Frequently Asked Questions & Student Knowledge Base, Google Search Console Site Verification Token (googled1934658a17ddea1) (+8 more)

### Community 9 - "Spatial Desk Interactive Scripts"
Cohesion: 0.24
Nodes (9): getRandomClusterNode(), initSpatialDeskCanvas(), smoothPanTo(), updateCameraTransform(), isExplicitMirrorLink(), randomizeAllClusterLinks(), showDeskMode(), toggleGlobalTheme() (+1 more)

### Community 10 - "Multi-Cluster Agent Runbook"
Cohesion: 0.50
Nodes (4): Single Source of Truth Config (configs/global_config.json), Strict Lazy Model Loading & File Watcher Invariant, Turnitout-Core Engine & 8-Node Cluster Architecture, Universal Push Protocol (sync_cluster.sh)

### Community 11 - "Client-Side Cluster Load Balancer"
Cohesion: 0.83
Nodes (3): getRandomClusterNode(), isExplicitMirrorLink(), randomizeAllClusterLinks()

### Community 12 - "Vercel Serverless Routing Config"
Cohesion: 0.50
Nodes (3): builds, routes, version

## Knowledge Gaps
- **34 isolated node(s):** `version`, `builds`, `routes`, `Single Source of Truth Config (configs/global_config.json)`, `Privacy Policy: In-Memory Zero Permanent Storage` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HumanizerEngine` connect `Core Humanizer Engine & DOCX` to `Chunker, Detector & Postprocessor`, `Flask API & Token Cleaner`, `Automated Unit Test Suite`, `Gemini Priority Waterfall Router`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `GeminiWaterfallRouter` connect `Gemini Priority Waterfall Router` to `Chunker, Detector & Postprocessor`, `Core Humanizer Engine & DOCX`, `Flask API & Token Cleaner`, `Automated Unit Test Suite`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `analyze_ai_Footprint()` connect `Chunker, Detector & Postprocessor` to `Core Humanizer Engine & DOCX`, `Flask API & Token Cleaner`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `HumanizerEngine` (e.g. with `DocxProcessor` and `TokenProtector`) actually correct?**
  _`HumanizerEngine` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `TiniX Documentation & Trending Badge System` (e.g. with `TiniX Academic Writing Light Badge` and `TiniX AI Remover Light Badge`) actually correct?**
  _`TiniX Documentation & Trending Badge System` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `version`, `builds`, `routes` to the rest of the system?**
  _34 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Chunker, Detector & Postprocessor` be split into smaller, more focused modules?**
  _Cohesion score 0.0960960960960961 - nodes in this community are weakly interconnected._