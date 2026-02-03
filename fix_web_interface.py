#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление веб-интерфейса
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

def fix_web_interface(ssh):
    """Исправление веб-интерфейса"""
    print("=" * 70)
    print("ИСПРАВЛЕНИЕ ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/web-interface.cjs', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Исправление 1: Убрать убийство процесса при disconnect
        # Заменяем kill на просто логирование
        old_kill = """        // Обработка закрытия соединения клиентом
        req.on('close', () => {
            console.log('Client disconnected, killing process');
            if (!child.killed) {
                child.kill();
            }
        });"""
        
        new_kill = """        // Обработка закрытия соединения клиентом
        // НЕ убиваем процесс - позволяем пентесту завершиться
        req.on('close', () => {
            console.log('Client disconnected, but process continues...');
            // Процесс продолжит работу до завершения
            // Если нужно убить - используйте отдельный механизм управления
        });"""
        
        if old_kill in content:
            content = content.replace(old_kill, new_kill)
            print("[OK] Исправлено: процесс не убивается при disconnect")
        else:
            print("[WARNING] Код kill не найден в ожидаемом формате")
        
        # Исправление 2: Добавить удаление старых результатов перед запуском
        # Находим место где запускается команда
        command_start = content.find("const command = 'bash -c")
        if command_start != -1:
            # Находим начало блока где определяется target
            target_start = content.rfind("const target =", 0, command_start)
            if target_start != -1:
                # Добавляем удаление старых результатов перед командой
                cleanup_code = """
        // Удаляем старые результаты для свежего запуска
        const outputDir = path.join(PROJECT_PATH, 'test-output', 'repos', new URL(target).hostname);
        const fs = require('fs');
        try {
            if (fs.existsSync(outputDir)) {
                console.log('Cleaning up old results...');
                const { execSync } = require('child_process');
                execSync(`rm -rf "${outputDir}"`, { cwd: PROJECT_PATH });
            }
        } catch (e) {
            console.log('Warning: Could not clean old results:', e.message);
        }
        
"""
                # Вставляем перед командой
                content = content[:command_start] + cleanup_code + content[command_start:]
                print("[OK] Добавлено: удаление старых результатов перед запуском")
        
        # Сохраняем
        with sftp.open('shannon-uncontained/web-interface.cjs', 'w') as f:
            f.write(content)
        
        sftp.close()
        
        # Проверяем синтаксис
        print("\nПроверка синтаксиса...")
        stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -c web-interface.cjs 2>&1")
        syntax_check = stdout.read().decode('utf-8', errors='ignore')
        error_check = stderr.read().decode('utf-8', errors='ignore')
        
        if syntax_check or error_check:
            print("Ошибки:")
            print(syntax_check)
            print(error_check)
            return False
        else:
            print("[OK] Синтаксис корректен")
            return True
            
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def restart_web_interface(ssh):
    """Перезапуск веб-интерфейса"""
    print("\n" + "=" * 70)
    print("ПЕРЕЗАПУСК ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    # Останавливаем старый процесс
    print("\n1. Остановка старого процесса...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f 'web-interface.cjs' 2>&1")
    kill_output = stdout.read().decode('utf-8', errors='ignore')
    print(kill_output if kill_output else "Процесс остановлен")
    
    # Ждем немного
    import time
    time.sleep(2)
    
    # Запускаем новый
    print("\n2. Запуск нового процесса...")
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &")
    start_output = stdout.read().decode('utf-8', errors='ignore')
    print(start_output if start_output else "Запущен")
    
    # Проверяем что запустился
    time.sleep(2)
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    processes = stdout.read().decode('utf-8', errors='ignore')
    if processes:
        print("\n✅ Веб-интерфейс запущен:")
        print(processes)
    else:
        print("\n❌ Веб-интерфейс не запущен")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        if fix_web_interface(ssh):
            restart_web_interface(ssh)
            print("\n✅ ВЕБ-ИНТЕРФЕЙС ИСПРАВЛЕН И ПЕРЕЗАПУЩЕН!")
            print("\nИзменения:")
            print("1. Процесс не убивается при disconnect клиента")
            print("2. Старые результаты удаляются перед запуском (свежий пентест)")
        else:
            print("\n❌ Ошибка при исправлении")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

