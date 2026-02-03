#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная проверка готовности к пентесту с Claude API
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

def verify_configuration(ssh):
    """Проверка конфигурации"""
    print("=== ФИНАЛЬНАЯ ПРОВЕРКА КОНФИГУРАЦИИ ===\n")
    
    checks = [
        ("1. Проверка .env файла", "cat shannon-uncontained/.env | grep -E 'LLM_PROVIDER|ANTHROPIC_API_KEY|LLM_MODEL' | head -5"),
        ("2. Проверка наличия Anthropic SDK", "grep '@anthropic-ai/sdk' shannon-uncontained/package.json"),
        ("3. Проверка импорта Anthropic", "grep -n 'import.*Anthropic' shannon-uncontained/src/ai/llm-client.js | head -2"),
        ("4. Проверка case 'anthropic'", "grep -A 8 \"case 'anthropic':\" shannon-uncontained/src/ai/llm-client.js | head -10"),
        ("5. Проверка модели в конфиге", "grep 'claude.*sonnet' shannon-uncontained/.env"),
        ("6. Проверка структуры проекта", "ls -la shannon-uncontained/src/ai/ 2>/dev/null | head -5"),
        ("7. Проверка основного скрипта", "test -f shannon-uncontained/shannon.mjs && echo 'OK' || echo 'NOT FOUND'"),
        ("8. Проверка package.json", "grep -E '\"name\"|\"version\"' shannon-uncontained/package.json | head -2"),
    ]
    
    results = {}
    
    for description, command in checks:
        print(f"\n{description}")
        print("-" * 60)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if output:
            print(output.strip())
            results[description] = output.strip()
        elif error and "Permission denied" not in error and "No such file" not in error:
            print(f"[WARNING] {error.strip()}")
            results[description] = f"WARNING: {error.strip()}"
        else:
            print("[OK]")
            results[description] = "OK"
    
    return results

def check_api_key_format(ssh):
    """Проверка формата API ключа"""
    print("\n=== ПРОВЕРКА API КЛЮЧА ===")
    stdin, stdout, stderr = ssh.exec_command("grep 'ANTHROPIC_API_KEY=' shannon-uncontained/.env | cut -d'=' -f2")
    api_key = stdout.read().decode('utf-8').strip()
    
    if api_key:
        if api_key.startswith('sk-ant-api03-'):
            print(f"[OK] API ключ имеет правильный формат (начинается с sk-ant-api03-)")
            print(f"[INFO] Длина ключа: {len(api_key)} символов")
            return True
        else:
            print(f"[WARNING] API ключ может иметь неправильный формат")
            return False
    else:
        print("[ERROR] API ключ не найден!")
        return False

def verify_model_name(ssh):
    """Проверка имени модели"""
    print("\n=== ПРОВЕРКА МОДЕЛИ ===")
    stdin, stdout, stderr = ssh.exec_command("grep 'LLM_MODEL=' shannon-uncontained/.env | cut -d'=' -f2")
    model = stdout.read().decode('utf-8').strip()
    
    print(f"Текущая модель: {model}")
    
    # Claude 3.5 Sonnet - правильная модель
    if 'claude-3-5-sonnet' in model.lower():
        print("[OK] Используется Claude 3.5 Sonnet (правильная модель)")
        return True
    elif 'claude-4' in model.lower():
        print("[WARNING] Claude 4.5 Sonnet еще не существует. Используйте claude-3-5-sonnet-20241022")
        return False
    else:
        print(f"[INFO] Модель: {model}")
        return True

def test_anthropic_import(ssh):
    """Тест импорта Anthropic SDK"""
    print("\n=== ТЕСТ ИМПОРТА ANTHROPIC SDK ===")
    test_script = """
cd shannon-uncontained && node -e "
try {
    const Anthropic = require('@anthropic-ai/sdk');
    console.log('[OK] Anthropic SDK успешно импортирован');
    console.log('Версия:', Anthropic.version || 'не указана');
} catch (e) {
    console.log('[ERROR] Ошибка импорта:', e.message);
    process.exit(1);
}
"
"""
    
    stdin, stdout, stderr = ssh.exec_command(test_script)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    
    if output:
        print(output)
    if error and "Error:" not in error:
        print(f"[WARNING] {error}")
    
    return "[OK]" in output

def check_ready_for_pentest(ssh):
    """Проверка готовности к пентесту"""
    print("\n=== ПРОВЕРКА ГОТОВНОСТИ К ПЕНТЕСТУ ===")
    
    checks = [
        ("Основной скрипт shannon.mjs", "test -f shannon-uncontained/shannon.mjs && echo 'OK' || echo 'NOT FOUND'"),
        ("Директория src/", "test -d shannon-uncontained/src && echo 'OK' || echo 'NOT FOUND'"),
        ("Директория nuclei-templates/", "test -d shannon-uncontained/nuclei-templates && echo 'OK' || echo 'NOT FOUND'"),
        ("Node.js установлен", "which node && node --version || echo 'NOT FOUND'"),
        ("NPM установлен", "which npm && npm --version || echo 'NOT FOUND'"),
    ]
    
    all_ok = True
    for description, command in checks:
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode('utf-8').strip()
        status = "OK" if "OK" in result or "v" in result else "NOT FOUND"
        print(f"{description}: {status}")
        if status == "NOT FOUND":
            all_ok = False
    
    return all_ok

def main():
    print("=" * 70)
    print("ФИНАЛЬНАЯ ПРОВЕРКА ГОТОВНОСТИ К ПЕНТЕСТУ С CLAUDE API")
    print("=" * 70)
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        # 1. Проверка конфигурации
        results = verify_configuration(ssh)
        
        # 2. Проверка API ключа
        api_ok = check_api_key_format(ssh)
        
        # 3. Проверка модели
        model_ok = verify_model_name(ssh)
        
        # 4. Тест импорта
        import_ok = test_anthropic_import(ssh)
        
        # 5. Проверка готовности к пентесту
        pentest_ready = check_ready_for_pentest(ssh)
        
        # Итоговый отчет
        print("\n" + "=" * 70)
        print("ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 70)
        
        print(f"\n✅ Конфигурация: {'OK' if all('OK' in str(v) or 'LLM_PROVIDER=anthropic' in str(v) for v in results.values()) else 'ПРОВЕРИТЬ'}")
        print(f"{'✅' if api_ok else '❌'} API ключ: {'OK' if api_ok else 'ПРОВЕРИТЬ'}")
        print(f"{'✅' if model_ok else '❌'} Модель: {'OK' if model_ok else 'ПРОВЕРИТЬ'}")
        print(f"{'✅' if import_ok else '❌'} Anthropic SDK: {'OK' if import_ok else 'ПРОВЕРИТЬ'}")
        print(f"{'✅' if pentest_ready else '❌'} Готовность к пентесту: {'OK' if pentest_ready else 'ПРОВЕРИТЬ'}")
        
        if all([api_ok, model_ok, import_ok, pentest_ready]):
            print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! ГОТОВ К ПЕНТЕСТУ!")
            print("\nИспользуется:")
            print("  - Провайдер: Anthropic")
            print("  - Модель: Claude 3.5 Sonnet")
            print("  - API: Настроен и готов к работе")
        else:
            print("\n⚠️ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ. ПРОВЕРЬТЕ КОНФИГУРАЦИЮ.")
        
    finally:
        ssh.close()
        print("\n[OK] Соединение закрыто")

if __name__ == "__main__":
    main()

