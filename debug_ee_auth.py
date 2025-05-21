#!/usr/bin/env python
import os
import json
import sys
import ee

def debug_ee_auth():
    """Debug Earth Engine authentication issues on PythonAnywhere."""
    print("Earth Engine Authentication Debug Script")
    print("========================================")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"1. Current directory: {current_dir}")
    
    # Look for service-account.json
    service_account_path = os.path.join(current_dir, 'service-account.json')
    print(f"2. Looking for service account at: {service_account_path}")
    
    if not os.path.exists(service_account_path):
        print(f"   ✗ Service account file not found at {service_account_path}")
        # Try looking in parent directories
        parent_dir = os.path.dirname(current_dir)
        alt_path = os.path.join(parent_dir, 'service-account.json')
        print(f"   Checking alternative location: {alt_path}")
        if os.path.exists(alt_path):
            print(f"   ✓ Found service account file at alternative location")
            service_account_path = alt_path
        else:
            print(f"   ✗ Service account file not found at alternative location")
            print("Please make sure service-account.json is uploaded to the correct location.")
            return
    else:
        print(f"   ✓ Found service-account.json file at {service_account_path}")
    
    # Try to read the service account info
    try:
        print("3. Attempting to read service account file...")
        with open(service_account_path, 'r') as f:
            service_account_info = json.load(f)
        
        # Basic validation
        required_keys = ["type", "project_id", "private_key_id", "private_key", 
                         "client_email", "client_id", "auth_uri", "token_uri"]
        missing_keys = [key for key in required_keys if key not in service_account_info]
        
        if missing_keys:
            print(f"   ✗ Service account file is missing required keys: {', '.join(missing_keys)}")
            return
        
        print(f"   ✓ Service account file is valid JSON")
        print(f"   Service account: {service_account_info.get('client_email')}")
        print(f"   Project ID: {service_account_info.get('project_id')}")
    except json.JSONDecodeError:
        print(f"   ✗ Service account file is not valid JSON")
        return
    except Exception as e:
        print(f"   ✗ Error reading service account file: {str(e)}")
        return
    
    # Try Earth Engine authentication
    try:
        print("4. Testing Earth Engine authentication...")
        credentials = ee.ServiceAccountCredentials(
            service_account_info["client_email"], 
            service_account_path
        )
        ee.Initialize(credentials)
        print("   ✓ Authentication successful!")
        
        # Test a simple Earth Engine operation
        print("5. Testing Earth Engine with a simple operation...")
        image = ee.Image("LANDSAT/LC08/C02/T1_TOA/LC08_123032_20140515")
        info = image.getInfo()
        print(f"   ✓ Successfully retrieved image info. Image ID: {info.get('id')}")
        
        print("\nAUTHENTICATION DEBUG SUCCESSFUL!")
        print("Your service account file is valid and can authenticate with Earth Engine.")
        print("\nIf your web app is still failing:")
        print("1. Make sure the service-account.json file is in the correct location")
        print("2. Check file permissions (chmod 644 service-account.json)")
        print("3. Ensure your PythonAnywhere web app is using the same Python environment")
        print("4. Check your WSGI configuration file for correct paths")
    except Exception as e:
        print(f"   ✗ Authentication failed: {str(e)}")
        print("\nSuggestions:")
        print("1. Verify your service account has Earth Engine access")
        print("2. Check that the private key in the service account file is valid")
        print("3. Ensure your service account is properly set up in Google Cloud")

if __name__ == "__main__":
    debug_ee_auth() 