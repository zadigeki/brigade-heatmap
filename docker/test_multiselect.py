#!/usr/bin/env python3
"""
Test script for the multi-select alarm type filter functionality
"""
import sys
import json
import tempfile
import os
from web_server import AlarmHeatmapServer
from database import DatabaseManager
from config import DATABASE_CONFIG
from logging_config import setup_logging

def test_multiselect_filter():
    """Test the multi-select alarm type filter"""
    print("Testing Multi-Select Alarm Type Filter...")
    
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
        
        # Insert test alarms with different types using current time
        from datetime import datetime, timedelta
        now = datetime.now()
        
        test_alarms = [
            {
                'terid': 'TEST001',
                'gpstime': (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'altitude': 100, 'direction': 90,
                'gpslat': 40.7589, 'gpslng': -73.9851,
                'speed': 30, 'recordspeed': 30, 'state': 0,
                'time': (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'type': 13,  # Panic Button
                'content': 'Panic button pressed', 'cmdtype': 2
            },
            {
                'terid': 'TEST001',
                'gpstime': (now - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
                'altitude': 120, 'direction': 180,
                'gpslat': 40.7614, 'gpslng': -73.9776,
                'speed': 45, 'recordspeed': 45, 'state': 0,
                'time': (now - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
                'type': 17,  # G-Force
                'content': 'Hard braking detected', 'cmdtype': 2
            },
            {
                'terid': 'TEST001',
                'gpstime': (now - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S'),
                'altitude': 110, 'direction': 270,
                'gpslat': 40.7505, 'gpslng': -73.9934,
                'speed': 60, 'recordspeed': 60, 'state': 0,
                'time': (now - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S'),
                'type': 24,  # Overspeed
                'content': 'Speed limit exceeded', 'cmdtype': 2
            },
            {
                'terid': 'TEST001',
                'gpstime': (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'altitude': 95, 'direction': 45,
                'gpslat': 40.7580, 'gpslng': -73.9855,
                'speed': 25, 'recordspeed': 25, 'state': 0,
                'time': (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'type': 58,  # Driver Fatigue
                'content': 'Driver fatigue detected', 'cmdtype': 2
            }
        ]
        
        for alarm in test_alarms:
            db_manager.insert_alarm(alarm)
        
        # Create Flask test client
        server = AlarmHeatmapServer()
        client = server.app.test_client()
        
        # Test alarm types API
        response = client.get('/api/alarm-types')
        types_success = response.status_code == 200
        alarm_types_data = None
        if types_success:
            data = json.loads(response.data)
            types_success = data.get('success', False)
            alarm_types_data = data.get('alarm_types', [])
        print(f"  Alarm Types API test: {'PASS' if types_success else 'FAIL'}")
        
        # Test that we have the expected alarm types
        expected_types = [13, 17, 24, 58]
        found_types = [t['type'] for t in alarm_types_data if t['type'] in expected_types]
        types_match = len(found_types) == len(expected_types)
        print(f"  Expected alarm types found: {'PASS' if types_match else 'FAIL'}")
        
        # Check if data was actually inserted by querying database directly
        all_alarms_direct = db_manager.get_recent_alarms(hours=8760, limit=100)
        print(f"    DEBUG: Direct DB query returned {len(all_alarms_direct)} alarms")
        if all_alarms_direct:
            for alarm in all_alarms_direct[:3]:
                print(f"    DEBUG: DB Alarm ID {alarm.get('id')}: type={alarm.get('alarm_type')}, gps_time={alarm.get('gps_time')}")
        
        # First test without date filtering to see if data exists via API
        response = client.get('/api/alarms?hours=8760&limit=100')  # 1 year
        all_data_response = response.status_code == 200
        if all_data_response:
            data = json.loads(response.data)
            print(f"    DEBUG: All alarms API response: count={len(data.get('data', []))}")
            if data.get('data'):
                for alarm in data['data'][:3]:  # Show first 3 alarms
                    print(f"    DEBUG: API Alarm ID {alarm.get('id')}: type={alarm.get('alarm_type')}, time={alarm.get('gps_time')}")
        
        # Test filtering by single alarm type
        response = client.get('/api/alarms?hours=8760&alarm_types=13')  # Use 1 year to ensure we get data
        single_filter_success = response.status_code == 200
        if single_filter_success:
            data = json.loads(response.data)
            print(f"    DEBUG: Single filter response: success={data.get('success')}, count={len(data.get('data', []))}")
            if data.get('data'):
                print(f"    DEBUG: First alarm type: {data['data'][0].get('alarm_type')}")
            single_filter_success = (data.get('success', False) and 
                                   len(data.get('data', [])) >= 1 and
                                   all(alarm['alarm_type'] == 13 for alarm in data['data']))
        else:
            print(f"    DEBUG: Single filter HTTP error: {response.status_code}")
        print(f"  Single alarm type filter test: {'PASS' if single_filter_success else 'FAIL'}")
        
        # Test filtering by multiple alarm types
        response = client.get('/api/alarms?hours=24&alarm_types=13,17,24')
        multi_filter_success = response.status_code == 200
        if multi_filter_success:
            data = json.loads(response.data)
            multi_filter_success = (data.get('success', False) and 
                                  len(data.get('data', [])) == 3)
            if multi_filter_success:
                returned_types = [alarm['alarm_type'] for alarm in data['data']]
                multi_filter_success = all(t in [13, 17, 24] for t in returned_types)
        print(f"  Multiple alarm types filter test: {'PASS' if multi_filter_success else 'FAIL'}")
        
        # Test alarm type names mapping
        test_type_names = {
            13: "Panic Button",
            17: "G-Force", 
            24: "Overspeed",
            58: "Driver Fatigue",
            168: "Using Phone"  # Test a newer alarm type
        }
        
        names_success = True
        for alarm_type in alarm_types_data:
            if alarm_type['type'] in test_type_names:
                expected_name = test_type_names[alarm_type['type']]
                if not alarm_type['name'].startswith(expected_name):
                    names_success = False
                    break
        print(f"  Alarm type names mapping test: {'PASS' if names_success else 'FAIL'}")
        
        # Restore original database path
        DATABASE_CONFIG.db_path = original_path
        
        return all([
            types_success,
            types_match,
            single_filter_success,
            multi_filter_success,
            names_success
        ])
        
    except Exception as e:
        print(f"  Multi-select filter test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)

def main():
    """Run multi-select filter tests"""
    setup_logging('ERROR')  # Suppress logs during testing
    
    print("=== Multi-Select Alarm Type Filter Tests ===\n")
    
    test_result = test_multiselect_filter()
    
    print("\n=== Test Results ===")
    if test_result:
        print("All multi-select filter tests passed!")
        return 0
    else:
        print("Some multi-select filter tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())