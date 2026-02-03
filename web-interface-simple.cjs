#!/usr/bin/env node
/**
 * Простой веб-интерфейс для Shannon-Uncontained
 * Только поле ввода, кнопка и вывод CLI
 */

const http = require('http');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

const PORT = 3000;
const PROJECT_PATH = process.cwd() || __dirname;

// Простой HTML интерфейс
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
            
            // Блокируем кнопку
            button.disabled = true;
            statusDiv.innerHTML = '<div class="status info">Запуск пентеста...</div>';
            outputDiv.textContent = 'Запуск...\\n';
            
            // Запускаем тест через SSE
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
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }
    
    // Главная страница
    if (req.url === '/' || req.url === '/index.html') {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(html);
        return;
    }
    
    // API: запуск теста через SSE
    if (req.url.startsWith('/api/run-test')) {
        const url = new URL(req.url, 'http://localhost');
        const target = url.searchParams.get('target');
        
        if (!target) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Target required' }));
            return;
        }
        
        // Настраиваем SSE
        res.writeHead(200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        });
        
        // Отправляем начальное сообщение
        res.write('data: ' + JSON.stringify({ type: 'output', data: 'Запуск пентеста для ' + target + '...\\n' }) + '\\n\\n');
        
        // Запускаем команду через bash с правильным окружением
        const command = 'bash -c "cd ' + PROJECT_PATH + ' && export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && export GOPATH=$HOME/go && source $HOME/.cargo/env 2>/dev/null || true && ./shannon.mjs generate \\"' + target + '\\" --workspace ./test-output 2>&1"';
        
        const child = exec(command, {
            cwd: PROJECT_PATH,
            shell: '/bin/bash',
            env: { 
                ...process.env, 
                PATH: process.env.PATH + ':/usr/local/go/bin:/root/go/bin:/root/.cargo/bin:/root/.local/bin:/usr/local/bin',
                GOPATH: '/root/go'
            }
        });
        
        // Отправляем вывод в реальном времени
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
    
    // 404
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Простой веб-интерфейс запущен на http://0.0.0.0:${PORT}`);
    console.log(`📁 Проект: ${PROJECT_PATH}`);
});
