#!/usr/bin/env python3
"""
Скрипт для автоматического расчета лимитов ресурсов для микросервисов
на основе конфигурации системы Apple Silicon M4
"""

import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List

class ResourceLimitsCalculator:
    def __init__(self):
        self.system_info = self.get_system_info()
        self.microservices = {
            'backend': {
                'description': 'Основной FastAPI сервис',
                'cpu_weight': 3,
                'memory_weight': 2,
                'priority': 'high'
            },
            'frontend': {
                'description': 'React frontend',
                'cpu_weight': 1,
                'memory_weight': 1,
                'priority': 'medium'
            },
            'llm_tuning': {
                'description': 'LLM тюнинг сервис',
                'cpu_weight': 4,
                'memory_weight': 4,
                'priority': 'high'
            },
            'monitoring': {
                'description': 'Мониторинг и алерты',
                'cpu_weight': 1,
                'memory_weight': 1,
                'priority': 'low'
            },
            'docs': {
                'description': 'Документация',
                'cpu_weight': 1,
                'memory_weight': 1,
                'priority': 'low'
            },
            'testing': {
                'description': 'Тестирование',
                'cpu_weight': 2,
                'memory_weight': 2,
                'priority': 'medium'
            },
            'ollama': {
                'description': 'LLM модели',
                'cpu_weight': 6,
                'memory_weight': 8,
                'priority': 'critical'
            },
            'redis': {
                'description': 'Кэш Redis',
                'cpu_weight': 1,
                'memory_weight': 2,
                'priority': 'high'
            },
            'postgres': {
                'description': 'База данных',
                'cpu_weight': 2,
                'memory_weight': 3,
                'priority': 'high'
            }
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Получает информацию о системе"""
        info = {}
        
        # CPU ядра
        try:
            result = subprocess.run(['sysctl', '-n', 'hw.ncpu'], 
                                  capture_output=True, text=True, check=True)
            info['cpu_cores'] = int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            info['cpu_cores'] = 10  # Fallback для M4
        
        # Память
        try:
            result = subprocess.run(['sysctl', '-n', 'hw.memsize'], 
                                  capture_output=True, text=True, check=True)
            memory_bytes = int(result.stdout.strip())
            info['memory_gb'] = memory_bytes // (1024**3)
        except (subprocess.CalledProcessError, ValueError):
            info['memory_gb'] = 16  # Fallback для M4
        
        # Чип
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True, check=True)
            info['chip'] = result.stdout.strip()
        except subprocess.CalledProcessError:
            info['chip'] = "Apple M4"
        
        return info
    
    def calculate_limits(self) -> Dict[str, Dict[str, Any]]:
        """Рассчитывает лимиты ресурсов для каждого микросервиса"""
        total_cpu = self.system_info['cpu_cores']
        total_memory = self.system_info['memory_gb']
        
        # Резерв для системы (20%)
        reserved_cpu = total_cpu * 0.2
        reserved_memory = total_memory * 0.2
        
        available_cpu = total_cpu - reserved_cpu
        available_memory = total_memory - reserved_memory
        
        # Сумма весов
        total_cpu_weight = sum(service['cpu_weight'] for service in self.microservices.values())
        total_memory_weight = sum(service['memory_weight'] for service in self.microservices.values())
        
        limits = {}
        
        for service_name, service_config in self.microservices.items():
            # Расчет CPU лимитов
            cpu_share = (service_config['cpu_weight'] / total_cpu_weight) * available_cpu
            cpu_limit = max(0.1, min(cpu_share, available_cpu * 0.8))  # Минимум 0.1, максимум 80%
            
            # Расчет Memory лимитов
            memory_share = (service_config['memory_weight'] / total_memory_weight) * available_memory
            memory_limit = max(0.5, min(memory_share, available_memory * 0.8))  # Минимум 0.5GB, максимум 80%
            
            limits[service_name] = {
                'cpu': {
                    'request': f"{cpu_limit:.1f}",
                    'limit': f"{cpu_limit * 1.5:.1f}",
                    'shares': int(cpu_limit * 100)
                },
                'memory': {
                    'request': f"{memory_limit:.1f}Gi",
                    'limit': f"{memory_limit * 1.5:.1f}Gi",
                    'bytes': int(memory_limit * 1024 * 1024 * 1024)
                },
                'priority': service_config['priority'],
                'description': service_config['description']
            }
        
        return limits
    
    def generate_docker_compose(self, limits: Dict[str, Dict[str, Any]]) -> str:
        """Генерирует docker-compose.yml с лимитами ресурсов"""
        compose_content = f"""# Docker Compose с автоматически рассчитанными лимитами ресурсов
# Система: {self.system_info['chip']} - {self.system_info['cpu_cores']} ядер, {self.system_info['memory_gb']}GB RAM
# Сгенерировано автоматически

version: '3.8'

services:
"""
        
        for service_name, service_limits in limits.items():
            compose_content += f"""  {service_name}:
    build:
      context: ./{service_name}
      dockerfile: Dockerfile
    environment:
      - NODE_ENV=production
    deploy:
      resources:
        limits:
          cpus: '{service_limits["cpu"]["limit"]}'
          memory: {service_limits["memory"]["limit"]}
        reservations:
          cpus: '{service_limits["cpu"]["request"]}'
          memory: {service_limits["memory"]["request"]}
    restart: unless-stopped
    networks:
      - relink-network

"""
        
        compose_content += """networks:
  relink-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
"""
        
        return compose_content
    
    def generate_kubernetes(self, limits: Dict[str, Dict[str, Any]]) -> str:
        """Генерирует Kubernetes манифесты с лимитами ресурсов"""
        k8s_content = f"""# Kubernetes манифесты с автоматически рассчитанными лимитами ресурсов
# Система: {self.system_info['chip']} - {self.system_info['cpu_cores']} ядер, {self.system_info['memory_gb']}GB RAM
# Сгенерировано автоматически

apiVersion: v1
kind: Namespace
metadata:
  name: relink
---
"""
        
        for service_name, service_limits in limits.items():
            k8s_content += f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_name}
  namespace: relink
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {service_name}
  template:
    metadata:
      labels:
        app: {service_name}
    spec:
      containers:
      - name: {service_name}
        image: relink/{service_name}:latest
        resources:
          requests:
            cpu: {service_limits["cpu"]["request"]}
            memory: {service_limits["memory"]["request"]}
          limits:
            cpu: {service_limits["cpu"]["limit"]}
            memory: {service_limits["memory"]["limit"]}
        ports:
        - containerPort: 8000
        env:
        - name: NODE_ENV
          value: "production"
---
apiVersion: v1
kind: Service
metadata:
  name: {service_name}-service
  namespace: relink
spec:
  selector:
    app: {service_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
"""
        
        return k8s_content
    
    def generate_monitoring_config(self, limits: Dict[str, Dict[str, Any]]) -> str:
        """Генерирует конфигурацию мониторинга"""
        prometheus_config = f"""# Prometheus конфигурация для мониторинга ресурсов
# Система: {self.system_info['chip']} - {self.system_info['cpu_cores']} ядер, {self.system_info['memory_gb']}GB RAM

global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
"""
        
        for service_name, service_limits in limits.items():
            prometheus_config += f"""  - job_name: '{service_name}'
    static_configs:
      - targets: ['{service_name}:8000']
    metrics_path: /metrics
    scrape_interval: 30s
    scrape_timeout: 10s
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        regex: '([^:]+)(?::\d+)?'
        replacement: '${{1}}'
      - source_labels: [__address__]
        target_label: service
        regex: '([^:]+)(?::\d+)?'
        replacement: '{service_name}'

"""
        
        return prometheus_config
    
    def save_configurations(self, limits: Dict[str, Dict[str, Any]]):
        """Сохраняет все конфигурации в файлы"""
        project_root = Path(".")
        
        # Docker Compose
        docker_compose = self.generate_docker_compose(limits)
        with open(project_root / "docker-compose.resources.yml", 'w') as f:
            f.write(docker_compose)
        
        # Kubernetes
        k8s_config = self.generate_kubernetes(limits)
        with open(project_root / "k8s" / "deployments.yml", 'w') as f:
            f.write(k8s_config)
        
        # Prometheus
        prometheus_config = self.generate_monitoring_config(limits)
        with open(project_root / "monitoring" / "prometheus.yml", 'w') as f:
            f.write(prometheus_config)
        
        # JSON конфигурация
        config_data = {
            'system_info': self.system_info,
            'limits': limits,
            'generated_at': subprocess.run(['date'], capture_output=True, text=True).stdout.strip()
        }
        
        with open(project_root / "resource_limits.json", 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print("✅ Конфигурации сохранены:")
        print("   - docker-compose.resources.yml")
        print("   - k8s/deployments.yml")
        print("   - monitoring/prometheus.yml")
        print("   - resource_limits.json")
    
    def print_summary(self, limits: Dict[str, Dict[str, Any]]):
        """Выводит сводку по лимитам ресурсов"""
        print(f"\n📊 Сводка лимитов ресурсов для {self.system_info['chip']}")
        print("=" * 80)
        print(f"Система: {self.system_info['cpu_cores']} ядер, {self.system_info['memory_gb']}GB RAM")
        print("=" * 80)
        
        total_cpu_request = 0
        total_memory_request = 0
        
        for service_name, service_limits in limits.items():
            cpu_req = float(service_limits["cpu"]["request"])
            memory_req = float(service_limits["memory"]["request"].replace('Gi', ''))
            
            total_cpu_request += cpu_req
            total_memory_request += memory_req
            
            print(f"{service_name:15} | CPU: {cpu_req:4.1f} | Memory: {memory_req:4.1f}GB | Priority: {service_limits['priority']:8}")
        
        print("=" * 80)
        print(f"Итого запросов: CPU {total_cpu_request:.1f}, Memory {total_memory_request:.1f}GB")
        print(f"Доступно:       CPU {self.system_info['cpu_cores']:.1f}, Memory {self.system_info['memory_gb']:.1f}GB")
        print(f"Использование:  CPU {total_cpu_request/self.system_info['cpu_cores']*100:.1f}%, Memory {total_memory_request/self.system_info['memory_gb']*100:.1f}%")

def main():
    """Основная функция"""
    calculator = ResourceLimitsCalculator()
    
    print("🚀 Расчет лимитов ресурсов для микросервисов reLink")
    print("=" * 60)
    
    # Расчет лимитов
    limits = calculator.calculate_limits()
    
    # Вывод сводки
    calculator.print_summary(limits)
    
    # Сохранение конфигураций
    print("\n💾 Сохранение конфигураций...")
    calculator.save_configurations(limits)
    
    print("\n🎉 Расчет лимитов ресурсов завершен!")

if __name__ == "__main__":
    main() 