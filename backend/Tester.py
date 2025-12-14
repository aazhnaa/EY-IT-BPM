import utils

# 1. Define a real NPI number you found
real_npi = "1134527302"  # Replace with the one you found if different

print(f"--- Testing NPI API for {real_npi} ---")

# 2. Call your function
result = utils.fetch_npi_data(real_npi)

# 3. Print the result
if "error" in result:
    print("❌ Error:", result["error"])
    print("Tip: Check your internet connection or the API URL.")
else:
    print("✅ Success! Data fetched from Government API:")
    print(f"Name: {result.get('official_name')}")
    print(f"Address: {result.get('official_address')}")
    print(f"Phone: {result.get('official_phone')}")
    print(f"Status: {result.get('status')}")

    # OPTIONAL: Check your Mock DB logic
    print("\n--- Testing Mock DB Logic ---")
    mock_check = utils.validate_provider({"npi_number": real_npi})
    print("Mock DB Result:", mock_check['state_board'])


print("\n--- Testing Full Validation Logic (The Judge) ---")

# Simulate data coming from the PDF (Job 1)
# We will intentionally use a WRONG phone number to see if the score drops!
fake_extracted_data = {
    "npi_number": real_npi,
    "phone_number": "000-000-0000", # This is WRONG, so score should drop
    "provider_name": "Dr. Test"
}

# Run the Judge (Job 3)
final_report = utils.validate_provider(fake_extracted_data)

print(f"Final Score: {final_report['validation_result']['score']}")
print(f"Priority:    {final_report['validation_result']['priority']}")
print(f"Mismatches:  {final_report['validation_result']['mismatches']}")