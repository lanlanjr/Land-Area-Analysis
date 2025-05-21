#!/usr/bin/env python
import ee
import os
import json

print("Earth Engine Service Account Verification Script")
print("===============================================")

try:
    print("1. Checking for service-account.json...")
    
    # Check for service-account.json
    if not os.path.exists('service-account.json'):
        print("   ✗ service-account.json file not found!")
        print("\nPlease make sure the service-account.json file exists in the project root.")
        exit(1)
    
    print("   ✓ Found service-account.json file")
    
    # Load the service account email from the JSON file
    with open('service-account.json', 'r') as f:
        service_account_info = json.load(f)
    
    service_account = service_account_info["client_email"]
    print(f"2. Service account: {service_account}")
    
    print("3. Testing authentication using service-account.json...")
    
    try:
        credentials = ee.ServiceAccountCredentials(service_account, 'service-account.json')
        ee.Initialize(credentials)
        print("   ✓ Authentication successful using service-account.json!")
    except Exception as e:
        print(f"   ✗ Authentication failed using service-account.json: {str(e)}")
        raise
    
    # Test with a simple EE operation
    print("\n4. Testing Earth Engine with a simple operation...")
    image = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_123032_20140515')
    info = image.getInfo()
    print(f"   ✓ Successfully retrieved image info. Image ID: {info['id']}")
    
    print("\nSERVICE ACCOUNT VERIFICATION SUCCESSFUL!")
    print("You can now deploy your application to a web server.")
    
except Exception as e:
    print(f"\nVERIFICATION FAILED: {str(e)}")
    
    # Provide more helpful information
    print("\nPossible issues and solutions:")
    print("1. Check that your service account has the necessary permissions for Earth Engine")
    print("2. Verify that the service account has been properly activated in the Google Cloud Console")
    print("3. Confirm the service-account.json file contains valid credentials")
    print("4. Make sure you have the latest version of the earthengine-api package installed")
    print("\nFor web deployment, you must use service account authentication, not interactive authentication.") 