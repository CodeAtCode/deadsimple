#!/usr/bin/env python
"""
Automated acceptance tests for backend selection.

Tests factory function behavior and /process endpoint with logging verification.
Uses pytest and FastAPI's TestClient.
"""

import logging
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend import get_backend

os.environ["LLM_TOKEN"] = ""
os.environ["LLM_URL"] = ""
os.environ["LLM_MODEL"] = ""

from fastapi import FastAPI
from process import router as process_router


app = FastAPI(title="DeadSimple Test")
app.include_router(process_router)

# Configure logging for capture
logging.basicConfig(level=logging.INFO)


class TestBackendFactory:
    """Tests for the backend.get_backend() factory function."""

    def test_get_backend_default(self):
        """Default backend selection returns MarkItDownBackend instance."""
        backend = get_backend()
        assert backend is not None
        assert backend.name == "markitdown"

    def test_get_backend_explicit(self):
        """Explicit 'markitdown' backend returns valid instance."""
        backend = get_backend(name="markitdown")
        assert backend is not None
        assert backend.name == "markitdown"

    def test_get_backend_unknown(self):
        """Unknown backend name raises HTTPException with 400 status."""
        with pytest.raises(Exception) as exc_info:
            get_backend(name="unknown_backend")
        
        assert exc_info.value.status_code == 400


class TestProcessEndpoint:
    """Tests for the /process endpoint using TestClient."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        return TestClient(app)

    def test_process_endpoint_default(self, client):
        """POST /process with sample data returns 200 and markdown content."""
        sample_text = b"Hello World"

        response = client.post(
            "/process",
            content=sample_text,
            headers={"Content-Type": "application/octet-stream"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "page_content" in data
        assert "metadata" in data
        assert isinstance(data["page_content"], str)

    def test_process_endpoint_no_data(self, client):
        """POST /process with empty body returns 400."""
        response = client.post(
            "/process",
            content=b"",
            headers={"Content-Type": "application/octet-stream"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


class TestLogging:
    """Tests for logging output verification."""

    @pytest.fixture
    def client(self):
        """Create TestClient for the FastAPI app."""
        return TestClient(app)

    def test_process_logs_backend_selection(self, client, caplog):
        """Logging output contains 'Selected backend: markitdown'."""
        caplog.set_level(logging.INFO)

        sample_text = b"Test content"

        response = client.post(
            "/process",
            content=sample_text,
            headers={"Content-Type": "application/octet-stream"}
        )

        assert response.status_code == 200

        log_messages = [record.message for record in caplog.records]
        backend_selection_logs = [msg for msg in log_messages if "Selected backend:" in msg]

        assert len(backend_selection_logs) >= 1
        assert "Selected backend: markitdown" in " ".join(backend_selection_logs)



