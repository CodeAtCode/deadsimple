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
* LLM_TOKEN # You can use a LLM to read images
* LLM_MODEL # The LLM model
* LLM_URL # The URL of an OpenAI compatible provider

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

