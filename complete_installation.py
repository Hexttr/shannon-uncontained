#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная установка всех инструментов пентестинга на сервере
"""
import paramiko
import sys
import os
import time

SERVER_IP = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASS = "m8J@2_6whwza6U"

# Fix Windows encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

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

def execute_command(ssh, command, timeout=300):
    """Выполнение команды на сервере с выводом в реальном времени"""
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        
        output_lines = []
        error_lines = []
        
        for line in iter(stdout.readline, ""):
            if not line:
                break
            line = line.rstrip()
            print(f"   {line}")
            output_lines.append(line)
        
        for line in iter(stderr.readline, ""):
            if not line:
                break
            line = line.rstrip()
            if line and not line.startswith('WARNING:'):
                print(f"   [stderr] {line}")
            error_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        output = '\n'.join(output_lines)
        error = '\n'.join(error_lines)
        
        return exit_status == 0, output, error
    except Exception as e:
        return False, "", str(e)

def setup_environment(ssh):
    """Настройка окружения с правильным PATH"""
    print("\n🔧 Настройка окружения...")
    
    commands = [
        # Обновление Go до последней версии
        "curl -fsSL https://go.dev/dl/go1.22.5.linux-amd64.tar.gz -o /tmp/go.tar.gz",
        "sudo rm -rf /usr/local/go",
        "sudo tar -C /usr/local -xzf /tmp/go.tar.gz",
        "rm -f /tmp/go.tar.gz",
        "mkdir -p $HOME/go/bin",
        
        # Настройка PATH в .bashrc
        "grep -q 'go/bin' ~/.bashrc || echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> ~/.bashrc",
        "grep -q 'GOPATH' ~/.bashrc || echo 'export GOPATH=$HOME/go' >> ~/.bashrc",
        "grep -q '.cargo/bin' ~/.bashrc || echo 'export PATH=$PATH:$HOME/.cargo/bin' >> ~/.bashrc",
        "grep -q '.cargo/env' ~/.bashrc || echo 'source $HOME/.cargo/env 2>/dev/null || true' >> ~/.bashrc",
        "grep -q '.local/bin' ~/.bashrc || echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc",
    ]
    
    for cmd in commands:
        execute_command(ssh, cmd)
    
    # Применяем PATH в текущей сессии - создаем одну строку для bash -c
    env_setup = "export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin && export GOPATH=$HOME/go && source $HOME/.cargo/env 2>/dev/null || true"
    
    return env_setup

def install_all_tools(ssh, env_setup):
    """Установка всех инструментов"""
    print("\n" + "=" * 80)
    print("📦 УСТАНОВКА ВСЕХ ИНСТРУМЕНТОВ")
    print("=" * 80)
    
    # Go инструменты
    go_tools = [
        ('subfinder', 'go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest'),
        ('katana', 'go install github.com/projectdiscovery/katana/cmd/katana@latest'),
        ('nuclei', 'go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest'),
        ('httpx', 'go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest'),
        ('gau', 'go install github.com/lc/gau/v2/cmd/gau@latest'),
        ('ffuf', 'go install github.com/ffuf/ffuf/v2@latest'),
        ('trufflehog', 'go install github.com/trufflesecurity/trufflehog/v3@latest'),
        ('gitleaks', 'go install github.com/zricethezav/gitleaks/v8@latest'),
    ]
    
    print("\n🔧 Установка Go инструментов...")
    for tool_name, install_cmd in go_tools:
        print(f"\n   Установка {tool_name}...")
        full_cmd = f'{env_setup} && {install_cmd}'
        success, output, error = execute_command(ssh, f'bash -c "{full_cmd}"', timeout=600)
        if success:
            print(f"   ✅ {tool_name} установлен")
        else:
            # Пробуем без env_setup, так как PATH уже настроен
            success2, output2, error2 = execute_command(ssh, install_cmd, timeout=600)
            if success2:
                print(f"   ✅ {tool_name} установлен (без env_setup)")
            else:
                print(f"   ⚠️  {tool_name}: {error[:100] if error else error2[:100]}")
    
    # Python инструменты
    print("\n🐍 Установка Python инструментов...")
    python_tools = [
        ('sslyze', 'pip3 install --break-system-packages sslyze'),
        ('wafw00f', 'pip3 install --break-system-packages wafw00f'),
        ('sqlmap', 'pip3 install --break-system-packages sqlmap'),
        ('xsstrike', 'pip3 install --break-system-packages xsstrike'),
        ('commix', 'pip3 install --break-system-packages commix'),
    ]
    
    for tool_name, install_cmd in python_tools:
        print(f"\n   Установка {tool_name}...")
        success, output, error = execute_command(ssh, install_cmd, timeout=600)
        if success:
            print(f"   ✅ {tool_name} установлен")
        else:
            print(f"   ⚠️  {tool_name}: {error[:100]}")
    
    # Rust/Cargo и feroxbuster
    print("\n🦀 Установка Rust инструментов...")
    
    # Проверка Cargo
    success, output, _ = execute_command(ssh, 'bash -c "source $HOME/.cargo/env 2>/dev/null && cargo --version"')
    if not success or 'not found' in output.lower():
        print("   Установка Rust/Cargo...")
        execute_command(ssh, "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y", timeout=600)
        env_setup = f"{env_setup} && source $HOME/.cargo/env 2>/dev/null || true"
    
    # Установка feroxbuster
    print("\n   Установка feroxbuster...")
    success, output, error = execute_command(ssh, f'bash -c "{env_setup} && cargo install feroxbuster"', timeout=1800)
    if success:
        print("   ✅ feroxbuster установлен")
    else:
        # Пробуем напрямую
        success2, output2, error2 = execute_command(ssh, 'bash -c "source $HOME/.cargo/env && cargo install feroxbuster"', timeout=1800)
        if success2:
            print("   ✅ feroxbuster установлен (напрямую)")
        else:
            print(f"   ⚠️  feroxbuster: {error[:100] if error else error2[:100]}")
    
    # Обновление шаблонов nuclei
    print("\n📥 Обновление шаблонов nuclei...")
    execute_command(ssh, f'{env_setup} && nuclei -update-templates', timeout=600)

def verify_installation(ssh, env_setup):
    """Проверка установки всех инструментов"""
    print("\n" + "=" * 80)
    print("✅ ПРОВЕРКА УСТАНОВКИ")
    print("=" * 80)
    
    tools = [
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
    
    for tool_name, check_cmd in tools:
        # Пробуем с env_setup
        success, output, error = execute_command(ssh, f'bash -c "{env_setup} && {check_cmd} 2>&1 | head -1"')
        if not success or 'not found' in (output + error).lower():
            # Пробуем без env_setup, но с базовым PATH
            success, output, error = execute_command(ssh, f'bash -c "export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin && {check_cmd} 2>&1 | head -1"')
        
        if success and output.strip() and 'not found' not in (output + error).lower() and 'command not found' not in (output + error).lower():
            print(f"   ✅ {tool_name}: {output.strip()[:50]}")
            installed.append(tool_name)
        else:
            print(f"   ❌ {tool_name}: не найден")
            missing.append(tool_name)
    
    print("\n" + "=" * 80)
    print("📊 РЕЗЮМЕ")
    print("=" * 80)
    print(f"\n✅ Установлено ({len(installed)}): {', '.join(installed)}")
    if missing:
        print(f"\n❌ Не установлено ({len(missing)}): {', '.join(missing)}")
    else:
        print("\n🎉 Все инструменты установлены успешно!")
    
    return len(missing) == 0

def main():
    """Основная функция"""
    print("=" * 80)
    print("🚀 ПОЛНАЯ УСТАНОВКА ВСЕХ ИНСТРУМЕНТОВ ПЕНТЕСТИНГА")
    print("=" * 80)
    
    ssh = connect_server()
    if not ssh:
        return
    
    try:
        # Настройка окружения
        env_setup = setup_environment(ssh)
        
        # Установка всех инструментов
        install_all_tools(ssh, env_setup)
        
        # Проверка установки
        all_installed = verify_installation(ssh, env_setup)
        
        if all_installed:
            print("\n" + "=" * 80)
            print("✅ ВСЕ ИНСТРУМЕНТЫ УСТАНОВЛЕНЫ УСПЕШНО!")
            print("=" * 80)
            print("""
📝 СЛЕДУЮЩИЕ ШАГИ:

1. Переподключитесь к серверу для применения изменений:
   ssh root@72.56.79.153
   source ~/.bashrc

2. Проверьте установку:
   cd /root/shannon-uncontained
   which subfinder katana nuclei httpx gau ffuf trufflehog gitleaks
   which sslyze wafw00f sqlmap xsstrike commix feroxbuster

3. Запустите тестовый пентест:
   ./shannon.mjs generate https://example.com --workspace ./test-output
""")
        else:
            print("\n⚠️  Некоторые инструменты не установлены. Проверьте логи выше.")
    
    finally:
        ssh.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

