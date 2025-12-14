import os
import json
import mimetypes
import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory

class ExtractionAgent:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API Key is required for Extraction Agent")
        genai.configure(api_key=api_key)
        # Using the stable 1.5-flash model
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def process_document(self, file_path):
        filename = os.path.basename(file_path)
        print(f"🕵️ [ExtractionAgent] Analyzing document: {filename}")
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None: mime_type = "application/pdf"

        try:
            uploaded_file = genai.upload_file(file_path, mime_type=mime_type)
            
            prompt = """
            You are an expert Data Entry Specialist. 
            Extract the following fields from the provider application form into a strict JSON object:
            - provider_name (String): Full legal name
            - npi_number (String): 10-digit NPI
            - phone_number (String): Office phone
            - address (String): Practice address
            
            Rules:
            1. Return ONLY valid JSON.
            2. If a value is missing or illegible, set it to null.
            3. Do not include markdown formatting like ```json.
            """
            
            # Disable safety filters to ensure medical forms are processed
            response = self.model.generate_content(
                [prompt, uploaded_file],
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Clean and Parse
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            print("✅ [ExtractionAgent] Data extracted successfully.")
            return data

        except Exception as e:
            print(f"❌ [ExtractionAgent] Critical Error: {e}")
            return {"error": str(e), "provider_name": "Error"}