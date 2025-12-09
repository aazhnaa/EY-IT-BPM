# backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import utils # Imports your existing logic
import shutil
import os
import json

app = FastAPI(title="Provider Validator API")

class ValidationResponse(BaseModel):
    extracted: dict
    official: dict
    validation_result: dict

@app.get("/")
def health_check():
    return {"status": "running", "service": "Backend API"}

@app.post("/validate_document")
async def validate_document(file: UploadFile = File(...)):
    """
    Receives a file, runs Gemini extraction + NPI validation, returns JSON.
    """
    try:
        # 1. Save the uploaded file temporarily so Gemini can read it
        temp_filename = f"temp_{file.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Run the Agentic Workflow (using your existing utils)
        # We need to open the file again as a binary object for your util function
            # We assume your utils.extract_data_with_gemini takes a file-like object
            # You might need to adjust utils.py slightly to accept raw bytes or a path
            # For now, let's assume we pass the file object
            print(f"DEBUG: sending {temp_filename} to Gemini...")
        extracted_data = utils.extract_data_with_gemini(temp_filename)

        # 3. Validate
        report = utils.validate_provider(extracted_data)

        # 4. Cleanup
        os.remove(temp_filename)

        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))