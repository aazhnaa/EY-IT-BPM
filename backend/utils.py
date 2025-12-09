import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import mimetypes
from google.generativeai.types import HarmBlockThreshold,HarmCategory
# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
# Configure Gemini
# Make sure GOOGLE_API_KEY is in your .env file
if not api_key:
    print("❌ CRITICAL ERROR: GOOGLE_API_KEY not found in .env file!")
else:
    print(f"✅ API Key loaded: {api_key[:5]}... (hidden)")
    genai.configure(api_key=api_key)


# Load the Mock DB
def load_mock_db():
    try:
        with open('mock-db.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ Warning: mock_db.json not found.")
        return {}

# --- JOB 1: THE EYES (Gemini VLM Extraction) ---
def extract_data_with_gemini(file_path):
    """
    Sends the uploaded image to Gemini Flash to extract structured data.
    """
    print(f"\n--- 🕵️ STARTED EXTRACTION FOR: {file_path} ---")
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        mime_type,_=mimetypes.guess_type(file_path)#returns a tuple , file type and encoding 
        if mime_type is None:
            mime_type="application/pdf"

        print(f"debug : processing file as {mime_type}")
        uploaded_file=genai.upload_file(file_path,mime_type=mime_type)

        # The prompt is critical. We force it to return JSON.
        prompt = """
        Analyze this scanned medical provider application form.
        Extract the following fields and return them strictly as a JSON object:
        - provider_name (String)
        - npi_number (String)
        - phone_number (String)
        - address (String)
        
        Do not add any markdown formatting like ```json ... ```. Just return the raw JSON string.
        Rules:
        1. If the NPI is not visible, look for "National Provider Identifier".
        2. Return ONLY valid JSON. Do not write "Here is the JSON".
        3. If a value is missing, return null.
        """
    
        print("DEBUG: Sending prompt to model...")
        response = model.generate_content(
            [prompt, uploaded_file],
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        # Clean up response (Gemini sometimes adds markdown backticks)
        print(f"DEBUG: Response Feedback: {response.prompt_feedback}")
        
        # Check if the response was blocked
        if not response.parts:
            print(f"❌ ERROR: Gemini returned no content. Finish Reason: {response.candidates[0].finish_reason}")
            return {"provider_name": "Blocked", "npi_number": "Error", "phone_number": "Error"}

        print(f"DEBUG: Raw Response Text: {response.text}")
        
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    
    except Exception as e:
        # THIS PRINT IS MISSING IN YOUR CODE:
        print(f"❌ CRASH IN EXTRACTION: {e}") 
        return {"error": str(e), "provider_name": "Error", "npi_number": "Error"}

# --- JOB 2: THE TRUTH (NPI Registry API) ---
def fetch_npi_data(npi_number):
    
    """
    Queries the official CMS NPI Registry API.
    """
    if not npi_number or npi_number == "Error":
        return {"official_name": "Invalid NPI", "official_phone": "N/A"}
        
    print(f"DEBUG: Querying NPI Registry for: {npi_number}")
    url = f"https://npiregistry.cms.hhs.gov/api/?number={npi_number}&version=2.1"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("result_count") > 0:
            result = data["results"][0]
            addr = result.get('addresses', [{}])[0]
            # Extract only what we need
            return {
                "official_name": f"{result['basic']['first_name']} {result['basic']['last_name']}",
                "official_address": addr.get('address_1', 'N/A'),
                "official_phone": addr.get('telephone_number', 'N/A'),
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
    
    
    # 3. Compare Logic (The "Smart" Part)
    score = 100
    mismatches = []
    
    ext_phone = str(extracted_data.get("phone_number", "")).replace("-", "").replace(" ", "")
    off_phone = str(npi_data.get("official_phone", "")).replace("-", "").replace(" ", "")
    # Compare Phone Numbers (Simple string check for demo)
    # In real life, you'd strip dashes/spaces first
    if npi_data.get("official_name") == "Not Found":
        score = 0
        mismatches.append("Invalid NPI")
    
    # Simple check: Do phones match?
    elif ext_phone != off_phone:
        score -= 40
        mismatches.append("Phone Number Mismatch")
    # Determine Priority
    priority = "Low"
    if score < 80:
        priority = "Medium"
    if score < 50:
        priority = "High"

    return {
        "extracted": extracted_data,
        "official": npi_data,
        "state_board": {"state_license_status": "Active"}, # Still mocking State Board for now
        "validation_result": {
            "score": score,
            "priority": priority,
            "mismatches": mismatches
        }
    }