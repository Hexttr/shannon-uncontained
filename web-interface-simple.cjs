#!/usr/bin/env node
/**
 * Простой веб-интерфейс для Shannon-Uncontained
 * Просто форма + CLI вывод
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const PORT = 3000;
const PROJECT_PATH = __dirname || process.cwd();

const html = `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shannon-Uncontained</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #4ec9b0;
            margin-bottom: 20px;
            font-size: 24px;
        }
        .form {
            background: #252526;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            border: 1px solid #3e3e42;
        }
        .form-group {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        input[type="text"] {
            flex: 1;
            background: #1e1e1e;
            border: 1px solid #3e3e42;
            color: #d4d4d4;
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            border-radius: 3px;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #4ec9b0;
        }
        button {
            background: #0e639c;
            color: white;
            border: none;
            padding: 10px 20px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            border-radius: 3px;
            cursor: pointer;
        }
        button:hover {
            background: #1177bb;
        }
        button:disabled {
            background: #3e3e42;
            cursor: not-allowed;
        }
        .output {
            background: #1e1e1e;
            border: 1px solid #3e3e42;
            padding: 15px;
            border-radius: 5px;
            min-height: 400px;
            max-height: 80vh;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 13px;
            line-height: 1.5;
        }
        .status {
            color: #4ec9b0;
            margin-bottom: 10px;
        }
        .error {
            color: #f48771;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔮 Shannon-Uncontained CLI Interface</h1>
        
        <div class="form">
            <form id="testForm" onsubmit="return false;">
                <div class="form-group">
                    <input type="text" id="target" placeholder="https://target.com" value="https://tcell.tj" required>
                    <button type="button" id="runBtn" onclick="runTest()">Запустить тест</button>
                </div>
            </form>
            <div id="status" class="status"></div>
        </div>
        
        <div class="output" id="output">Готов к запуску теста. Введите URL и нажмите "Запустить тест".</div>
    </div>
    
    <script>
        function runTest() {
            const target = document.getElementById('target').value;
            const output = document.getElementById('output');
            const status = document.getElementById('status');
            const btn = document.getElementById('runBtn');
            
            if (!target) {
                status.textContent = 'Введите URL цели';
                status.className = 'status error';
                return;
            }
            
            btn.disabled = true;
            status.textContent = 'Запуск теста...';
            status.className = 'status';
            output.textContent = 'Запуск теста на ' + target + '...\\n\\n';
            
            fetch('/api/run-test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target: target })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                function readStream() {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            btn.disabled = false;
                            status.textContent = 'Тест завершен';
                            status.className = 'status';
                            return;
                        }
                        
                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\\n');
                        buffer = lines.pop() || '';
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    if (data.type === 'output' || data.type === 'error') {
                                        output.textContent += data.data;
                                        output.scrollTop = output.scrollHeight;
                                    } else if (data.type === 'done') {
                                        btn.disabled = false;
                                        status.textContent = data.code === 0 ? 'Тест завершен успешно' : 'Тест завершен с ошибкой (код: ' + data.code + ')';
                                        status.className = data.code === 0 ? 'status' : 'status error';
                                    }
                                } catch (e) {
                                    // Игнорировать ошибки парсинга
                                }
                            }
                        }
                        
                        readStream();
                    }).catch(error => {
                        btn.disabled = false;
                        status.textContent = 'Ошибка: ' + error.message;
                        status.className = 'status error';
                        output.textContent += '\\n[ERROR] ' + error.message;
                    });
                }
                
                readStream();
            })
            .catch(error => {
                btn.disabled = false;
                status.textContent = 'Ошибка: ' + error.message;
                status.className = 'status error';
                output.textContent += '\\n[ERROR] ' + error.message;
            });
        }
        
        // Запуск по Enter
        document.getElementById('target').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                runTest();
            }
        });
    </script>
</body>
</html>`;

const server = http.createServer((req, res) => {
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
    
    if (req.url === '/api/run-test' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const { target } = JSON.parse(body);
                // Использовать unbuffered вывод
                const command = `cd ${PROJECT_PATH} && export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && node shannon.mjs generate ${target} --no-ai 2>&1`;
                
                res.writeHead(200, {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'X-Accel-Buffering': 'no'
                });
                
                const child = exec(command, { 
                    cwd: PROJECT_PATH,
                    env: { 
                        ...process.env, 
                        NODE_ENV: 'production',
                        PYTHONUNBUFFERED: '1',
                        NODE_NO_WARNINGS: '1'
                    },
                    maxBuffer: 10 * 1024 * 1024 // 10MB
                });
                
                // Отключить буферизацию
                child.stdout.setEncoding('utf8');
                child.stderr.setEncoding('utf8');
                
                let hasData = false;
                
                child.stdout.on('data', (data) => {
                    hasData = true;
                    const text = data.toString();
                    try {
                        const message = 'data: ' + JSON.stringify({ type: 'output', data: text }) + '\\n\\n';
                        if (!res.destroyed) {
                            res.write(message);
                        }
                    } catch (e) {
                        // Игнорировать ошибки если соединение закрыто
                    }
                });
                
                child.stderr.on('data', (data) => {
                    hasData = true;
                    const text = data.toString();
                    try {
                        const message = 'data: ' + JSON.stringify({ type: 'error', data: text }) + '\\n\\n';
                        if (!res.destroyed) {
                            res.write(message);
                        }
                    } catch (e) {
                        // Игнорировать ошибки если соединение закрыто
                    }
                });
                
                child.on('close', (code) => {
                    try {
                        if (!hasData) {
                            res.write('data: ' + JSON.stringify({ type: 'output', data: '\\n[WARNING] Команда завершилась без вывода. Код: ' + code + '\\n' }) + '\\n\\n');
                        }
                        res.write('data: ' + JSON.stringify({ type: 'done', code: code }) + '\\n\\n');
                        res.end();
                    } catch (e) {
                        console.error('Close error:', e);
                    }
                });
                
                child.on('error', (error) => {
                    try {
                        res.write('data: ' + JSON.stringify({ type: 'error', data: 'Ошибка запуска: ' + error.message + '\\n' }) + '\\n\\n');
                        res.write('data: ' + JSON.stringify({ type: 'done', code: 1 }) + '\\n\\n');
                        res.end();
                    } catch (e) {
                        console.error('Error handler:', e);
                    }
                });
                
                req.on('close', () => {
                    if (!child.killed) {
                        child.kill('SIGTERM');
                    }
                });
            } catch (error) {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: error.message }));
            }
        });
        return;
    }
    
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
});

server.listen(PORT, '0.0.0.0', () => {
    console.log('Shannon-Uncontained Web Interface запущен на http://localhost:' + PORT);
    console.log('Доступен на http://72.56.79.153:' + PORT);
});

