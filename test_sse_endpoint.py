#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование SSE endpoint напрямую
"""
import requests
import sys

SERVER_IP = "72.56.79.153"

def test_sse():
    print("=" * 80)
    print("TESTING SSE ENDPOINT")
    print("=" * 80)
    
    url = f"http://{SERVER_IP}:3000/api/run-test?target=https://example.com"
    
    print(f"\nConnecting to: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        
        print(f"\nReading data...")
        count = 0
        for line in response.iter_lines():
            if line:
                count += 1
                decoded = line.decode('utf-8', errors='ignore')
                print(f"   [{count}] {decoded[:200]}")
                if count >= 10:
                    print("   ... (limited to 10 lines)")
                    break
            if count >= 10:
                break
        
        if count == 0:
            print("   WARNING: No data received")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sse()

