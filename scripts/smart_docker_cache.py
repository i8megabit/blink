#!/usr/bin/env python3
"""
🚀 УМНЫЙ КЕШ ДЛЯ DOCKER СБОРКИ
Оптимизирует сборку с разделением стабильных и проблемных слоев
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import List, Dict, Any

class SmartDockerCache:
    """Умный кеш для Docker сборки"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.cache_dir = self.project_root / ".docker_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Стабильные слои (кешируются)
        self.stable_layers = [
            "system_deps",
            "python_base",
            "bootstrap_code"
        ]
        
        # Проблемные слои (пересобираются)
        self.problematic_layers = [
            "ai_deps",
            "db_deps", 
            "monitoring_deps"
        ]
    
    def get_cache_key(self, layer_name: str) -> str:
        """Генерация ключа кеша для слоя"""
        if layer_name == "system_deps":
            return "system_deps_v1"
        elif layer_name == "python_base":
            return "python_base_v1"
        elif layer_name == "bootstrap_code":
            # Кеш зависит от изменений в bootstrap/
            bootstrap_hash = self._get_dir_hash("bootstrap")
            return f"bootstrap_{bootstrap_hash}"
        elif layer_name == "ai_deps":
            # AI зависимости часто обновляются
            return f"ai_deps_{int(time.time() / 3600)}"  # Обновляется каждый час
        else:
            return f"{layer_name}_{int(time.time() / 86400)}"  # Обновляется каждый день
    
    def _get_dir_hash(self, directory: str) -> str:
        """Получение хеша директории"""
        try:
            result = subprocess.run(
                ["find", directory, "-type", "f", "-exec", "sha256sum", "{}", "+"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                # Простой хеш от всех файлов
                return str(hash(result.stdout))[-8:]
        except:
            pass
        return "unknown"
    
    def build_base_with_cache(self, force_rebuild: bool = False) -> bool:
        """Сборка базового образа с умным кешированием"""
        print("🔨 Сборка базового образа с умным кешированием...")
        
        # Проверяем существующий образ
        if not force_rebuild and self._image_exists("eberil/relink-base:latest"):
            print("✅ Базовый образ уже существует, используем кеш")
            return True
        
        # Собираем с BuildKit для лучшего кеширования
        cmd = [
            "docker", "build",
            "--build-arg", "BUILDKIT_INLINE_CACHE=1",
            "--cache-from", "eberil/relink-base:latest",
            "-f", "Dockerfile.base",
            "-t", "eberil/relink-base:latest",
            "."
        ]
        
        if force_rebuild:
            cmd.insert(2, "--no-cache")
        
        print(f"🚀 Команда сборки: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode == 0
    
    def build_service_with_cache(self, service_name: str, force_rebuild: bool = False) -> bool:
        """Сборка сервиса с кешированием"""
        print(f"🔨 Сборка сервиса {service_name} с кешированием...")
        
        # Проверяем Dockerfile сервиса
        service_dockerfile = self.project_root / service_name / "Dockerfile"
        if not service_dockerfile.exists():
            print(f"❌ Dockerfile не найден для {service_name}")
            return False
        
        # Собираем сервис
        cmd = [
            "docker", "build",
            "--build-arg", "BUILDKIT_INLINE_CACHE=1",
            "--cache-from", f"eberil/relink-{service_name}:latest",
            "--cache-from", "eberil/relink-base:latest",
            "-f", str(service_dockerfile),
            "-t", f"eberil/relink-{service_name}:latest",
            str(self.project_root / service_name)
        ]
        
        if force_rebuild:
            cmd.insert(2, "--no-cache")
        
        print(f"🚀 Команда сборки {service_name}: {' '.join(cmd)}")
        
        result = subprocess.run(cmd)
        return result.returncode == 0
    
    def build_all_services(self, services: List[str], force_rebuild: bool = False) -> Dict[str, bool]:
        """Сборка всех сервисов с кешированием"""
        results = {}
        
        # Сначала собираем базовый образ
        if not self.build_base_with_cache(force_rebuild):
            print("❌ Ошибка сборки базового образа")
            return results
        
        # Собираем сервисы параллельно
        import concurrent.futures
        
        def build_service(service):
            return service, self.build_service_with_cache(service, force_rebuild)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(build_service, service) for service in services]
            
            for future in concurrent.futures.as_completed(futures):
                service, success = future.result()
                results[service] = success
                
                if success:
                    print(f"✅ {service} собран успешно")
                else:
                    print(f"❌ Ошибка сборки {service}")
        
        return results
    
    def _image_exists(self, image_name: str) -> bool:
        """Проверка существования образа"""
        result = subprocess.run(
            ["docker", "images", "-q", image_name],
            capture_output=True, text=True
        )
        return bool(result.stdout.strip())
    
    def clean_cache(self):
        """Очистка кеша"""
        print("🧹 Очистка Docker кеша...")
        
        # Удаляем неиспользуемые образы
        subprocess.run(["docker", "image", "prune", "-f"])
        
        # Удаляем неиспользуемые контейнеры
        subprocess.run(["docker", "container", "prune", "-f"])
        
        # Удаляем неиспользуемые volumes
        subprocess.run(["docker", "volume", "prune", "-f"])
        
        print("✅ Кеш очищен")
    
    def show_cache_stats(self):
        """Показать статистику кеша"""
        print("📊 Статистика Docker кеша:")
        
        # Размер образов
        result = subprocess.run(
            ["docker", "images", "--format", "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"],
            capture_output=True, text=True
        )
        print(result.stdout)
        
        # Использование диска
        result = subprocess.run(
            ["docker", "system", "df"],
            capture_output=True, text=True
        )
        print(result.stdout)

def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Умный кеш для Docker сборки")
    parser.add_argument("--build-base", action="store_true", help="Собрать базовый образ")
    parser.add_argument("--build-service", type=str, help="Собрать конкретный сервис")
    parser.add_argument("--build-all", action="store_true", help="Собрать все сервисы")
    parser.add_argument("--force", action="store_true", help="Принудительная пересборка")
    parser.add_argument("--clean", action="store_true", help="Очистить кеш")
    parser.add_argument("--stats", action="store_true", help="Показать статистику")
    
    args = parser.parse_args()
    
    cache = SmartDockerCache()
    
    if args.clean:
        cache.clean_cache()
    elif args.stats:
        cache.show_cache_stats()
    elif args.build_base:
        success = cache.build_base_with_cache(args.force)
        sys.exit(0 if success else 1)
    elif args.build_service:
        success = cache.build_service_with_cache(args.build_service, args.force)
        sys.exit(0 if success else 1)
    elif args.build_all:
        services = ["router", "backend", "relink", "llm_tuning", "monitoring", "benchmark"]
        results = cache.build_all_services(services, args.force)
        
        failed = [service for service, success in results.items() if not success]
        if failed:
            print(f"❌ Ошибки сборки: {', '.join(failed)}")
            sys.exit(1)
        else:
            print("✅ Все сервисы собраны успешно")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 