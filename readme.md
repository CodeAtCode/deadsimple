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

## 🧪 Setup (with virtual environment)

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

./main.py
```
