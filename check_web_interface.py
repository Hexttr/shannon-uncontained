#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка веб-интерфейса для пентеста
"""
import paramiko
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER_HOST = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASSWORD = "m8J@2_6whwza6U"
SERVER_PORT = 22

def connect_to_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASSWORD, timeout=10)
        return ssh
    except Exception as e:
        print(f"[ERROR] Ошибка подключения: {e}")
        return None

def check_web_interface(ssh):
    """Проверка веб-интерфейса"""
    print("=" * 70)
    print("ПРОВЕРКА ВЕБ-ИНТЕРФЕЙСА ДЛЯ ПЕНТЕСТА")
    print("=" * 70)
    
    # 1. Поиск файлов веб-интерфейса
    print("\n1. ПОИСК ФАЙЛОВ ВЕБ-ИНТЕРФЕЙСА")
    print("-" * 70)
    commands = [
        ("web-interface.js", "ls -lh shannon-uncontained/web-interface.js 2>/dev/null || echo 'НЕ НАЙДЕНО'"),
        ("web-interface.cjs", "ls -lh shannon-uncontained/web-interface.cjs 2>/dev/null || echo 'НЕ НАЙДЕНО'"),
        ("start_web_interface.py", "ls -lh shannon-uncontained/start_web_interface.py 2>/dev/null || echo 'НЕ НАЙДЕНО'"),
        ("public директория", "ls -ld shannon-uncontained/public 2>/dev/null && echo 'НАЙДЕНО' || echo 'НЕ НАЙДЕНО'"),
    ]
    
    for desc, cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = stdout.read().decode('utf-8').strip()
        print(f"{desc}: {result}")
    
    # 2. Проверка конфигурации веб-интерфейса
    print("\n2. ПРОВЕРКА КОНФИГУРАЦИИ")
    print("-" * 70)
    
    # Проверяем web-interface.cjs
    stdin, stdout, stderr = ssh.exec_command("head -50 shannon-uncontained/web-interface.cjs 2>/dev/null | head -30")
    web_interface_head = stdout.read().decode('utf-8', errors='ignore')
    if web_interface_head:
        print("Начало web-interface.cjs:")
        print(web_interface_head)
    
    # Проверяем использование .env
    stdin, stdout, stderr = ssh.exec_command("grep -n 'process.env\|dotenv\|\.env' shannon-uncontained/web-interface.cjs 2>/dev/null | head -10")
    env_usage = stdout.read().decode('utf-8', errors='ignore')
    if env_usage:
        print("\nИспользование переменных окружения:")
        print(env_usage)
    
    # 3. Проверка порта и запуска
    print("\n3. ПРОВЕРКА ПОРТА И ПРОЦЕССОВ")
    print("-" * 70)
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'web-interface|node.*web|shannon.*web' | grep -v grep")
    processes = stdout.read().decode('utf-8', errors='ignore')
    if processes:
        print("Найденные процессы веб-интерфейса:")
        print(processes)
    else:
        print("Веб-интерфейс не запущен")
    
    # Проверка портов
    stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep -E ':3000|:8080|:5000|:8000' || ss -tlnp 2>/dev/null | grep -E ':3000|:8080|:5000|:8000' || echo 'Порты не найдены'")
    ports = stdout.read().decode('utf-8', errors='ignore')
    print(f"\nОткрытые порты веб-серверов:\n{ports}")
    
    # 4. Проверка package.json для веб-интерфейса
    print("\n4. ПРОВЕРКА ЗАВИСИМОСТЕЙ")
    print("-" * 70)
    stdin, stdout, stderr = ssh.exec_command("grep -E 'express|http-server|fastify|hono' shannon-uncontained/package.json 2>/dev/null | head -5")
    web_deps = stdout.read().decode('utf-8', errors='ignore')
    if web_deps:
        print("Веб-зависимости в package.json:")
        print(web_deps)
    else:
        print("Веб-зависимости не найдены в package.json")
    
    # 5. Проверка README для веб-интерфейса
    print("\n5. ДОКУМЕНТАЦИЯ")
    print("-" * 70)
    stdin, stdout, stderr = ssh.exec_command("grep -i 'web\|interface\|frontend' shannon-uncontained/WEB_INTERFACE_GUIDE.md 2>/dev/null | head -10 || echo 'Файл не найден'")
    web_docs = stdout.read().decode('utf-8', errors='ignore')
    print(web_docs)
    
    return True

def check_env_in_web_interface(ssh):
    """Проверка использования .env в веб-интерфейсе"""
    print("\n6. ПРОВЕРКА ИСПОЛЬЗОВАНИЯ .ENV В ВЕБ-ИНТЕРФЕЙСЕ")
    print("-" * 70)
    
    # Проверяем все файлы веб-интерфейса
    files_to_check = [
        "shannon-uncontained/web-interface.cjs",
        "shannon-uncontained/web-interface.js",
        "shannon-uncontained/start_web_interface.py",
    ]
    
    for file_path in files_to_check:
        stdin, stdout, stderr = ssh.exec_command(f"test -f {file_path} && echo 'EXISTS' || echo 'NOT_EXISTS'")
        exists = stdout.read().decode('utf-8').strip()
        
        if exists == "EXISTS":
            print(f"\nПроверка {file_path}:")
            # Ищем использование переменных окружения
            stdin, stdout, stderr = ssh.exec_command(f"grep -n 'LLM_PROVIDER\\|ANTHROPIC\\|process.env' {file_path} 2>/dev/null | head -10")
            env_vars = stdout.read().decode('utf-8', errors='ignore')
            if env_vars:
                print(env_vars)
            else:
                print("  Переменные окружения не найдены в этом файле")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_web_interface(ssh)
        check_env_in_web_interface(ssh)
        
        print("\n" + "=" * 70)
        print("ИТОГОВАЯ ПРОВЕРКА ВЕБ-ИНТЕРФЕЙСА")
        print("=" * 70)
        
        # Проверяем готовность
        stdin, stdout, stderr = ssh.exec_command("test -f shannon-uncontained/web-interface.cjs && echo 'OK' || echo 'NOT_FOUND'")
        web_file = stdout.read().decode('utf-8').strip()
        
        stdin, stdout, stderr = ssh.exec_command("test -f shannon-uncontained/.env && grep -q 'LLM_PROVIDER=anthropic' shannon-uncontained/.env && echo 'OK' || echo 'NOT_CONFIGURED'")
        env_config = stdout.read().decode('utf-8').strip()
        
        print(f"\n✅ Файл веб-интерфейса: {'Найден' if web_file == 'OK' else 'Не найден'}")
        print(f"{'✅' if env_config == 'OK' else '❌'} Конфигурация Claude API: {'Настроена' if env_config == 'OK' else 'Не настроена'}")
        
        if web_file == 'OK' and env_config == 'OK':
            print("\n🚀 ВЕБ-ИНТЕРФЕЙС ГОТОВ К РАБОТЕ С CLAUDE API!")
            print("\nДля запуска веб-интерфейса:")
            print("  cd shannon-uncontained")
            print("  node web-interface.cjs")
            print("\nИли используйте:")
            print("  python start_web_interface.py")
        else:
            print("\n⚠️ Требуется дополнительная настройка веб-интерфейса")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

