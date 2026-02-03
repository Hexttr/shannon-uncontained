#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Развертывание исправления на сервер
"""

import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def main():
    print("=" * 60)
    print("Развертывание исправления")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Создать директорию если нужно
        exit_status, output, error = execute_command(
            client,
            f"mkdir -p {PROJECT_PATH}/src/local-source-generator/v2/adaptation"
        )
        
        # Создать файл domain-profiler.js
        domain_profiler_content = '''/**
 * Domain Profiler - Tracks domain metrics over time for drift detection
 */

import { fs, path } from 'zx';

export class DomainProfiler {
    constructor(options = {}) {
        this.profileDir = options.profileDir || path.join(process.cwd(), 'domain-profiles');
        this.profiles = new Map();
    }

    async init() {
        await fs.ensureDir(this.profileDir);
        return this;
    }

    async updateProfile(domain, metrics) {
        const profilePath = path.join(this.profileDir, `${domain}.json`);
        
        let profile = {
            domain,
            firstSeen: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
            scans: [],
            currentMetrics: metrics,
            drift_score: 0
        };

        try {
            if (await fs.pathExists(profilePath)) {
                const existing = JSON.parse(await fs.readFile(profilePath, 'utf-8'));
                profile.firstSeen = existing.firstSeen || profile.firstSeen;
                profile.scans = existing.scans || [];
            }
        } catch (err) {
            // Start fresh
        }

        profile.scans.push({
            timestamp: new Date().toISOString(),
            metrics: { ...metrics }
        });

        if (profile.scans.length > 10) {
            profile.scans = profile.scans.slice(-10);
        }

        if (profile.scans.length > 1) {
            const previous = profile.scans[profile.scans.length - 2].metrics;
            const current = metrics;
            
            let changes = 0;
            let total = 0;
            
            for (const key in current) {
                if (previous[key] !== undefined) {
                    total++;
                    const change = Math.abs((current[key] || 0) - (previous[key] || 0));
                    const threshold = previous[key] * 0.2;
                    if (change > threshold) {
                        changes++;
                    }
                }
            }
            
            profile.drift_score = total > 0 ? changes / total : 0;
        }

        profile.lastUpdated = new Date().toISOString();
        profile.currentMetrics = metrics;

        await fs.writeFile(profilePath, JSON.stringify(profile, null, 2));
        this.profiles.set(domain, profile);
        return profile;
    }

    hasDrifted(domain, threshold = 0.3) {
        const profile = this.profiles.get(domain);
        if (!profile) return false;
        return profile.drift_score >= threshold;
    }

    getProfile(domain) {
        return this.profiles.get(domain) || null;
    }
}
'''
        
        # Записать файл через heredoc
        command = f"""cat > {PROJECT_PATH}/src/local-source-generator/v2/adaptation/domain-profiler.js << 'ENDOFFILE'
{domain_profiler_content}
ENDOFFILE
"""
        exit_status, output, error = execute_command(client, command)
        
        if exit_status == 0:
            print("[OK] Файл domain-profiler.js создан")
        else:
            print(f"[ERROR] Ошибка создания файла: {error}")
            return
        
        # Проверка
        exit_status, output, error = execute_command(
            client,
            f"test -f {PROJECT_PATH}/src/local-source-generator/v2/adaptation/domain-profiler.js && echo 'exists'"
        )
        if 'exists' in output:
            print("[OK] Файл проверен")
        else:
            print("[ERROR] Файл не найден после создания")
        
        print("\n[OK] Исправление развернуто")
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

