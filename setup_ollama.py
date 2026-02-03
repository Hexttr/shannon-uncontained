#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для установки и настройки Ollama на сервере
"""

import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"

def main():
    print("=" * 60)
    print("Ollama Setup for Shannon-Uncontained")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Проверка существующей установки
        print("[INFO] Проверка существующей установки Ollama...")
        stdin, stdout, stderr = client.exec_command("which ollama")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("[OK] Ollama уже установлен")
            ollama_path = stdout.read().decode('utf-8').strip()
            print(f"  Путь: {ollama_path}")
        else:
            print("[INFO] Ollama не установлен, начинаем установку...")
            
            # Установка Ollama
            print("\n[INFO] Установка Ollama...")
            install_cmd = "curl -fsSL https://ollama.com/install.sh | sh"
            stdin, stdout, stderr = client.exec_command(install_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                output = stdout.read().decode('utf-8')
                print("[OK] Ollama установлен")
            else:
                error = stderr.read().decode('utf-8')
                print(f"[ERROR] Ошибка установки: {error}")
                return
        
        # Запуск Ollama в фоне
        print("\n[INFO] Запуск Ollama сервера...")
        stdin, stdout, stderr = client.exec_command("pkill ollama || true")
        stdin, stdout, stderr = client.exec_command("nohup ollama serve > /tmp/ollama.log 2>&1 &")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("[OK] Ollama сервер запущен")
        else:
            print("[WARN] Возможна проблема с запуском Ollama")
        
        # Ожидание запуска сервера
        import time
        print("[INFO] Ожидание запуска сервера (5 секунд)...")
        time.sleep(5)
        
        # Проверка работы сервера
        print("\n[INFO] Проверка работы Ollama сервера...")
        stdin, stdout, stderr = client.exec_command("curl -s http://localhost:11434/api/tags")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            output = stdout.read().decode('utf-8')
            print("[OK] Ollama сервер работает")
            if output.strip():
                print(f"  Ответ: {output[:100]}...")
        else:
            print("[WARN] Сервер не отвечает, возможно требуется больше времени")
        
        # Загрузка рекомендуемых моделей
        print("\n[INFO] Загрузка моделей...")
        models = [
            "llama3.2",      # Базовая модель для тестов
            # "llama3.1:70b",  # Более мощная (раскомментируйте если нужно)
            # "codellama",     # Для генерации кода
        ]
        
        for model in models:
            print(f"  Загрузка {model}...")
            stdin, stdout, stderr = client.exec_command(f"ollama pull {model}")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                output = stdout.read().decode('utf-8')
                if "pulling" in output.lower() or "success" in output.lower():
                    print(f"    [OK] {model} загружена")
                else:
                    print(f"    [INFO] {model} уже загружена или в процессе")
            else:
                error = stderr.read().decode('utf-8')
                print(f"    [WARN] Ошибка загрузки {model}: {error[:100]}")
        
        # Список загруженных моделей
        print("\n[INFO] Список загруженных моделей:")
        stdin, stdout, stderr = client.exec_command("ollama list")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            output = stdout.read().decode('utf-8')
            print(output)
        
        # Настройка .env для Ollama
        print("\n[INFO] Настройка .env файла...")
        env_path = "/root/shannon-uncontained/.env"
        
        # Проверка существования .env
        stdin, stdout, stderr = client.exec_command(f"test -f {env_path} && echo 'exists' || echo 'not exists'")
        env_exists = stdout.read().decode('utf-8').strip() == 'exists'
        
        if env_exists:
            # Добавить или обновить настройки Ollama
            stdin, stdout, stderr = client.exec_command(
                f"grep -q 'LLM_PROVIDER=ollama' {env_path} && echo 'exists' || echo 'not exists'"
            )
            provider_exists = stdout.read().decode('utf-8').strip() == 'exists'
            
            if not provider_exists:
                stdin, stdout, stderr = client.exec_command(
                    f"echo '' >> {env_path} && echo '# Ollama configuration' >> {env_path} && "
                    f"echo 'LLM_PROVIDER=ollama' >> {env_path} && "
                    f"echo 'LLM_MODEL=llama3.2' >> {env_path}"
                )
                print("[OK] Настройки Ollama добавлены в .env")
            else:
                print("[INFO] Настройки Ollama уже присутствуют в .env")
        else:
            print(f"[WARN] Файл {env_path} не найден, создайте его вручную")
        
        # Тест работы модели
        print("\n[INFO] Тест работы модели...")
        stdin, stdout, stderr = client.exec_command("ollama run llama3.2 'Hello, this is a test' --verbose false")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            output = stdout.read().decode('utf-8')
            print("[OK] Модель работает")
            print(f"  Ответ: {output[:200]}...")
        else:
            print("[WARN] Тест не прошел, но это может быть нормально")
        
        print("\n" + "=" * 60)
        print("[OK] Настройка Ollama завершена!")
        print("=" * 60)
        print("\nСледующие шаги:")
        print("1. Проверьте .env файл: ssh root@72.56.79.153 'cat /root/shannon-uncontained/.env'")
        print("2. Для тестов используйте: LLM_PROVIDER=ollama LLM_MODEL=llama3.2")
        print("3. Для продакшена используйте: LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-...")
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

