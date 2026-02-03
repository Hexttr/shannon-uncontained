#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная настройка сервера: проверка характеристик, установка Ollama, настройка .env
"""

import paramiko
import sys
import io
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def execute_command(client, command, description=""):
    """Выполнить команду и вернуть результат"""
    if description:
        print(f"[INFO] {description}...")
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def check_server_specs(client):
    """Проверка характеристик сервера"""
    print("\n" + "=" * 60)
    print("Проверка характеристик сервера")
    print("=" * 60)
    
    specs = {}
    
    # RAM
    exit_status, output, error = execute_command(client, "free -h | grep Mem")
    if exit_status == 0:
        parts = output.split()
        specs['ram_total'] = parts[1]
        specs['ram_available'] = parts[6] if len(parts) > 6 else parts[3]
        print(f"  RAM: {specs['ram_total']} (доступно: {specs['ram_available']})")
    
    # CPU
    exit_status, output, error = execute_command(client, "nproc")
    if exit_status == 0:
        specs['cpu_cores'] = int(output.strip())
        print(f"  CPU cores: {specs['cpu_cores']}")
    
    # RAM в GB для вычислений
    exit_status, output, error = execute_command(client, "free -g | grep Mem | awk '{print $2}'")
    if exit_status == 0:
        specs['ram_gb'] = int(output.strip())
        print(f"  RAM: {specs['ram_gb']} GB")
    
    # Диск
    exit_status, output, error = execute_command(client, "df -h / | tail -1 | awk '{print $4}'")
    if exit_status == 0:
        specs['disk_free'] = output.strip()
        print(f"  Свободно на диске: {specs['disk_free']}")
    
    return specs

def select_ollama_model(specs):
    """Выбор модели Ollama на основе характеристик сервера"""
    ram_gb = specs.get('ram_gb', 0)
    cpu_cores = specs.get('cpu_cores', 0)
    
    print("\n[INFO] Выбор модели Ollama...")
    
    # Рекомендации по моделям:
    # llama3.2 (3B) - минимум 4GB RAM
    # llama3.1:8b - минимум 8GB RAM
    # llama3.1:70b - минимум 40GB RAM
    # codellama:7b - минимум 8GB RAM
    # mistral:7b - минимум 8GB RAM
    
    if ram_gb >= 32:
        model = "llama3.1:70b"
        print(f"  Выбрана модель: {model} (требует ~40GB RAM)")
    elif ram_gb >= 16:
        model = "llama3.1:8b"
        print(f"  Выбрана модель: {model} (требует ~8GB RAM)")
    elif ram_gb >= 8:
        model = "codellama:7b"
        print(f"  Выбрана модель: {model} (требует ~8GB RAM)")
    else:
        model = "llama3.2"
        print(f"  Выбрана модель: {model} (требует ~4GB RAM)")
    
    return model

def install_ollama(client):
    """Установка Ollama"""
    print("\n" + "=" * 60)
    print("Установка Ollama")
    print("=" * 60)
    
    # Проверка существующей установки
    exit_status, output, error = execute_command(client, "which ollama")
    if exit_status == 0:
        print("[OK] Ollama уже установлен")
        return True
    
    # Установка
    print("[INFO] Установка Ollama...")
    exit_status, output, error = execute_command(
        client,
        "curl -fsSL https://ollama.com/install.sh | sh"
    )
    
    if exit_status == 0:
        print("[OK] Ollama установлен")
        return True
    else:
        print(f"[ERROR] Ошибка установки: {error}")
        return False

def start_ollama_service(client):
    """Запуск Ollama сервера"""
    print("\n[INFO] Запуск Ollama сервера...")
    
    # Остановка существующего процесса
    execute_command(client, "pkill ollama || true")
    time.sleep(2)
    
    # Запуск в фоне
    exit_status, output, error = execute_command(
        client,
        "nohup ollama serve > /tmp/ollama.log 2>&1 &"
    )
    
    # Ожидание запуска
    print("[INFO] Ожидание запуска сервера (5 секунд)...")
    time.sleep(5)
    
    # Проверка
    exit_status, output, error = execute_command(
        client,
        "curl -s http://localhost:11434/api/tags"
    )
    
    if exit_status == 0:
        print("[OK] Ollama сервер работает")
        return True
    else:
        print("[WARN] Сервер может быть еще не готов")
        return False

def download_model(client, model):
    """Загрузка модели"""
    print(f"\n[INFO] Загрузка модели {model}...")
    print("  Это может занять несколько минут...")
    
    exit_status, output, error = execute_command(
        client,
        f"ollama pull {model}"
    )
    
    if exit_status == 0:
        print(f"[OK] Модель {model} загружена")
        return True
    else:
        print(f"[ERROR] Ошибка загрузки: {error}")
        return False

def create_env_file(client, selected_model):
    """Создание .env файла со всеми возможными ключами"""
    print("\n" + "=" * 60)
    print("Настройка .env файла")
    print("=" * 60)
    
    env_content = f"""# ============================================
# Shannon-Uncontained LLM Configuration
# ============================================

# ============================================
# LLM Provider Selection
# ============================================
# Выберите один из провайдеров:
# - ollama (локальный, бесплатный для тестов)
# - anthropic (Claude для продакшена)
# - openai (GPT-4 для продакшена)
# - github (GitHub Models, бесплатный)
# - openrouter (множество моделей)
# - llamacpp (локальный llama.cpp)
# - lmstudio (локальный LM Studio)
# - custom (кастомный endpoint)

# Текущая настройка для тестов (Ollama)
LLM_PROVIDER=ollama
LLM_MODEL={selected_model}

# Для продакшена раскомментируйте одну из строк ниже:
# LLM_PROVIDER=anthropic
# LLM_PROVIDER=openai
# LLM_PROVIDER=github
# LLM_PROVIDER=openrouter

# ============================================
# Cloud Providers API Keys
# ============================================
# Раскомментируйте и заполните нужные ключи:

# Anthropic Claude (для продакшена)
# ANTHROPIC_API_KEY=sk-ant-your_key_here
# Получить ключ: https://console.anthropic.com/

# OpenAI (GPT-4, GPT-4o)
# OPENAI_API_KEY=sk-your_key_here
# Получить ключ: https://platform.openai.com/api-keys

# GitHub Models (бесплатный tier)
# GITHUB_TOKEN=ghp_your_token_here
# Получить токен: https://github.com/settings/tokens

# OpenRouter (доступ к множеству моделей)
# OPENROUTER_API_KEY=sk-or-your_key_here
# Получить ключ: https://openrouter.ai/keys

# ============================================
# Local Providers Configuration
# ============================================

# Ollama (локальный, для тестов)
# LLM_PROVIDER=ollama
# LLM_MODEL=llama3.2
# Endpoint: http://localhost:11434/v1

# llama.cpp (локальный)
# LLM_PROVIDER=llamacpp
# LLM_MODEL=local-model
# LLM_BASE_URL=http://localhost:8080/v1

# LM Studio (локальный)
# LLM_PROVIDER=lmstudio
# LLM_MODEL=local-model
# LLM_BASE_URL=http://localhost:1234/v1

# ============================================
# Custom Endpoint Configuration
# ============================================
# LLM_PROVIDER=custom
# LLM_BASE_URL=https://your-endpoint.com/v1
# LLM_MODEL=your-model-name

# ============================================
# Advanced Model Configuration
# ============================================
# Разные модели для разных задач:

# Базовая модель (используется по умолчанию)
# LLM_MODEL=gpt-4o                    # Для OpenAI
# LLM_MODEL=claude-3-5-sonnet-20241022  # Для Anthropic
# LLM_MODEL=llama3.2                  # Для Ollama

# Быстрая модель (для простых задач)
# LLM_FAST_MODEL=gpt-3.5-turbo        # Для OpenAI
# LLM_FAST_MODEL=claude-3-haiku-20240307  # Для Anthropic

# Умная модель (для сложных задач)
# LLM_SMART_MODEL=gpt-4o              # Для OpenAI
# LLM_SMART_MODEL=claude-3-5-sonnet-20241022  # Для Anthropic

# Модель для генерации кода
# LLM_CODE_MODEL=claude-3-5-sonnet-20241022  # Для Anthropic
# LLM_CODE_MODEL=gpt-4o               # Для OpenAI

# ============================================
# Claude 4.5 Sonnet Configuration
# ============================================
# Когда Claude 4.5 Sonnet станет доступен:
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-your_key_here
# LLM_MODEL=claude-4-5-sonnet-20250101

# ============================================
# Notes
# ============================================
# - Для тестов используйте Ollama (бесплатно)
# - Для продакшена используйте Claude 4.5 Sonnet или GPT-4
# - Все ключи закомментированы по умолчанию для безопасности
# - Раскомментируйте только нужные вам ключи
"""
    
    # Запись .env файла
    env_path = f"{PROJECT_PATH}/.env"
    
    # Создание директории если нужно
    execute_command(client, f"mkdir -p {PROJECT_PATH}")
    
    # Запись файла
    stdin, stdout, stderr = client.exec_command(f"cat > {env_path} << 'ENVEOF'\n{env_content}\nENVEOF")
    exit_status = stdout.channel.recv_exit_status()
    
    if exit_status == 0:
        print(f"[OK] .env файл создан: {env_path}")
        return True
    else:
        error = stderr.read().decode('utf-8')
        print(f"[ERROR] Ошибка создания .env: {error}")
        return False

def verify_setup(client, model):
    """Проверка настройки"""
    print("\n" + "=" * 60)
    print("Проверка настройки")
    print("=" * 60)
    
    # Проверка Ollama
    exit_status, output, error = execute_command(client, "ollama list")
    if exit_status == 0:
        print("[OK] Ollama работает")
        if model in output:
            print(f"  Модель {model} найдена")
        else:
            print(f"  [WARN] Модель {model} не найдена в списке")
    
    # Проверка .env
    exit_status, output, error = execute_command(client, f"test -f {PROJECT_PATH}/.env && echo 'exists'")
    if exit_status == 0 and 'exists' in output:
        print("[OK] .env файл существует")
        
        # Показать текущие настройки
        exit_status, output, error = execute_command(
            client,
            f"grep -E '^[^#]*LLM_' {PROJECT_PATH}/.env | head -5"
        )
        if exit_status == 0 and output.strip():
            print("  Текущие настройки:")
            for line in output.strip().split('\n'):
                print(f"    {line}")
    
    # Тест модели
    print("\n[INFO] Тест работы модели...")
    exit_status, output, error = execute_command(
        client,
        f"timeout 30 ollama run {model} 'Hello, test' 2>&1 | head -5"
    )
    if exit_status == 0:
        print("[OK] Модель отвечает")
        print(f"  Ответ: {output[:100]}...")
    else:
        print("[WARN] Тест не прошел, но это может быть нормально")

def main():
    print("=" * 60)
    print("Полная настройка Shannon-Uncontained")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # 1. Проверка характеристик
        specs = check_server_specs(client)
        
        # 2. Выбор модели
        selected_model = select_ollama_model(specs)
        
        # 3. Установка Ollama
        if not install_ollama(client):
            print("[ERROR] Не удалось установить Ollama")
            return
        
        # 4. Запуск сервера
        if not start_ollama_service(client):
            print("[WARN] Проблемы с запуском Ollama сервера")
        
        # 5. Загрузка модели
        if not download_model(client, selected_model):
            print("[ERROR] Не удалось загрузить модель")
            return
        
        # 6. Создание .env файла
        if not create_env_file(client, selected_model):
            print("[ERROR] Не удалось создать .env файл")
            return
        
        # 7. Проверка настройки
        verify_setup(client, selected_model)
        
        print("\n" + "=" * 60)
        print("[OK] Настройка завершена!")
        print("=" * 60)
        print(f"\nИспользуемая модель: {selected_model}")
        print(f"Файл конфигурации: {PROJECT_PATH}/.env")
        print("\nСледующие шаги:")
        print("1. Проверьте .env файл: ssh root@72.56.79.153 'cat /root/shannon-uncontained/.env'")
        print("2. Для продакшена раскомментируйте ANTHROPIC_API_KEY в .env")
        print("3. Запустите тест: ssh root@72.56.79.153 'cd /root/shannon-uncontained && ./shannon.mjs generate https://example.com'")
        
    except Exception as e:
        print(f"[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

