#!/usr/bin/env python
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
from markitdown import MarkItDown
from dotenv import load_dotenv
from io import BytesIO
from openai import OpenAI
import uvicorn
import os

load_dotenv()

app = FastAPI(title="DeadSimple")
LLM_CLIENT = ""
LLM_MODEL = ""
if os.getenv("LLM_TOKEN") != "":
    LLM_CLIENT = OpenAI(api_key=os.getenv("LLM_TOKEN"), base_url=os.getenv("LLM_URL"))
    LLM_MODEL = os.getenv("LLM_MODEL")

@app.api_route("/process", methods=["PUT", "POST"])
async def process(
    request: Request,
    authorization: str | None = Header(None),
    content_type: str = Header(...),
):
    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="No document data provided")

    try:
        result = MarkItDown(llm_client=LLM_CLIENT, llm_model=LLM_MODEL,enable_plugins=True).convert_stream(stream=BytesIO(data))

        return {"page_content": result.markdown, "metadata": {}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading document: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 5000)), reload=True)
