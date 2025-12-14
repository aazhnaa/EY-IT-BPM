import requests
import json
import os

class DataValidationAgent:
    def __init__(self):
        self.base_url = "https://npiregistry.cms.hhs.gov/api/"

    def validate_npi(self, npi_number):
        """
        REAL LOGIC:
        1. Checks NPI format (10 digits).
        2. Runs Luhn Checksum (Mathematical validation).
        3. Queries CMS Government API.
        """
        print(f"🔍 [ValidationAgent] Validating NPI: {npi_number}")
        
        # 1. Sanity Check
        if not npi_number or len(npi_number) != 10 or not npi_number.isdigit():
            return {"official_name": "Invalid Format", "status": "Invalid Input"}

        # 2. Mathematical Checksum (Luhn Algorithm) - Core Logic
        if not self._luhn_check(npi_number):
            print("   ↳ [ValidationAgent] Luhn Checksum Failed (Fake NPI detected)")
            return {"official_name": "Fake NPI", "status": "Checksum Fail"}

        # 3. External API Call
        try:
            url = f"{self.base_url}?number={npi_number}&version=2.1"
            response = requests.get(url, timeout=5) # 5s timeout for safety
            data = response.json()
            
            if data.get("result_count", 0) > 0:
                res = data["results"][0]
                addr = res.get('addresses', [{}])[0]
                return {
                    "official_name": f"{res['basic']['first_name']} {res['basic']['last_name']}",
                    "official_phone": addr.get('telephone_number', 'N/A'),
                    "official_address": addr.get('address_1', 'N/A'),
                    "status": "Active"
                }
            return {"official_name": "Not Found", "status": "Not Found"}
        except Exception as e:
            print(f"❌ [ValidationAgent] API Error: {e}")
            return {"error": "Registry Unreachable"}

    def check_state_license(self, npi_number):
        """
        Treats the local JSON as a 'Cached State Database'.
        No sleep, just fast lookup.
        """
        print(f"📜 [ValidationAgent] Checking Local State License Cache for {npi_number}...")
        
        try:
            filename = 'mock_db.json' if os.path.exists('mock_db.json') else 'mock-db.json'
            # Fallback path logic
            if not os.path.exists(filename) and os.path.exists(f"../{filename}"):
                filename = f"../{filename}"

            with open(filename, 'r') as f:
                db = json.load(f)
                record = db.get(str(npi_number))
                
                if record:
                    return record
                else:
                    # Return "Unverified" instead of Active if not in DB
                    return {"state_license_status": "Unverified", "note": "Not in State DB"}
                    
        except Exception as e:
            return {"state_license_status": "Error", "note": str(e)}

    def _luhn_check(self, n):
        """
        Validates NPI using the Luhn algorithm.
        CRITICAL: CMS requires prefixing '80840' to the NPI before calculation.
        """
        # 1. Add the secret prefix
        full_number = "80840" + str(n)
        
        # 2. Run standard Luhn
        r = [int(ch) for ch in full_number][::-1]
        return (sum(r[0::2]) + sum(sum(divmod(d*2,10)) for d in r[1::2])) % 10 == 0