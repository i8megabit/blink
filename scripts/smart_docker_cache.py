#!/usr/bin/env python3
"""
🚀 УМНЫЙ КЕШ ДЛЯ DOCKER СБОРКИ
Оптимизирует сборку с разделением стабильных и проблемных слоев
Расширенная версия с поддержкой ChromaDB и автоматического управления
"""

import os
import sys
import subprocess
import json
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import argparse

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
            "monitoring_deps",
            "chromadb_deps"
        ]
        
        # Специфичные кейсы для ChromaDB
        self.chromadb_cases = [
            "chromadb_optimization",
            "vector_embeddings",
            "rag_integration"
        ]
        
        # Кеш метаданных
        self.cache_metadata_file = self.cache_dir / "cache_metadata.json"
        self.cache_metadata = self._load_cache_metadata()
    
    def _load_cache_metadata(self) -> Dict[str, Any]:
        """Загрузка метаданных кеша"""
        if self.cache_metadata_file.exists():
            try:
                with open(self.cache_metadata_file, 'r') as f:
                    data = json.load(f)
                    # Обеспечиваем обратную совместимость
                    if "layer_hashes" not in data:
                        data["layer_hashes"] = {}
                    if "build_times" not in data:
                        data["build_times"] = {}
                    return data
            except:
                pass
        return {
            "last_cleanup": None,
            "cache_hits": 0,
            "cache_misses": 0,
            "build_times": {},
            "layer_hashes": {}
        }
    
    def _save_cache_metadata(self):
        """Сохранение метаданных кеша"""
        with open(self.cache_metadata_file, 'w') as f:
            json.dump(self.cache_metadata, f, indent=2)
    
    def _get_layer_hash(self, service_name: str, layer_type: str) -> str:
        """Получение хеша слоя для кеширования"""
        import hashlib
        
        # Базовые файлы для хеширования
        base_files = [
            "Dockerfile.base",
            "requirements-base.txt",
            "bootstrap/config.py"
        ]
        
        # Файлы сервиса
        service_files = [
            f"{service_name}/Dockerfile",
            f"{service_name}/requirements.txt",
            f"{service_name}/app/main.py"
        ]
        
        # Собираем все файлы для хеширования
        files_to_hash = []
        
        for file_path in base_files + service_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                files_to_hash.append(str(full_path))
        
        # Создаем хеш
        content = "|".join(files_to_hash)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _check_cache_validity(self, service_name: str, layer_type: str) -> bool:
        """Проверка валидности кеша"""
        layer_hash = self._get_layer_hash(service_name, layer_type)
        cached_hash = self.cache_metadata["layer_hashes"].get(f"{service_name}_{layer_type}")
        
        return layer_hash == cached_hash
    
    def _update_cache_hash(self, service_name: str, layer_type: str):
        """Обновление хеша кеша"""
        layer_hash = self._get_layer_hash(service_name, layer_type)
        self.cache_metadata["layer_hashes"][f"{service_name}_{layer_type}"] = layer_hash
        self._save_cache_metadata()
    
    def build_base_image(self, force: bool = False) -> bool:
        """Сборка базового образа с умным кешированием"""
        
        print("🔨 Сборка базового образа...")
        
        if not force and self._check_cache_validity("base", "system_deps"):
            print("✅ Кеш базового образа актуален, пропускаем сборку")
            self.cache_metadata["cache_hits"] += 1
            self._save_cache_metadata()
            return True
        
        start_time = time.time()
        
        try:
            # Сборка базового образа
            cmd = [
                "docker", "build",
                "-f", "Dockerfile.base",
                "-t", "eberil/relink-base:latest",
                "--build-arg", "BUILDKIT_INLINE_CACHE=1",
                "."
            ]
            
            if force:
                cmd.extend(["--no-cache"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                build_time = time.time() - start_time
                self.cache_metadata["build_times"]["base"] = build_time
                self._update_cache_hash("base", "system_deps")
                self.cache_metadata["cache_misses"] += 1
                self._save_cache_metadata()
                
                print(f"✅ Базовый образ собран за {build_time:.2f}с")
                return True
            else:
                print(f"❌ Ошибка сборки базового образа: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при сборке базового образа: {e}")
            return False
    
    def build_service(self, service_name: str, force: bool = False) -> bool:
        """Сборка сервиса с умным кешированием"""
        
        print(f"🔨 Сборка сервиса {service_name}...")
        
        # Проверяем кеш для стабильных слоев
        cache_valid = True
        for layer in self.stable_layers:
            if not self._check_cache_validity(service_name, layer):
                cache_valid = False
                break
        
        if not force and cache_valid:
            print(f"✅ Кеш сервиса {service_name} актуален, пропускаем сборку")
            self.cache_metadata["cache_hits"] += 1
            self._save_cache_metadata()
            return True
        
        start_time = time.time()
        
        try:
            # Сборка сервиса
            service_dir = self.project_root / service_name
            if not service_dir.exists():
                print(f"❌ Директория сервиса {service_name} не найдена")
                return False
            
            cmd = [
                "docker", "build",
                "-f", f"{service_name}/Dockerfile",
                "-t", f"eberil/relink-{service_name}:latest",
                "--build-arg", "BUILDKIT_INLINE_CACHE=1",
                "."
            ]
            
            if force:
                cmd.extend(["--no-cache"])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                build_time = time.time() - start_time
                self.cache_metadata["build_times"][service_name] = build_time
                
                # Обновляем хеши для всех слоев
                for layer in self.stable_layers + self.problematic_layers:
                    self._update_cache_hash(service_name, layer)
                
                self.cache_metadata["cache_misses"] += 1
                self._save_cache_metadata()
                
                print(f"✅ Сервис {service_name} собран за {build_time:.2f}с")
                return True
            else:
                print(f"❌ Ошибка сборки сервиса {service_name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при сборке сервиса {service_name}: {e}")
            return False
    
    def build_all_services(self, force: bool = False) -> bool:
        """Сборка всех сервисов"""
        
        print("🚀 Сборка всех сервисов...")
        
        # Сначала собираем базовый образ
        if not self.build_base_image(force):
            return False
        
        # Список сервисов для сборки
        services = ["router", "backend", "frontend", "monitoring", "testing"]
        
        success_count = 0
        for service in services:
            if self.build_service(service, force):
                success_count += 1
        
        print(f"✅ Собрано {success_count}/{len(services)} сервисов")
        return success_count == len(services)
    
    def cleanup_cache(self):
        """Очистка кеша"""
        
        print("🧹 Очистка кеша...")
        
        try:
            # Удаляем старые образы
            subprocess.run(["docker", "system", "prune", "-f"], capture_output=True)
            
            # Очищаем метаданные кеша
            self.cache_metadata = {
                "last_cleanup": time.time(),
                "cache_hits": 0,
                "cache_misses": 0,
                "build_times": {},
                "layer_hashes": {}
            }
            self._save_cache_metadata()
            
            print("✅ Кеш очищен")
            
        except Exception as e:
            print(f"❌ Ошибка очистки кеша: {e}")
    
    def show_stats(self):
        """Показать статистику кеша"""
        
        print("📊 Статистика кеша:")
        print(f"  Хиты кеша: {self.cache_metadata['cache_hits']}")
        print(f"  Промахи кеша: {self.cache_metadata['cache_misses']}")
        
        if self.cache_metadata['cache_hits'] + self.cache_metadata['cache_misses'] > 0:
            hit_rate = self.cache_metadata['cache_hits'] / (self.cache_metadata['cache_hits'] + self.cache_metadata['cache_misses']) * 100
            print(f"  Эффективность кеша: {hit_rate:.1f}%")
        
        print("\n⏱️ Время сборки:")
        for service, build_time in self.cache_metadata['build_times'].items():
            print(f"  {service}: {build_time:.2f}с")
        
        if self.cache_metadata['last_cleanup']:
            cleanup_time = time.time() - self.cache_metadata['last_cleanup']
            print(f"\n🧹 Последняя очистка: {cleanup_time/3600:.1f} часов назад")
    
    def chromadb_optimization(self):
        """Специальная оптимизация для ChromaDB"""
        
        print("🔧 Оптимизация ChromaDB...")
        
        # Проверяем специфичные файлы ChromaDB
        chromadb_files = [
            "bootstrap/rag_manager.py",
            "bootstrap/rag_service.py",
            "bootstrap/routers/router_router.py"
        ]
        
        files_changed = False
        for file_path in chromadb_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                # Проверяем, изменились ли файлы ChromaDB
                if not self._check_cache_validity("chromadb", "rag_integration"):
                    files_changed = True
                    break
        
        if files_changed:
            print("🔄 Обнаружены изменения в ChromaDB, пересобираем роутер...")
            return self.build_service("router", force=True)
        else:
            print("✅ ChromaDB файлы не изменились")
            return True
    
    def auto_cleanup_collections(self):
        """Автоматическая очистка коллекций ChromaDB"""
        
        print("🧹 Автоматическая очистка коллекций ChromaDB...")
        
        try:
            # Проверяем, запущен ли роутер
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=relink-router", "--format", "{{.Names}}"],
                capture_output=True, text=True
            )
            
            if "relink-router" in result.stdout:
                # Запускаем очистку через API
                cleanup_cmd = [
                    "curl", "-X", "POST",
                    "http://localhost:8001/api/v1/rag/cleanup"
                ]
                
                subprocess.run(cleanup_cmd, capture_output=True)
                print("✅ Очистка коллекций запущена")
            else:
                print("⚠️ Роутер не запущен, очистка пропущена")
                
        except Exception as e:
            print(f"❌ Ошибка автоматической очистки: {e}")

def main():
    """Главная функция"""
    
    parser = argparse.ArgumentParser(description="Умный кеш для Docker сборки")
    parser.add_argument("--build-all", action="store_true", help="Собрать все сервисы")
    parser.add_argument("--build-base", action="store_true", help="Собрать базовый образ")
    parser.add_argument("--build-service", type=str, help="Собрать конкретный сервис")
    parser.add_argument("--force", action="store_true", help="Принудительная сборка")
    parser.add_argument("--clean", action="store_true", help="Очистить кеш")
    parser.add_argument("--stats", action="store_true", help="Показать статистику")
    parser.add_argument("--chromadb-optimization", action="store_true", help="Оптимизация ChromaDB")
    parser.add_argument("--auto-cleanup", action="store_true", help="Автоматическая очистка коллекций")
    
    args = parser.parse_args()
    
    cache = SmartDockerCache()
    
    if args.clean:
        cache.cleanup_cache()
    elif args.stats:
        cache.show_stats()
    elif args.chromadb_optimization:
        cache.chromadb_optimization()
    elif args.auto_cleanup:
        cache.auto_cleanup_collections()
    elif args.build_base:
        cache.build_base_image(args.force)
    elif args.build_service:
        cache.build_service(args.build_service, args.force)
    elif args.build_all:
        cache.build_all_services(args.force)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 