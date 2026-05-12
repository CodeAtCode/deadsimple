# D(ocument)e(xtractor)adSimple

This FastAPI service extracts text content from a wide variety of document formats (PDF, DOCX, PPTX, EPUB, HTML, TXT, etc.) using [`markitdown`](https://github.com/markitdown/markitdown). It returns the content as an array of strings, one for each logical page, slide, or section.

---

## 🚀 Features

- Supports multiple document formats
- Returns page-wise content as a JSON array
- Automatically detects file type via content-type
- FastAPI + Uvicorn app, easy to deploy

---

## 📦 Supported File Types

- PDF (`application/pdf`)
- DOCX / Word
- PPTX / PowerPoint
- EPUB
- HTML
- Markdown
- TXT
- CSV

---

## Example usage

* In OpenWebUI, configure for Document Extractor external and as url `http://localhost:5000` (you can change this based on your needs)
* Locally, `curl -X POST http://localhost:5000/process -H "Content-Type: application/pdf" --data-binary @file.pdf`

### Env

* PORT=5000
* LLM_TOKEN # OpenAI API key (or compatible provider) for vision/OCR
* LLM_MODEL # Model name (e.g., gpt-4o, gpt-4o-mini)
* LLM_URL # OpenAI-compatible endpoint (default: https://api.openai.com/v1)

### LLM Mode (Vision OCR)

By setting `LLM_TOKEN`, `LLM_MODEL`, and optionally `LLM_URL`, the service uses **markitdown** with LLM vision capabilities:

- Scanned PDFs and images are processed via the LLM's vision API
- Each page is sent as an image to the LLM for text extraction
- Works with any OpenAI-compatible provider (OpenAI, Ollama, Groq, etc.)

**Example for local Ollama:**
```
LLM_TOKEN=ollama
LLM_MODEL=llava
LLM_URL=http://localhost:11434/v1
```

---

## 🧪 Setup (with virtual environment)

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

./main.py
```

## Optional Backends

The service can work with optional backends that provide extra capabilities such as OCR, document linking, and content analysis. These backends are not required for basic operation; the API works out‑of‑the‑box.

**Available backends**

- `ocrflux` – OCR extraction backend
- `doclings` – Document linking backend
- `docstrange` – Specialized document processing backend
- `marker` – Marker based backend

**Installation**

Each backend is provided as an extra in *pyproject.toml*. Install the desired backend with pip, for example:

```bash
pip install .[ocrflux]
pip install .[doclings]
pip install .[docstrange]
pip install .[marker]
```

You can also install multiple extras at once:

```bash
pip install .[ocrflux,doclings,docstrange,marker]
```

If no extra is installed, the core service runs without these features.

