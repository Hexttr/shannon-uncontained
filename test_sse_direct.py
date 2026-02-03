#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест SSE напрямую"""

import requests
import json
import sys

url = "http://72.56.79.153:3000/api/run-test"
data = {"target": "https://test.example.com"}

print("Отправка запроса...")
response = requests.post(url, json=data, stream=True, timeout=60)

print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print("\nВывод:\n")

try:
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            print(line_str, flush=True)
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'done':
                        print(f"\nЗавершено с кодом: {data.get('code')}")
                        break
                except:
                    pass
except Exception as e:
    print(f"Ошибка: {e}")

print("\nГотово")

