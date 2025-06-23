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
