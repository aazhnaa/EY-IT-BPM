import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
# Make sure GOOGLE_API_KEY is in your .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load the Mock DB
def load_mock_db():
    with open('mock-db.json', 'r') as f:
        return json.load(f)

# --- JOB 1: THE EYES (Gemini VLM Extraction) ---
def extract_data_with_gemini(image_file):
    """
    Sends the uploaded image to Gemini Flash to extract structured data.
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # The prompt is critical. We force it to return JSON.
        prompt = """
        Analyze this scanned medical provider application form.
        Extract the following fields and return them strictly as a JSON object:
        - provider_name (String)
        - npi_number (String)
        - phone_number (String)
        - address (String)
        
        Do not add any markdown formatting like ```json ... ```. Just return the raw JSON string.
        """
        
        # Load image data (Streamlit passes a BytesIO object)
        image_parts = [
            {
                "mime_type": "image/png", # Adjust if using PDF/JPEG
                "data": image_file.getvalue()
            }
        ]

        response = model.generate_content([prompt, image_parts[0]])
        
        # Clean up response (Gemini sometimes adds markdown backticks)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(clean_json)
    
    except Exception as e:
        return {"error": str(e)}

# --- JOB 2: THE TRUTH (NPI Registry API) ---
def fetch_npi_data(npi_number):
    """
    Queries the official CMS NPI Registry API.
    """
    url = f"https://npiregistry.cms.hhs.gov/api/?number={npi_number}&version=2.1"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("result_count") > 0:
            result = data["results"][0]
            # Extract only what we need
            return {
                "official_name": f"{result['basic']['first_name']} {result['basic']['last_name']}",
                "official_address": result['addresses'][0]['address_1'],
                "official_phone": result['addresses'][0]['telephone_number'],
                "status": "Active" # NPI registry usually returns active providers
            }
        else:
            return {"error": "NPI Not Found"}
            
    except Exception as e:
        return {"error": str(e)}

# --- JOB 3: THE JUDGE (Validation Logic) ---
def validate_provider(extracted_data):
    """
    Orchestrates the validation:
    1. Gets Extracted Data
    2. Gets NPI Data
    3. Checks Mock DB (State Board)
    4. Compares and Scores
    """
    npi = extracted_data.get("npi_number")
    
    # 1. Fetch Official Data
    npi_data = fetch_npi_data(npi)
    
    # 2. Fetch Mock State Board Data
    mock_db = load_mock_db()
    state_data = mock_db.get(npi, {"state_license_status": "Unknown", "google_rating": "N/A"})
    
    # 3. Compare Logic (The "Smart" Part)
    score = 100
    mismatches = []
    
    # Compare Phone Numbers (Simple string check for demo)
    # In real life, you'd strip dashes/spaces first
    if extracted_data.get("phone_number") != npi_data.get("official_phone"):
        score -= 30
        mismatches.append("Phone Number Mismatch")
        
    # Check State License
    if state_data.get("state_license_status") != "Active":
        score -= 50
        mismatches.append("State License Issue")

    # Determine Priority
    priority = "Low"
    if score < 80:
        priority = "Medium"
    if score < 50:
        priority = "High"

    return {
        "extracted": extracted_data,
        "official": npi_data,
        "state_board": state_data,
        "validation_result": {
            "score": score,
            "priority": priority,
            "mismatches": mismatches
        }
    }