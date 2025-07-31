#!/usr/bin/env python3
"""
Test API connection to Brigade Electronics server
"""
import sys
from api_client import BrigadeAPIClient
from config import API_CONFIG

def test_api_connection():
    """Test the API connection"""
    print("Testing Brigade Electronics API Connection...")
    print(f"API URL: {API_CONFIG.base_url}")
    print(f"Username: {API_CONFIG.username}")
    print(f"Password: {'*' * len(API_CONFIG.password)}")
    
    try:
        # Create API client
        client = BrigadeAPIClient()
        
        # Test authentication
        print("\n1. Testing authentication...")
        if client.authenticate():
            print("SUCCESS: Authentication successful!")
            print(f"   Auth key: {client._auth_key}")
        else:
            print("FAILED: Authentication failed!")
            return False
        
        # Test device list
        print("\n2. Testing device list retrieval...")
        devices = client.get_devices()
        if devices is not None:
            print(f"SUCCESS: Device list retrieved successfully!")
            print(f"   Found {len(devices)} devices")
            if devices:
                print(f"   First device: {devices[0].get('terid', 'Unknown')} - {devices[0].get('carlicense', 'Unknown')}")
        else:
            print("FAILED: Failed to retrieve device list!")
            return False
        
        return True
        
    except Exception as e:
        print(f"ERROR: Connection test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_connection()
    if success:
        print("\nSUCCESS: API connection test passed!")
        print("You can now run: python main.py --command sync")
    else:
        print("\nFAILED: API connection test failed!")
        print("Please check your API configuration and network connectivity.")
    
    sys.exit(0 if success else 1)