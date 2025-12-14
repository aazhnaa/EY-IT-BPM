import os
# Import your agent
from .extraction_agent import ExtractionAgent
# Import Teammate A's agents 
from .data_validation_agent import DataValidationAgent
from .enrichment_agent import InformationEnrichmentAgent

class DirectoryManagementAgent:
    def __init__(self):
        # Initialize the workforce
        api_key = os.getenv("GOOGLE_API_KEY")
        
        # 1. Your Agent
        self.extractor = ExtractionAgent(api_key)
        
        # 2. Teammate A's Agents
        self.validator = DataValidationAgent()
        self.enricher = InformationEnrichmentAgent()

    def process_application(self, file_path):
        print("\n🤖 [DirectoryManager] New Task Received. Starting Workflow...")
        
        # STEP 1: Extraction (The Eyes)
        extracted = self.extractor.process_document(file_path)
        if "error" in extracted:
            return {"error": "Extraction Failed", "details": extracted}

        # STEP 2: Validation (The Verifier)
        npi = extracted.get("npi_number")
        official_data = self.validator.validate_npi(npi)
        license_data = self.validator.check_state_license(npi)

        # STEP 3: Enrichment (The Researcher)
        # We search based on the extracted name to see if they exist online
        web_data = self.enricher.enrich_provider_data(extracted.get("provider_name"), "USA")

        # STEP 4: Quality Assurance (The Judge)
        report = self._perform_quality_assurance(extracted, official_data, license_data, web_data)
        
        print("✅ [DirectoryManager] Workflow Complete. Report Ready.")
        return report

    def _perform_quality_assurance(self, extracted, official, license_data, web_data):
        """
        Calculates confidence score based on data consistency across sources.
        """
        score = 100
        mismatches = []
        priority = "Low"

        # Normalization
        pdf_phone = str(extracted.get("phone_number", "")).replace("-", "").replace(" ", "")
        npi_phone = str(official.get("official_phone", "")).replace("-", "").replace(" ", "")
        
        # Rule 1: Existence Check
        if official.get("official_name") == "Not Found":
            score = 0
            mismatches.append("CRITICAL: Provider not found in NPI Registry")
            priority = "Critical"
        
        # Rule 2: Phone Verification
        elif pdf_phone != npi_phone:
            score -= 40
            mismatches.append(f"Phone Discrepancy (PDF: {pdf_phone} vs Registry: {npi_phone})")
            priority = "High"

        # Rule 3: License Check
        if license_data.get("state_license_status") != "Active":
            score -= 20
            mismatches.append(f"State License Issue: {license_data.get('state_license_status')}")

        return {
            "extracted": extracted,
            "official": official,
            "state_board": license_data,
            "web_enrichment": web_data,
            "validation_result": {
                "score": score,
                "priority": priority,
                "mismatches": mismatches
            }
        }