#!/usr/bin/env python3
"""
Скрипт для расчета лимитов ресурсов для всех микросервисов проекта
Оптимизирован для Apple Silicon M4 с 10 ядрами и 16GB RAM
"""

import os
import subprocess
import yaml
from pathlib import Path

class ResourceCalculator:
    def __init__(self):
        self.system_info = self.get_system_info()
        self.services = self.define_services()
        
    def get_system_info(self):
        """Получение информации о системе"""
        try:
            # CPU cores
            cpu_result = subprocess.run(['sysctl', '-n', 'hw.ncpu'], capture_output=True, text=True)
            cpu_cores = int(cpu_result.stdout.strip())
            
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
            return {'cpu_cores': 10, 'memory_gb': 16, 'is_apple_silicon': True}
    
    def define_services(self):
        """Определение всех микросервисов проекта"""
        return {
            'backend': {
                'description': 'FastAPI backend сервис',
                'cpu_weight': 2.0,  # 20% от общего CPU
                'memory_weight': 2.0,  # 2GB RAM
                'priority': 'high'
            },
            'frontend': {
                'description': 'React frontend сервис',
                'cpu_weight': 1.0,  # 10% от общего CPU
                'memory_weight': 1.0,  # 1GB RAM
                'priority': 'medium'
            },
            'llm_tuning': {
                'description': 'LLM tuning сервис',
                'cpu_weight': 3.0,  # 30% от общего CPU
                'memory_weight': 4.0,  # 4GB RAM
                'priority': 'high'
            },
            'monitoring': {
                'description': 'Prometheus/Grafana мониторинг',
                'cpu_weight': 0.5,  # 5% от общего CPU
                'memory_weight': 1.0,  # 1GB RAM
                'priority': 'low'
            },
            'docs': {
                'description': 'Документация сервис',
                'cpu_weight': 0.5,  # 5% от общего CPU
                'memory_weight': 0.5,  # 0.5GB RAM
                'priority': 'low'
            },
            'testing': {
                'description': 'Тестирование сервис',
                'cpu_weight': 1.0,  # 10% от общего CPU
                'memory_weight': 1.0,  # 1GB RAM
                'priority': 'medium'
            },
            'ollama': {
                'description': 'Ollama LLM сервис',
                'cpu_weight': 2.0,  # 20% от общего CPU
                'memory_weight': 6.0,  # 6GB RAM
                'priority': 'high'
            },
            'redis': {
                'description': 'Redis кэш',
                'cpu_weight': 0.5,  # 5% от общего CPU
                'memory_weight': 0.5,  # 0.5GB RAM
                'priority': 'medium'
            },
            'postgres': {
                'description': 'PostgreSQL база данных',
                'cpu_weight': 1.0,  # 10% от общего CPU
                'memory_weight': 1.0,  # 1GB RAM
                'priority': 'high'
            }
        }
    
    def calculate_limits(self):
        """Расчет лимитов ресурсов для всех сервисов"""
        total_cpu = self.system_info['cpu_cores']
        total_memory = self.system_info['memory_gb']
        
        # Резерв для системы (20% CPU, 10% RAM)
        system_cpu = total_cpu * 0.2
        system_memory = total_memory * 0.1
        
        available_cpu = total_cpu - system_cpu
        available_memory = total_memory - system_memory
        
        # Расчет весов
        total_cpu_weight = sum(service['cpu_weight'] for service in self.services.values())
        total_memory_weight = sum(service['memory_weight'] for service in self.services.values())
        
        limits = {}
        
        for service_name, service_config in self.services.items():
            # CPU лимиты (в милликорях)
            cpu_percent = service_config['cpu_weight'] / total_cpu_weight
            cpu_cores = available_cpu * cpu_percent
            cpu_millicores = int(cpu_cores * 1000)
            
            # Memory лимиты (в MB)
            memory_percent = service_config['memory_weight'] / total_memory_weight
            memory_gb = available_memory * memory_percent
            memory_mb = int(memory_gb * 1024)
            
            limits[service_name] = {
                'cpu': {
                    'request': f"{max(100, cpu_millicores // 2)}m",  # 50% от лимита
                    'limit': f"{cpu_millicores}m"
                },
                'memory': {
                    'request': f"{max(128, memory_mb // 2)}Mi",  # 50% от лимита
                    'limit': f"{memory_mb}Mi"
                },
                'description': service_config['description'],
                'priority': service_config['priority']
            }
        
        return limits
    
    def generate_docker_compose_config(self, limits):
        """Генерация конфигурации Docker Compose"""
        config = {
            'version': '3.8',
            'services': {}
        }
        
        for service_name, service_limits in limits.items():
            config['services'][service_name] = {
                'deploy': {
                    'resources': {
                        'limits': {
                            'cpus': f"{float(service_limits['cpu']['limit'].replace('m', '')) / 1000}",
                            'memory': service_limits['memory']['limit']
                        },
                        'reservations': {
                            'cpus': f"{float(service_limits['cpu']['request'].replace('m', '')) / 1000}",
                            'memory': service_limits['memory']['request']
                        }
                    }
                }
            }
        
        return config
    
    def generate_kubernetes_config(self, limits):
        """Генерация конфигурации Kubernetes"""
        configs = []
        
        for service_name, service_limits in limits.items():
            deployment = {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': f'{service_name}-deployment',
                    'labels': {
                        'app': service_name
                    }
                },
                'spec': {
                    'replicas': 1,
                    'selector': {
                        'matchLabels': {
                            'app': service_name
                        }
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': service_name
                            }
                        },
                        'spec': {
                            'containers': [{
                                'name': service_name,
                                'image': f'{service_name}:latest',
                                'resources': {
                                    'requests': {
                                        'cpu': service_limits['cpu']['request'],
                                        'memory': service_limits['memory']['request']
                                    },
                                    'limits': {
                                        'cpu': service_limits['cpu']['limit'],
                                        'memory': service_limits['memory']['limit']
                                    }
                                }
                            }]
                        }
                    }
                }
            }
            configs.append(deployment)
        
        return configs
    
    def generate_prometheus_config(self, limits):
        """Генерация конфигурации Prometheus для мониторинга ресурсов"""
        config = {
            'global': {
                'scrape_interval': '15s',
                'evaluation_interval': '15s'
            },
            'rule_files': ['resource_alerts.yml'],
            'scrape_configs': [
                {
                    'job_name': 'kubernetes-pods',
                    'kubernetes_sd_configs': [{'role': 'pod'}],
                    'relabel_configs': [
                        {
                            'source_labels': ['__meta_kubernetes_pod_annotation_prometheus_io_scrape'],
                            'action': 'keep',
                            'regex': 'true'
                        }
                    ]
                }
            ]
        }
        
        # Создание правил алертов
        alert_rules = []
        
        for service_name, service_limits in limits.items():
            # CPU алерты
            cpu_limit = float(service_limits['cpu']['limit'].replace('m', '')) / 1000
            alert_rules.append({
                'alert': f'{service_name}_high_cpu',
                'expr': f'rate(container_cpu_usage_seconds_total{{container="{service_name}"}}[5m]) > {cpu_limit * 0.8}',
                'for': '5m',
                'labels': {
                    'severity': 'warning',
                    'service': service_name
                },
                'annotations': {
                    'summary': f'{service_name} CPU usage is high',
                    'description': f'{service_name} CPU usage is above 80% of limit ({cpu_limit} cores)'
                }
            })
            
            # Memory алерты
            memory_limit = int(service_limits['memory']['limit'].replace('Mi', ''))
            alert_rules.append({
                'alert': f'{service_name}_high_memory',
                'expr': f'container_memory_usage_bytes{{container="{service_name}"}} > {memory_limit * 1024 * 1024 * 0.8}',
                'for': '5m',
                'labels': {
                    'severity': 'warning',
                    'service': service_name
                },
                'annotations': {
                    'summary': f'{service_name} memory usage is high',
                    'description': f'{service_name} memory usage is above 80% of limit ({memory_limit}Mi)'
                }
            })
        
        return config, alert_rules
    
    def save_configs(self, limits):
        """Сохранение всех конфигураций в файлы"""
        # Docker Compose
        docker_config = self.generate_docker_compose_config(limits)
        with open('docker-compose.resources.yml', 'w') as f:
            yaml.dump(docker_config, f, default_flow_style=False, sort_keys=False)
        
        # Kubernetes
        k8s_configs = self.generate_kubernetes_config(limits)
        with open('kubernetes-deployments.yml', 'w') as f:
            yaml.dump_all(k8s_configs, f, default_flow_style=False, sort_keys=False)
        
        # Prometheus
        prometheus_config, alert_rules = self.generate_prometheus_config(limits)
        with open('prometheus.yml', 'w') as f:
            yaml.dump(prometheus_config, f, default_flow_style=False, sort_keys=False)
        
        with open('resource_alerts.yml', 'w') as f:
            yaml.dump(alert_rules, f, default_flow_style=False, sort_keys=False)
    
    def print_summary(self, limits):
        """Вывод сводки по лимитам ресурсов"""
        print("🚀 РАСЧЕТ ЛИМИТОВ РЕСУРСОВ ДЛЯ APPLE SILICON M4")
        print("=" * 60)
        print(f"💻 Система: {self.system_info['cpu_cores']} ядер, {self.system_info['memory_gb']}GB RAM")
        print(f"🍎 Apple Silicon: {'Да' if self.system_info['is_apple_silicon'] else 'Нет'}")
        print()
        
        print("📊 ЛИМИТЫ РЕСУРСОВ ПО СЕРВИСАМ:")
        print("-" * 60)
        
        total_cpu_request = 0
        total_cpu_limit = 0
        total_memory_request = 0
        total_memory_limit = 0
        
        for service_name, service_limits in limits.items():
            cpu_request = float(service_limits['cpu']['request'].replace('m', '')) / 1000
            cpu_limit = float(service_limits['cpu']['limit'].replace('m', '')) / 1000
            memory_request = int(service_limits['memory']['request'].replace('Mi', ''))
            memory_limit = int(service_limits['memory']['limit'].replace('Mi', ''))
            
            total_cpu_request += cpu_request
            total_cpu_limit += cpu_limit
            total_memory_request += memory_request
            total_memory_limit += memory_limit
            
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }
            
            print(f"{priority_emoji[service_limits['priority']]} {service_name:15} | "
                  f"CPU: {cpu_request:.1f}-{cpu_limit:.1f} cores | "
                  f"RAM: {memory_request}-{memory_limit}Mi | "
                  f"{service_limits['description']}")
        
        print("-" * 60)
        print(f"📈 ИТОГО: CPU {total_cpu_request:.1f}-{total_cpu_limit:.1f} cores, "
              f"RAM {total_memory_request}-{total_memory_limit}Mi")
        print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ:")
        print("-" * 60)
        print("🔧 Для Ollama:")
        print("   - Установите OLLAMA_METAL=1 для GPU ускорения")
        print("   - Используйте OLLAMA_FLASH_ATTENTION=1")
        print("   - Настройте OLLAMA_KV_CACHE_TYPE=q8_0")
        print()
        print("⚡ Для производительности:")
        print("   - Мониторьте использование ресурсов через Prometheus")
        print("   - Настройте auto-scaling для критичных сервисов")
        print("   - Используйте кэширование Redis для снижения нагрузки")
        print()
        print("🛡️ Для стабильности:")
        print("   - Установите health checks для всех сервисов")
        print("   - Настройте graceful shutdown")
        print("   - Мониторьте логи и метрики")

def main():
    """Основная функция"""
    calculator = ResourceCalculator()
    limits = calculator.calculate_limits()
    
    # Вывод сводки
    calculator.print_summary(limits)
    
    # Сохранение конфигураций
    calculator.save_configs(limits)
    
    print("✅ Конфигурации сохранены:")
    print("   📄 docker-compose.resources.yml")
    print("   📄 kubernetes-deployments.yml")
    print("   📄 prometheus.yml")
    print("   📄 resource_alerts.yml")

if __name__ == "__main__":
    main() 