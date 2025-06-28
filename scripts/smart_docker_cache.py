#!/usr/bin/env python3
"""
🧠 Умная система управления Docker кешем

Аналог Git для Docker слоев - автоматически определяет изменения в коде
и пересобирает только затронутые слои, сохраняя кеш для неизмененных частей.
"""

import os
import sys
import json
import hashlib
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import docker
from docker.errors import DockerException
import yaml

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class LayerInfo:
    """Информация о Docker слое"""
    layer_id: str
    files_hash: str
    dependencies: List[str] = field(default_factory=list)
    build_time: Optional[datetime] = None
    size: Optional[int] = None
    is_valid: bool = True

@dataclass
class BuildContext:
    """Контекст сборки"""
    service_name: str
    dockerfile_path: str
    context_path: str
    build_args: Dict[str, str] = field(default_factory=dict)
    target: Optional[str] = None
    cache_from: List[str] = field(default_factory=list)
    cache_to: Optional[str] = None

class SmartDockerCache:
    """Умная система управления Docker кешем"""
    
    def __init__(self, cache_dir: str = ".docker_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.layer_cache: Dict[str, LayerInfo] = {}
        self.docker_client = docker.from_env()
        self.load_cache_metadata()
    
    def load_cache_metadata(self):
        """Загрузка метаданных кеша"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.layer_cache = {
                        layer_id: LayerInfo(**layer_data)
                        for layer_id, layer_data in data.items()
                    }
            except Exception as e:
                logger.warning(f"Ошибка загрузки метаданных кеша: {e}")
    
    def save_cache_metadata(self):
        """Сохранение метаданных кеша"""
        try:
            data = {
                layer_id: {
                    'layer_id': layer.layer_id,
                    'files_hash': layer.files_hash,
                    'dependencies': layer.dependencies,
                    'build_time': layer.build_time.isoformat() if layer.build_time else None,
                    'size': layer.size,
                    'is_valid': layer.is_valid
                }
                for layer_id, layer in self.layer_cache.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных кеша: {e}")
    
    def calculate_files_hash(self, context_path: str, dockerfile_path: str) -> str:
        """Вычисление хеша файлов в контексте сборки"""
        context_path = Path(context_path)
        dockerfile_path = Path(dockerfile_path)
        
        # Читаем Dockerfile для определения файлов
        dockerfile_content = dockerfile_path.read_text()
        
        # Анализируем COPY и ADD команды
        files_to_hash = set()
        
        for line in dockerfile_content.split('\n'):
            line = line.strip()
            if line.startswith(('COPY', 'ADD')):
                # Извлекаем пути файлов из команды
                parts = line.split()
                if len(parts) >= 3:
                    source = parts[1]
                    if not source.startswith('--'):
                        files_to_hash.add(source)
        
        # Добавляем сам Dockerfile
        files_to_hash.add(str(dockerfile_path.relative_to(context_path)))
        
        # Вычисляем хеш всех файлов
        hasher = hashlib.sha256()
        
        for file_pattern in files_to_hash:
            # Обрабатываем wildcards
            if '*' in file_pattern or '?' in file_pattern:
                import glob
                matching_files = glob.glob(str(context_path / file_pattern), recursive=True)
                for file_path in matching_files:
                    if Path(file_path).is_file():
                        self._add_file_to_hash(hasher, file_path)
            else:
                file_path = context_path / file_pattern
                if file_path.is_file():
                    self._add_file_to_hash(hasher, file_path)
                elif file_path.is_dir():
                    # Рекурсивно добавляем все файлы в директории
                    for subfile in file_path.rglob('*'):
                        if subfile.is_file():
                            self._add_file_to_hash(hasher, str(subfile))
        
        return hasher.hexdigest()
    
    def _add_file_to_hash(self, hasher, file_path: str):
        """Добавление файла к хешу"""
        try:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
        except Exception as e:
            logger.warning(f"Не удалось прочитать файл {file_path}: {e}")
    
    def get_layer_dependencies(self, dockerfile_path: str) -> List[str]:
        """Получение зависимостей слоя из Dockerfile"""
        dockerfile_content = Path(dockerfile_path).read_text()
        dependencies = []
        
        for line in dockerfile_content.split('\n'):
            line = line.strip()
            if line.startswith('FROM'):
                parts = line.split()
                if len(parts) >= 2:
                    base_image = parts[1]
                    dependencies.append(base_image)
        
        return dependencies
    
    def is_layer_valid(self, layer_id: str, context_path: str, dockerfile_path: str) -> bool:
        """Проверка валидности слоя"""
        if layer_id not in self.layer_cache:
            return False
        
        layer = self.layer_cache[layer_id]
        if not layer.is_valid:
            return False
        
        # Проверяем хеш файлов
        current_hash = self.calculate_files_hash(context_path, dockerfile_path)
        if layer.files_hash != current_hash:
            logger.info(f"Хеш файлов изменился для слоя {layer_id}")
            return False
        
        # Проверяем зависимости
        current_deps = self.get_layer_dependencies(dockerfile_path)
        if layer.dependencies != current_deps:
            logger.info(f"Зависимости изменились для слоя {layer_id}")
            return False
        
        return True
    
    def invalidate_layer(self, layer_id: str):
        """Инвалидация слоя"""
        if layer_id in self.layer_cache:
            self.layer_cache[layer_id].is_valid = False
            logger.info(f"Слой {layer_id} инвалидирован")
    
    def invalidate_dependent_layers(self, layer_id: str):
        """Инвалидация зависимых слоев"""
        invalidated = set()
        to_invalidate = {layer_id}
        
        while to_invalidate:
            current = to_invalidate.pop()
            if current in invalidated:
                continue
            
            invalidated.add(current)
            self.invalidate_layer(current)
            
            # Находим слои, которые зависят от текущего
            for layer_id, layer in self.layer_cache.items():
                if current in layer.dependencies and layer_id not in invalidated:
                    to_invalidate.add(layer_id)
    
    def build_with_smart_cache(self, context: BuildContext, force_rebuild: bool = False) -> bool:
        """Умная сборка с кешем"""
        logger.info(f"🔨 Умная сборка {context.service_name}")
        
        # Вычисляем хеш файлов
        files_hash = self.calculate_files_hash(context.context_path, context.dockerfile_path)
        
        # Создаем ID слоя
        layer_id = f"{context.service_name}_{files_hash[:8]}"
        
        # Проверяем валидность кеша
        if not force_rebuild and self.is_layer_valid(layer_id, context.context_path, context.dockerfile_path):
            logger.info(f"✅ Используем кеш для {context.service_name}")
            return True
        
        # Инвалидируем зависимые слои
        if layer_id in self.layer_cache:
            self.invalidate_dependent_layers(layer_id)
        
        # Выполняем сборку
        logger.info(f"🏗️ Пересборка {context.service_name}")
        
        try:
            build_args = {
                'DOCKER_BUILDKIT': '1',
                'COMPOSE_DOCKER_CLI_BUILD': '1'
            }
            build_args.update(context.build_args)
            
            # Подготавливаем команду сборки
            cmd = [
                'docker', 'build',
                '-f', context.dockerfile_path,
                '--build-arg', f'DOCKER_BUILDKIT=1'
            ]
            
            # Добавляем кеш
            if context.cache_from:
                for cache_from in context.cache_from:
                    cmd.extend(['--cache-from', cache_from])
            
            if context.cache_to:
                cmd.extend(['--cache-to', context.cache_to])
            
            # Добавляем target если указан
            if context.target:
                cmd.extend(['--target', context.target])
            
            # Добавляем тег
            cmd.extend(['-t', f"{context.service_name}:latest"])
            
            # Добавляем контекст
            cmd.append(context.context_path)
            
            # Выполняем сборку
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Обновляем метаданные кеша
                self.layer_cache[layer_id] = LayerInfo(
                    layer_id=layer_id,
                    files_hash=files_hash,
                    dependencies=self.get_layer_dependencies(context.dockerfile_path),
                    build_time=datetime.now(),
                    is_valid=True
                )
                self.save_cache_metadata()
                
                logger.info(f"✅ Сборка {context.service_name} завершена успешно")
                return True
            else:
                logger.error(f"❌ Ошибка сборки {context.service_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка сборки {context.service_name}: {e}")
            return False
    
    def clean_invalid_cache(self):
        """Очистка невалидного кеша"""
        invalid_layers = [
            layer_id for layer_id, layer in self.layer_cache.items()
            if not layer.is_valid
        ]
        
        for layer_id in invalid_layers:
            del self.layer_cache[layer_id]
        
        if invalid_layers:
            self.save_cache_metadata()
            logger.info(f"🧹 Удалено {len(invalid_layers)} невалидных слоев")
    
    def get_cache_stats(self) -> Dict:
        """Получение статистики кеша"""
        total_layers = len(self.layer_cache)
        valid_layers = sum(1 for layer in self.layer_cache.values() if layer.is_valid)
        total_size = sum(layer.size or 0 for layer in self.layer_cache.values())
        
        return {
            'total_layers': total_layers,
            'valid_layers': valid_layers,
            'invalid_layers': total_layers - valid_layers,
            'total_size_mb': total_size / (1024 * 1024) if total_size else 0,
            'cache_dir': str(self.cache_dir)
        }

def parse_docker_compose(compose_file: str) -> List[BuildContext]:
    """Парсинг docker-compose.yml для извлечения контекстов сборки"""
    with open(compose_file, 'r') as f:
        compose_data = yaml.safe_load(f)
    
    contexts = []
    
    for service_name, service_config in compose_data.get('services', {}).items():
        if 'build' in service_config:
            build_config = service_config['build']
            
            if isinstance(build_config, dict):
                context_path = build_config.get('context', '.')
                dockerfile = build_config.get('dockerfile', 'Dockerfile')
                dockerfile_path = os.path.join(context_path, dockerfile)
                target = build_config.get('target')
                
                contexts.append(BuildContext(
                    service_name=service_name,
                    dockerfile_path=dockerfile_path,
                    context_path=context_path,
                    target=target
                ))
    
    return contexts

def main():
    parser = argparse.ArgumentParser(description='Умная система управления Docker кешем')
    parser.add_argument('--compose-file', default='docker-compose.yml', help='Путь к docker-compose.yml')
    parser.add_argument('--service', help='Сборка конкретного сервиса')
    parser.add_argument('--force', action='store_true', help='Принудительная пересборка')
    parser.add_argument('--clean', action='store_true', help='Очистка невалидного кеша')
    parser.add_argument('--stats', action='store_true', help='Показать статистику кеша')
    parser.add_argument('--cache-dir', default='.docker_cache', help='Директория кеша')
    
    args = parser.parse_args()
    
    cache_manager = SmartDockerCache(args.cache_dir)
    
    if args.stats:
        stats = cache_manager.get_cache_stats()
        print("📊 Статистика кеша:")
        print(f"   Всего слоев: {stats['total_layers']}")
        print(f"   Валидных: {stats['valid_layers']}")
        print(f"   Невалидных: {stats['invalid_layers']}")
        print(f"   Размер: {stats['total_size_mb']:.2f} MB")
        print(f"   Директория: {stats['cache_dir']}")
        return
    
    if args.clean:
        cache_manager.clean_invalid_cache()
        return
    
    # Парсим docker-compose.yml
    if not os.path.exists(args.compose_file):
        logger.error(f"Файл {args.compose_file} не найден")
        return
    
    contexts = parse_docker_compose(args.compose_file)
    
    if args.service:
        contexts = [ctx for ctx in contexts if ctx.service_name == args.service]
        if not contexts:
            logger.error(f"Сервис {args.service} не найден")
            return
    
    # Выполняем сборку
    success_count = 0
    for context in contexts:
        if cache_manager.build_with_smart_cache(context, args.force):
            success_count += 1
    
    logger.info(f"✅ Сборка завершена: {success_count}/{len(contexts)} сервисов")

if __name__ == '__main__':
    main() 