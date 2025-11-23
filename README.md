
OpenAI PDF Editor — Full Tool Prototype

What this project contains:
- Flask backend (app.py) that:
  - accepts PDF uploads (/upload)
  - extracts words and coordinates using pdfplumber (/extract)
  - sends selected text to OpenAI for editing (/ai_edit) -- requires OPENAI_API_KEY in environment
  - applies queued replacements and exports an edited PDF (/apply_replacements)
  - download endpoint (/download/<name>)

- Frontend simple single-page app (templates/index.html):
  - Upload PDF, view words per page, click a word to select it
  - Send selected text + instruction to OpenAI and get edited text
  - Apply edited text as overlay replacements (queued per page)
  - Export edited PDF and download

How to run (quick):
1. Install dependencies (recommend inside a virtualenv):
   pip install -r requirements.txt
2. Set environment variable OPENAI_API_KEY (if you want AI editing):
   export OPENAI_API_KEY="your_api_key_here"
3. Run the Flask app:
   python app.py
4. Open http://localhost:5000 in your browser.

Notes / Limitations:
- This is a working prototype intended as a starting point. It focuses on correctness and clarity rather than production hardening.
- Replacements are applied visually by drawing overlay text at word coordinates (ReportLab). This may not remove the original text (it overlays on top).
- For scanned PDFs (images), OCR (tesseract) would be required; pdfplumber works for text-based PDFs.
- Font matching, kerning, complex layouts, multi-line replacements, and exact positioning may need iteration for perfect visual fidelity.
- The OpenAI usage here uses ChatCompletion; adjust model & parameters as needed for cost/performance.
- For production, add authentication, file size limits, rate limits, and secure API key handling.
