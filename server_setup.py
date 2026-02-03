#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для подключения к серверу и настройки окружения Shannon-Uncontained
Использует paramiko для SSH подключения
"""

import paramiko
import sys
import time
import io
from pathlib import Path

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class ServerManager:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        
    def connect(self):
        """Подключение к серверу через SSH"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30
            )
            print(f"[OK] Успешное подключение к {self.host}")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка подключения: {e}")
            return False
    
    def execute_command(self, command, sudo=False):
        """Выполнение команды на сервере"""
        if not self.client:
            print("[ERROR] Нет подключения к серверу")
            return None, None, None
            
        try:
            if sudo:
                command = f"sudo {command}"
            
            stdin, stdout, stderr = self.client.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            return exit_status, output, error
        except Exception as e:
            print(f"[ERROR] Ошибка выполнения команды: {e}")
            return None, None, str(e)
    
    def clean_server(self):
        """Очистка сервера от существующих данных"""
        print("\n[INFO] Очистка сервера...")
        
        commands = [
            # Удаление старых установок Node.js
            "rm -rf /root/.nvm",
            "rm -rf /usr/local/bin/node",
            "rm -rf /usr/local/bin/npm",
            
            # Удаление старых проектов
            "rm -rf /root/shannon-uncontained",
            "rm -rf /root/shannon",
            
            # Очистка npm кэша
            "rm -rf /root/.npm",
            
            # Очистка временных файлов
            "rm -rf /tmp/shannon-*",
            
            # Проверка и очистка процессов
            "pkill -f 'node.*shannon' || true",
        ]
        
        for cmd in commands:
            print(f"  Выполнение: {cmd}")
            exit_status, output, error = self.execute_command(cmd)
            if exit_status != 0 and exit_status is not None:
                print(f"    ⚠️  Предупреждение: {error}")
        
        print("[OK] Очистка завершена\n")
    
    def check_system(self):
        """Проверка системы и установленных инструментов"""
        print("\n[INFO] Проверка системы...")
        
        checks = {
            "OS": "uname -a",
            "Node.js": "node --version 2>/dev/null || echo 'не установлен'",
            "npm": "npm --version 2>/dev/null || echo 'не установлен'",
            "Python": "python3 --version 2>/dev/null || echo 'не установлен'",
            "Git": "git --version 2>/dev/null || echo 'не установлен'",
            "nmap": "nmap --version 2>/dev/null | head -1 || echo 'не установлен'",
            "curl": "curl --version 2>/dev/null | head -1 || echo 'не установлен'",
            "wget": "wget --version 2>/dev/null | head -1 || echo 'не установлен'",
        }
        
        results = {}
        for name, cmd in checks.items():
            exit_status, output, error = self.execute_command(cmd)
            results[name] = output.strip() if output else "недоступно"
            print(f"  {name}: {results[name]}")
        
        return results
    
    def install_nodejs(self, version="20"):
        """Установка Node.js через nvm"""
        print(f"\n[INFO] Установка Node.js {version}...")
        
        commands = [
            # Установка nvm
            "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash",
            # Загрузка nvm в текущую сессию
            "export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm install {version}",
            "export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use {version}",
            "export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm alias default {version}",
        ]
        
        for cmd_template in commands:
            cmd = cmd_template.format(version=version)
            print(f"  Выполнение: {cmd[:80]}...")
            exit_status, output, error = self.execute_command(cmd)
            if exit_status != 0:
                print(f"    ⚠️  Ошибка: {error}")
            else:
                print(f"    ✅ Успешно")
        
        # Проверка установки
        exit_status, output, error = self.execute_command(
            "export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node --version"
        )
        if exit_status == 0:
            print(f"[OK] Node.js установлен: {output.strip()}")
        else:
            print(f"[ERROR] Ошибка установки Node.js")
    
    def install_system_tools(self):
        """Установка системных инструментов для пентестинга"""
        print("\n[INFO] Установка системных инструментов...")
        
        # Определение дистрибутива
        exit_status, os_info, _ = self.execute_command("cat /etc/os-release | grep ^ID=")
        distro = os_info.strip().split('=')[1].strip('"') if os_info else "ubuntu"
        
        if distro in ["ubuntu", "debian"]:
            commands = [
                "apt-get update",
                "apt-get install -y curl wget git build-essential python3 python3-pip",
                "apt-get install -y nmap subfinder amass katana whatweb nuclei || true",
            ]
        elif distro in ["centos", "rhel", "fedora"]:
            commands = [
                "yum update -y",
                "yum install -y curl wget git gcc gcc-c++ make python3 python3-pip",
                "yum install -y nmap || true",
            ]
        else:
            print(f"[WARN] Неизвестный дистрибутив: {distro}")
            return
        
        for cmd in commands:
            print(f"  Выполнение: {cmd[:80]}...")
            exit_status, output, error = self.execute_command(cmd, sudo=True)
            if exit_status != 0:
                print(f"    [WARN] Предупреждение: {error[:200]}")
            else:
                print(f"    [OK] Успешно")
    
    def setup_workspace(self, workspace_path="/root/shannon-uncontained"):
        """Создание рабочей директории"""
        print(f"\n[INFO] Создание рабочей директории: {workspace_path}...")
        
        commands = [
            f"mkdir -p {workspace_path}",
            f"chmod 755 {workspace_path}",
        ]
        
        for cmd in commands:
            exit_status, output, error = self.execute_command(cmd)
            if exit_status == 0:
                print(f"  [OK] {cmd}")
            else:
                print(f"  [ERROR] Ошибка: {error}")
    
    def close(self):
        """Закрытие подключения"""
        if self.client:
            self.client.close()
            print("\n[INFO] Подключение закрыто")

def main():
    """Основная функция"""
    print("=" * 60)
    print("Shannon-Uncontained Server Setup")
    print("=" * 60)
    
    # Параметры подключения
    HOST = "72.56.79.153"
    USERNAME = "root"
    PASSWORD = "m8J@2_6whwza6U"
    
    manager = ServerManager(HOST, USERNAME, PASSWORD)
    
    if not manager.connect():
        sys.exit(1)
    
    try:
        # Проверка системы
        manager.check_system()
        
        # Очистка сервера
        manager.clean_server()
        
        # Установка системных инструментов
        manager.install_system_tools()
        
        # Установка Node.js
        manager.install_nodejs(version="20")
        
        # Создание рабочей директории
        manager.setup_workspace()
        
        print("\n" + "=" * 60)
        print("[OK] Настройка сервера завершена!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.close()

if __name__ == "__main__":
    main()

