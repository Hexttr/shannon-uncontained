#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматическая установка недостающих инструментов на сервере
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
        
        # Читаем вывод в реальном времени
        output_lines = []
        error_lines = []
        
        # Читаем stdout
        for line in iter(stdout.readline, ""):
            if not line:
                break
            line = line.rstrip()
            print(f"   {line}")
            output_lines.append(line)
        
        # Читаем stderr
        for line in iter(stderr.readline, ""):
            if not line:
                break
            line = line.rstrip()
            if line:  # Показываем только непустые строки
                print(f"   [stderr] {line}")
            error_lines.append(line)
        
        exit_status = stdout.channel.recv_exit_status()
        output = '\n'.join(output_lines)
        error = '\n'.join(error_lines)
        
        return exit_status == 0, output, error
    except Exception as e:
        return False, "", str(e)

def check_tool_installed(ssh, tool_name, check_cmd):
    """Проверка установлен ли инструмент"""
    success, output, error = execute_command(ssh, f"{check_cmd} 2>&1 | head -1")
    if not success:
        return False
    output_lower = (output + error).lower()
    # Проверяем что команда не выдала ошибку "not found" или "command not found"
    if 'not found' in output_lower or 'command not found' in output_lower:
        return False
    # Если есть какой-то вывод (версия, help и т.д.), считаем что инструмент установлен
    return bool(output.strip())

def install_go(ssh):
    """Установка Go"""
    print("\n📦 Установка Go...")
    print("-" * 80)
    
    # Проверка уже установлен ли Go
    if check_tool_installed(ssh, "go", "go version"):
        print("   ✅ Go уже установлен")
        success, output, _ = execute_command(ssh, "go version")
        print(f"   {output.strip()}")
        return True
    
    # Установка Go
    print("   Скачивание Go...")
    success, output, error = execute_command(ssh, "curl -fsSL https://go.dev/dl/go1.21.5.linux-amd64.tar.gz -o /tmp/go.tar.gz", timeout=300)
    if not success:
        print(f"   ❌ Ошибка скачивания: {error[:200]}")
        return False
    
    print("   Распаковка Go...")
    commands = [
        "sudo rm -rf /usr/local/go",
        "sudo tar -C /usr/local -xzf /tmp/go.tar.gz",
        "rm -f /tmp/go.tar.gz",
        "mkdir -p $HOME/go/bin",
    ]
    
    for cmd in commands:
        success, output, error = execute_command(ssh, cmd)
        if not success:
            print(f"   ⚠️  Предупреждение: {error[:100]}")
    
    # Настройка PATH в текущей сессии
    print("   Настройка PATH...")
    execute_command(ssh, 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin')
    execute_command(ssh, 'export GOPATH=$HOME/go')
    
    # Добавление в .bashrc
    execute_command(ssh, 'grep -q "go/bin" ~/.bashrc || echo "export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin" >> ~/.bashrc')
    execute_command(ssh, 'grep -q "GOPATH" ~/.bashrc || echo "export GOPATH=$HOME/go" >> ~/.bashrc')
    
    # Проверка установки
    print("   Проверка установки...")
    success, output, error = execute_command(ssh, "/usr/local/go/bin/go version")
    if success and output.strip():
        print(f"   ✅ Go установлен: {output.strip()}")
        return True
    else:
        print("   ❌ Ошибка установки Go")
        print(f"   {error[:200]}")
        return False

def install_go_tool(ssh, tool_name, install_cmd, check_cmd):
    """Установка Go инструмента"""
    print(f"\n🔧 Установка {tool_name}...")
    
    # Проверка уже установлен ли
    if check_tool_installed(ssh, tool_name, check_cmd):
        print(f"   ✅ {tool_name} уже установлен")
        success, output, _ = execute_command(ssh, check_cmd)
        if success:
            print(f"   {output.strip()[:100]}")
        return True
    
    # Установка с применением PATH
    print(f"   Выполняется: {install_cmd}")
    full_cmd = f'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin && export GOPATH=$HOME/go && {install_cmd}'
    success, output, error = execute_command(ssh, full_cmd, timeout=600)
    
    if success:
        # Проверка установки
        check_success, check_output, _ = execute_command(ssh, check_cmd)
        if check_success:
            print(f"   ✅ {tool_name} установлен успешно")
            print(f"   {check_output.strip()[:100]}")
            return True
        else:
            print(f"   ⚠️  {tool_name} установлен, но проверка не прошла")
            return False
    else:
        print(f"   ❌ Ошибка установки {tool_name}")
        print(f"   {error[:200]}")
        return False

def install_python_tool(ssh, tool_name, install_cmd, check_cmd):
    """Установка Python инструмента через pip"""
    print(f"\n🐍 Установка {tool_name}...")
    
    # Проверка уже установлен ли
    if check_tool_installed(ssh, tool_name, check_cmd):
        print(f"   ✅ {tool_name} уже установлен")
        success, output, _ = execute_command(ssh, check_cmd)
        if success:
            print(f"   {output.strip()[:100]}")
        return True
    
    # Установка с --break-system-packages или через pipx
    print(f"   Выполняется: {install_cmd}")
    # Пробуем сначала через pipx, если доступен
    pipx_cmd = install_cmd.replace('pip3 install --user', 'pipx install')
    success, output, error = execute_command(ssh, f'which pipx && {pipx_cmd} || {install_cmd} --break-system-packages', timeout=600)
    
    if success:
        # Проверка установки
        check_success, check_output, _ = execute_command(ssh, check_cmd)
        if check_success:
            print(f"   ✅ {tool_name} установлен успешно")
            print(f"   {check_output.strip()[:100]}")
            return True
        else:
            print(f"   ⚠️  {tool_name} установлен, но проверка не прошла")
            return False
    else:
        print(f"   ❌ Ошибка установки {tool_name}")
        print(f"   {error[:200]}")
        return False

def install_cargo(ssh):
    """Установка Rust/Cargo если не установлен"""
    print("\n🦀 Проверка Rust/Cargo...")
    
    if check_tool_installed(ssh, "cargo", "cargo --version"):
        print("   ✅ Cargo уже установлен")
        success, output, _ = execute_command(ssh, "cargo --version")
        print(f"   {output.strip()}")
        return True
    
    print("   ⚠️  Cargo не установлен. Установка Rust...")
    # Установка Rust через rustup
    commands = [
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
        "source $HOME/.cargo/env",
        "cargo --version"
    ]
    
    for cmd in commands:
        success, output, error = execute_command(ssh, cmd, timeout=600)
        if not success and 'cargo --version' not in cmd:
            print(f"   ⚠️  Предупреждение: {error[:200]}")
    
    if check_tool_installed(ssh, "cargo", "cargo --version"):
        print("   ✅ Cargo установлен")
        return True
    else:
        print("   ⚠️  Не удалось установить Cargo. Пропускаем feroxbuster.")
        return False

def setup_path(ssh):
    """Настройка PATH для всех инструментов"""
    print("\n🔧 Настройка PATH...")
    commands = [
        'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin',
        'export GOPATH=$HOME/go',
        'echo "export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin" >> ~/.bashrc',
        'echo "export GOPATH=$HOME/go" >> ~/.bashrc',
        'echo $PATH | grep -q go/bin && echo "PATH configured" || echo "PATH needs update"'
    ]
    
    for cmd in commands:
        execute_command(ssh, cmd)

def main():
    """Основная функция"""
    print("=" * 80)
    print("🚀 АВТОМАТИЧЕСКАЯ УСТАНОВКА ИНСТРУМЕНТОВ НА СЕРВЕРЕ")
    print("=" * 80)
    
    ssh = connect_server()
    if not ssh:
        return
    
    results = {
        'go': False,
        'subfinder': False,
        'katana': False,
        'nuclei': False,
        'httpx': False,
        'gau': False,
        'ffuf': False,
        'trufflehog': False,
        'gitleaks': False,
        'sslyze': False,
        'wafw00f': False,
        'sqlmap': False,
        'xsstrike': False,
        'commix': False,
        'feroxbuster': False,
        'cargo': False
    }
    
    # 1. Установка Go
    results['go'] = install_go(ssh)
    
    if not results['go']:
        print("\n❌ Не удалось установить Go. Прерывание.")
        ssh.close()
        return
    
    # Настройка PATH
    setup_path(ssh)
    
    # 2. Установка критичных инструментов
    print("\n" + "=" * 80)
    print("📦 УСТАНОВКА КРИТИЧНЫХ ИНСТРУМЕНТОВ")
    print("=" * 80)
    
    critical_tools = [
        ('subfinder', 
         'go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest',
         'subfinder -version'),
    ]
    
    for tool_name, install_cmd, check_cmd in critical_tools:
        results[tool_name] = install_go_tool(ssh, tool_name, install_cmd, check_cmd)
    
    # 3. Установка рекомендуемых Go инструментов
    print("\n" + "=" * 80)
    print("📦 УСТАНОВКА РЕКОМЕНДУЕМЫХ GO ИНСТРУМЕНТОВ")
    print("=" * 80)
    
    recommended_go_tools = [
        ('katana',
         'go install github.com/projectdiscovery/katana/cmd/katana@latest',
         'katana -version'),
        ('nuclei',
         'go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest',
         'nuclei -version'),
        ('httpx',
         'go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest',
         'httpx -version'),
        ('gau',
         'go install github.com/lc/gau/v2/cmd/gau@latest',
         'gau --version'),
        ('ffuf',
         'go install github.com/ffuf/ffuf/v2@latest',
         'ffuf -V'),
        ('trufflehog',
         'go install github.com/trufflesecurity/trufflehog/v3@latest',
         'trufflehog --version'),
        ('gitleaks',
         'go install github.com/gitleaks/gitleaks/v8@latest',
         'gitleaks version'),
    ]
    
    for tool_name, install_cmd, check_cmd in recommended_go_tools:
        results[tool_name] = install_go_tool(ssh, tool_name, install_cmd, check_cmd)
    
    # 4. Установка Python инструментов
    print("\n" + "=" * 80)
    print("🐍 УСТАНОВКА PYTHON ИНСТРУМЕНТОВ")
    print("=" * 80)
    
    python_tools = [
        ('sslyze',
         'pip3 install sslyze',
         'sslyze --version'),
        ('wafw00f',
         'pip3 install wafw00f',
         'wafw00f --version'),
        ('sqlmap',
         'pip3 install sqlmap',
         'sqlmap --version'),
        ('xsstrike',
         'pip3 install xsstrike',
         'xsstrike --help'),
        ('commix',
         'pip3 install commix',
         'commix --version'),
    ]
    
    for tool_name, install_cmd, check_cmd in python_tools:
        results[tool_name] = install_python_tool(ssh, tool_name, install_cmd, check_cmd)
    
    # 5. Установка Rust/Cargo и feroxbuster
    print("\n" + "=" * 80)
    print("🦀 УСТАНОВКА RUST ИНСТРУМЕНТОВ")
    print("=" * 80)
    
    results['cargo'] = install_cargo(ssh)
    
    if results['cargo']:
        # Добавляем cargo bin в PATH
        execute_command(ssh, 'source $HOME/.cargo/env')
        execute_command(ssh, 'export PATH=$PATH:$HOME/.cargo/bin')
        execute_command(ssh, 'echo "export PATH=$PATH:$HOME/.cargo/bin" >> ~/.bashrc')
        
        # Установка feroxbuster
        if not check_tool_installed(ssh, "feroxbuster", "feroxbuster --version"):
            print("\n🔧 Установка feroxbuster...")
            success, output, error = execute_command(ssh, 'source $HOME/.cargo/env && export PATH=$PATH:$HOME/.cargo/bin && cargo install feroxbuster', timeout=1800)
            if success:
                results['feroxbuster'] = check_tool_installed(ssh, "feroxbuster", "feroxbuster --version")
            else:
                print(f"   ⚠️  Ошибка установки feroxbuster: {error[:200]}")
        else:
            results['feroxbuster'] = True
    
    # 6. Обновление шаблонов nuclei (если установлен)
    if results['nuclei']:
        print("\n📥 Обновление шаблонов nuclei...")
        execute_command(ssh, "nuclei -update-templates", timeout=600)
    
    # 7. Финальная проверка
    print("\n" + "=" * 80)
    print("✅ ФИНАЛЬНАЯ ПРОВЕРКА")
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
        ('sslyze', 'sslyze --version'),
        ('wafw00f', 'wafw00f --version'),
        ('sqlmap', 'sqlmap --version'),
        ('xsstrike', 'xsstrike --help'),
        ('commix', 'commix --version'),
        ('feroxbuster', 'feroxbuster --version'),
    ]
    
    print("\nПроверка установленных инструментов:")
    for tool_name, check_cmd in all_tools:
        # Применяем PATH для проверки и проверяем в разных местах
        full_check = f'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && {check_cmd} 2>&1 | head -1'
        success, output, error = execute_command(ssh, full_check)
        output_combined = (output + error).lower()
        if success and output.strip() and 'not found' not in output_combined and 'command not found' not in output_combined and 'error:' not in output_combined[:20]:
            print(f"   ✅ {tool_name}: {output.strip()[:60]}")
        else:
            # Проверяем напрямую в go/bin
            if tool_name in ['katana', 'gau', 'ffuf', 'trufflehog', 'gitleaks']:
                direct_check = f'$HOME/go/bin/{tool_name} -version 2>&1 | head -1 || $HOME/go/bin/{tool_name} --version 2>&1 | head -1 || $HOME/go/bin/{tool_name} version 2>&1 | head -1'
                success2, output2, _ = execute_command(ssh, direct_check)
                if success2 and output2.strip():
                    print(f"   ✅ {tool_name}: установлен в $HOME/go/bin ({output2.strip()[:40]})")
                else:
                    print(f"   ❌ {tool_name}: не найден")
            else:
                print(f"   ❌ {tool_name}: не найден")
    
    # Проверка PATH
    print("\nПроверка PATH:")
    success, output, _ = execute_command(ssh, 'echo $PATH')
    paths_found = []
    if 'go/bin' in output:
        paths_found.append('go/bin')
    if '.cargo/bin' in output:
        paths_found.append('.cargo/bin')
    if '.local/bin' in output:
        paths_found.append('.local/bin')
    
    if paths_found:
        print(f"   ✅ PATH содержит: {', '.join(paths_found)}")
    else:
        print("   ⚠️  PATH не содержит необходимые пути - проверьте ~/.bashrc")
    
    ssh.close()
    
    # Резюме
    print("\n" + "=" * 80)
    print("📊 РЕЗЮМЕ")
    print("=" * 80)
    
    installed = [name for name, status in results.items() if status]
    missing = [name for name, status in results.items() if not status]
    
    if installed:
        print(f"\n✅ Установлено ({len(installed)}): {', '.join(installed)}")
    
    if missing:
        print(f"\n❌ Не установлено ({len(missing)}): {', '.join(missing)}")
        print("\nПопробуйте установить вручную или проверьте логи выше.")
    else:
        print("\n🎉 Все инструменты установлены успешно!")
    
    print("\n" + "=" * 80)
    print("📝 СЛЕДУЮЩИЕ ШАГИ")
    print("=" * 80)
    print("""
1. Переподключитесь к серверу для применения изменений PATH:
   ssh root@72.56.79.153

2. Проверьте установку:
   cd /root/shannon-uncontained
   which subfinder katana nuclei httpx gau ffuf trufflehog gitleaks
   which sslyze wafw00f sqlmap xsstrike commix feroxbuster

3. Запустите тестовый пентест:
   ./shannon.mjs generate https://example.com --workspace ./test-output
   
4. Для применения изменений PATH переподключитесь к серверу или выполните:
   source ~/.bashrc
""")

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

