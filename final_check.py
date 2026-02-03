#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная проверка готовности к пентесту
"""
import paramiko
import sys
import os

SERVER_IP = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASS = "m8J@2_6whwza6U"

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def connect_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)
    return ssh

def execute_command(ssh, command, timeout=300):
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, output, error
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 80)
    print("✅ ФИНАЛЬНАЯ ПРОВЕРКА ГОТОВНОСТИ К ПЕНТЕСТУ")
    print("=" * 80)
    
    ssh = connect_server()
    PROJECT_PATH = "/root/shannon-uncontained"
    
    all_ok = True
    
    # 1. Проверка веб-интерфейса
    print("\n🌐 ВЕБ-ИНТЕРФЕЙС")
    print("-" * 80)
    
    success, output, _ = execute_command(ssh, "ps aux | grep 'web-interface.cjs' | grep -v grep")
    if success and output.strip():
        print("   ✅ Запущен")
    else:
        print("   ❌ Не запущен")
        all_ok = False
    
    success, output, _ = execute_command(ssh, "ss -tlnp 2>/dev/null | grep :3000 || netstat -tlnp 2>/dev/null | grep :3000")
    if success and output.strip():
        print("   ✅ Порт 3000 слушается")
    else:
        print("   ❌ Порт 3000 не слушается")
        all_ok = False
    
    # 2. Проверка команды
    print("\n🔧 КОМАНДА SHANNON.MJS")
    print("-" * 80)
    
    test_cmd = f"cd {PROJECT_PATH} && export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && export GOPATH=$HOME/go && ./shannon.mjs --help 2>&1 | head -3"
    success, output, error = execute_command(ssh, test_cmd)
    if success and 'shannon' in output.lower():
        print("   ✅ Команда работает")
    else:
        print(f"   ❌ Команда не работает: {error[:100]}")
        all_ok = False
    
    # 3. Проверка инструментов
    print("\n🔧 ИНСТРУМЕНТЫ")
    print("-" * 80)
    
    env_cmd = "export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && export GOPATH=$HOME/go"
    
    critical_tools = ['subfinder', 'nuclei', 'httpx', 'nmap']
    for tool in critical_tools:
        success, output, _ = execute_command(ssh, f"bash -c '{env_cmd} && which {tool} 2>&1'")
        if success and output.strip():
            print(f"   ✅ {tool}")
        else:
            print(f"   ❌ {tool} не найден")
            all_ok = False
    
    # 4. Проверка Ollama
    print("\n🤖 OLLAMA")
    print("-" * 80)
    
    success, output, _ = execute_command(ssh, "curl -s http://localhost:11434/api/tags 2>&1 | head -3")
    if success and ('codellama' in output.lower() or 'models' in output.lower()):
        print("   ✅ Ollama работает")
    else:
        print("   ❌ Ollama не отвечает")
        all_ok = False
    
    # 5. Проверка .env
    print("\n⚙️  КОНФИГУРАЦИЯ")
    print("-" * 80)
    
    success, env_content, _ = execute_command(ssh, f"cat {PROJECT_PATH}/.env 2>&1")
    if 'LLM_PROVIDER=ollama' in env_content:
        print("   ✅ .env настроен для Ollama")
    else:
        print("   ⚠️  .env не настроен для Ollama")
    
    ssh.close()
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ ВСЕ ГОТОВО К ПЕНТЕСТУ!")
    else:
        print("⚠️  ЕСТЬ ПРОБЛЕМЫ - ПРОВЕРЬТЕ ВЫШЕ")
    print("=" * 80)
    
    print("""
🌐 Веб-интерфейс: http://72.56.79.153:3000

📝 ИНСТРУКЦИЯ ПО ЗАПУСКУ:

1. Откройте http://72.56.79.153:3000 в браузере
2. Введите URL цели (например: https://tcell.tj)
3. Нажмите кнопку "Запустить"
4. Вывод будет отображаться в реальном времени

💡 Если возникает ошибка соединения:
   - Откройте консоль браузера (F12 -> Console)
   - Проверьте что видите ошибки
   - Обновите страницу (F5)
   - Проверьте логи на сервере: tail -f /tmp/web-interface.log

🔍 Диагностика на сервере:
   ssh root@72.56.79.153
   cd /root/shannon-uncontained
   ./run-pentest.sh https://example.com
""")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

