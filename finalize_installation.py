#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Завершение установки - проверка и исправление PATH для всех инструментов
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
        output_lines = []
        for line in iter(stdout.readline, ""):
            if not line:
                break
            line = line.rstrip()
            print(f"   {line}")
            output_lines.append(line)
        exit_status = stdout.channel.recv_exit_status()
        output = '\n'.join(output_lines)
        return exit_status == 0, output
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 80)
    print("🔍 ПРОВЕРКА И ИСПРАВЛЕНИЕ УСТАНОВКИ")
    print("=" * 80)
    
    ssh = connect_server()
    
    # Проверяем где находятся инструменты
    print("\n📍 Поиск установленных инструментов...")
    
    tools_to_find = ['katana', 'trufflehog', 'wafw00f']
    
    for tool in tools_to_find:
        print(f"\n   Поиск {tool}...")
        # Проверяем в разных местах
        locations = [
            f'$HOME/go/bin/{tool}',
            f'/usr/local/bin/{tool}',
            f'/usr/bin/{tool}',
            f'which {tool}',
            f'find $HOME -name {tool} -type f 2>/dev/null | head -1'
        ]
        
        for loc_cmd in locations:
            if 'which' in loc_cmd or 'find' in loc_cmd:
                cmd = loc_cmd
            else:
                cmd = f'test -f {loc_cmd} && echo {loc_cmd} || echo "not found"'
            
            success, output = execute_command(ssh, f'bash -c "export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && {cmd}"')
            if success and output.strip() and 'not found' not in output.lower():
                print(f"   ✅ {tool} найден: {output.strip()}")
                break
    
    # Проверяем katana напрямую
    print("\n🔧 Проверка katana...")
    success, output = execute_command(ssh, 'bash -c "export PATH=$PATH:$HOME/go/bin && katana -version 2>&1 | head -1"')
    if success and output.strip():
        print(f"   ✅ katana работает: {output.strip()[:50]}")
    else:
        # Проверяем напрямую
        success2, output2 = execute_command(ssh, '$HOME/go/bin/katana -version 2>&1 | head -1')
        if success2:
            print(f"   ✅ katana найден в $HOME/go/bin: {output2.strip()[:50]}")
    
    # Проверяем wafw00f
    print("\n🔧 Проверка wafw00f...")
    success, output = execute_command(ssh, 'bash -c "export PATH=$PATH:/usr/local/bin && wafw00f --version 2>&1 | head -1"')
    if success and output.strip():
        print(f"   ✅ wafw00f работает: {output.strip()[:50]}")
    else:
        # Проверяем напрямую
        success2, output2 = execute_command(ssh, '/usr/local/bin/wafw00f --version 2>&1 | head -1')
        if success2:
            print(f"   ✅ wafw00f найден в /usr/local/bin: {output2.strip()[:50]}")
    
    # Установка trufflehog через другой метод (если не установлен)
    print("\n🔧 Попытка установки trufflehog...")
    success, output = execute_command(ssh, 'bash -c "export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin && go install github.com/trufflesecurity/trufflehog/v3@latest"', timeout=600)
    if success:
        success2, output2 = execute_command(ssh, 'bash -c "export PATH=$PATH:$HOME/go/bin && trufflehog --version 2>&1 | head -1"')
        if success2:
            print(f"   ✅ trufflehog установлен: {output2.strip()[:50]}")
    
    # Финальная проверка всех инструментов
    print("\n" + "=" * 80)
    print("✅ ФИНАЛЬНАЯ ПРОВЕРКА ВСЕХ ИНСТРУМЕНТОВ")
    print("=" * 80)
    
    all_tools = [
        ('go', 'go version'),
        ('subfinder', 'subfinder -version'),
        ('katana', 'katana -version'),
        ('nuclei', 'nuclei -version'),
        ('httpx', 'httpx -version'),
        ('gau', 'gau --version'),
        ('ffuf', 'ffuf -V'),
        ('trufflehog', 'trufflehog --version'),
        ('gitleaks', 'gitleaks version'),
        ('sslyze', 'sslyze --help | head -1'),
        ('wafw00f', 'wafw00f --version'),
        ('sqlmap', 'sqlmap --version'),
        ('xsstrike', 'xsstrike --help | head -1'),
        ('commix', 'commix --help | head -1'),
        ('feroxbuster', 'feroxbuster --version'),
    ]
    
    installed = []
    missing = []
    
    env_cmd = 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin'
    
    for tool_name, check_cmd in all_tools:
        success, output = execute_command(ssh, f'bash -c "{env_cmd} && {check_cmd} 2>&1 | head -1"')
        if success and output.strip() and 'not found' not in output.lower() and 'command not found' not in output.lower():
            print(f"   ✅ {tool_name}: {output.strip()[:50]}")
            installed.append(tool_name)
        else:
            print(f"   ❌ {tool_name}: не найден")
            missing.append(tool_name)
    
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 80)
    print(f"\n✅ Установлено ({len(installed)}/{len(all_tools)}): {', '.join(installed)}")
    if missing:
        print(f"\n❌ Не установлено ({len(missing)}): {', '.join(missing)}")
    else:
        print("\n🎉 ВСЕ ИНСТРУМЕНТЫ УСТАНОВЛЕНЫ И РАБОТАЮТ!")
    
    print("\n" + "=" * 80)
    print("📝 ВАЖНО: Примените изменения PATH")
    print("=" * 80)
    print("""
Для применения всех изменений выполните на сервере:

ssh root@72.56.79.153
source ~/.bashrc

Или добавьте вручную в ~/.bashrc:
export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin
export GOPATH=$HOME/go
source $HOME/.cargo/env 2>/dev/null || true
""")
    
    ssh.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

