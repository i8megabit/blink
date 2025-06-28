#!/usr/bin/env python3
"""
Скрипт для автоматического обновления метрик проекта в README.md
"""

import os
import subprocess
import re
from pathlib import Path

def get_lines_of_code():
    """Подсчет строк кода"""
    try:
        result = subprocess.run([
            'find', '.', '-name', '*.py', '-o', '-name', '*.ts', '-o', 
            '-name', '*.tsx', '-o', '-name', '*.js', '-o', '-name', '*.jsx'
        ], capture_output=True, text=True, cwd='.')
        
        files = result.stdout.strip().split('\n')
        files = [f for f in files if f and 'node_modules' not in f]
        
        if not files:
            return 0
            
        wc_result = subprocess.run(['wc', '-l'] + files, capture_output=True, text=True)
        lines = wc_result.stdout.strip().split('\n')[-1]
        return int(lines.split()[0])
    except Exception as e:
        print(f"Ошибка при подсчете строк кода: {e}")
        return 0

def get_repository_size():
    """Получение размера репозитория"""
    try:
        result = subprocess.run(['du', '-sh', '.'], capture_output=True, text=True)
        size = result.stdout.strip().split()[0]
        return size
    except Exception as e:
        print(f"Ошибка при получении размера репозитория: {e}")
        return "0B"

def get_files_count():
    """Подсчет количества файлов"""
    try:
        result = subprocess.run([
            'find', '.', '-type', 'f', '-name', '*.py', '-o', '-name', '*.ts', 
            '-o', '-name', '*.tsx', '-o', '-name', '*.js', '-o', '-name', '*.jsx'
        ], capture_output=True, text=True)
        
        files = [f for f in result.stdout.strip().split('\n') if f and 'node_modules' not in f]
        return len(files)
    except Exception as e:
        print(f"Ошибка при подсчете файлов: {e}")
        return 0

def get_system_info():
    """Получение информации о системе"""
    try:
        # CPU cores
        cpu_result = subprocess.run(['sysctl', '-n', 'hw.ncpu'], capture_output=True, text=True)
        cpu_cores = cpu_result.stdout.strip()
        
        # Memory
        mem_result = subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True)
        mem_bytes = int(mem_result.stdout.strip())
        mem_gb = mem_bytes / (1024**3)
        
        # Apple Silicon detection
        arch_result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
        is_apple_silicon = 'arm64' in arch_result.stdout.strip()
        
        return {
            'cpu_cores': cpu_cores,
            'memory_gb': int(mem_gb),
            'is_apple_silicon': is_apple_silicon
        }
    except Exception as e:
        print(f"Ошибка при получении информации о системе: {e}")
        return {'cpu_cores': '0', 'memory_gb': 0, 'is_apple_silicon': False}

def update_readme_metrics():
    """Обновление метрик в README.md"""
    readme_path = Path('README.md')
    
    if not readme_path.exists():
        print("README.md не найден")
        return
    
    # Получение метрик
    lines_of_code = get_lines_of_code()
    repo_size = get_repository_size()
    files_count = get_files_count()
    system_info = get_system_info()
    
    # Форматирование метрик
    lines_formatted = f"{lines_of_code:,}"
    cpu_text = f"{system_info['cpu_cores']} cores Apple M4" if system_info['is_apple_silicon'] else f"{system_info['cpu_cores']} cores"
    memory_text = f"{system_info['memory_gb']}GB"
    silicon_text = "M4 Optimized" if system_info['is_apple_silicon'] else "x86_64"
    
    # Чтение README.md
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Обновление бейджей метрик
    metrics_section = f"""## 📊 Проектные метрики

![Lines of Code](https://img.shields.io/badge/lines%20of%20code-{lines_formatted}-brightgreen.svg)
![Repository Size](https://img.shields.io/badge/repository%20size-{repo_size}-blue.svg)
![Files Count](https://img.shields.io/badge/files-{files_count}-orange.svg)
![CPU Cores](https://img.shields.io/badge/CPU-{cpu_text}-purple.svg)
![Memory](https://img.shields.io/badge/memory-{memory_text}-red.svg)
![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-{silicon_text}-yellow.svg)"""
    
    # Замена секции метрик
    pattern = r'## 📊 Проектные метрики\n\n.*?(?=\n## )'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, metrics_section, content, flags=re.DOTALL)
    else:
        # Если секция не найдена, добавляем после заголовка
        content = content.replace(
            '![Tests](https://img.shields.io/badge/tests-vitest%20+%20playwright-brightgreen.svg)\n',
            f'![Tests](https://img.shields.io/badge/tests-vitest%20+%20playwright-brightgreen.svg)\n\n{metrics_section}\n'
        )
    
    # Запись обновленного файла
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Метрики обновлены:")
    print(f"   📝 Строк кода: {lines_formatted}")
    print(f"   📦 Размер репозитория: {repo_size}")
    print(f"   📁 Файлов: {files_count}")
    print(f"   🖥️  CPU: {cpu_text}")
    print(f"   💾 Память: {memory_text}")
    print(f"   🍎 Apple Silicon: {silicon_text}")

if __name__ == "__main__":
    update_readme_metrics() 