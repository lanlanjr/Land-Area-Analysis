#!/usr/bin/env python
import os
import json
import ee
import glob

def try_alternative_auth():
    """Try alternative approaches for Earth Engine authentication."""
    print("Earth Engine Alternative Authentication Script")
    print("=============================================")
    
    # Get all possible locations for the service account file
    possible_locations = []
    
    # Current directory and parent
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_locations.append(os.path.join(current_dir, 'service-account.json'))
    possible_locations.append(os.path.join(os.path.dirname(current_dir), 'service-account.json'))
    
    # Home directory
    home_dir = os.path.expanduser("~")
    possible_locations.append(os.path.join(home_dir, 'service-account.json'))
    
    # PythonAnywhere specific locations
    possible_locations.append('/home/xekixaw298/service-account.json')
    possible_locations.append('/home/xekixaw298/Land-Area-Analysis/service-account.json')
    
    # Look in the entire home directory for any service-account.json files
    for potential_file in glob.glob(f"{home_dir}/**/service-account.json", recursive=True):
        if potential_file not in possible_locations:
            possible_locations.append(potential_file)
    
    print("1. Searching for service-account.json in possible locations:")
    found_files = []
    
    for location in possible_locations:
        if os.path.exists(location):
            print(f"   ✓ Found at: {location}")
            found_files.append(location)
        else:
            print(f"   ✗ Not found at: {location}")
    
    if not found_files:
        print("No service-account.json file found. Please upload it to your PythonAnywhere account.")
        return
    
    print(f"\n2. Attempting authentication with {len(found_files)} found file(s):")
    
    for service_account_path in found_files:
        try:
            print(f"\nTrying with: {service_account_path}")
            
            # Read the service account email from the JSON file
            with open(service_account_path, 'r') as f:
                service_account_info = json.load(f)
            
            service_account = service_account_info["client_email"]
            print(f"Service account email: {service_account}")
            
            # Try authentication
            credentials = ee.ServiceAccountCredentials(service_account, service_account_path)
            ee.Initialize(credentials)
            
            # Test a simple operation
            image = ee.Image("LANDSAT/LC08/C02/T1_TOA/LC08_123032_20140515")
            info = image.getInfo()
            
            print(f"SUCCESS! Authentication works with: {service_account_path}")
            print(f"Image ID: {info.get('id')}")
            print("\nFix for app.py:")
            print("================")
            print("1. Modify the service account path in app.py to use this exact path:")
            print(f"service_account_path = '{service_account_path}'")
            print("\n2. Replace the authentication code with:")
            print("try:")
            print(f"    service_account_path = '{service_account_path}'")
            print("    with open(service_account_path, 'r') as f:")
            print("        service_account_info = json.load(f)")
            print("    service_account = service_account_info['client_email']")
            print("    credentials = ee.ServiceAccountCredentials(service_account, service_account_path)")
            print("    ee.Initialize(credentials)")
            print("    print(f\"Earth Engine initialized with service account: {service_account}\")")
            print("except Exception as e:")
            print("    print(f\"Error initializing Earth Engine: {str(e)}\")")
            print("    raise RuntimeError(f\"Earth Engine authentication failed: {str(e)}\")")
            
            # No need to try other files if one works
            return
            
        except Exception as e:
            print(f"Authentication failed with {service_account_path}: {str(e)}")
    
    print("\nAll authentication attempts failed.")
    print("Recommendations:")
    print("1. Make sure your service account has Earth Engine access enabled")
    print("2. Verify the service-account.json file has the correct format and valid keys")
    print("3. Try uploading a fresh copy of the service-account.json file")
    print("4. Check for any permissions issues on PythonAnywhere")

if __name__ == "__main__":
    try_alternative_auth() 