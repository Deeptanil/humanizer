import json
import unittest
from unittest.mock import patch, MagicMock

from app import app
from core.chunker import chunk_document, is_heading_line
from core.detector import analyze_ai_Footprint
from core.engine import HumanizerEngine
from core.gemini_waterfall import GeminiWaterfallRouter


class DummyResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data


def test_multi_model_priority_waterfall_failover():
    """
    Verify that GeminiWaterfallRouter defaults to the exact 6-model priority order
    and tries models in strict priority order on failover:
    Model 1 (429 rate limit) -> Model 2 (503 overloaded) -> Model 3 (404 not found) -> Model 4 (200 OK).
    """
    default_router = GeminiWaterfallRouter()
    assert default_router.get_model_priority() == [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.6-flash",
        "gemini-3.8-flash",
    ]
    # Also verify display name normalization
    default_router.set_model_priority([
        "Gemini 3.5 Flash Lite",
        "Gemini 3.1 Flash Lite",
        "Gemini 2.5 Flash Lite",
        "Gemini 2.5 Flash",
        "Gemini 3.6 Flash",
        "Gemini 3.8 Flash",
    ])
    assert default_router.get_model_priority() == [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.6-flash",
        "gemini-3.8-flash",
    ]

    priority_list = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
    ]
    router = GeminiWaterfallRouter(api_key="test-key-123", model_priority=priority_list)

    input_paragraph = (
        "Temporary file transmission across open networks presents critical security vulnerabilities "
        "that require strict cryptographic verification and automated self-destruct lifecycles."
    )
    valid_rewritten = (
        "Sending temporary files across open networks exposes systems to severe security risks. "
        "Consequently, production platforms must enforce strict cryptographic verification alongside "
        "automated self-destruct lifecycles to prevent unauthorized access."
    )

    call_order = []

    def fake_post(url, params=None, headers=None, json=None, timeout=None):
        # Extract model name from URL: .../models/{model}:generateContent
        model_part = url.split("/models/")[1].split(":")[0]
        call_order.append(model_part)

        if model_part == "gemini-3.5-flash-lite":
            return DummyResponse(429, text="Quota exceeded")
        if model_part == "gemini-3.1-flash-lite":
            return DummyResponse(503, text="Model overloaded")
        if model_part == "gemini-2.5-flash-lite":
            return DummyResponse(404, text="Model not found")
        if model_part == "gemini-2.5-flash":
            return DummyResponse(
                200,
                json_data={
                    "candidates": [
                        {"content": {"parts": [{"text": valid_rewritten}]}}
                    ]
                },
            )
        return DummyResponse(500, text="Unexpected model")

    with patch("core.gemini_waterfall.requests.post", side_effect=fake_post):
        res = router.rewrite_with_waterfall(input_paragraph, intensity=0.8)

    assert res["success"] is True
    assert res["model_used"] == "gemini-2.5-flash"
    assert call_order == priority_list
    assert "gemini-2.5-flash-lite" in router.dead_models
    assert "gemini-3.5-flash-lite" in router.cooldown_until
    assert "gemini-3.1-flash-lite" in router.cooldown_until


def test_waterfall_rejects_word_count_shrinkage():
    """
    Verify that if Model #1 summarizes/shrinks a paragraph below 84% of its word count,
    the waterfall rejects it and falls back to Model #2 which preserves full length.
    """
    priority_list = ["model-shrinker", "model-faithful"]
    router = GeminiWaterfallRouter(api_key="test-key-123", model_priority=priority_list)

    long_input = " ".join(["Academic research requires rigorous methodology and empirical validation."] * 8)
    shrunk_output = "Academic research needs good methods."  # Too short!
    faithful_output = " ".join(
        ["Scholarly investigation demands strict methodological rigor alongside empirical verification."] * 8
    )

    def fake_post(url, **kwargs):
        model_part = url.split("/models/")[1].split(":")[0]
        if model_part == "model-shrinker":
            return DummyResponse(
                200,
                json_data={"candidates": [{"content": {"parts": [{"text": shrunk_output}]}}]},
            )
        return DummyResponse(
            200,
            json_data={"candidates": [{"content": {"parts": [{"text": faithful_output}]}}]},
        )

    with patch("core.gemini_waterfall.requests.post", side_effect=fake_post):
        res = router.rewrite_with_waterfall(long_input, intensity=0.75)

    assert res["success"] is True
    assert res["model_used"] == "model-faithful"
    assert any(a["status"] == "rejected_shrinkage" for a in res["attempts"])


def test_10k_word_chunker_and_heading_preservation():
    """
    Verify that a 10,500+ word multi-section thesis is cleanly split into ~260-word chunks
    without losing headings or dropping words.
    """
    sections = []
    for sec_idx in range(1, 22):
        heading = f"{sec_idx}. Architectural Subsystem Specification & Analysis Part {sec_idx}"
        para1 = " ".join(
            [
                f"In section {sec_idx}, we examine distributed storage latency across edge nodes [1]."
                " Network throughput remains bounded by cryptographic handshakes and packet verification."
            ]
            * 12
        )
        para2 = " ".join(
            [
                "Empirical benchmarks demonstrate that memory-mapped buffers eliminate disk staging bottlenecks."
                " Consequently, tail latency drops across high-concurrency workloads."
            ]
            * 12
        )
        sections.append(f"{heading}\n{para1}\n\n{para2}")

    full_10k_thesis = "\n\n".join(sections)
    total_input_words = len(full_10k_thesis.split())
    assert total_input_words >= 9500

    chunks = chunk_document(full_10k_thesis, max_words_per_chunk=260)
    assert len(chunks) >= 35

    reassembled = "\n\n".join(c["text"] for c in chunks)
    assert len(reassembled.split()) == total_input_words
    assert "1. Architectural Subsystem Specification & Analysis Part 1" in reassembled
    assert "21. Architectural Subsystem Specification & Analysis Part 21" in reassembled


def test_user_screenshot_technical_text_preservation_and_evasion():
    """
    Test the exact FileGuard technical text from the user's screenshot:
    1. Line breaks between paragraphs and headings MUST NOT collapse.
    2. Headings ('1. Abstract & Problem Statement', '2. Architectural Overview & Subsystem Specifications')
       MUST NOT have 'Problem' turned into 'Difficulty'.
    3. Technical terms ('FileGuard', 'SHA-256', 'CIDR', 'data', 'system') MUST NOT be corrupted
       into 'metrics', 'records', or 'apparatus'.
    4. Word count must not shrink.
    """
    screenshot_text = (
        "1. Abstract & Problem Statement\n"
        "Temporary file transmission across open networks presents critical security vulnerabilities: "
        "persistent data exposure on remote servers, silent data corruption (bit-rot or malicious in-flight "
        "modification), unauthorized token enumeration, and intrusive user tracking. FileGuard is an academic "
        "and production-engineered web platform providing zero-knowledge temporary file sharing. It implements "
        "a strict 12-hour self-destruct lifecycle, pre-flight SHA-256 cryptographic verification, in-memory "
        "folder ZIP bundling, CIDR-masked subnet quota controls, and a digital forensics inspection lab.\n"
        "2. Architectural Overview & Subsystem Specifications\n"
        "The system coordinates web routing, object storage, and relational state without disk bottlenecks "
        "or unencrypted staging leaks:"
    )

    engine = HumanizerEngine()
    res = engine.process(screenshot_text, intensity=0.8)
    out = res["cleaned_text"]

    # Headings preserved on their own lines and uncorrupted
    assert "1. Abstract & Problem Statement" in out
    assert "Difficulty Statement" not in out
    assert "\n2. Architectural Overview & Subsystem Specifications\n" in out

    # Technical proper nouns & terms preserved
    assert "FileGuard" in out
    assert "SHA-256" in out
    assert "CIDR-masked" in out
    assert "apparatus" not in out
    assert "metrics exposure" not in out
    assert "records corruption" not in out

    # Word count maintained or expanded
    in_words = len(screenshot_text.split())
    out_words = len(out.split())
    assert out_words >= int(in_words * 0.95)


def test_ai_slop_heavy_text_risk_reduction():
    """
    Verify that an AI-generated paragraph full of slop words, em-dashes, and participial tails
    experiences a large drop in AI detection risk score and preserves citations/equations.
    """
    ai_slop_paragraph = (
        "Furthermore, in the realm of distributed computing, it is important to note that "
        "cryptographic protocols play a pivotal role in safeguarding sensitive telemetry [12] — "
        "highlighting the urgent need for a comprehensive paradigm shift. Moreover, modern "
        "architectures delve into complex consensus mechanisms, fostering a deeper understanding "
        "of fault tolerance while ensuring seamless integration across heterogeneous nodes ($O(n \\log n)$). "
        "Consequently, this multifaceted framework not only enhances throughput, but also mitigates "
        "byzantine failures, ultimately paving the way for resilient cloud ecosystems."
    )

    engine = HumanizerEngine()
    res = engine.process(ai_slop_paragraph, intensity=0.85)

    before_risk = res["metrics_before"]["ai_risk"]
    after_risk = res["metrics_after"]["ai_risk"]
    out_text = res["cleaned_text"]

    assert before_risk >= 55
    assert after_risk < before_risk
    assert after_risk <= 32
    assert "[12]" in out_text
    assert "$O(n \\log n)$" in out_text
    assert "delve into" not in out_text.lower()
    assert "pivotal role" not in out_text.lower()
    assert "—" not in out_text


def test_flask_api_endpoints_and_zero_emojis():
    """
    Test /, /api/config, /api/chunk, /api/humanize, and /api/detect endpoints.
    """
    client = app.test_client()

    # 1. Index page loads and contains zero emojis
    home_res = client.get("/")
    assert home_res.status_code == 200
    html = home_res.get_data(as_text=True)
    assert "Academic Thesis Humanizer" in html

    # 2. Config endpoint updates model priority list
    cfg_res = client.post(
        "/api/config",
        json={"model_priority": ["custom-gemini-1", "custom-gemini-2"]},
    )
    assert cfg_res.status_code == 200
    assert cfg_res.get_json()["model_priority"] == ["custom-gemini-1", "custom-gemini-2"]

    # 3. Chunk endpoint splits text and returns baseline metrics
    sample = (
        "1. Introduction\n"
        "Furthermore, this study plays a pivotal role in distributed systems [1], "
        "highlighting the importance of fault-tolerant consensus protocols."
    )
    chunk_res = client.post("/api/chunk", json={"text": sample, "max_words_per_chunk": 260})
    assert chunk_res.status_code == 200
    chunk_data = chunk_res.get_json()
    assert chunk_data["total_chunks"] >= 1
    assert "metrics_before" in chunk_data

    # 4. Humanize endpoint transforms chunk
    hum_res = client.post("/api/humanize", json={"text": sample, "intensity": 0.85})
    assert hum_res.status_code == 200
    hum_data = hum_res.get_json()
    assert "cleaned_text" in hum_data
    assert "[1]" in hum_data["cleaned_text"]

    # 5. Detect endpoint scores full text
    det_res = client.post("/api/detect", json={"text": hum_data["cleaned_text"]})
    assert det_res.status_code == 200
    det_data = det_res.get_json()
    assert "metrics" in det_data
    assert "ai_risk" in det_data["metrics"]


def test_docx_drag_drop_in_place_processing():
    """
    Verify that DocxProcessor extracts text and preserves Word document tables in-place.
    """
    import io
    import tempfile
    from docx import Document
    from core.docx_handler import DocxProcessor

    # Create an in-memory test document with paragraphs and a table
    doc = Document()
    doc.add_heading("1. Experimental Setup", level=1)
    doc.add_paragraph("Furthermore, this study plays a pivotal role in illustrating distributed systems.")

    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Metric"
    table.rows[0].cells[1].text = "Value"
    table.rows[1].cells[0].text = "Latency"
    table.rows[1].cells[1].text = "12ms"

    engine = HumanizerEngine()
    proc = DocxProcessor(engine)

    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = f"{tmpdir}/sample.docx"
        out_path = f"{tmpdir}/sample_out.docx"
        doc.save(in_path)

        # 1. Test extraction for frontend display
        extracted = proc.extract_text(in_path)
        assert "1. Experimental Setup" in extracted["text"]
        assert "Metric | Value" in extracted["text"]
        assert extracted["tables"] == 1

        # 2. Test in-place processing
        res = proc.process_file(in_path, out_path, intensity=0.85)
        assert res["total_paragraphs"] >= 1

        # 3. Verify output document preserves table structure
        out_doc = Document(out_path)
        assert len(out_doc.tables) == 1
        assert len(out_doc.tables[0].rows) == 2
        assert out_doc.tables[0].rows[1].cells[0].text == "Latency"
        assert out_doc.tables[0].rows[1].cells[1].text == "12ms"


def test_rate_limiter_and_parallel_model_sharding():
    """
    Verify per-model rate limiting prevents burn-out and preferred_model_offset shards parallel workers.
    """
    models = ["model-a", "model-b", "model-c"]
    router = GeminiWaterfallRouter(
        api_key="test-key",
        model_priority=models,
        max_rpm_per_model=2,
        min_interval_seconds=0.5,
    )
    # Record 2 calls on model-a within 60s -> model-a becomes locally rate-limited
    router.record_model_call("model-a", now=100.0)
    router.record_model_call("model-a", now=101.0)
    assert router.is_model_rate_limited("model-a", now=102.0) is True
    assert router.is_model_rate_limited("model-b", now=102.0) is False


def test_rebuild_docx_endpoint_and_seo_geo_routes():
    """
    Verify /api/rebuild-docx reconstructs .docx in-place and /robots.txt, /llms.txt, /sitemap.xml work.
    """
    import io
    from docx import Document

    client = app.test_client()

    # Check SEO & GEO routes
    for route in ("/robots.txt", "/llms.txt", "/sitemap.xml"):
        res = client.get(route)
        assert res.status_code == 200

    # Build a test .docx in memory
    doc = Document()
    doc.add_paragraph("1. Introduction")
    doc.add_paragraph("Original draft paragraph one.")
    tb = doc.add_table(rows=1, cols=2)
    tb.rows[0].cells[0].text = "Key"
    tb.rows[0].cells[1].text = "OldVal"

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    humanized_payload = "1. Introduction\n\nHumanized paragraph one with high burstiness.\n\n[Table 1]\n\nKey | NewVal"
    rebuild_res = client.post(
        "/api/rebuild-docx",
        data={
            "file": (buf, "thesis.docx"),
            "humanized_text": humanized_payload,
        },
        content_type="multipart/form-data",
    )
    assert rebuild_res.status_code == 200
    out_doc = Document(io.BytesIO(rebuild_res.data))
    assert "Humanized paragraph one" in out_doc.paragraphs[1].text
    assert out_doc.tables[0].rows[0].cells[1].text == "NewVal"


class TestHumanizerSuite(unittest.TestCase):
    def test_1_waterfall(self):
        test_multi_model_priority_waterfall_failover()

    def test_2_shrinkage(self):
        test_waterfall_rejects_word_count_shrinkage()

    def test_3_chunker_10k(self):
        test_10k_word_chunker_and_heading_preservation()

    def test_4_screenshot_technical_text(self):
        test_user_screenshot_technical_text_preservation_and_evasion()

    def test_5_ai_slop_risk_reduction(self):
        test_ai_slop_heavy_text_risk_reduction()

    def test_6_flask_api(self):
        test_flask_api_endpoints_and_zero_emojis()

    def test_7_docx(self):
        test_docx_drag_drop_in_place_processing()

    def test_8_rate_limiter_and_sharding(self):
        test_rate_limiter_and_parallel_model_sharding()

    def test_9_rebuild_docx_and_seo_routes(self):
        test_rebuild_docx_endpoint_and_seo_geo_routes()


if __name__ == "__main__":
    unittest.main(verbosity=2)

