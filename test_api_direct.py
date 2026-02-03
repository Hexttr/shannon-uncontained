#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест API напрямую"""

import requests
import json
import sys
import time

url = "http://72.56.79.153:3000/api/run-test"
data = {"target": "https://tcell.tj"}

print("Отправка запроса...")
print(f"URL: {url}")
print(f"Data: {data}")

try:
    response = requests.post(url, json=data, stream=True, timeout=60)
    
    print(f"\nStatus: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("\nВывод (первые 10 секунд):\n")
    
    start_time = time.time()
    chunk_count = 0
    
    for line in response.iter_lines():
        if time.time() - start_time > 10:
            print("\n[Timeout after 10 seconds]")
            break
            
        if line:
            chunk_count += 1
            line_str = line.decode('utf-8', errors='ignore')
            print(f"[Chunk {chunk_count}] {line_str[:200]}")
            
            if line_str.startswith('data: '):
                try:
                    data_obj = json.loads(line_str[6:])
                    if data_obj.get('type') == 'done':
                        print(f"\n[TEST DONE] Code: {data_obj.get('code')}")
                        break
                except:
                    pass
    
    print(f"\n[INFO] Всего чанков: {chunk_count}")
    print(f"[INFO] Время: {time.time() - start_time:.2f} секунд")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()

