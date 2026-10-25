"""
Turnitout Local Web Application
Serves interactive humanizer GUI for Google Docs / Thesis text and .docx files.
"""

import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from core.engine import HumanizerEngine
from core.docx_handler import DocxProcessor
from core.cleaner import WatermarkSanitizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "web", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB max upload

engine = HumanizerEngine()
docx_proc = DocxProcessor(engine)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/humanize', methods=['POST'])
def humanize():
    data = request.get_json() or {}
    text = data.get('text', '')
    intensity = float(data.get('intensity', 0.6))
    seed = data.get('seed', None)
    if seed is not None:
        try:
            engine.set_seed(int(seed))
        except ValueError:
            pass

    result = engine.process(text, intensity=intensity)
    return jsonify(result)

@app.route('/api/inspect-watermark', methods=['POST'])
def inspect_watermark():
    data = request.get_json() or {}
    text = data.get('text', '')
    inspect_result = WatermarkSanitizer.inspect(text)
    return jsonify(inspect_result)

@app.route('/api/upload-docx', methods=['POST'])
def upload_docx():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if not file.filename.endswith('.docx'):
        return jsonify({'error': 'Only .docx files are supported'}), 400

    intensity = float(request.form.get('intensity', 0.6))
    filename = secure_filename(file.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, filename)
        output_filename = f"Humanized_{filename}"
        output_path = os.path.join(tmpdir, output_filename)

        file.save(input_path)
        stats = docx_proc.process_file(input_path, output_path, intensity=intensity)

        # Read output file bytes to stream back
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f">> Turnitout Humanizer Studio running at:")
    print(f">> http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host='127.0.0.1', port=port, debug=False)

