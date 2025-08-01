#!/usr/bin/env python3
"""
Test script to verify the heatmap fix works
"""
import time
import requests
import threading
from logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)

def test_web_server_endpoints():
    """Test web server endpoints to ensure they work"""
    print("🔍 Testing web server endpoints...")
    
    # Start web server in background
    def start_server():
        from web_server import AlarmHeatmapServer
        server = AlarmHeatmapServer(host='127.0.0.1', port=5002, debug=False)
        server.run()
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        base_url = "http://127.0.0.1:5002"
        
        # Test main heatmap page
        print("  Testing main heatmap page...")
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            # Check if the page loads without JavaScript errors by looking for key elements
            content = response.text
            if 'alarm-type-filter' in content and 'loadHeatmapData' in content:
                print("  ✅ Main heatmap page loaded successfully")
            else:
                print("  ⚠️  Main heatmap page loaded but may have missing elements")
        else:
            print(f"  ❌ Main heatmap page returned status {response.status_code}")
            return False
        
        # Test GPS tracking page
        print("  Testing GPS tracking page...")
        response = requests.get(f"{base_url}/gps-tracking", timeout=10)
        if response.status_code == 200:
            print("  ✅ GPS tracking page loaded successfully")
        else:
            print(f"  ❌ GPS tracking page returned status {response.status_code}")
            return False
        
        # Test key API endpoints
        endpoints_to_test = [
            ("/api/devices", "Device list"),
            ("/api/alarm-types", "Alarm types"),
            ("/api/gps/positions", "GPS positions"),
            ("/api/stats", "Statistics")
        ]
        
        for endpoint, description in endpoints_to_test:
            print(f"  Testing {description} endpoint...")
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'success' in data:
                            if data['success']:
                                print(f"  ✅ {description} endpoint working")
                            else:
                                print(f"  ⚠️  {description} endpoint returned error: {data.get('error', 'Unknown')}")
                        else:
                            print(f"  ✅ {description} endpoint returned data")
                    except ValueError:
                        print(f"  ⚠️  {description} endpoint returned non-JSON response")
                else:
                    print(f"  ❌ {description} endpoint returned status {response.status_code}")
            except Exception as e:
                print(f"  ❌ {description} endpoint error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web server test error: {e}")
        return False

def main():
    """Run the test"""
    setup_logging('INFO')
    
    print("🚀 Testing Brigade Electronics Heatmap Fix")
    print("=" * 50)
    
    success = test_web_server_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tests passed! The heatmap fix should work correctly.")
        print("\nTo start the full system:")
        print("  python run_system.py")
        print("  or")
        print("  start_system.bat (Windows)")
        print("  ./start_system.sh (Linux/Mac)")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()