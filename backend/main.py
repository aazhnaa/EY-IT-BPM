from fastapi import FastAPI, UploadFile, File, HTTPException
# Import your new Orchestrator
from agents.directory_management_agent import DirectoryManagementAgent
import shutil
import os
from dotenv import load_dotenv

# Load Environment
load_dotenv()

app = FastAPI(title="Provider Validator Agent System")

# Initialize the Master Agent
try:
    manager = DirectoryManagementAgent()
except Exception as e:
    print(f"❌ Startup Error: {e}")
    manager = None

@app.post("/validate_document")
async def validate_document(file: UploadFile = File(...)):
    if not manager:
        raise HTTPException(status_code=500, detail="Agent System not initialized")

    temp_filename = f"temp_{file.filename}"
    
    try:
        # Save File
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Delegate to the Master Agent
        report = manager.process_application(temp_filename)
        return report

    except Exception as e:
        print(f"SERVER ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)