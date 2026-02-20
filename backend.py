#!/usr/bin/env python
"""
Backend factory module for Deadsimple.

Reads backends.ini at module import (static config) and provides
a factory function to get backend instances.
"""

import importlib.util
from abc import ABC, abstractmethod
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

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


class MarkItDownBackend(BackendInterface):
    """MarkItDown backend implementation."""

    def __init__(self, llm_client=None, llm_model=None):
        from markitdown import MarkItDown as MarkItDownClass

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
    """OCRFlux backend implementation (optional)."""

    def __init__(self):
        self._name = "ocrflux"
        self._backend = None

    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """Convert a stream to markdown using OCR."""
        if self._backend is None:
            raise RuntimeError("OCRFlux not initialized")
        # Placeholder for actual implementation
        raise NotImplementedError("OCRFlux backend not fully implemented")


class DoclingsBackend(BackendInterface):
    """Doclings backend implementation (optional)."""

    def __init__(self):
        self._name = "doclings"
        self._backend = None

    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """Convert a stream to markdown using Doclings."""
        if self._backend is None:
            raise RuntimeError("Doclings not initialized")
        # Placeholder for actual implementation
        raise NotImplementedError("Doclings backend not fully implemented")


class DocstrangeBackend(BackendInterface):
    """Docstrange backend implementation (optional)."""

    def __init__(self):
        self._name = "docstrange"
        self._backend = None

    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """Convert a stream to markdown using Docstrange."""
        if self._backend is None:
            raise RuntimeError("Docstrange not initialized")
        # Placeholder for actual implementation
        raise NotImplementedError("Docstrange backend not fully implemented")


class MarkerBackend(BackendInterface):
    """Marker backend implementation (optional)."""

    def __init__(self):
        self._name = "marker"
        self._backend = None

    @property
    def name(self) -> str:
        return self._name

    def convert_stream(self, stream) -> str:
        """Convert a stream to markdown using Marker."""
        if self._backend is None:
            raise RuntimeError("Marker not initialized")
        # Placeholder for actual implementation
        raise NotImplementedError("Marker backend not fully implemented")


def _is_backend_available(backend_name: str) -> bool:
    """Check if a backend's Python module is installed."""
    if backend_name == "markitdown":
        return True  # markitdown is required (always available)
    if backend_name == "ocrflux":
        return importlib.util.find_spec("ocrflux") is not None
    if backend_name == "doclings":
        return importlib.util.find_spec("doclings") is not None
    if backend_name == "docstrange":
        return importlib.util.find_spec("docstrange") is not None
    if backend_name == "marker":
        return importlib.util.find_spec("marker") is not None
    return False


def _get_available_backends() -> list[str]:
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
    available_backends = _CONFIG.get("backends", "available", fallback="")
    available_list = [b.strip() for b in available_backends.split(",") if b.strip()]

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
