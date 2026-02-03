#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обновление веб-интерфейса без SSH (через файл)"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Просто проверить что файл обновлен локально
with open('web-interface-simple.cjs', 'r', encoding='utf-8') as f:
    content = f.read()
    
if '--no-ai' in content:
    print("[ERROR] Флаг --no-ai все еще присутствует!")
    print("Нужно обновить файл на сервере вручную")
else:
    print("[OK] Локальный файл не содержит --no-ai")
    print("Файл готов к загрузке на сервер")

# Показать команду для обновления
print("\n" + "=" * 60)
print("ДЛЯ ОБНОВЛЕНИЯ НА СЕРВЕРЕ:")
print("=" * 60)
print("\nВыполните на сервере:")
print("cd /root/shannon-uncontained")
print("pkill -9 -f 'web-interface.cjs'")
print("nohup node web-interface.cjs > web-interface.log 2>&1 &")
print("\nИли загрузите файл web-interface-simple.cjs на сервер")

