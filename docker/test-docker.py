#!/usr/bin/env python3
"""
Test Docker container functionality
"""
import sys
import json
import time
import requests
import subprocess
from datetime import datetime

def run_command(cmd, check=True):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode

def test_docker_build():
    """Test Docker image build"""
    print("🔨 Testing Docker image build...")
    
    stdout, stderr, code = run_command("docker build -t brigade-heatmap-test:latest .", check=False)
    
    if code == 0:
        print("✅ Docker image built successfully")
        return True
    else:
        print(f"❌ Docker build failed: {stderr}")
        return False

def test_container_start():
    """Test container startup"""
    print("🚀 Testing container startup...")
    
    # Stop any existing test container
    run_command("docker stop heatmap-test-container 2>/dev/null", check=False)
    run_command("docker rm heatmap-test-container 2>/dev/null", check=False)
    
    # Start test container
    cmd = """docker run -d --name heatmap-test-container \
        -p 5002:5000 \
        -e BRIGADE_API_URL=http://host.docker.internal:12056 \
        -e BRIGADE_USERNAME=admin \
        -e BRIGADE_PASSWORD=admin \
        -e DATABASE_PATH=/app/data/devices.db \
        brigade-heatmap-test:latest"""
    
    stdout, stderr, code = run_command(cmd, check=False)
    
    if code == 0:
        print("✅ Container started successfully")
        return True
    else:
        print(f"❌ Container start failed: {stderr}")
        return False

def test_service_health():
    """Test service health endpoint"""
    print("🏥 Testing service health...")
    
    # Wait for container to be ready
    print("   Waiting for service to start...")
    time.sleep(15)
    
    try:
        response = requests.get("http://localhost:5002/api/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Health check passed")
                print(f"   Statistics: {json.dumps(data.get('stats', {}), indent=2)}")
                return True
            else:
                print(f"❌ Health check failed: {data}")
                return False
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_web_interface():
    """Test web interface accessibility"""
    print("🌐 Testing web interface...")
    
    try:
        response = requests.get("http://localhost:5002/", timeout=10)
        if response.status_code == 200 and "Brigade Electronics" in response.text:
            print("✅ Web interface accessible")
            return True
        else:
            print(f"❌ Web interface test failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web interface test failed: {e}")
        return False

def cleanup_test_container():
    """Clean up test container"""
    print("🧹 Cleaning up test container...")
    
    # Get container logs first
    stdout, stderr, code = run_command("docker logs heatmap-test-container", check=False)
    if code == 0:
        print("📋 Container logs:")
        print(stdout)
    
    # Stop and remove container
    run_command("docker stop heatmap-test-container 2>/dev/null", check=False)
    run_command("docker rm heatmap-test-container 2>/dev/null", check=False)
    
    # Clean up test image
    run_command("docker rmi brigade-heatmap-test:latest 2>/dev/null", check=False)

def main():
    """Run Docker tests"""
    print("🐳 Brigade Electronics Heatmap - Docker Testing")
    print("=" * 50)
    
    tests = [
        ("Docker Build", test_docker_build),
        ("Container Start", test_container_start), 
        ("Service Health", test_service_health),
        ("Web Interface", test_web_interface)
    ]
    
    results = []
    
    try:
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name} test...")
            result = test_func()
            results.append((test_name, result))
            
            if not result:
                print(f"❌ {test_name} test failed, stopping tests")
                break
                
    finally:
        cleanup_test_container()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All Docker tests passed!")
        print("\nYour Docker container is ready for deployment!")
        print("\nTo deploy:")
        print("   ./deploy.sh")
        print("\nOr manually:")
        print("   docker-compose up -d")
        return 0
    else:
        print("\n❌ Some Docker tests failed!")
        print("Please check the errors above and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())