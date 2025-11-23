
import os
import io
import json
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import pdfplumber
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import openai

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXT = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set your OpenAI API key in environment variable OPENAI_API_KEY
OPENAI_KEY = os.getenv('export OPENAI_API_KEY="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')
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'no file part'}), 400
    f = request.files['file']
    if f.filename == '' or not allowed_file(f.filename):
        return jsonify({'error': 'invalid file'}), 400
    filename = secure_filename(f.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(path)
    return jsonify({'filename': filename})

@app.route('/extract', methods=['POST'])
def extract():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error':'missing filename'}), 400
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(path):
        return jsonify({'error':'file not found'}), 404

    pages = []
    with pdfplumber.open(path) as pdf:
        for pagenum, page in enumerate(pdf.pages, start=1):
            words = page.extract_words()
            pages.append({'page': pagenum, 'words': words, 'width': page.width, 'height': page.height})
    return jsonify({'pages': pages})

@app.route('/ai_edit', methods=['POST'])
def ai_edit():
    if OPENAI_KEY is None:
        return jsonify({'error':'OpenAI API key not configured on server.'}), 500

    data = request.get_json()
    filename = data.get('filename')
    page = data.get('page', 1)
    selection_text = data.get('selection_text', '')
    instruction = data.get('instruction', 'Please rewrite the selected text clearly.')
    if not filename or not selection_text:
        return jsonify({'error':'missing filename or selection_text'}), 400
    prompt = f"""You are a helpful PDF editor assistant. Instruction: {instruction}\n\nText to edit:\n{selection_text}\n\nReturn an edited version only (no extra commentary)."""
    try:
        resp = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=[{'role':'user','content': prompt}],
            temperature=0.2,
            max_tokens=1000
        )
        edited = resp['choices'][0]['message']['content'].strip()
        return jsonify({'edited_text': edited})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def make_overlay_page(words, replacements, page_width, page_height):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    for r in replacements:
        x = r.get('x0', 0)
        y = page_height - r.get('bottom', 0)
        text = r.get('text', '')
        c.setFont('Helvetica', 10)
        c.drawString(x, y, text)
    c.save()
    packet.seek(0)
    return packet

@app.route('/apply_replacements', methods=['POST'])
def apply_replacements():
    data = request.get_json()
    filename = data.get('filename')
    replacements = data.get('replacements', {})
    if not filename:
        return jsonify({'error':'missing filename'}), 400
    in_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(in_path):
        return jsonify({'error':'file not found'}), 404

    reader = PdfReader(in_path)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        if str(page_num) in replacements and replacements[str(page_num)]:
            with pdfplumber.open(in_path) as pdf:
                pdfpage = pdf.pages[i]
                w = pdfpage.width
                h = pdfpage.height
            overlay_pdf_stream = make_overlay_page(replacements[str(page_num)], replacements[str(page_num)], w, h)
            overlay_reader = PdfReader(overlay_pdf_stream)
            overlay_page = overlay_reader.pages[0]
            page.merge_page(overlay_page)
        writer.add_page(page)
    out_name = f"edited_{filename}"
    out_path = os.path.join(OUTPUT_FOLDER, out_name)
    with open(out_path, 'wb') as f:
        writer.write(f)
    return jsonify({'output': out_name})

@app.route('/download/<name>')
def download(name):
    path = os.path.join(OUTPUT_FOLDER, name)
    if not os.path.exists(path):
        return 'Not found', 404
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
