#!/usr/bin/env node
/**
 * Простой веб-интерфейс для Shannon-Uncontained
 * Запуск: node web-interface.js
 * Доступ: http://localhost:3000
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

const PORT = 3000;
const PROJECT_PATH = process.cwd();

// HTML интерфейс
const html = `<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shannon-Uncontained Web Interface</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 { font-size: 2em; margin-bottom: 10px; }
        .subtitle { opacity: 0.9; }
        .content { padding: 30px; }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        input[type="text"], select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 16px;
            margin-bottom: 10px;
        }
        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: scale(1.05); }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .output {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            margin-top: 15px;
        }
        .status {
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 15px;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
        .status.info { background: #d1ecf1; color: #0c5460; }
        .workspace-list {
            list-style: none;
            padding: 0;
        }
        .workspace-item {
            padding: 10px;
            background: white;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }
        .workspace-item a {
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
        }
        .workspace-item a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔮 Shannon-Uncontained</h1>
            <p class="subtitle">AI Penetration Testing Framework</p>
        </header>
        <div class="content">
            <div class="section">
                <h2>🚀 Запустить тест</h2>
                <input type="text" id="target" placeholder="https://target.com" value="https://tcell.tj">
                <select id="framework">
                    <option value="express">Express.js</option>
                    <option value="fastapi">FastAPI</option>
                </select>
                <button onclick="runTest()">Запустить тест</button>
                <div id="testStatus"></div>
                <div id="testOutput" class="output" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h2>📊 Просмотр результатов</h2>
                <div id="workspaces"></div>
                <button onclick="loadWorkspaces()">Обновить список</button>
            </div>
            
            <div class="section">
                <h2>📈 Визуализация</h2>
                <select id="workspaceSelect">
                    <option value="">Выберите workspace...</option>
                </select>
                <select id="viewMode">
                    <option value="topology">Topology</option>
                    <option value="evidence">Evidence</option>
                    <option value="provenance">Provenance</option>
                </select>
                <button onclick="exportGraph()">Экспортировать граф</button>
                <div id="graphStatus"></div>
            </div>
        </div>
    </div>
    
    <script>
        async function runTest() {
            const target = document.getElementById('target').value;
            const framework = document.getElementById('framework').value;
            const statusDiv = document.getElementById('testStatus');
            const outputDiv = document.getElementById('testOutput');
            
            if (!target) {
                statusDiv.innerHTML = '<div class="status error">Введите URL цели</div>';
                return;
            }
            
            statusDiv.innerHTML = '<div class="status info">Запуск теста...</div>';
            outputDiv.style.display = 'block';
            outputDiv.textContent = 'Запуск...';
            
            try {
                const response = await fetch('/api/run-test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target, framework })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.innerHTML = '<div class="status success">Тест завершен успешно!</div>';
                    outputDiv.textContent = data.output || 'Готово';
                    loadWorkspaces();
                } else {
                    statusDiv.innerHTML = '<div class="status error">Ошибка: ' + data.error + '</div>';
                    outputDiv.textContent = data.output || data.error;
                }
            } catch (error) {
                statusDiv.innerHTML = '<div class="status error">Ошибка: ' + error.message + '</div>';
                outputDiv.textContent = error.message;
            }
        }
        
        async function loadWorkspaces() {
            try {
                const response = await fetch('/api/workspaces');
                const data = await response.json();
                
                const workspacesDiv = document.getElementById('workspaces');
                const select = document.getElementById('workspaceSelect');
                
                if (data.workspaces && data.workspaces.length > 0) {
                    let html = '<ul class="workspace-list">';
                    select.innerHTML = '<option value="">Выберите workspace...</option>';
                    
                    data.workspaces.forEach(ws => {
                        html += '<li class="workspace-item">';
                        html += '<a href="/workspace/' + encodeURIComponent(ws) + '" target="_blank">' + ws + '</a>';
                        html += '</li>';
                        select.innerHTML += '<option value="' + ws + '">' + ws + '</option>';
                    });
                    
                    html += '</ul>';
                    workspacesDiv.innerHTML = html;
                } else {
                    workspacesDiv.innerHTML = '<p>Нет доступных workspace</p>';
                }
            } catch (error) {
                console.error('Ошибка загрузки workspace:', error);
            }
        }
        
        async function exportGraph() {
            const workspace = document.getElementById('workspaceSelect').value;
            const viewMode = document.getElementById('viewMode').value;
            const statusDiv = document.getElementById('graphStatus');
            
            if (!workspace) {
                statusDiv.innerHTML = '<div class="status error">Выберите workspace</div>';
                return;
            }
            
            statusDiv.innerHTML = '<div class="status info">Экспорт графа...</div>';
            
            try {
                const response = await fetch('/api/export-graph', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ workspace, viewMode })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.innerHTML = '<div class="status success">Граф экспортирован! <a href="' + data.url + '" target="_blank">Открыть</a></div>';
                } else {
                    statusDiv.innerHTML = '<div class="status error">Ошибка: ' + data.error + '</div>';
                }
            } catch (error) {
                statusDiv.innerHTML = '<div class="status error">Ошибка: ' + error.message + '</div>';
            }
        }
        
        // Загрузить список workspace при загрузке страницы
        loadWorkspaces();
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
    
    // API: запуск теста
    if (req.url === '/api/run-test' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', async () => {
            try {
                const { target, framework } = JSON.parse(body);
                const command = `cd ${PROJECT_PATH} && export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && node shannon.mjs generate ${target} --framework ${framework} 2>&1`;
                
                const { stdout, stderr } = await execAsync(command, { timeout: 600000 });
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: true, output: stdout + stderr }));
            } catch (error) {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: error.message, output: error.stdout || error.stderr || '' }));
            }
        });
        return;
    }
    
    // API: список workspace
    if (req.url === '/api/workspaces') {
        try {
            const resultsDir = path.join(PROJECT_PATH, 'shannon-results', 'repos');
            const workspaces = fs.existsSync(resultsDir) 
                ? fs.readdirSync(resultsDir).filter(f => fs.statSync(path.join(resultsDir, f)).isDirectory())
                : [];
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ workspaces }));
        } catch (error) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: error.message }));
        }
        return;
    }
    
    // API: экспорт графа
    if (req.url === '/api/export-graph' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', async () => {
            try {
                const { workspace, viewMode } = JSON.parse(body);
                const workspacePath = path.join(PROJECT_PATH, 'shannon-results', 'repos', workspace);
                const outputFile = path.join(PROJECT_PATH, 'public', `graph-${viewMode}.html`);
                
                // Создать директорию public если нет
                const publicDir = path.join(PROJECT_PATH, 'public');
                if (!fs.existsSync(publicDir)) fs.mkdirSync(publicDir, { recursive: true });
                
                const command = `cd ${PROJECT_PATH} && export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && node shannon.mjs model export-html --workspace "${workspacePath}" --view ${viewMode} -o "${outputFile}" 2>&1`;
                
                const { stdout, stderr } = await execAsync(command, { timeout: 60000 });
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: true, url: `/public/graph-${viewMode}.html` }));
            } catch (error) {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: false, error: error.message }));
            }
        });
        return;
    }
    
    // Статические файлы
    if (req.url.startsWith('/public/')) {
        const filePath = path.join(PROJECT_PATH, req.url);
        if (fs.existsSync(filePath)) {
            const ext = path.extname(filePath);
            const contentType = ext === '.html' ? 'text/html' : 'application/octet-stream';
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(fs.readFileSync(filePath));
            return;
        }
    }
    
    // Workspace просмотр
    if (req.url.startsWith('/workspace/')) {
        const workspace = decodeURIComponent(req.url.replace('/workspace/', ''));
        const workspacePath = path.join(PROJECT_PATH, 'shannon-results', 'repos', workspace);
        const worldModelPath = path.join(workspacePath, 'world-model.json');
        
        if (fs.existsSync(worldModelPath)) {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(fs.readFileSync(worldModelPath));
            return;
        }
    }
    
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`Shannon-Uncontained Web Interface запущен на http://localhost:${PORT}`);
    console.log(`Доступен на http://72.56.79.153:${PORT}`);
});

