#!/usr/bin/env python
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv()

import process

app = process.app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 5000)), reload=True)