#!/usr/bin/env python3
"""
Скрипт для автоматического обновления метрик в README.md
Обновляет количество строк кода, размер репозитория и другие метрики
"""

import os
import subprocess
import re
from pathlib import Path
from typing import Dict, Any

class MetricsUpdater:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.readme_path = self.project_root / "README.md"
        
    def get_lines_of_code(self) -> int:
        """Подсчитывает количество строк кода в проекте"""
        try:
            # Поиск всех файлов с кодом
            result = subprocess.run([
                "find", str(self.project_root), 
                "-name", "*.py", "-o", "-name", "*.ts", "-o", "-name", "*.tsx", 
                "-o", "-name", "*.js", "-o", "-name", "*.jsx"
            ], capture_output=True, text=True, check=True)
            
            files = result.stdout.strip().split('\n')
            total_lines = 0
            
            for file_path in files:
                if file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                            total_lines += lines
                    except (UnicodeDecodeError, PermissionError):
                        continue
                        
            return total_lines
        except subprocess.CalledProcessError:
            return 0
    
    def get_repository_size(self) -> str:
        """Получает размер репозитория в удобном формате"""
        try:
            result = subprocess.run([
                "du", "-sh", str(self.project_root)
            ], capture_output=True, text=True, check=True)
            
            size = result.stdout.strip().split('\t')[0]
            return size
        except subprocess.CalledProcessError:
            return "Unknown"
    
    def get_file_count(self) -> int:
        """Подсчитывает количество файлов в проекте"""
        try:
            result = subprocess.run([
                "find", str(self.project_root), "-type", "f",
                "-name", "*.py", "-o", "-name", "*.ts", "-o", "-name", "*.tsx",
                "-o", "-name", "*.js", "-o", "-name", "*.jsx", "-o", "-name", "*.md",
                "-o", "-name", "*.yml", "-o", "-name", "*.yaml", "-o", "-name", "*.json",
                "-o", "-name", "*.txt", "-o", "-name", "*.sh", "-o", "-name", "*.sql"
            ], capture_output=True, text=True, check=True)
            
            files = [f for f in result.stdout.strip().split('\n') if f]
            return len(files)
        except subprocess.CalledProcessError:
            return 0
    
    def get_system_info(self) -> Dict[str, Any]:
        """Получает информацию о системе"""
        info = {}
        
        # Получение информации о процессоре
        try:
            result = subprocess.run([
                "sysctl", "-n", "hw.ncpu"
            ], capture_output=True, text=True, check=True)
            info['cpu_cores'] = int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            info['cpu_cores'] = 0
        
        # Получение информации о памяти
        try:
            result = subprocess.run([
                "sysctl", "-n", "hw.memsize"
            ], capture_output=True, text=True, check=True)
            memory_bytes = int(result.stdout.strip())
            info['memory_gb'] = memory_bytes // (1024**3)
        except (subprocess.CalledProcessError, ValueError):
            info['memory_gb'] = 0
        
        # Получение информации о чипе
        try:
            result = subprocess.run([
                "sysctl", "-n", "machdep.cpu.brand_string"
            ], capture_output=True, text=True, check=True)
            info['chip'] = result.stdout.strip()
        except subprocess.CalledProcessError:
            info['chip'] = "Unknown"
        
        return info
    
    def update_readme_metrics(self):
        """Обновляет метрики в README.md"""
        if not self.readme_path.exists():
            print(f"❌ README.md не найден в {self.readme_path}")
            return False
        
        # Чтение текущего README
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Получение новых метрик
        lines_of_code = self.get_lines_of_code()
        repo_size = self.get_repository_size()
        file_count = self.get_file_count()
        system_info = self.get_system_info()
        
        print(f"📊 Обновление метрик:")
        print(f"   Строк кода: {lines_of_code:,}")
        print(f"   Размер репозитория: {repo_size}")
        print(f"   Количество файлов: {file_count}")
        print(f"   CPU ядер: {system_info['cpu_cores']}")
        print(f"   Память: {system_info['memory_gb']}GB")
        
        # Обновление бейджей
        content = self.update_badges(content, {
            'lines_of_code': lines_of_code,
            'repo_size': repo_size,
            'file_count': file_count,
            'cpu_cores': system_info['cpu_cores'],
            'memory_gb': system_info['memory_gb']
        })
        
        # Запись обновленного README
        with open(self.readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ README.md обновлен успешно!")
        return True
    
    def update_badges(self, content: str, metrics: Dict[str, Any]) -> str:
        """Обновляет бейджи в README.md"""
        
        # Обновление строк кода
        content = re.sub(
            r'!\[Lines of Code\]\(https://img\.shields\.io/badge/lines%20of%20code-\d+(?:,\d+)?-brightgreen\)',
            f'![Lines of Code](https://img.shields.io/badge/lines%20of%20code-{metrics["lines_of_code"]:,}-brightgreen)',
            content
        )
        
        # Обновление размера репозитория
        content = re.sub(
            r'!\[Repository Size\]\(https://img\.shields\.io/badge/repository%20size-[^-]+-blue\)',
            f'![Repository Size](https://img.shields.io/badge/repository%20size-{metrics["repo_size"]}-blue)',
            content
        )
        
        # Обновление количества файлов
        content = re.sub(
            r'!\[Files\]\(https://img\.shields\.io/badge/files-\d+-blue\)',
            f'![Files](https://img.shields.io/badge/files-{metrics["file_count"]}-blue)',
            content
        )
        
        # Обновление CPU ядер
        content = re.sub(
            r'!\[CPU Cores\]\(https://img\.shields\.io/badge/CPU%20cores-\d+-orange\)',
            f'![CPU Cores](https://img.shields.io/badge/CPU%20cores-{metrics["cpu_cores"]}-orange)',
            content
        )
        
        # Обновление памяти
        content = re.sub(
            r'!\[Memory\]\(https://img\.shields\.io/badge/memory-\d+GB-red\)',
            f'![Memory](https://img.shields.io/badge/memory-{metrics["memory_gb"]}GB-red)',
            content
        )
        
        return content
    
    def create_github_action(self):
        """Создает GitHub Action для автоматического обновления метрик"""
        workflows_dir = self.project_root / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        action_content = """name: Update Metrics

on:
  schedule:
    - cron: '0 0 * * 0'  # Каждое воскресенье в полночь
  workflow_dispatch:  # Ручной запуск

jobs:
  update-metrics:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Update metrics
      run: |
        python scripts/update_metrics.py
        
    - name: Commit changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add README.md
        git diff --quiet && git diff --staged --quiet || git commit -m "📊 Auto-update metrics"
        
    - name: Push changes
      uses: ad-m/github-push-action@master
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        branch: ${{ github.ref }}
"""
        
        action_path = workflows_dir / "update-metrics.yml"
        with open(action_path, 'w', encoding='utf-8') as f:
            f.write(action_content)
        
        print(f"✅ GitHub Action создан: {action_path}")

def main():
    """Основная функция"""
    updater = MetricsUpdater()
    
    print("🚀 Обновление метрик проекта reLink")
    print("=" * 50)
    
    # Обновление README
    success = updater.update_readme_metrics()
    
    if success:
        # Создание GitHub Action
        print("\n🔧 Создание GitHub Action для автоматического обновления...")
        updater.create_github_action()
        
        print("\n🎉 Все метрики обновлены успешно!")
        print("📝 GitHub Action создан для автоматического обновления каждое воскресенье")
    else:
        print("\n❌ Ошибка при обновлении метрик")

if __name__ == "__main__":
    main() 