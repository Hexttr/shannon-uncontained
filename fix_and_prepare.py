#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление проблем и финальная подготовка к пентесту
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
    print("🔧 ФИНАЛЬНАЯ ПОДГОТОВКА К ПЕНТЕСТУ")
    print("=" * 80)
    
    ssh = connect_server()
    PROJECT_PATH = "/root/shannon-uncontained"
    
    # 1. Исправляем окончания строк в shannon.mjs
    print("\n🔧 1. ИСПРАВЛЕНИЕ ОКОНЧАНИЙ СТРОК")
    print("-" * 80)
    
    execute_command(ssh, f"cd {PROJECT_PATH} && dos2unix shannon.mjs 2>/dev/null || sed -i 's/\\r$//' shannon.mjs")
    execute_command(ssh, f"cd {PROJECT_PATH} && chmod +x shannon.mjs")
    print("   ✅ shannon.mjs исправлен")
    
    # 2. Устанавливаем katana если не установлен
    print("\n🔧 2. УСТАНОВКА KATANA")
    print("-" * 80)
    
    success, output, error = execute_command(ssh, "bash -c 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin && katana -version 2>&1 | head -1'")
    if not success or 'not found' in (output + error).lower():
        print("   Установка katana...")
        success2, output2, error2 = execute_command(ssh, "bash -c 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin && export GOPATH=$HOME/go && go install github.com/projectdiscovery/katana/cmd/katana@latest'", timeout=600)
        if success2:
            print("   ✅ katana установлен")
        else:
            print(f"   ⚠️  Ошибка установки: {error2[:200]}")
    else:
        print("   ✅ katana уже установлен")
    
    # 3. Исправляем веб-интерфейс - добавляем правильное окружение
    print("\n🔧 3. ИСПРАВЛЕНИЕ ВЕБ-ИНТЕРФЕЙСА")
    print("-" * 80)
    
    # Читаем текущий файл
    success, content, error = execute_command(ssh, f"cat {PROJECT_PATH}/web-interface.cjs")
    
    # Исправляем команду чтобы использовать правильное окружение
    if 'export PATH=$PATH:/usr/local/go/bin' in content:
        print("   ✅ Веб-интерфейс уже использует правильное окружение")
    else:
        # Заменяем команду на более надежную
        old_cmd_pattern = r"const command = `cd \$\{PROJECT_PATH\} && export PATH=\$PATH:/usr/local/go/bin.*?2>&1`;"
        new_cmd = """const command = `cd ${PROJECT_PATH} && source .env.sh 2>/dev/null || true && export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && export GOPATH=$HOME/go && source $HOME/.cargo/env 2>/dev/null || true && ./shannon.mjs generate "${target}" --workspace ./test-output 2>&1`;"""
        
        import re
        fixed_content = re.sub(
            r"const command = `.*?2>&1`;",
            new_cmd,
            content,
            flags=re.DOTALL
        )
        
        if fixed_content != content:
            with ssh.open_sftp() as sftp:
                with sftp.file(f"{PROJECT_PATH}/web-interface.cjs", 'w') as f:
                    f.write(fixed_content)
            execute_command(ssh, f"chmod +x {PROJECT_PATH}/web-interface.cjs")
            print("   ✅ Веб-интерфейс обновлен")
        else:
            print("   ✅ Веб-интерфейс уже корректен")
    
    # 4. Перезапускаем веб-интерфейс
    print("\n🔄 4. ПЕРЕЗАПУСК ВЕБ-ИНТЕРФЕЙСА")
    print("-" * 80)
    
    execute_command(ssh, "pkill -f 'web-interface.cjs' || true")
    import time
    time.sleep(2)
    
    execute_command(ssh, f"cd {PROJECT_PATH} && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &")
    time.sleep(2)
    
    # Проверяем
    success, output, error = execute_command(ssh, "ps aux | grep 'web-interface.cjs' | grep -v grep")
    if success and output.strip():
        print("   ✅ Веб-интерфейс запущен")
    else:
        print("   ⚠️  Веб-интерфейс не запустился")
        success2, logs, _ = execute_command(ssh, "tail -20 /tmp/web-interface.log")
        if logs:
            print(f"   Логи: {logs}")
    
    # 5. Тестовый запуск команды
    print("\n🧪 5. ТЕСТОВЫЙ ЗАПУСК")
    print("-" * 80)
    
    test_cmd = f"cd {PROJECT_PATH} && source .env.sh && ./shannon.mjs --help 2>&1 | head -5"
    success, output, error = execute_command(ssh, test_cmd)
    if success and output.strip():
        print("   ✅ Команда работает")
        print(f"   {output.strip()[:150]}")
    else:
        print(f"   ⚠️  Проблема с командой: {error[:200]}")
    
    # 6. Проверка доступности инструментов
    print("\n🔍 6. ПРОВЕРКА ДОСТУПНОСТИ ИНСТРУМЕНТОВ")
    print("-" * 80)
    
    env_cmd = "source .env.sh && export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin"
    
    tools = ['subfinder', 'katana', 'nuclei', 'httpx', 'nmap']
    for tool in tools:
        success, output, error = execute_command(ssh, f"cd {PROJECT_PATH} && {env_cmd} && which {tool} 2>&1")
        if success and output.strip():
            print(f"   ✅ {tool}: {output.strip()}")
        else:
            print(f"   ❌ {tool}: не найден")
    
    ssh.close()
    
    print("\n" + "=" * 80)
    print("✅ ПОДГОТОВКА ЗАВЕРШЕНА")
    print("=" * 80)
    print("""
🌐 Веб-интерфейс: http://72.56.79.153:3000

📝 Для запуска пентеста:
   1. Откройте http://72.56.79.153:3000
   2. Введите URL (например: https://tcell.tj)
   3. Нажмите "Запустить"
   4. Смотрите вывод в реальном времени

🔍 Если ошибка соединения:
   - Проверьте что веб-интерфейс запущен: ps aux | grep web-interface
   - Проверьте логи: tail -f /tmp/web-interface.log
   - Проверьте порт: ss -tlnp | grep 3000
""")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

