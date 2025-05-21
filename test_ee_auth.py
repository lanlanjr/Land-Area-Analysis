import ee
import os
import json

print("Earth Engine Authentication Test Script")
print("======================================")

try:
    # Check for service-account.json
    if not os.path.exists('service-account.json'):
        print("ERROR: service-account.json file not found!")
        print("Please make sure the service-account.json file exists in the project root.")
        exit(1)
    
    print("1. Using service-account.json file")
    
    # Load the service account email from the JSON file
    with open('service-account.json', 'r') as f:
        service_account_info = json.load(f)
    
    service_account = service_account_info["client_email"]
    print(f"   Service account: {service_account}")
    
    credentials = ee.ServiceAccountCredentials(service_account, 'service-account.json')
    ee.Initialize(credentials)
    print("   Initialization successful!")
    
    # Test with a simple EE operation
    print("\n2. Testing Earth Engine with a simple operation...")
    image = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_123032_20140515')
    info = image.getInfo()
    print(f"   Successfully retrieved image info. Image ID: {info['id']}")
    
    print("\nAUTHENTICATION TEST SUCCESSFUL!")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    print("\nAUTHENTICATION TEST FAILED!")
    
    # For debugging - print if the file exists
    if os.path.exists('service-account.json'):
        print("Note: service-account.json exists, but may contain invalid credentials")
    else:
        print("Note: service-account.json does not exist") 