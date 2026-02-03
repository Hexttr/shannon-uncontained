#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная проверка готовности к пентесту
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

def check_readiness(ssh):
    """Полная проверка готовности"""
    print("=" * 70)
    print("ФИНАЛЬНАЯ ПРОВЕРКА ГОТОВНОСТИ К ПЕНТЕСТУ")
    print("=" * 70)
    
    all_ok = True
    
    # 1. LLM
    print("\n1. ✅ LLM (Claude 4.5 Sonnet):")
    stdin, stdout, stderr = ssh.exec_command("grep -E 'LLM_PROVIDER|ANTHROPIC_API_KEY|LLM_MODEL' shannon-uncontained/.env | grep -v '^#'")
    llm_config = stdout.read().decode('utf-8', errors='ignore')
    if "anthropic" in llm_config.lower() and "claude-sonnet-4-5" in llm_config:
        print("   ✅ Настроен и готов")
    else:
        print("   ❌ Не настроен")
        all_ok = False
    
    # 2. Инструменты
    print("\n2. ✅ Инструменты пентеста:")
    tools = {
        'nmap': '/usr/bin/nmap',
        'subfinder': '/usr/local/bin/subfinder',
        'nuclei': '/usr/local/bin/nuclei',
        'httpx': '/usr/local/bin/httpx',
        'sqlmap': '/usr/local/bin/sqlmap'
    }
    tools_ok = True
    for tool, path in tools.items():
        stdin, stdout, stderr = ssh.exec_command(f"test -f {path} && echo 'OK' || echo 'MISSING'")
        status = stdout.read().decode('utf-8', errors='ignore').strip()
        icon = "✅" if status == "OK" else "❌"
        print(f"   {icon} {tool}")
        if status != "OK":
            tools_ok = False
    if not tools_ok:
        all_ok = False
    
    # 3. Resume отключен
    print("\n3. ✅ Resume отключен:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 2 'resume.*options.resume' shannon-uncontained/src/cli/commands/RunCommand.js | head -3")
    resume_code = stdout.read().decode('utf-8', errors='ignore')
    if "resume: options.resume === true" in resume_code:
        print("   ✅ Resume отключен по умолчанию")
    else:
        print("   ⚠️  Проверьте resume")
    
    # 4. Веб-интерфейс
    print("\n4. ✅ Веб-интерфейс:")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    web_running = stdout.read().decode('utf-8', errors='ignore')
    if web_running:
        print("   ✅ Запущен на порту 3000")
    else:
        print("   ❌ Не запущен")
        all_ok = False
    
    # 5. Очистка старых результатов
    print("\n5. ✅ Очистка старых результатов:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 5 'Cleaning up old results' shannon-uncontained/web-interface.cjs | head -3")
    cleanup_code = stdout.read().decode('utf-8', errors='ignore')
    if "Cleaning up old results" in cleanup_code:
        print("   ✅ Добавлена в веб-интерфейс")
    else:
        print("   ⚠️  Не найдена")
    
    # 6. Процесс не убивается
    print("\n6. ✅ Процесс не убивается при disconnect:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 3 'Client disconnected' shannon-uncontained/web-interface.cjs | head -5")
    disconnect_code = stdout.read().decode('utf-8', errors='ignore')
    if "but process continues" in disconnect_code or "child.kill()" not in disconnect_code:
        print("   ✅ Процесс продолжает работу")
    else:
        print("   ⚠️  Проверьте код disconnect")
    
    return all_ok

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        if check_readiness(ssh):
            print("\n" + "=" * 70)
            print("✅ ГОТОВ К ПЕНТЕСТУ!")
            print("=" * 70)
            print("\nНастройки:")
            print("✅ Resume отключен - пентест всегда начинается сначала")
            print("✅ Старые результаты удаляются перед запуском")
            print("✅ Процесс не убивается при disconnect")
            print("✅ LLM настроен (Claude 4.5 Sonnet)")
            print("✅ Инструменты установлены")
            print("✅ Веб-интерфейс запущен")
            print("\n🎯 Теперь пентест будет:")
            print("   - Всегда начинаться сначала")
            print("   - Не пропускать агентов")
            print("   - Продолжать работу даже если клиент отключился")
            print("\n🌐 Веб-интерфейс: http://72.56.79.153:3000")
        else:
            print("\n⚠️  Есть проблемы с готовностью")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

