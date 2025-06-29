#!/usr/bin/env python3
"""
🧪 АНАЛИЗАТОР ПОКРЫТИЯ ТЕСТАМИ МИКРОСЕРВИСОВ reLink
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple
import requests
import time

class TestCoverageAnalyzer:
    """Анализатор покрытия тестами микросервисов"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.services = {
            'router': {'port': 8001, 'path': 'router'},
            'benchmark': {'port': 8002, 'path': 'benchmark'},
            'relink': {'port': 8003, 'path': 'relink'},
            'backend': {'port': 8004, 'path': 'backend'},
            'llm_tuning': {'port': 8007, 'path': 'llm_tuning'},
            'monitoring': {'port': 8005, 'path': 'monitoring'},
            'testing': {'port': 8006, 'path': 'testing'},
            'frontend': {'port': 3000, 'path': 'frontend'}
        }
        self.results = {}
    
    def analyze_service_structure(self, service_name: str) -> Dict:
        """Анализ структуры сервиса"""
        service_path = self.project_root / self.services[service_name]['path']
        
        if not service_path.exists():
            return {
                'exists': False,
                'test_files': 0,
                'source_files': 0,
                'test_coverage': 0.0
            }
        
        # Подсчет файлов исходного кода
        source_files = 0
        test_files = 0
        
        for root, dirs, files in os.walk(service_path):
            # Исключаем служебные папки
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            for file in files:
                file_path = Path(root) / file
                
                # Python файлы
                if file.endswith('.py'):
                    if 'test' in file.lower() or 'tests' in str(file_path):
                        test_files += 1
                    else:
                        source_files += 1
                
                # TypeScript/JavaScript файлы
                elif file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    if 'test' in file.lower() or 'spec' in file.lower():
                        test_files += 1
                    else:
                        source_files += 1
        
        test_coverage = (test_files / max(source_files, 1)) * 100 if source_files > 0 else 0.0
        
        return {
            'exists': True,
            'test_files': test_files,
            'source_files': source_files,
            'test_coverage': round(test_coverage, 2)
        }
    
    def run_service_tests(self, service_name: str) -> Dict:
        """Запуск тестов сервиса"""
        service_path = self.project_root / self.services[service_name]['path']
        
        if not service_path.exists():
            return {
                'success': False,
                'error': 'Service directory not found',
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
        
        try:
            # Проверяем наличие тестов
            test_dirs = ['tests', 'test', '__tests__']
            test_files = []
            
            for test_dir in test_dirs:
                test_path = service_path / test_dir
                if test_path.exists():
                    test_files.extend(list(test_path.rglob('test_*.py')))
                    test_files.extend(list(test_path.rglob('*_test.py')))
            
            if not test_files:
                return {
                    'success': True,
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0,
                    'message': 'No test files found'
                }
            
            # Запускаем pytest
            result = subprocess.run(
                ['python', '-m', 'pytest', str(service_path), '-v', '--tb=short'],
                capture_output=True,
                text=True,
                cwd=service_path
            )
            
            # Парсим результаты
            output = result.stdout + result.stderr
            
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            
            for line in output.split('\n'):
                if 'passed' in line and 'failed' in line:
                    # Пример: "3 passed, 1 failed in 2.34s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i > 0:
                            if parts[i-1] == 'passed':
                                tests_passed = int(part)
                            elif parts[i-1] == 'failed':
                                tests_failed = int(part)
                    tests_run = tests_passed + tests_failed
                    break
            
            return {
                'success': result.returncode == 0,
                'tests_run': tests_run,
                'tests_passed': tests_passed,
                'tests_failed': tests_failed,
                'output': output[:1000]  # Ограничиваем вывод
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0
            }
    
    def check_service_health(self, service_name: str) -> Dict:
        """Проверка здоровья сервиса"""
        port = self.services[service_name]['port']
        
        try:
            response = requests.get(f'http://localhost:{port}/health', timeout=5)
            return {
                'healthy': response.status_code == 200,
                'status_code': response.status_code,
                'response': response.json() if response.status_code == 200 else None
            }
        except requests.exceptions.RequestException as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def analyze_all_services(self) -> Dict:
        """Анализ всех сервисов"""
        print("🔍 Анализ покрытия тестами микросервисов reLink...")
        print("=" * 60)
        
        total_source_files = 0
        total_test_files = 0
        total_tests_run = 0
        total_tests_passed = 0
        healthy_services = 0
        
        for service_name in self.services:
            print(f"\n📊 Анализ сервиса: {service_name.upper()}")
            print("-" * 40)
            
            # Анализ структуры
            structure = self.analyze_service_structure(service_name)
            print(f"📁 Структура: {structure['source_files']} исходных файлов, {structure['test_files']} тестовых файлов")
            print(f"📈 Покрытие тестами: {structure['test_coverage']}%")
            
            # Запуск тестов
            test_results = self.run_service_tests(service_name)
            print(f"🧪 Тесты: {test_results['tests_run']} запущено, {test_results['tests_passed']} прошло, {test_results['tests_failed']} упало")
            
            # Проверка здоровья
            health = self.check_service_health(service_name)
            status = "✅ Здоров" if health['healthy'] else "❌ Недоступен"
            print(f"💚 Статус: {status}")
            
            # Сбор статистики
            total_source_files += structure['source_files']
            total_test_files += structure['test_files']
            total_tests_run += test_results['tests_run']
            total_tests_passed += test_results['tests_passed']
            if health['healthy']:
                healthy_services += 1
            
            self.results[service_name] = {
                'structure': structure,
                'tests': test_results,
                'health': health
            }
        
        # Общая статистика
        print("\n" + "=" * 60)
        print("📊 ОБЩАЯ СТАТИСТИКА")
        print("=" * 60)
        
        overall_coverage = (total_test_files / max(total_source_files, 1)) * 100
        test_success_rate = (total_tests_passed / max(total_tests_run, 1)) * 100
        service_health_rate = (healthy_services / len(self.services)) * 100
        
        print(f"📁 Всего исходных файлов: {total_source_files}")
        print(f"🧪 Всего тестовых файлов: {total_test_files}")
        print(f"📈 Общее покрытие тестами: {overall_coverage:.2f}%")
        print(f"✅ Тестов запущено: {total_tests_run}")
        print(f"✅ Тестов прошло: {total_tests_passed}")
        print(f"❌ Тестов упало: {total_tests_run - total_tests_passed}")
        print(f"📊 Успешность тестов: {test_success_rate:.2f}%")
        print(f"💚 Здоровых сервисов: {healthy_services}/{len(self.services)} ({service_health_rate:.2f}%)")
        
        return {
            'total_source_files': total_source_files,
            'total_test_files': total_test_files,
            'overall_coverage': overall_coverage,
            'total_tests_run': total_tests_run,
            'total_tests_passed': total_tests_passed,
            'test_success_rate': test_success_rate,
            'healthy_services': healthy_services,
            'service_health_rate': service_health_rate,
            'services': self.results
        }
    
    def generate_report(self, results: Dict):
        """Генерация отчета"""
        report_path = self.project_root / 'reports' / 'test_coverage_report.json'
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Отчет сохранен: {report_path}")
        
        # Создание HTML отчета
        self.generate_html_report(results, report_path.parent / 'test_coverage_report.html')
    
    def generate_html_report(self, results: Dict, output_path: Path):
        """Генерация HTML отчета"""
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет покрытия тестами reLink</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric h3 {{ margin: 0; color: #666; font-size: 14px; }}
        .metric .value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .service {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 8px; }}
        .service h3 {{ margin: 0 0 10px 0; color: #333; }}
        .service-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
        .status {{ padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .status.healthy {{ background: #d4edda; color: #155724; }}
        .status.unhealthy {{ background: #f8d7da; color: #721c24; }}
        .coverage {{ background: #e2e3e5; padding: 5px 10px; border-radius: 4px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Отчет покрытия тестами reLink</h1>
        
        <div class="summary">
            <div class="metric">
                <h3>Исходных файлов</h3>
                <div class="value">{results['total_source_files']}</div>
            </div>
            <div class="metric">
                <h3>Тестовых файлов</h3>
                <div class="value">{results['total_test_files']}</div>
            </div>
            <div class="metric">
                <h3>Покрытие тестами</h3>
                <div class="value">{results['overall_coverage']:.1f}%</div>
            </div>
            <div class="metric">
                <h3>Тестов прошло</h3>
                <div class="value">{results['total_tests_passed']}/{results['total_tests_run']}</div>
            </div>
            <div class="metric">
                <h3>Успешность тестов</h3>
                <div class="value">{results['test_success_rate']:.1f}%</div>
            </div>
            <div class="metric">
                <h3>Здоровых сервисов</h3>
                <div class="value">{results['healthy_services']}/{len(results['services'])}</div>
            </div>
        </div>
        
        <h2>📋 Детали по сервисам</h2>
"""
        
        for service_name, service_data in results['services'].items():
            structure = service_data['structure']
            tests = service_data['tests']
            health = service_data['health']
            
            health_status = "healthy" if health.get('healthy', False) else "unhealthy"
            health_text = "Здоров" if health.get('healthy', False) else "Недоступен"
            
            html_content += f"""
        <div class="service">
            <h3>🔧 {service_name.upper()}</h3>
            <div class="service-grid">
                <div>
                    <strong>Структура:</strong><br>
                    📁 {structure['source_files']} исходных файлов<br>
                    🧪 {structure['test_files']} тестовых файлов<br>
                    <span class="coverage">📈 {structure['test_coverage']}% покрытие</span>
                </div>
                <div>
                    <strong>Тесты:</strong><br>
                    ✅ {tests['tests_passed']} прошло<br>
                    ❌ {tests['tests_failed']} упало<br>
                    📊 {tests['tests_run']} всего
                </div>
                <div>
                    <strong>Статус:</strong><br>
                    <span class="status {health_status}">{health_text}</span>
                </div>
            </div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 HTML отчет сохранен: {output_path}")

def main():
    """Главная функция"""
    analyzer = TestCoverageAnalyzer()
    
    # Ждем запуска сервисов
    print("⏳ Ожидание запуска сервисов...")
    time.sleep(30)
    
    # Анализируем все сервисы
    results = analyzer.analyze_all_services()
    
    # Генерируем отчеты
    analyzer.generate_report(results)
    
    print("\n🎉 Анализ завершен!")

if __name__ == "__main__":
    main() 