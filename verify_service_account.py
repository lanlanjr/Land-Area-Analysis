#!/usr/bin/env python
import ee
import os
import json
from dotenv import load_dotenv

print("Earth Engine Service Account Verification Script")
print("===============================================")

# Load environment variables
print("1. Loading environment variables...")
load_dotenv()
print("   .env file loaded")

# Verify the necessary environment variables exist
required_vars = [
    "GEE_TYPE", "GEE_PROJECT_ID", "GEE_PRIVATE_KEY_ID", "GEE_PRIVATE_KEY",
    "GEE_CLIENT_EMAIL", "GEE_CLIENT_ID", "GEE_AUTH_URI", "GEE_TOKEN_URI",
    "GEE_AUTH_PROVIDER_X509_CERT_URL", "GEE_CLIENT_X509_CERT_URL", "GEE_UNIVERSE_DOMAIN"
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print("\nERROR: The following required environment variables are missing:")
    for var in missing_vars:
        print(f"  - {var}")
    print("\nPlease make sure these variables are defined in your .env file.")
    exit(1)

try:
    # Process the private key from environment
    private_key = os.getenv("GEE_PRIVATE_KEY", "")
    # If the private key has \n literals, replace them with actual newlines
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n") 
    # If the private key is surrounded by quotes, remove them
    if private_key.startswith('"') and private_key.endswith('"'):
        private_key = private_key[1:-1]
    
    service_account = os.getenv("GEE_CLIENT_EMAIL")
    
    print(f"2. Service account: {service_account}")
    print("3. Checking for service-account.json...")
    
    # Check for service-account.json
    if os.path.exists('service-account.json'):
        print("   Found service-account.json file")
        print("4. Testing authentication using service-account.json...")
        
        try:
            credentials = ee.ServiceAccountCredentials(service_account, 'service-account.json')
            ee.Initialize(credentials)
            print("   ✓ Authentication successful using service-account.json!")
        except Exception as e:
            print(f"   ✗ Authentication failed using service-account.json: {str(e)}")
            raise
    
    # Always try environment variables as well, even if service-account.json exists
    print("5. Testing authentication using environment variables...")
    
    try:
        # Create credentials dictionary
        credentials = {
            "type": os.getenv("GEE_TYPE"),
            "project_id": os.getenv("GEE_PROJECT_ID"),
            "private_key_id": os.getenv("GEE_PRIVATE_KEY_ID"),
            "private_key": private_key,
            "client_email": service_account,
            "client_id": os.getenv("GEE_CLIENT_ID"),
            "auth_uri": os.getenv("GEE_AUTH_URI"),
            "token_uri": os.getenv("GEE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("GEE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("GEE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("GEE_UNIVERSE_DOMAIN")
        }
        
        # Initialize Earth Engine
        credentials_object = ee.ServiceAccountCredentials(service_account, key_data=json.dumps(credentials))
        ee.Initialize(credentials_object)
        print("   ✓ Authentication successful using environment variables!")
    except Exception as e:
        print(f"   ✗ Authentication failed using environment variables: {str(e)}")
        raise
    
    # Test with a simple EE operation
    print("\n6. Testing Earth Engine with a simple operation...")
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
    print("3. Make sure your .env file has the correct format for the private key")
    print("4. Confirm the service-account.json file contains valid credentials")
    print("5. Make sure you have the latest version of the earthengine-api package installed")
    print("\nFor web deployment, you must use service account authentication, not interactive authentication.") 