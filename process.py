#!/usr/bin/env python
import logging
from fastapi import FastAPI, APIRouter, Request, HTTPException
from io import BytesIO

from backend import get_backend

logger = logging.getLogger(__name__)

app = FastAPI(title="DeadSimple")
router = APIRouter()


@router.api_route("/process", methods=["PUT", "POST"])
async def process(request: Request):
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


app.include_router(router)