#!/usr/bin/env python3
"""
Test script for AI Image Generator API
Tests basic functionality without requiring real images
"""

import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8001/api"

def print_test(test_name: str, status: bool):
    """Print test result with emoji"""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {test_name}")

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        result = response.status_code == 200 and response.json().get("status") == "healthy"
        print_test("Health Check", result)
        if result:
            print(f"   Status: {response.json()}")
        return result
    except Exception as e:
        print_test("Health Check", False)
        print(f"   Error: {e}")
        return False

def test_history_endpoint():
    """Test history endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/history", timeout=5)
        result = response.status_code == 200
        print_test("History Endpoint", result)
        if result:
            data = response.json()
            print(f"   Found {data.get('count', 0)} images")
        return result
    except Exception as e:
        print_test("History Endpoint", False)
        print(f"   Error: {e}")
        return False

def test_directories():
    """Test that required directories exist"""
    backend_dir = Path("/app/backend")
    uploads_dir = backend_dir / "uploads"
    outputs_dir = backend_dir / "outputs"
    
    dirs_ok = all([
        backend_dir.exists(),
        uploads_dir.exists(),
        outputs_dir.exists()
    ])
    
    print_test("Required Directories", dirs_ok)
    if dirs_ok:
        print(f"   ✓ {backend_dir}")
        print(f"   ✓ {uploads_dir}")
        print(f"   ✓ {outputs_dir}")
    return dirs_ok

def test_hf_token():
    """Test Hugging Face token configuration"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        result = response.json().get("hf_token_configured", False)
        print_test("Hugging Face Token Configured", result)
        return result
    except Exception as e:
        print_test("Hugging Face Token Configured", False)
        print(f"   Error: {e}")
        return False

def main():
    print("=" * 60)
    print("  🧪 AI Image Generator - API Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        test_health_check,
        test_hf_token,
        test_directories,
        test_history_endpoint,
    ]
    
    results = []
    for test_func in tests:
        results.append(test_func())
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"  ✅ All tests passed! ({passed}/{total})")
        print("  🎉 System is ready for image generation!")
    else:
        print(f"  ⚠️  Some tests failed ({passed}/{total})")
        print("  Please check the errors above")
    
    print("=" * 60)
    print()
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
