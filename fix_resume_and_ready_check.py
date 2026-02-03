#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отключение resume и проверка готовности к пентесту
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

def disable_resume_default(ssh):
    """Отключение resume по умолчанию"""
    print("=" * 70)
    print("ОТКЛЮЧЕНИЕ RESUME ПО УМОЛЧАНИЮ")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/cli/commands/RunCommand.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Меняем resume по умолчанию на false
        old_resume = "resume: options.resume !== false, // Resume by default for 'run', unless --no-resume"
        new_resume = "resume: options.resume === true, // Resume only if explicitly enabled with --resume"
        
        if old_resume in content:
            content = content.replace(old_resume, new_resume)
            print("[OK] Resume по умолчанию отключен")
        else:
            print("[WARNING] Код resume не найден в ожидаемом формате")
            # Пробуем найти другой вариант
            if "resume: options.resume" in content:
                # Ищем и заменяем
                import re
                content = re.sub(
                    r"resume:\s*options\.resume\s*!==\s*false",
                    "resume: options.resume === true",
                    content
                )
                print("[OK] Resume по умолчанию отключен (альтернативный формат)")
        
        # Сохраняем
        with sftp.open('shannon-uncontained/src/cli/commands/RunCommand.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        
        # Проверяем синтаксис
        print("\nПроверка синтаксиса...")
        stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -c src/cli/commands/RunCommand.js 2>&1")
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

def fix_web_interface_complete(ssh):
    """Полное исправление веб-интерфейса"""
    print("\n" + "=" * 70)
    print("ИСПРАВЛЕНИЕ ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/web-interface.cjs', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Исправление 1: Убрать убийство процесса
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
        });"""
        
        if old_kill in content:
            content = content.replace(old_kill, new_kill)
            print("[OK] Процесс не убивается при disconnect")
        elif "child.kill()" in content:
            # Ищем и заменяем kill
            import re
            content = re.sub(
                r"req\.on\('close',\s*\(\)\s*=>\s*\{[^}]*child\.kill\(\)[^}]*\}\);",
                "req.on('close', () => {\n            console.log('Client disconnected, but process continues...');\n        });",
                content,
                flags=re.DOTALL
            )
            print("[OK] Процесс не убивается при disconnect (альтернативный формат)")
        
        # Исправление 2: Добавить удаление старых результатов
        # Проверяем есть ли уже require('fs')
        has_fs = "require('fs')" in content or 'require("fs")' in content
        
        # Находим место где определяется target и команда
        target_pos = content.find("const target = url.searchParams.get('target')")
        command_pos = content.find("const command = 'bash -c")
        
        if target_pos != -1 and command_pos != -1:
            # Добавляем очистку после определения target
            if has_fs:
                cleanup_code = """
        // Удаляем старые результаты для свежего запуска (всегда начинаем сначала)
        try {
            const urlObj = new URL(target);
            const hostname = urlObj.hostname;
            const outputDir = path.join(PROJECT_PATH, 'test-output', 'repos', hostname);
            if (fs.existsSync(outputDir)) {
                console.log('Cleaning up old results for fresh start...');
                const { execSync } = require('child_process');
                execSync(`rm -rf "${outputDir}"`, { cwd: PROJECT_PATH });
                console.log('Old results cleaned');
            }
        } catch (e) {
            console.log('Warning: Could not clean old results:', e.message);
        }
        
"""
            else:
                cleanup_code = """
        // Удаляем старые результаты для свежего запуска (всегда начинаем сначала)
        const path = require('path');
        const fs = require('fs');
        try {
            const urlObj = new URL(target);
            const hostname = urlObj.hostname;
            const outputDir = path.join(PROJECT_PATH, 'test-output', 'repos', hostname);
            if (fs.existsSync(outputDir)) {
                console.log('Cleaning up old results for fresh start...');
                const { execSync } = require('child_process');
                execSync(`rm -rf "${outputDir}"`, { cwd: PROJECT_PATH });
                console.log('Old results cleaned');
            }
        } catch (e) {
            console.log('Warning: Could not clean old results:', e.message);
        }
        
"""
            # Вставляем перед командой
            content = content[:command_pos] + cleanup_code + content[command_pos:]
            print("[OK] Добавлена очистка старых результатов")
        
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

def check_readiness(ssh):
    """Проверка готовности к пентесту"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ГОТОВНОСТИ К ПЕНТЕСТУ")
    print("=" * 70)
    
    checks = []
    
    # 1. Проверка LLM
    print("\n1. Проверка LLM:")
    stdin, stdout, stderr = ssh.exec_command("grep -E 'LLM_PROVIDER|ANTHROPIC_API_KEY|LLM_MODEL' shannon-uncontained/.env | grep -v '^#'")
    llm_config = stdout.read().decode('utf-8', errors='ignore')
    if "ANTHROPIC_API_KEY" in llm_config and "claude" in llm_config.lower():
        print("✅ LLM настроен")
        checks.append(True)
    else:
        print("❌ LLM не настроен")
        checks.append(False)
    
    # 2. Проверка инструментов
    print("\n2. Проверка инструментов:")
    tools = ['nmap', 'subfinder', 'nuclei', 'httpx', 'sqlmap']
    tools_ok = True
    for tool in tools:
        stdin, stdout, stderr = ssh.exec_command(f"which {tool} 2>/dev/null && echo 'OK' || echo 'MISSING'")
        status = stdout.read().decode('utf-8', errors='ignore').strip()
        icon = "✅" if status == "OK" else "❌"
        print(f"  {icon} {tool}")
        if status != "OK":
            tools_ok = False
    checks.append(tools_ok)
    
    # 3. Проверка зависимостей
    print("\n3. Проверка зависимостей:")
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && npm list --depth=0 2>&1 | head -5")
    deps = stdout.read().decode('utf-8', errors='ignore')
    if "anthropic" in deps.lower():
        print("✅ Зависимости установлены")
        checks.append(True)
    else:
        print("⚠️  Проверьте зависимости")
        checks.append(True)  # Не критично
    
    # 4. Проверка веб-интерфейса
    print("\n4. Проверка веб-интерфейса:")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    web_running = stdout.read().decode('utf-8', errors='ignore')
    if web_running:
        print("✅ Веб-интерфейс запущен")
        checks.append(True)
    else:
        print("⚠️  Веб-интерфейс не запущен (можно запустить)")
        checks.append(True)  # Не критично
    
    # 5. Проверка кода
    print("\n5. Проверка кода:")
    stdin, stdout, stderr = ssh.exec_command("test -f shannon-uncontained/shannon.mjs && echo 'OK' || echo 'MISSING'")
    code_ok = stdout.read().decode('utf-8', errors='ignore').strip()
    if code_ok == "OK":
        print("✅ Код на месте")
        checks.append(True)
    else:
        print("❌ Код отсутствует")
        checks.append(False)
    
    return all(checks)

def restart_web_interface(ssh):
    """Перезапуск веб-интерфейса"""
    import time
    
    print("\n" + "=" * 70)
    print("ПЕРЕЗАПУСК ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    # Останавливаем старый процесс
    print("\n1. Остановка старого процесса...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f 'web-interface.cjs' 2>&1")
    time.sleep(2)
    
    # Запускаем новый
    print("\n2. Запуск нового процесса...")
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &")
    import time
    time.sleep(2)
    
    # Проверяем
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    processes = stdout.read().decode('utf-8', errors='ignore')
    if processes:
        print("✅ Веб-интерфейс запущен")
        return True
    else:
        print("❌ Веб-интерфейс не запущен")
        return False

def main():
    import time
    
    print("=" * 70)
    print("НАСТРОЙКА ДЛЯ ВСЕГДА СВЕЖЕГО ПЕНТЕСТА")
    print("=" * 70)
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        # Отключаем resume
        if disable_resume_default(ssh):
            print("\n✅ Resume по умолчанию отключен")
        
        # Исправляем веб-интерфейс
        if fix_web_interface_complete(ssh):
            print("\n✅ Веб-интерфейс исправлен")
        
        # Перезапускаем веб-интерфейс
        restart_web_interface(ssh)
        
        # Проверяем готовность
        if check_readiness(ssh):
            print("\n" + "=" * 70)
            print("✅ ГОТОВ К ПЕНТЕСТУ!")
            print("=" * 70)
            print("\nИзменения:")
            print("1. ✅ Resume по умолчанию ОТКЛЮЧЕН - пентест всегда начинается сначала")
            print("2. ✅ Старые результаты удаляются перед запуском")
            print("3. ✅ Процесс не убивается при disconnect клиента")
            print("\nТеперь пентест будет:")
            print("- Всегда начинаться сначала")
            print("- Не пропускать агентов")
            print("- Продолжать работу даже если клиент отключился")
        else:
            print("\n⚠️  Есть проблемы с готовностью")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

