"""
Turnitout Web Application (v3.0 — 3-Layer Hybrid + Multi-Model Priority Waterfall)
Supports 10,000+ word full-document humanization via smart paragraph chunking
and priority-ordered Google Gemini model failover.
"""

import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from core.engine import HumanizerEngine
from core.docx_handler import DocxProcessor
from core.cleaner import WatermarkSanitizer
from core.chunker import chunk_document
from core.detector import analyze_ai_Footprint

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "web", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB max upload

engine = HumanizerEngine()
docx_proc = DocxProcessor(engine)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET", "POST"])
def config_endpoint():
    if request.method == "POST":
        data = request.get_json() or {}
        if "api_key" in data and data["api_key"]:
            engine.set_api_key(str(data["api_key"]))
        raw_models = data.get("models") or data.get("model_priority")
        if isinstance(raw_models, list):
            engine.set_model_priority([str(m) for m in raw_models if str(m).strip()])

    current_models = engine.waterfall.get_model_priority()
    return jsonify({
        "has_api_key": len(engine.waterfall.get_api_keys()) > 0,
        "models": current_models,
        "model_priority": current_models,
        "dead_models": list(engine.waterfall.dead_models),
    })


@app.route("/api/chunk", methods=["POST"])
def chunk_endpoint():
    data = request.get_json() or {}
    text = data.get("text", "")
    max_words = int(data.get("max_words_per_chunk") or data.get("max_words") or 260)
    chunks = chunk_document(text, max_words_per_chunk=max_words)
    metrics_before = analyze_ai_Footprint(text)
    watermarks = WatermarkSanitizer.inspect(text)
    return jsonify({
        "total_chunks": len(chunks),
        "chunks": chunks,
        "metrics_before": metrics_before,
        "watermarks_found": watermarks["total_watermarks"],
    })


@app.route("/api/detect", methods=["POST"])
def detect_endpoint():
    data = request.get_json() or {}
    text = data.get("text", "")
    metrics = analyze_ai_Footprint(text)
    return jsonify({"metrics": metrics, **metrics})


@app.route("/api/humanize", methods=["POST"])
def humanize():
    data = request.get_json() or {}
    text = data.get("text", "")
    intensity = float(data.get("intensity", 0.65))
    seed = data.get("seed", None)

    if data.get("api_key"):
        engine.set_api_key(str(data["api_key"]))
    if isinstance(data.get("models"), list) and data["models"]:
        engine.set_model_priority([str(m) for m in data["models"] if str(m).strip()])

    if seed is not None:
        try:
            engine.set_seed(int(seed))
        except ValueError:
            pass

    result = engine.process(text, intensity=intensity)
    return jsonify(result)


@app.route("/api/inspect-watermark", methods=["POST"])
def inspect_watermark():
    data = request.get_json() or {}
    text = data.get("text", "")
    inspect_result = WatermarkSanitizer.inspect(text)
    return jsonify(inspect_result)


@app.route("/api/upload-docx", methods=["POST"])
def upload_docx():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename.endswith(".docx"):
        return jsonify({"error": "Only .docx files are supported"}), 400

    intensity = float(request.form.get("intensity", 0.65))
    filename = secure_filename(file.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, filename)
        output_filename = f"Humanized_{filename}"
        output_path = os.path.join(tmpdir, output_filename)

        file.save(input_path)
        docx_proc.process_file(input_path, output_path, intensity=intensity)

        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n=======================================================")
    print(">> Turnitout Humanizer Studio running at:")
    print(f">> http://127.0.0.1:{port}")
    print("=======================================================\n")
    app.run(host="127.0.0.1", port=port, debug=False)
