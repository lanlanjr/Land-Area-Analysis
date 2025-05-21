#!/usr/bin/env python
import os
import json
import shutil
import stat

def fix_ee_auth():
    """Fix Earth Engine authentication issues on PythonAnywhere."""
    print("Earth Engine Authentication Fix Script")
    print("======================================")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"1. Current directory: {current_dir}")
    
    # Check for service-account.json in current directory
    service_account_path = os.path.join(current_dir, 'service-account.json')
    
    if not os.path.exists(service_account_path):
        print(f"   ✗ Service account file not found at {service_account_path}")
        print("Please upload service-account.json to this directory first.")
        return
    
    print(f"   ✓ Found service-account.json at {service_account_path}")
    
    # Make sure the file has the right permissions
    try:
        print("2. Setting correct file permissions (644)...")
        os.chmod(service_account_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        print("   ✓ Permissions set correctly")
    except Exception as e:
        print(f"   ✗ Failed to set permissions: {str(e)}")
    
    # Verify the file is valid JSON
    try:
        print("3. Verifying service account file...")
        with open(service_account_path, 'r') as f:
            service_account_info = json.load(f)
            
        required_keys = ["type", "project_id", "private_key_id", "private_key", 
                         "client_email", "client_id", "auth_uri", "token_uri"]
        missing_keys = [key for key in required_keys if key not in service_account_info]
        
        if missing_keys:
            print(f"   ✗ Service account file is missing required keys: {', '.join(missing_keys)}")
        else:
            print(f"   ✓ Service account file is valid")
            print(f"   Service account: {service_account_info.get('client_email')}")
    except json.JSONDecodeError:
        print(f"   ✗ Service account file is not valid JSON")
    except Exception as e:
        print(f"   ✗ Error reading service account file: {str(e)}")
    
    # Create a symbolic link in the parent directory (sometimes helps with path issues)
    try:
        print("4. Creating backup copy in home directory...")
        home_dir = os.path.expanduser("~")
        backup_path = os.path.join(home_dir, 'service-account.json')
        
        # Copy the file to the home directory
        shutil.copy2(service_account_path, backup_path)
        os.chmod(backup_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        print(f"   ✓ Created backup at {backup_path}")
    except Exception as e:
        print(f"   ✗ Failed to create backup: {str(e)}")
    
    print("\nFIX COMPLETED")
    print("Please restart your web app and check if the authentication is now working")
    print("If it's still not working, run the debug_ee_auth.py script for more diagnostics")

if __name__ == "__main__":
    fix_ee_auth() 