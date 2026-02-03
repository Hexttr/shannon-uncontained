#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ состояния сервера для запуска пентеста через Ollama
"""
import paramiko
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

SERVER_IP = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASS = "m8J@2_6whwza6U"

def connect_server():
    """Подключение к серверу"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)
        return ssh
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return None

def execute_command(ssh, command):
    """Выполнение команды на сервере"""
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        return exit_status == 0, output, error
    except Exception as e:
        return False, "", str(e)

def check_file_exists(ssh, path):
    """Проверка существования файла"""
    success, output, _ = execute_command(ssh, f"test -f {path} && echo 'exists' || echo 'not_found'")
    return 'exists' in output

def check_dir_exists(ssh, path):
    """Проверка существования директории"""
    success, output, _ = execute_command(ssh, f"test -d {path} && echo 'exists' || echo 'not_found'")
    return 'exists' in output

def list_directory(ssh, path):
    """Список содержимого директории"""
    success, output, _ = execute_command(ssh, f"ls -la {path} 2>/dev/null || echo 'DIR_NOT_FOUND'")
    return output if 'DIR_NOT_FOUND' not in output else None

def analyze_server():
    """Основной анализ сервера"""
    print("=" * 80)
    print("🔍 АНАЛИЗ СЕРВЕРА ДЛЯ ЗАПУСКА ПЕНТЕСТА ЧЕРЕЗ OLLAMA")
    print("=" * 80)
    print()
    
    ssh = connect_server()
    if not ssh:
        return
    
    results = {
        'system': {},
        'nodejs': {},
        'ollama': {},
        'project': {},
        'tools': {},
        'env': {}
    }
    
    # 1. Системная информация
    print("📋 1. СИСТЕМНАЯ ИНФОРМАЦИЯ")
    print("-" * 80)
    success, output, _ = execute_command(ssh, "uname -a")
    if success:
        print(f"   OS: {output.strip()}")
        results['system']['os'] = output.strip()
    
    success, output, _ = execute_command(ssh, "free -h | head -2")
    if success:
        print(f"   RAM: {output.strip()}")
        results['system']['ram'] = output.strip()
    
    success, output, _ = execute_command(ssh, "df -h / | tail -1")
    if success:
        print(f"   Disk: {output.strip()}")
        results['system']['disk'] = output.strip()
    
    # 2. Node.js
    print("\n📦 2. NODE.JS")
    print("-" * 80)
    success, output, _ = execute_command(ssh, "node --version 2>/dev/null || echo 'NOT_INSTALLED'")
    if 'NOT_INSTALLED' in output:
        print("   ❌ Node.js не установлен")
        results['nodejs']['installed'] = False
    else:
        print(f"   ✅ Node.js: {output.strip()}")
        results['nodejs']['installed'] = True
        results['nodejs']['version'] = output.strip()
    
    success, output, _ = execute_command(ssh, "npm --version 2>/dev/null || echo 'NOT_INSTALLED'")
    if 'NOT_INSTALLED' not in output:
        print(f"   ✅ npm: {output.strip()}")
        results['nodejs']['npm_version'] = output.strip()
    
    # 3. Ollama
    print("\n🤖 3. OLLAMA")
    print("-" * 80)
    success, output, _ = execute_command(ssh, "which ollama 2>/dev/null || echo 'NOT_FOUND'")
    if 'NOT_FOUND' in output:
        print("   ❌ Ollama не установлен")
        results['ollama']['installed'] = False
    else:
        print(f"   ✅ Ollama найден: {output.strip()}")
        results['ollama']['installed'] = True
        
        # Проверка статуса сервиса
        success, output, _ = execute_command(ssh, "curl -s http://localhost:11434/api/tags 2>&1 | head -5")
        if 'connection refused' in output.lower() or 'failed' in output.lower():
            print("   ⚠️  Ollama сервис не запущен")
            results['ollama']['running'] = False
        else:
            print("   ✅ Ollama сервис работает")
            results['ollama']['running'] = True
            
            # Список моделей
            success, output, _ = execute_command(ssh, "ollama list 2>/dev/null || echo 'ERROR'")
            if 'ERROR' not in output:
                print(f"   Модели:\n{output}")
                results['ollama']['models'] = output
    
    # 4. Проект Shannon
    print("\n📁 4. ПРОЕКТ SHANNON-UNCONTAINED")
    print("-" * 80)
    
    possible_paths = [
        "/root/shannon-uncontained",
        "/root/shannon",
        "/opt/shannon-uncontained",
        "/home/root/shannon-uncontained"
    ]
    
    project_path = None
    for path in possible_paths:
        if check_dir_exists(ssh, path):
            project_path = path
            print(f"   ✅ Проект найден: {path}")
            results['project']['path'] = path
            break
    
    if not project_path:
        print("   ❌ Проект не найден в стандартных местах")
        results['project']['path'] = None
    else:
        # Проверка структуры проекта
        print(f"\n   Структура проекта:")
        
        # package.json
        if check_file_exists(ssh, f"{project_path}/package.json"):
            print("   ✅ package.json существует")
            results['project']['package_json'] = True
            
            # Версия и зависимости
            success, output, _ = execute_command(ssh, f"cd {project_path} && cat package.json | grep -A 5 '\"name\"' | head -10")
            if success:
                print(f"   {output.strip()[:200]}")
        else:
            print("   ❌ package.json не найден")
            results['project']['package_json'] = False
        
        # node_modules
        if check_dir_exists(ssh, f"{project_path}/node_modules"):
            print("   ✅ node_modules существует")
            results['project']['node_modules'] = True
        else:
            print("   ❌ node_modules не установлен")
            results['project']['node_modules'] = False
        
        # .env файл
        if check_file_exists(ssh, f"{project_path}/.env"):
            print("   ✅ .env файл существует")
            results['env']['exists'] = True
            
            # Проверка конфигурации Ollama
            success, output, _ = execute_command(ssh, f"cd {project_path} && grep -E 'LLM_PROVIDER|LLM_MODEL|OLLAMA' .env 2>/dev/null || echo 'NO_OLLAMA_CONFIG'")
            if 'NO_OLLAMA_CONFIG' not in output and output.strip():
                print(f"   Конфигурация:\n{output}")
                results['env']['ollama_config'] = output
            else:
                print("   ⚠️  Ollama не настроен в .env")
                results['env']['ollama_config'] = None
        else:
            print("   ❌ .env файл не найден")
            results['env']['exists'] = False
        
        # Основные файлы
        files_to_check = [
            "shannon.mjs",
            "local-source-generator.mjs",
            "src/ai/llm-client.js"
        ]
        
        print(f"\n   Критичные файлы:")
        for file in files_to_check:
            if check_file_exists(ssh, f"{project_path}/{file}"):
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} отсутствует")
    
    # 5. Инструменты пентестинга
    print("\n🔧 5. ИНСТРУМЕНТЫ ПЕНТЕСТИНГА")
    print("-" * 80)
    
    tools = {
        'nmap': 'nmap --version 2>/dev/null | head -1',
        'go': 'go version 2>/dev/null',
        'subfinder': 'subfinder -version 2>/dev/null | head -1',
        'katana': 'katana -version 2>/dev/null | head -1',
        'nuclei': 'nuclei -version 2>/dev/null | head -1',
        'whatweb': 'whatweb --version 2>/dev/null | head -1',
        'python3': 'python3 --version 2>/dev/null',
    }
    
    for tool, cmd in tools.items():
        success, output, _ = execute_command(ssh, cmd)
        if success and output.strip():
            print(f"   ✅ {tool}: {output.strip()[:50]}")
            results['tools'][tool] = True
        else:
            print(f"   ❌ {tool}: не установлен")
            results['tools'][tool] = False
    
    # 6. Порты и сервисы
    print("\n🌐 6. ПОРТЫ И СЕРВИСЫ")
    print("-" * 80)
    success, output, _ = execute_command(ssh, "netstat -tlnp 2>/dev/null | grep -E ':(11434|3000|8080)' || ss -tlnp 2>/dev/null | grep -E ':(11434|3000|8080)' || echo 'NO_MATCH'")
    if 'NO_MATCH' not in output and output.strip():
        print(f"   Открытые порты:\n{output}")
    else:
        print("   Порты 11434 (Ollama), 3000, 8080 не найдены")
    
    ssh.close()
    
    # Резюме
    print("\n" + "=" * 80)
    print("📊 РЕЗЮМЕ И РЕКОМЕНДАЦИИ")
    print("=" * 80)
    
    recommendations = []
    
    if not results.get('nodejs', {}).get('installed'):
        recommendations.append("1. Установить Node.js 18+ и npm")
    
    if not results.get('ollama', {}).get('installed'):
        recommendations.append("2. Установить Ollama: curl -fsSL https://ollama.com/install.sh | sh")
    
    if results.get('ollama', {}).get('installed') and not results.get('ollama', {}).get('running'):
        recommendations.append("3. Запустить Ollama: ollama serve (в фоне или через systemd)")
    
    if results.get('ollama', {}).get('installed') and not results.get('ollama', {}).get('models'):
        recommendations.append("4. Загрузить модель: ollama pull llama3.2")
    
    if not results.get('project', {}).get('path'):
        recommendations.append("5. Клонировать репозиторий: git clone https://github.com/Hexttr/shannon-uncontained.git")
    
    if results.get('project', {}).get('path') and not results.get('project', {}).get('node_modules'):
        recommendations.append("6. Установить зависимости: cd <project_path> && npm install")
    
    if not results.get('env', {}).get('exists'):
        recommendations.append("7. Создать .env файл с настройками Ollama")
    
    if results.get('env', {}).get('exists') and not results.get('env', {}).get('ollama_config'):
        recommendations.append("8. Настроить .env: LLM_PROVIDER=ollama, LLM_MODEL=llama3.2")
    
    missing_tools = [tool for tool, installed in results.get('tools', {}).items() if not installed]
    if missing_tools:
        recommendations.append(f"9. Установить недостающие инструменты: {', '.join(missing_tools)}")
    
    if recommendations:
        print("\n⚠️  НЕОБХОДИМЫЕ ДЕЙСТВИЯ:\n")
        for rec in recommendations:
            print(f"   {rec}")
    else:
        print("\n✅ Все компоненты готовы к запуску!")
    
    print("\n" + "=" * 80)
    
    return results

if __name__ == "__main__":
    try:
        analyze_server()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

