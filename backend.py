#!/usr/bin/env python
"""
Backend factory module for Deadsimple.

Reads backends.ini at module import (static config) and provides
a factory function to get backend instances.
"""

import importlib.util
import logging
import os
import tempfile
from abc import ABC, abstractmethod
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from openai import OpenAI

logger = logging.getLogger(__name__)

# Read config once at module import (static)
_CONFIG = ConfigParser()
_CONFIG.read(Path(__file__).parent / "backends.ini")


class BackendInterface(ABC):
    """Abstract base class for all backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the backend name."""
        pass

    @abstractmethod
    def convert_stream(self, stream) -> str:
        """Convert a stream to markdown and return the result."""
        pass


def _get_llm_client():
    """Get OpenAI client if LLM_TOKEN is configured."""
    llm_token = os.getenv("LLM_TOKEN", "")
    llm_url = os.getenv("LLM_URL", "https://api.openai.com/v1")
    llm_model = os.getenv("LLM_MODEL", "")

    if not llm_token:
        return None, None

    client = OpenAI(api_key=llm_token, base_url=llm_url)
    return client, llm_model


def _detect_file_format(stream) -> str:
    """
    Detect file format from stream content.
    
    Reads the first bytes to determine the file type based on magic numbers.
    
    Args:
        stream: BytesIO stream positioned at start
        
    Returns:
        Detected file extension (e.g., 'pdf', 'docx', 'pptx', 'png', 'jpg')
    """
    # Read first bytes for magic number detection
    header = stream.read(16)
    stream.seek(0)  # Reset position for subsequent reads
    
    if not header:
        return "unknown"
    
    # PDF magic number
    if header.startswith(b"%PDF"):
        return "pdf"
    
    # DOCX/XLSX/PPTX (ZIP-based)
    if header[:4] == b"PK\x03\x04":
        return "docx"  # Default to docx for office files
    
    # PNG
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    
    # JPEG
    if header[:3] == b"\xff\xd8\xff":
        return "jpg"
    
    # GIF
    if header[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    
    # TIFF
    if header[:4] in (b"II\x2a\x00", b"MM\x00\x2a"):
        return "tiff"
    
    # BMP
    if header[:2] == b"BM":
        return "bmp"
    
    # WebP
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    
    # HTML
    if header[:5].lower() in (b"<html", b"<!doc", b"<!htm"):
        return "html"
    
    # Plain text
    try:
        header.decode("utf-8")
        return "txt"
    except UnicodeDecodeError:
        pass
    
    return "unknown"


def _stream_to_temp_file(stream, suffix: str = "") -> str:
    """
    Write BytesIO stream to a temporary file and return its path.
    
    Args:
        stream: BytesIO stream to write
        suffix: File suffix/extension to use
        
    Returns:
        Path to temporary file
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        stream.seek(0)
        content = stream.read()
        os.write(fd, content)
    finally:
        os.close(fd)
    return path


class MarkItDownBackend(BackendInterface):
    """MarkItDown backend implementation."""

    def __init__(self, llm_client=None, llm_model=None):
        from markitdown import MarkItDown as MarkItDownClass

        if llm_client is None:
            llm_client, llm_model = _get_llm_client()

        self._backend = MarkItDownClass(
            llm_client=llm_client, llm_model=llm_model, enable_plugins=True
        )
        self._name = "markitdown"

    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """Convert a stream to markdown."""
        result = self._backend.convert_stream(stream=stream)
        return result.markdown


class OcrFluxBackend(BackendInterface):
    """
    OCRFlux backend implementation.
    
    OCRFlux is a multimodal LLM-based toolkit for converting PDFs and images
    into clean Markdown. It excels in complex layout handling, table parsing,
    and cross-page content merging.
    
    Usage:
        - Requires OCRFlux model and vllm server for local processing
        - Set OCRFLUX_MODEL_PATH environment variable for model location
        - Set OCRFLUX_API_URL environment variable for vllm server URL (default: http://localhost:8000/v1)
        
    Supported formats: PDF, PNG, JPG, TIFF
    
    Dependencies:
        - ocrflux
        - vllm
        - pypdf
        
    Note: OCRFlux requires significant GPU resources (3B model). For production,
    consider using the cloud API or alternative backends.
    """

    def __init__(self):
        self._name = "ocrflux"
        self._backend = None
        self._llm = None
        self._model_path = os.getenv("OCRFLUX_MODEL_PATH", "")
        self._api_url = os.getenv("OCRFLUX_API_URL", "http://localhost:8000/v1")
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of OCRFlux backend."""
        if self._initialized:
            return
            
        try:
            from ocrflux.inference import parse
            self._parse_func = parse
            
            if self._model_path:
                from vllm import LLM
                # Local mode with vllm
                self._llm = LLM(
                    model=self._model_path,
                    gpu_memory_utilization=0.8,
                    max_model_len=8192
                )
                self._mode = "local"
            else:
                # API mode - requires external vllm server
                self._mode = "api"
                
            self._initialized = True
            logger.info(f"OCRFlux initialized in {self._mode} mode")
            
        except ImportError as e:
            logger.error(f"OCRFlux not installed: {e}")
            raise RuntimeError(
                "OCRFlux not available. Install with: pip install ocrflux vllm"
            ) from e

    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """
        Convert a stream to markdown using OCRFlux.
        
        Args:
            stream: BytesIO stream containing document data
            
        Returns:
            Markdown string representation of the document
            
        Raises:
            RuntimeError: If OCRFlux is not properly initialized
            ValueError: If file format is not supported
        """
        file_format = _detect_file_format(stream)
        
        if file_format not in ("pdf", "png", "jpg", "jpeg", "tiff"):
            raise ValueError(
                f"OCRFlux does not support format: {file_format}. "
                f"Supported formats: PDF, PNG, JPG, TIFF"
            )
        
        # Determine suffix for temp file
        suffix = f".{file_format}" if file_format != "jpeg" else ".jpg"
        
        # Write stream to temp file
        temp_path = _stream_to_temp_file(stream, suffix=suffix)
        
        try:
            self._initialize()
            
            if self._mode == "local":
                result = self._parse_func(self._llm, temp_path)
                return result.get("document_text", "")
            else:
                # API mode - would need external vllm server
                raise NotImplementedError(
                    "OCRFlux API mode requires external vllm server. "
                    "Set OCRFLUX_MODEL_PATH environment variable for local processing."
                )
                
        except NotImplementedError:
            raise
        except Exception as e:
            logger.error(f"OCRFlux conversion failed: {e}")
            raise RuntimeError(f"OCRFlux conversion failed: {e}") from e
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


class DoclingsBackend(BackendInterface):
    """
    Doclings backend implementation.
    
    Docling is a powerful document processing library that parses diverse formats
    including PDF, DOCX, PPTX, XLSX, HTML, images, LaTeX, and more with advanced
    PDF understanding including layout, tables, code, and formulas.
    
    Usage:
        Simply instantiate and call convert_stream() with any supported format.
        
    Supported formats:
        - PDF (with advanced layout understanding)
        - DOCX (Microsoft Word)
        - PPTX (Microsoft PowerPoint)
        - XLSX (Microsoft Excel)
        - HTML
        - Images (PNG, TIFF, JPEG, etc.)
        - LaTeX
        - Plain text (.txt)
        
    Dependencies:
        - docling
        
    Example:
        backend = DoclingsBackend()
        markdown = backend.convert_stream(file_stream)
    """

    def __init__(self):
        from docling.document_converter import DocumentConverter
        
        self._name = "doclings"
        self._backend = DocumentConverter()
        logger.info("Doclings backend initialized")
        
    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """
        Convert a stream to markdown using Docling.
        
        Args:
            stream: BytesIO stream containing document data
            
        Returns:
            Markdown string representation of the document
            
        Raises:
            ValueError: If file format is not supported
            RuntimeError: If conversion fails
        """
        file_format = _detect_file_format(stream)
        
        # Map detected format to supported formats
        supported = {
            "pdf": "pdf",
            "docx": "docx",
            "pptx": "pptx", 
            "xlsx": "xlsx",
            "html": "html",
            "png": "image",
            "jpg": "image",
            "jpeg": "image",
            "tiff": "image",
            "gif": "image",
            "bmp": "image",
            "webp": "image",
            "txt": "txt",
        }
        
        if file_format not in supported:
            raise ValueError(
                f"Docling does not support format: {file_format}"
            )
        
        # Determine suffix for temp file
        suffix_map = {
            "pdf": ".pdf",
            "docx": ".docx",
            "pptx": ".pptx",
            "xlsx": ".xlsx",
            "html": ".html",
            "image": ".png",
            "txt": ".txt",
        }
        suffix = suffix_map.get(file_format, ".bin")
        
        # Write stream to temp file
        temp_path = _stream_to_temp_file(stream, suffix=suffix)
        
        try:
            # Convert using Docling
            result = self._backend.convert(temp_path)
            return result.document.export_to_markdown()
            
        except Exception as e:
            logger.error(f"Docling conversion failed: {e}")
            raise RuntimeError(f"Docling conversion failed: {e}") from e
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


class DocstrangeBackend(BackendInterface):
    """
    Docstrange backend implementation.
    
    Docstrange converts documents to Markdown, JSON, CSV, and HTML with
    intelligent structured data extraction and advanced OCR.
    
    Usage:
        Supports both cloud API and local processing modes:
        
        - Cloud mode (default): Uses API for processing
          Set DOCSTRANGE_API_KEY environment variable or pass api_key
          
        - Local GPU mode: Uses local GPU for processing
          Set gpu=True
          
        - Local CPU mode: Uses local CPU (slower)
          Set cpu=True
            
    Supported formats:
        - PDF, DOCX, PPTX, XLSX
        - Images (PNG, JPG, TIFF)
        - URLs (via convert_from_url)
        
    Dependencies:
        - docstrange
        - For local mode: CUDA-capable GPU recommended
        
    Example:
        # Cloud mode
        backend = DocstrangeBackend()
        
        # Local GPU mode
        backend = DocstrangeBackend(gpu=True)
    """

    def __init__(self, api_key: Optional[str] = None, gpu: bool = False, cpu: bool = False):
        """
        Initialize Docstrange backend.
        
        Args:
            api_key: Optional API key for cloud processing. 
                     If not provided, uses DOCSTRANGE_API_KEY env var.
            gpu: Force local GPU processing
            cpu: Force local CPU processing
        """
        from docstrange import DocumentExtractor
        
        self._name = "docstrange"
        
        # Get API key from env if not provided
        if api_key is None:
            api_key = os.getenv("DOCSTRANGE_API_KEY")
        
        # Initialize extractor
        self._backend = DocumentExtractor(
            api_key=api_key,
            gpu=gpu,
            cpu=cpu
        )
        
        self._mode = "cloud" if not (gpu or cpu) else ("gpu" if gpu else "cpu")
        logger.info(f"Docstrange initialized in {self._mode} mode")

    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """
        Convert a stream to markdown using Docstrange.
        
        Args:
            stream: BytesIO stream containing document data
            
        Returns:
            Markdown string representation of the document
            
        Raises:
            ValueError: If file format is not supported
            RuntimeError: If conversion fails
        """
        file_format = _detect_file_format(stream)
        
        # Docstrange supports these formats
        supported = ("pdf", "docx", "pptx", "xlsx", "png", "jpg", "jpeg", "tiff", "html")
        
        if file_format not in supported:
            raise ValueError(
                f"Docstrange does not support format: {file_format}. "
                f"Supported formats: {', '.join(supported)}"
            )
        
        # Determine suffix for temp file
        suffix_map = {
            "pdf": ".pdf",
            "docx": ".docx",
            "pptx": ".pptx",
            "xlsx": ".xlsx",
            "png": ".png",
            "jpg": ".jpg",
            "jpeg": ".jpg",
            "tiff": ".tiff",
            "html": ".html",
        }
        suffix = suffix_map.get(file_format, ".bin")
        
        # Write stream to temp file
        temp_path = _stream_to_temp_file(stream, suffix=suffix)
        
        try:
            # Convert to markdown
            result = self._backend.convert_to_markdown(temp_path)
            
            if result is None:
                raise RuntimeError("Docstrange returned empty result")
                
            # Handle different return types
            if hasattr(result, 'markdown'):
                return result.markdown
            elif isinstance(result, dict):
                return result.get("markdown", str(result))
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Docstrange conversion failed: {e}")
            raise RuntimeError(f"Docstrange conversion failed: {e}") from e
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


class MarkerBackend(BackendInterface):
    """
    Marker backend implementation.
    
    Marker converts PDF and other documents to markdown with high accuracy.
    It handles tables, forms, equations, code blocks, and more.
    
    Usage:
        Supports various document formats:
        - PDF (primary)
        - Images (PNG, JPG, TIFF)
        - DOCX, PPTX, XLSX (with full install: pip install marker-pdf[full])
        - HTML, EPUB (with full install)
        
    Features:
        - Table and form extraction
        - Equation handling (LaTeX)
        - Code block formatting
        - Header/footer removal
        - Optional LLM enhancement (via MARKER_USE_LLM env var)
        
    Dependencies:
        - marker-pdf
        - For full format support: pip install marker-pdf[full]
        
    Environment variables:
        - MARKER_USE_LLM: Enable LLM enhancement
        - MARKER_LLM_API_KEY: API key for LLM service
        
    Example:
        backend = MarkerBackend()
        markdown = backend.convert_stream(pdf_stream)
    """

    def __init__(self):
        self._name = "marker"
        self._backend = None
        self._artifact_dict = None
        self._use_llm = os.getenv("MARKER_USE_LLM", "false").lower() == "true"

    def _initialize(self):
        """Lazy initialization of Marker backend."""
        if self._backend is not None:
            return
            
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            
            self._artifact_dict = create_model_dict()
            self._backend = PdfConverter(
                artifact_dict=self._artifact_dict,
            )
            logger.info(f"Marker initialized (LLM: {self._use_llm})")
            
        except ImportError as e:
            logger.error(f"Marker not installed: {e}")
            raise RuntimeError(
                "Marker not available. Install with: pip install marker-pdf"
            ) from e

    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """
        Convert a stream to markdown using Marker.
        
        Args:
            stream: BytesIO stream containing document data
            
        Returns:
            Markdown string representation of the document
            
        Raises:
            ValueError: If file format is not supported
            RuntimeError: If conversion fails
        """
        from marker.output import text_from_rendered
        
        file_format = _detect_file_format(stream)
        
        # Marker supports these formats
        supported = ("pdf", "png", "jpg", "jpeg", "tiff", "docx", "pptx", "xlsx", "html", "epub")
        
        if file_format not in supported:
            raise ValueError(
                f"Marker does not support format: {file_format}. "
                f"Supported formats: {', '.join(supported)}"
            )
        
        # Determine suffix for temp file
        suffix_map = {
            "pdf": ".pdf",
            "png": ".png",
            "jpg": ".jpg",
            "jpeg": ".jpg",
            "tiff": ".tiff",
            "docx": ".docx",
            "pptx": ".pptx",
            "xlsx": ".xlsx",
            "html": ".html",
            "epub": ".epub",
        }
        suffix = suffix_map.get(file_format, ".bin")
        
        # Write stream to temp file
        temp_path = _stream_to_temp_file(stream, suffix=suffix)
        
        try:
            self._initialize()
            
            # Convert using Marker
            rendered = self._backend(temp_path)
            
            # Extract markdown from rendered result
            text, _, images = text_from_rendered(rendered)
            return text
            
        except Exception as e:
            logger.error(f"Marker conversion failed: {e}")
            raise RuntimeError(f"Marker conversion failed: {e}") from e
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def _is_backend_available(backend_name: str) -> bool:
    """Check if a backend's Python module is installed."""
    if backend_name == "markitdown":
        return True  # markitdown is required (always available)
    if backend_name == "ocrflux":
        return importlib.util.find_spec("ocrflux") is not None
    if backend_name == "doclings":
        return importlib.util.find_spec("docling") is not None
    if backend_name == "docstrange":
        return importlib.util.find_spec("docstrange") is not None
    if backend_name == "marker":
        return importlib.util.find_spec("marker") is not None
    return False


def _get_available_backends() -> list:
    """Get list of available backends from config that are installed."""
    available_spec = _CONFIG.get("backends", "available", fallback="")
    if not available_spec:
        return []

    backends = [b.strip() for b in available_spec.split(",") if b.strip()]
    return [b for b in backends if _is_backend_available(b)]


def _get_default_backend() -> str:
    """Get the default backend name from config."""
    return _CONFIG.get("default", "backend", fallback="markitdown")


def get_backend(name: Optional[str] = None):
    """
    Factory function to get a backend instance.

    Args:
        name: Backend name (e.g., "markitdown", "ocrflux", "doclings", "docstrange", "marker").
              If None, uses the default from backends.ini.

    Returns:
        BackendInterface instance.

    Raises:
        HTTPException(status_code=400): If the requested backend is unavailable.
    """
    default_backend = _get_default_backend()

    if name is None:
        name = default_backend

    # Validate backend name is in available list
    available_spec = _CONFIG.get("backends", "available", fallback="")
    available_list = [b.strip() for b in available_spec.split(",") if b.strip()]

    if name not in available_list:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown backend '{name}'. Available backends: {', '.join(available_list)}",
        )

    # Check if backend is installed
    if not _is_backend_available(name):
        raise HTTPException(
            status_code=400,
            detail=f"Backend '{name}' is not installed. Install it with: pip install {name}",
        )

    # Create and return backend instance
    if name == "markitdown":
        return MarkItDownBackend()
    elif name == "ocrflux":
        return OcrFluxBackend()
    elif name == "doclings":
        return DoclingsBackend()
    elif name == "docstrange":
        return DocstrangeBackend()
    elif name == "marker":
        return MarkerBackend()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Backend '{name}' is not supported. Available: {', '.join(available_list)}",
        )