import ee
import os
import json
from dotenv import load_dotenv

print("Earth Engine Authentication Test Script")
print("======================================")

# Load environment variables
print("1. Loading environment variables...")
load_dotenv()
print("   .env file loaded")

try:
    # Try to use service-account.json first if it exists
    if os.path.exists('service-account.json'):
        print("2. Using service-account.json file")
        service_account = os.getenv("GEE_CLIENT_EMAIL")
        credentials = ee.ServiceAccountCredentials(service_account, 'service-account.json')
        ee.Initialize(credentials)
        print("   Initialization successful!")
    else:
        # If not available, use the environment variables
        print("2. Using environment variables for authentication")
        
        service_account = os.getenv("GEE_CLIENT_EMAIL")
        print(f"   Service account: {service_account}")
        
        # Get private key and properly format it
        private_key = os.getenv("GEE_PRIVATE_KEY", "")
        # If the private key has \n literals, replace them with actual newlines
        if "\\n" in private_key:
            private_key = private_key.replace("\\n", "\n") 
        # If the private key is surrounded by quotes, remove them
        if private_key.startswith('"') and private_key.endswith('"'):
            private_key = private_key[1:-1]
        
        print(f"   Private key: {'*****[REDACTED]*****'}")
        
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
        
        print("   Created credentials dictionary")
        
        # Initialize Earth Engine
        credentials_object = ee.ServiceAccountCredentials(service_account, key_data=json.dumps(credentials))
        ee.Initialize(credentials_object)
        print("   Initialization successful!")
    
    # Test with a simple EE operation
    print("\n3. Testing Earth Engine with a simple operation...")
    image = ee.Image('LANDSAT/LC08/C02/T1_TOA/LC08_123032_20140515')
    info = image.getInfo()
    print(f"   Successfully retrieved image info. Image ID: {info['id']}")
    
    print("\nAUTHENTICATION TEST SUCCESSFUL!")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    print("\nAUTHENTICATION TEST FAILED!")
    
    # For debugging - print if the file exists
    if os.path.exists('service-account.json'):
        print("Note: service-account.json exists")
    else:
        print("Note: service-account.json does not exist")
        
    # List all environment variables that start with GEE_
    print("\nEnvironment Variables:")
    for key, value in os.environ.items():
        if key.startswith('GEE_'):
            if 'KEY' in key:
                print(f"{key}: *****[REDACTED]*****")
            else:
                print(f"{key}: {value}") 