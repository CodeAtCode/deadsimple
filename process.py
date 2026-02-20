#!/usr/bin/env python
"""FastAPI router for document processing with backend selection."""

import logging
from fastapi import APIRouter, Request, HTTPException
from io import BytesIO

from backend import get_backend

logger = logging.getLogger(__name__)

router = APIRouter()


@router.api_route("/process", methods=["PUT", "POST"])
async def process(request: Request):
    """
    Process a document using the default backend from config.

    Accepts binary document data in the request body and returns
    the processed markdown content.

    Returns:
        {"page_content": markdown, "metadata": {}}

    Raises:
        HTTPException(400): If no document data provided or processing fails.
    """
    data = await request.body()

    if not data:
        raise HTTPException(status_code=400, detail="No document data provided")

    try:
        backend = get_backend()
        logger.info(f"Selected backend: {backend.name}")
        markdown = backend.convert_stream(stream=BytesIO(data))

        return {"page_content": markdown, "metadata": {}}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading document: {e}")
