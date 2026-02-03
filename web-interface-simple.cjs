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
            color: #f48771;
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
            output.textContent = 'Запуск теста на ' + target + '...\n\n';
            
            console.log('[CLIENT] Starting fetch to /api/run-test');
            console.log('[CLIENT] Target:', target);
            
            fetch('/api/run-test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target: target })
            })
            .then(response => {
                console.log('[CLIENT] Response status:', response.status);
                console.log('[CLIENT] Response headers:', response.headers.get('content-type'));
                
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let chunkCount = 0;
                
                function readStream() {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            console.log('[CLIENT] Stream done, chunks received:', chunkCount);
                            btn.disabled = false;
                            status.textContent = 'Тест завершен';
                            status.className = 'status';
                            return;
                        }
                        
                        chunkCount++;
                        console.log('[CLIENT] Received chunk', chunkCount, 'size:', value ? value.length : 0);
                        
                        buffer += decoder.decode(value, { stream: true });
                        // Разделить по двойным переносам строк (SSE формат)
                        // ВАЖНО: используем реальные символы новой строки, не строку "\\n"
                        const parts = buffer.split('\n\n');
                        buffer = parts.pop() || ''; // Сохранить неполную часть
                        
                        for (const part of parts) {
                            if (!part.trim()) continue;
                            
                            // Найти строку начинающуюся с 'data: '
                            const lines = part.split('\n');
                            for (const line of lines) {
                                if (line.trim().startsWith('data: ')) {
                                    try {
                                        const jsonStr = line.slice(6).trim();
                                        if (!jsonStr) continue;
                                        const data = JSON.parse(jsonStr);
                                        console.log('[CLIENT] Parsed data:', data.type, 'data length:', data.data ? data.data.length : 0);
                                        
                                        if (data.type === 'output' || data.type === 'error') {
                                            if (data.data) {
                                                // Заменить экранированные символы на реальные
                                                // data.data уже содержит реальные символы новой строки из JSON
                                                const displayData = data.data;
                                                output.textContent += displayData;
                                                // Автопрокрутка
                                                output.scrollTop = output.scrollHeight;
                                            }
                                        } else if (data.type === 'done') {
                                            console.log('[CLIENT] Test done, code:', data.code);
                                            btn.disabled = false;
                                            status.textContent = data.code === 0 ? 'Тест завершен успешно' : 'Тест завершен с ошибкой (код: ' + data.code + ')';
                                            status.className = data.code === 0 ? 'status' : 'status error';
                                            return;
                                        }
                                    } catch (e) {
                                        console.error('[CLIENT] Parse error:', e, 'line:', line.substring(0, 200));
                                        // Попробовать показать сырые данные если парсинг не удался
                                        if (line.length > 6) {
                                            output.textContent += '\n[RAW] ' + line.substring(0, 100) + '\n';
                                            output.scrollTop = output.scrollHeight;
                                        }
                                    }
                                } else if (line.trim() && !line.startsWith('data:') && !line.startsWith('event:')) {
                                    // Показать необработанные строки
                                    output.textContent += line + '\n';
                                    output.scrollTop = output.scrollHeight;
                                }
                            }
                        }
                        
                        readStream();
                    }).catch(error => {
                        console.error('[CLIENT] Read error:', error);
                        btn.disabled = false;
                        status.textContent = 'Ошибка: ' + error.message;
                        status.className = 'status error';
                        output.textContent += '\n[ERROR] ' + error.message;
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
                
                if (!target) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: false, error: 'Target is required' }));
                    return;
                }
                // Использовать unbuffered вывод
                // Извлечь домен из URL для определения workspace
                let domain = target.replace(/^https?:\/\//, '').replace(/\/.*$/, '').split(':')[0];
                // Экранировать специальные символы в домене
                domain = domain.replace(/[^a-zA-Z0-9.-]/g, '');
                const workspacePath = `${PROJECT_PATH}/shannon-results/repos/${domain}`;
                
                // Удалить существующий workspace чтобы запустить полный тест
                // Используем Ollama (убрали --no-ai)
                const command = `cd ${PROJECT_PATH} && rm -rf "${workspacePath}" 2>/dev/null; export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && node shannon.mjs generate "${target}" 2>&1`;
                console.log('[WEB] Starting test:', target);
                console.log('[WEB] Command:', command);
                console.log('[WEB] PROJECT_PATH:', PROJECT_PATH);
                
                // Установить заголовки ПЕРЕД отправкой данных
                res.writeHead(200, {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'X-Accel-Buffering': 'no'
                });
                
                // Отправить начальное сообщение
                try {
                    res.write('data: ' + JSON.stringify({ type: 'output', data: 'Запуск теста на ' + target + '...\n' }) + '\n\n');
                } catch (e) {
                    console.error('[WEB] Initial write error:', e);
                }
                
                console.log('[WEB] Executing command:', command);
                
                const child = exec(command, { 
                    cwd: PROJECT_PATH,
                    env: { 
                        ...process.env, 
                        NODE_ENV: 'production',
                        PYTHONUNBUFFERED: '1',
                        NODE_NO_WARNINGS: '1'
                    },
                    maxBuffer: 10 * 1024 * 1024, // 10MB
                    killSignal: 'SIGKILL', // Использовать SIGKILL вместо SIGTERM
                    timeout: 0 // Без таймаута
                }, (error, stdout, stderr) => {
                    console.log('[WEB] Exec callback - error:', error ? error.message : 'none');
                    console.log('[WEB] Exec callback - stdout length:', stdout ? stdout.length : 0);
                    console.log('[WEB] Exec callback - stderr length:', stderr ? stderr.length : 0);
                });
                
                console.log('[WEB] Child process PID:', child.pid);
                
                // Отключить буферизацию
                child.stdout.setEncoding('utf8');
                child.stderr.setEncoding('utf8');
                
                let hasData = false;
                let stdoutChunks = 0;
                let stderrChunks = 0;
                
                child.stdout.on('data', (data) => {
                    hasData = true;
                    stdoutChunks++;
                    const text = data.toString();
                    console.log('[WEB] stdout chunk', stdoutChunks, ':', text.length, 'bytes, preview:', text.substring(0, 100));
                    try {
                        const message = 'data: ' + JSON.stringify({ type: 'output', data: text }) + '\n\n';
                        if (!res.destroyed) {
                            res.write(message);
                        } else {
                            console.log('[WEB] Response destroyed, stopping stdout');
                        }
                    } catch (e) {
                        console.error('[WEB] Write error:', e);
                    }
                });
                
                child.stderr.on('data', (data) => {
                    hasData = true;
                    stderrChunks++;
                    const text = data.toString();
                    console.log('[WEB] stderr chunk', stderrChunks, ':', text.length, 'bytes');
                    try {
                        const message = 'data: ' + JSON.stringify({ type: 'error', data: text }) + '\n\n';
                        if (!res.destroyed) {
                            res.write(message);
                        } else {
                            console.log('[WEB] Response destroyed, stopping stderr');
                        }
                    } catch (e) {
                        console.error('[WEB] stderr write error:', e);
                    }
                });
                
                child.on('close', (code, signal) => {
                    console.log('[WEB] Process closed - code:', code, 'signal:', signal, 'hasData:', hasData, 'stdoutChunks:', stdoutChunks, 'stderrChunks:', stderrChunks);
                    try {
                        if (!hasData) {
                            console.log('[WEB] No data received, sending warning');
                            res.write('data: ' + JSON.stringify({ type: 'output', data: '\n[WARNING] Команда завершилась без вывода. Код: ' + code + ', сигнал: ' + (signal || 'none') + '\n' }) + '\n\n');
                        }
                        res.write('data: ' + JSON.stringify({ type: 'done', code: code }) + '\n\n');
                        res.end();
                    } catch (e) {
                        console.error('[WEB] Close error:', e);
                    }
                });
                
                child.on('error', (error) => {
                    console.error('[WEB] Process error:', error);
                    try {
                        res.write('data: ' + JSON.stringify({ type: 'error', data: 'Ошибка запуска: ' + error.message + '\n' }) + '\n\n');
                        res.write('data: ' + JSON.stringify({ type: 'done', code: 1 }) + '\n\n');
                        res.end();
                    } catch (e) {
                        console.error('[WEB] Error handler:', e);
                    }
                });
                
                child.on('exit', (code, signal) => {
                    console.log('[WEB] Process exit - code:', code, 'signal:', signal);
                });
                
                // НЕ убивать процесс при закрытии соединения - пусть тест выполняется
                // req.on('close', () => {
                //     if (!child.killed) {
                //         child.kill('SIGTERM');
                //     }
                // });
            } catch (error) {
                console.error('[WEB] Request error:', error);
                if (!res.headersSent) {
                    res.writeHead(500, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({ success: false, error: error.message }));
                } else {
                    res.write('data: ' + JSON.stringify({ type: 'error', data: 'Ошибка: ' + error.message + '\n' }) + '\n\n');
                    res.write('data: ' + JSON.stringify({ type: 'done', code: 1 }) + '\n\n');
                    res.end();
                }
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

