#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Развертывание упрощенного веб-интерфейса
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

def main():
    print("=" * 80)
    print("🚀 РАЗВЕРТЫВАНИЕ УПРОЩЕННОГО ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 80)
    
    # Читаем упрощенный файл
    print("\n📖 Чтение web-interface-simple.cjs...")
    try:
        with open('web-interface-simple.cjs', 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Файл прочитан ({len(content)} байт)")
    except FileNotFoundError:
        # Если файл не найден, создаем упрощенную версию напрямую
        print("⚠️  Файл не найден, создаю упрощенную версию...")
        content = """#!/usr/bin/env node
const http = require('http');
const { exec } = require('child_process');

const PORT = 3000;
const PROJECT_PATH = process.cwd() || __dirname;

const html = `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shannon Pentest</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #4ec9b0;
            margin-bottom: 20px;
            font-size: 24px;
        }
        .input-group {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            background: #252526;
            border: 2px solid #3e3e42;
            color: #d4d4d4;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            border-radius: 4px;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #4ec9b0;
        }
        button {
            padding: 12px 30px;
            background: #007acc;
            color: white;
            border: none;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            cursor: pointer;
            border-radius: 4px;
        }
        button:hover {
            background: #005a9e;
        }
        button:disabled {
            background: #3e3e42;
            cursor: not-allowed;
        }
        .output {
            background: #1e1e1e;
            border: 2px solid #3e3e42;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 600px;
            overflow-y: auto;
            min-height: 200px;
        }
        .status {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 4px;
            font-size: 14px;
        }
        .status.info {
            background: #264f78;
            color: #4ec9b0;
        }
        .status.success {
            background: #0e639c;
            color: #4ec9b0;
        }
        .status.error {
            background: #a1260d;
            color: #f48771;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔮 Shannon Pentest</h1>
        
        <div class="input-group">
            <input type="text" id="target" placeholder="https://example.com" value="https://tcell.tj">
            <button id="runBtn" onclick="runTest()">Запустить</button>
        </div>
        
        <div id="status"></div>
        <div id="output" class="output">Готов к запуску...</div>
    </div>
    
    <script>
        function runTest() {
            const target = document.getElementById('target').value.trim();
            const outputDiv = document.getElementById('output');
            const statusDiv = document.getElementById('status');
            const button = document.getElementById('runBtn');
            
            if (!target) {
                statusDiv.innerHTML = '<div class="status error">Введите URL цели</div>';
                return;
            }
            
            button.disabled = true;
            statusDiv.innerHTML = '<div class="status info">Запуск пентеста...</div>';
            outputDiv.textContent = 'Запуск...\\n';
            
            const eventSource = new EventSource('/api/run-test?target=' + encodeURIComponent(target));
            
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'output') {
                    outputDiv.textContent += data.data;
                    outputDiv.scrollTop = outputDiv.scrollHeight;
                } else if (data.type === 'error') {
                    outputDiv.textContent += '[ERROR] ' + data.data + '\\n';
                    outputDiv.scrollTop = outputDiv.scrollHeight;
                } else if (data.type === 'done') {
                    eventSource.close();
                    button.disabled = false;
                    if (data.code === 0) {
                        statusDiv.innerHTML = '<div class="status success">Пентест завершен успешно!</div>';
                    } else {
                        statusDiv.innerHTML = '<div class="status error">Пентест завершен с ошибкой (код: ' + data.code + ')</div>';
                    }
                }
            };
            
            eventSource.onerror = function(error) {
                eventSource.close();
                button.disabled = false;
                statusDiv.innerHTML = '<div class="status error">Ошибка соединения</div>';
                outputDiv.textContent += '\\n[ERROR] Соединение прервано\\n';
            };
        }
    </script>
</body>
</html>`;

const server = http.createServer(async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    if (req.url === '/' || req.url === '/index.html') {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(html);
        return;
    }
    
    if (req.url.startsWith('/api/run-test')) {
        const url = new URL(req.url, 'http://localhost');
        const target = url.searchParams.get('target');
        
        if (!target) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Target required' }));
            return;
        }
        
        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        });
        
        res.write('data: ' + JSON.stringify({ type: 'output', data: 'Запуск пентеста для ' + target + '...\\n' }) + '\\n\\n');
        
        const command = 'cd ' + PROJECT_PATH + ' && export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && export GOPATH=$HOME/go && source $HOME/.cargo/env 2>/dev/null || true && ./shannon.mjs generate "' + target + '" --workspace ./test-output 2>&1';
        
        const child = exec(command, {
            cwd: PROJECT_PATH,
            env: { ...process.env, PATH: process.env.PATH + ':/usr/local/go/bin:/root/go/bin:/root/.cargo/bin:/root/.local/bin:/usr/local/bin' }
        });
        
        child.stdout.on('data', (data) => {
            const lines = data.toString().split('\\n');
            for (const line of lines) {
                if (line.trim()) {
                    res.write('data: ' + JSON.stringify({ type: 'output', data: line + '\\n' }) + '\\n\\n');
                }
            }
        });
        
        child.stderr.on('data', (data) => {
            const lines = data.toString().split('\\n');
            for (const line of lines) {
                if (line.trim()) {
                    res.write('data: ' + JSON.stringify({ type: 'error', data: line + '\\n' }) + '\\n\\n');
                }
            }
        });
        
        child.on('close', (code) => {
            res.write('data: ' + JSON.stringify({ type: 'done', code: code }) + '\\n\\n');
            res.end();
        });
        
        child.on('error', (error) => {
            res.write('data: ' + JSON.stringify({ type: 'error', data: error.message }) + '\\n\\n');
            res.write('data: ' + JSON.stringify({ type: 'done', code: 1 }) + '\\n\\n');
            res.end();
        });
        
        return;
    }
    
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
});

server.listen(PORT, '0.0.0.0', () => {
    console.log('🚀 Простой веб-интерфейс запущен на http://0.0.0.0:' + PORT);
    console.log('📁 Проект: ' + PROJECT_PATH);
});
"""
        print(f"✅ Упрощенная версия создана ({len(content)} байт)")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Подключаемся к серверу
    print("\n🔌 Подключение к серверу...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)
    
    PROJECT_PATH = "/root/shannon-uncontained"
    
    # Останавливаем старый процесс
    print("\n🛑 Остановка старого процесса...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f 'web-interface' || true")
    stdout.read()
    import time
    time.sleep(2)
    
    # Загружаем новый файл (заменяем старый)
    print("📤 Загрузка упрощенного интерфейса...")
    sftp = ssh.open_sftp()
    try:
        remote_file = sftp.file(f"{PROJECT_PATH}/web-interface.cjs", 'w')
        remote_file.write(content)
        remote_file.close()
        print("✅ Файл загружен")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        sftp.close()
        ssh.close()
        return
    finally:
        sftp.close()
    
    # Устанавливаем права
    stdin, stdout, stderr = ssh.exec_command(f"chmod +x {PROJECT_PATH}/web-interface.cjs")
    stdout.read()
    
    # Проверяем синтаксис
    print("\n✅ Проверка синтаксиса...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {PROJECT_PATH} && node -c web-interface.cjs")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("✅ Синтаксис корректен")
    else:
        error = stderr.read().decode('utf-8')
        print(f"⚠️  Ошибки синтаксиса:\n{error[:500]}")
    
    # Запускаем веб-интерфейс
    print("\n🚀 Запуск веб-интерфейса...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {PROJECT_PATH} && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &"
    )
    stdout.read()
    time.sleep(2)
    
    # Проверяем что запустился
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    output = stdout.read().decode('utf-8')
    if output.strip():
        print("✅ Веб-интерфейс запущен")
        print(f"   Процесс: {output.strip()[:100]}")
    else:
        print("⚠️  Процесс не найден, проверяем логи...")
        stdin, stdout, stderr = ssh.exec_command("tail -30 /tmp/web-interface.log")
        log_output = stdout.read().decode('utf-8')
        if log_output:
            print(f"   Логи:\n{log_output}")
    
    # Проверяем порт
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp 2>/dev/null | grep :3000 || netstat -tlnp 2>/dev/null | grep :3000")
    port_output = stdout.read().decode('utf-8')
    if port_output.strip():
        print(f"✅ Порт 3000 слушается")
    else:
        print("⚠️  Порт 3000 не найден")
    
    ssh.close()
    
    print("\n" + "=" * 80)
    print("✅ ГОТОВО")
    print("=" * 80)
    print("\n🌐 Упрощенный веб-интерфейс:")
    print("   http://72.56.79.153:3000")
    print("\n📝 Функции:")
    print("   - Поле для ввода URL цели")
    print("   - Кнопка запуска")
    print("   - Вывод CLI в реальном времени")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

