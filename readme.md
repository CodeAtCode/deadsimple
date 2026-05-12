# Deadsimple - Document Extractor

FastAPI service for extracting text from PDF, DOCX, PPTX, EPUB, HTML, TXT with **multi-backend architecture**.

---

## 🚀 Features

- **Multiple file formats**: Supports PDF, DOCX, PPTX, EPUB, HTML, Markdown, TXT, CSV, and more
- **Vision LLM**: Optional OpenAI-compatible API for extracting text from scanned PDFs/images
- **Page-wise output**: Returns structured output (one per page/slide)
- **Extensible backend architecture**: Designed for easy addition of new backends

---

## 📦 Installation

```bash
pip install -e .
```

### Supported Formats

markitdown supports these file types out of the box:

| Format | MIME Type |
|--------|-----------|
| PDF | `application/pdf` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| PPTX | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| EPUB | `application/epub+zip` |
| HTML | `text/html` |
| Markdown | `text/markdown` or `text/x-markdown` |
| TXT | `text/plain` |
| CSV | `text/csv` |
| DOC (legacy) | `application/msword` |
| PPT (legacy) | `application/vnd.ms-powerpoint` |
| XLSX | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| XLS (legacy) | `application/vnd.ms-excel` |

---

## 🌐 Vision LLM Mode

To use vision mode (scanned PDFs/images → text), set these environment variables:

```bash
export LLM_TOKEN="your_api_key"       # OpenAI or compatible API key
export LLM_MODEL="gpt-4o"             # model name (supports vision)
export LLM_URL="https://api.openai.com/v1"  # API endpoint (default)
```

---

## 🧪 Running

```bash
python deadsimple/main.py
```

API available at `http://localhost:5000`

---

## 📡 API

### Process Document

```bash
curl -X POST http://localhost:5000/process \
  -H "Content-Type: application/pdf" \
  --data-binary @document.pdf
```

**Response:**
```json
{
  "page_content": "page 1 text\n---\npagina 2 text",
  "metadata": {}
}
```

---

## 🧪 Testing

```bash
pytest tests/
```

## Optional Backends

The service supports optional backends that provide extra capabilities such as OCR, document linking, and content analysis. These backends are not required for basic operation; markitdown is always included.

**Available backends**

- `ocrflux` – OCR extraction backend
- `doclings` – Document linking backend
- `docstrange` – Specialized document processing backend
- `marker` – Marker based backend

**Installation**

Each backend is provided as an extra in *pyproject.toml*. Install the desired backend with pip, for example:

```bash
pip install -e ".[ocrflux]"
pip install -e ".[doclings]"
pip install -e ".[docstrange]"
pip install -e ".[marker]"
```

You can also install multiple extras at once:

```bash
pip install -e ".[ocrflux,doclings,docstrange,marker]"
```
