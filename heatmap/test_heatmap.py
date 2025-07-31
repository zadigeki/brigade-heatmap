#!/usr/bin/env python3
"""
Test script for the alarm heatmap functionality
"""
import sys
import json
import tempfile
import os
from unittest.mock import patch
from web_server import AlarmHeatmapServer
from database import DatabaseManager
from config import DATABASE_CONFIG
from logging_config import setup_logging

def test_heatmap_api():
    """Test the heatmap API endpoints"""
    print("Testing Heatmap API endpoints...")
    
    # Create temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Patch database path
        original_path = DATABASE_CONFIG.db_path
        DATABASE_CONFIG.db_path = temp_db.name
        
        # Initialize database with test data
        db_manager = DatabaseManager()
        
        # Insert test device
        test_device = {
            'carlicense': 'TEST123',
            'terid': 'TEST001',
            'sim': '1234567890',
            'channel': 4,
            'platecolor': 1,
            'groupid': 1,
            'cname': 'Test Device',
            'devicetype': '4',
            'linktype': '124',
            'companyname': 'Test Company'
        }
        db_manager.upsert_device(test_device)
        
        # Insert test alarms with GPS coordinates
        test_alarms = [
            {
                'terid': 'TEST001',
                'gpstime': '2024-01-15 10:30:00',
                'altitude': 100,
                'direction': 90,
                'gpslat': 40.7589,
                'gpslng': -73.9851,
                'speed': 30,
                'recordspeed': 30,
                'state': 0,
                'time': '2024-01-15 10:30:01',
                'type': 13,  # Panic button
                'content': 'Panic button pressed',
                'cmdtype': 2
            },
            {
                'terid': 'TEST001',
                'gpstime': '2024-01-15 11:00:00',
                'altitude': 120,
                'direction': 180,
                'gpslat': 40.7614,
                'gpslng': -73.9776,
                'speed': 45,
                'recordspeed': 45,
                'state': 0,
                'time': '2024-01-15 11:00:01',
                'type': 17,  # G-Force
                'content': 'Hard braking detected',
                'cmdtype': 2
            }
        ]
        
        for alarm in test_alarms:
            db_manager.insert_alarm(alarm)
        
        # Create Flask test client
        server = AlarmHeatmapServer()
        client = server.app.test_client()
        
        # Test main page
        response = client.get('/')
        print(f"  Main page test: {'PASS' if response.status_code == 200 else 'FAIL'}")
        
        # Test alarms API
        response = client.get('/api/alarms?hours=24&limit=100')
        alarms_success = response.status_code == 200
        if alarms_success:
            data = json.loads(response.data)
            alarms_success = data.get('success', False) and len(data.get('data', [])) > 0
        print(f"  Alarms API test: {'PASS' if alarms_success else 'FAIL'}")
        
        # Test devices API
        response = client.get('/api/devices')
        devices_success = response.status_code == 200
        if devices_success:
            data = json.loads(response.data)
            devices_success = data.get('success', False) and len(data.get('devices', [])) > 0
        print(f"  Devices API test: {'PASS' if devices_success else 'FAIL'}")
        
        # Test alarm types API
        response = client.get('/api/alarm-types')
        types_success = response.status_code == 200
        if types_success:
            data = json.loads(response.data)
            types_success = data.get('success', False)
        print(f"  Alarm Types API test: {'PASS' if types_success else 'FAIL'}")
        
        # Test alarm detail API
        response = client.get('/api/alarm/1')
        detail_success = response.status_code == 200
        if detail_success:
            data = json.loads(response.data)
            detail_success = data.get('success', False) and data.get('alarm') is not None
        print(f"  Alarm Detail API test: {'PASS' if detail_success else 'FAIL'}")
        
        # Test stats API
        response = client.get('/api/stats')
        stats_success = response.status_code == 200
        if stats_success:
            data = json.loads(response.data)
            stats_success = data.get('success', False)
        print(f"  Stats API test: {'PASS' if stats_success else 'FAIL'}")
        
        # Restore original database path
        DATABASE_CONFIG.db_path = original_path
        
        return all([
            alarms_success,
            devices_success, 
            types_success,
            detail_success,
            stats_success
        ])
        
    except Exception as e:
        print(f"  Heatmap API test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)

def test_heatmap_data_conversion():
    """Test alarm data conversion to heatmap format"""
    print("Testing Heatmap Data Conversion...")
    
    try:
        server = AlarmHeatmapServer()
        
        # Test data conversion
        test_alarms = [
            {
                'id': 1,
                'terid': 'TEST001',
                'gps_lat': 40.7589,
                'gps_lng': -73.9851,
                'alarm_type': 13,
                'alarm_content': 'Panic button',
                'gps_time': '2024-01-15 10:30:00',
                'speed': 30,
                'altitude': 100,
                'direction': 90
            },
            {
                'id': 2,
                'terid': 'TEST001',
                'gps_lat': 0,  # Invalid coordinate
                'gps_lng': 0,  # Invalid coordinate
                'alarm_type': 17,
                'alarm_content': 'G-Force',
                'gps_time': '2024-01-15 11:00:00',
                'speed': 45,
                'altitude': 120,
                'direction': 180
            }
        ]
        
        heatmap_data = server._convert_to_heatmap_format(test_alarms)
        
        # Should only include the valid coordinate alarm
        conversion_success = len(heatmap_data) == 1 and heatmap_data[0]['id'] == 1
        print(f"  Data conversion test: {'PASS' if conversion_success else 'FAIL'}")
        
        # Test intensity calculation
        intensity = server._get_alarm_intensity(13)  # Panic button
        intensity_success = intensity == 1.0  # Should be highest intensity
        print(f"  Intensity calculation test: {'PASS' if intensity_success else 'FAIL'}")
        
        return conversion_success and intensity_success
        
    except Exception as e:
        print(f"  Data conversion test failed: {e}")
        return False

def main():
    """Run heatmap tests"""
    setup_logging('ERROR')  # Suppress logs during testing
    
    print("=== Brigade Electronics Alarm Heatmap Tests ===\n")
    
    tests = [
        test_heatmap_api,
        test_heatmap_data_conversion
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  Test failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=== Heatmap Test Results ===")
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("All heatmap tests passed! ✅")
        return 0
    else:
        print("Some heatmap tests failed! ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())