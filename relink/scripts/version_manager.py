#!/usr/bin/env python3
"""
Комплексный менеджер версий для проекта reLink
Включает управление версиями, релизы и генерацию документации
"""

import re
import sys
import json
import subprocess
import requests
import yaml
import markdown
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
import os
import shutil
from jinja2 import Template
import sqlite3
import tempfile


# TODO: Добавить валидацию версии
# TODO: Добавить валидацию changelog
# TODO: Добавить валидацию README

@dataclass
class Version:
    """Класс для работы с версиями по SemVer 2.0"""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    def __post_init__(self):
        """Валидация версии после инициализации"""
        if not all(isinstance(x, int) and x >= 0 for x in [self.major, self.minor, self.patch]):
            raise ValueError("Major, minor и patch должны быть неотрицательными целыми числами")
        
        if self.prerelease and not re.match(r'^[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*$', self.prerelease):
            raise ValueError("Prerelease должен соответствовать формату SemVer")
        
        if self.build and not re.match(r'^[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*$', self.build):
            raise ValueError("Build должен соответствовать формату SemVer")
    
    @classmethod
    def parse(cls, version_string: str) -> 'Version':
        """Парсинг версии из строки"""
        # Основной паттерн SemVer 2.0
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
        match = re.match(pattern, version_string)
        
        if not match:
            raise ValueError(f"Неверный формат версии: {version_string}")
        
        major, minor, patch, prerelease, build = match.groups()
        
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build=build
        )
    
    def __str__(self) -> str:
        """Строковое представление версии"""
        version = f"{self.major}.{self.minor}.{self.patch}"
        
        if self.prerelease:
            version += f"-{self.prerelease}"
        
        if self.build:
            version += f"+{self.build}"
        
        return version
    
    def __eq__(self, other: 'Version') -> bool:
        """Сравнение версий"""
        if not isinstance(other, Version):
            return False
        
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)
    
    def __lt__(self, other: 'Version') -> bool:
        """Сравнение версий для сортировки"""
        if not isinstance(other, Version):
            raise TypeError("Можно сравнивать только с объектом Version")
        
        # Сравниваем основные компоненты
        if (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch):
            return True
        if (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch):
            return False
        
        # Если основные компоненты равны, сравниваем prerelease
        if self.prerelease is None and other.prerelease is not None:
            return False  # Версия без prerelease больше
        if self.prerelease is not None and other.prerelease is None:
            return True   # Версия с prerelease меньше
        
        if self.prerelease != other.prerelease:
            # Сравниваем prerelease компоненты
            return self._compare_prerelease(self.prerelease, other.prerelease)
        
        return False
    
    def _compare_prerelease(self, prerelease1: str, prerelease2: str) -> bool:
        """Сравнение prerelease компонентов"""
        parts1 = prerelease1.split('.')
        parts2 = prerelease2.split('.')
        
        for i in range(max(len(parts1), len(parts2))):
            part1 = parts1[i] if i < len(parts1) else None
            part2 = parts2[i] if i < len(parts2) else None
            
            if part1 is None:
                return True   # Меньше частей = меньше версия
            if part2 is None:
                return False  # Больше частей = больше версия
            
            # Пытаемся сравнить как числа
            try:
                num1, num2 = int(part1), int(part2)
                if num1 != num2:
                    return num1 < num2
            except ValueError:
                # Если не числа, сравниваем как строки
                if part1 != part2:
                    return part1 < part2
        
        return False
    
    def bump_major(self) -> 'Version':
        """Увеличение major версии"""
        return Version(self.major + 1, 0, 0)
    
    def bump_minor(self) -> 'Version':
        """Увеличение minor версии"""
        return Version(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> 'Version':
        """Увеличение patch версии"""
        return Version(self.major, self.minor, self.patch + 1)
    
    def set_prerelease(self, prerelease: str) -> 'Version':
        """Установка prerelease"""
        return Version(self.major, self.minor, self.patch, prerelease, self.build)
    
    def set_build(self, build: str) -> 'Version':
        """Установка build"""
        return Version(self.major, self.minor, self.patch, self.prerelease, build)
    
    def is_stable(self) -> bool:
        """Проверка, является ли версия стабильной"""
        return self.prerelease is None
    
    def is_prerelease(self) -> bool:
        """Проверка, является ли версия prerelease"""
        return self.prerelease is not None


@dataclass
class ChangelogEntry:
    """Запись в changelog"""
    version: str
    date: str
    changes: List[str]
    commit_hash: Optional[str] = None
    author: Optional[str] = None


@dataclass
class ReleaseInfo:
    """Информация о релизе"""
    version: str
    title: str
    description: str
    changes: List[str]
    date: str
    tag_name: str
    draft: bool = False
    prerelease: bool = False


@dataclass
class DocumentationConfig:
    """Конфигурация документации"""
    title: str = "reLink Documentation"
    description: str = "Документация проекта reLink"
    theme: str = "material"
    include_api_docs: bool = True
    include_architecture: bool = True
    include_database: bool = True
    include_changelog: bool = True
    output_dir: str = "docs"
    template_dir: Optional[str] = None


class VersionManager:
    """Комплексный менеджер версий проекта"""
    
    def __init__(self, project_root: str = ".", github_token: Optional[str] = None):
        self.project_root = Path(project_root)
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        
        # Файлы версий
        self.version_file = self.project_root / "VERSION"
        self.changelog_file = self.project_root / "CHANGELOG.md"
        self.package_json = self.project_root / "frontend" / "package.json"
        self.pyproject_toml = self.project_root / "pyproject.toml"
        
        # Конфигурация документации
        self.docs_config = DocumentationConfig()
        self.docs_dir = self.project_root / self.docs_config.output_dir
        
        # GitHub API
        self.github_api_base = "https://api.github.com"
        self.repo_owner = "your-username"  # Замените на реальные данные
        self.repo_name = "reLink"
        
    def get_current_version(self) -> Version:
        """Получение текущей версии"""
        # Пытаемся получить из файла VERSION
        if self.version_file.exists():
            with open(self.version_file, 'r', encoding='utf-8') as f:
                version_str = f.read().strip()
                return Version.parse(version_str)
        
        # Fallback: пытаемся получить из README
        readme_version = self._extract_version_from_readme()
        if readme_version:
            return Version.parse(readme_version)
        
        # Default версия
        return Version(0, 1, 0)
    
    def _extract_version_from_readme(self) -> Optional[str]:
        """Извлечение версии из README.md"""
        readme_file = self.project_root / "README.md"
        if not readme_file.exists():
            return None
        
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ищем версию в заголовках или специальных блоках
        patterns = [
            r'#.*v?(\d+\.\d+\.\d+)',
            r'Version[:\s]+v?(\d+\.\d+\.\d+)',
            r'Current Version[:\s]+v?(\d+\.\d+\.\d+)',
            r'```version\s*\n\s*v?(\d+\.\d+\.\d+)\s*\n\s*```'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1)
        
        return None
    
    def set_version(self, version: Union[Version, str]) -> None:
        """Установка версии во всех файлах проекта"""
        if isinstance(version, str):
            version = Version.parse(version)
        
        # Обновляем файл VERSION
        with open(self.version_file, 'w', encoding='utf-8') as f:
            f.write(str(version))
        
        # Обновляем README
        self._update_readme_version(version)
        
        # Обновляем package.json если существует
        if self.package_json.exists():
            self._update_package_json_version(version)
        
        # Обновляем pyproject.toml если существует
        if self.pyproject_toml.exists():
            self._update_pyproject_toml_version(version)
        
        # Обновляем .env файл
        self._update_env_version(version)
        
        print(f"✅ Версия {version} установлена во всех файлах")
    
    def _update_readme_version(self, version: Version) -> None:
        """Обновление версии в README.md"""
        readme_file = self.project_root / "README.md"
        if not readme_file.exists():
            return
        
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем версию в заголовках
        content = re.sub(
            r'(#.*?)(v?\d+\.\d+\.\d+)',
            r'\1v' + str(version),
            content,
            flags=re.IGNORECASE
        )
        
        # Заменяем версию в специальных блоках
        content = re.sub(
            r'(Version[:\s]+)v?\d+\.\d+\.\d+',
            r'\1v' + str(version),
            content,
            flags=re.IGNORECASE
        )
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _update_package_json_version(self, version: Version) -> None:
        """Обновление версии в package.json"""
        with open(self.package_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['version'] = str(version)
        
        with open(self.package_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _update_pyproject_toml_version(self, version: Version) -> None:
        """Обновление версии в pyproject.toml"""
        with open(self.pyproject_toml, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем версию в [tool.poetry] или [project] секции
        content = re.sub(
            r'(version\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
            r'\1' + str(version) + r'\2',
            content
        )
        
        with open(self.pyproject_toml, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _update_env_version(self, version: Version) -> None:
        """Обновление версии в .env файле"""
        env_file = self.project_root / ".env"
        if not env_file.exists():
            return
        
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем или добавляем VERSION переменную
        if re.search(r'^VERSION\s*=', content, re.MULTILINE):
            content = re.sub(
                r'^VERSION\s*=.*$',
                f'VERSION={version}',
                content,
                flags=re.MULTILINE
            )
        else:
            content += f'\nVERSION={version}\n'
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def bump_version(self, bump_type: str, prerelease: Optional[str] = None) -> Version:
        """Увеличение версии"""
        current_version = self.get_current_version()
        
        if bump_type == 'major':
            new_version = current_version.bump_major()
        elif bump_type == 'minor':
            new_version = current_version.bump_minor()
        elif bump_type == 'patch':
            new_version = current_version.bump_patch()
        else:
            raise ValueError("bump_type должен быть 'major', 'minor' или 'patch'")
        
        if prerelease:
            new_version = new_version.set_prerelease(prerelease)
        
        self.set_version(new_version)
        return new_version
    
    def create_release(self, release_type: str = 'patch', 
                      title: Optional[str] = None,
                      description: Optional[str] = None,
                      draft: bool = False,
                      prerelease: bool = False) -> ReleaseInfo:
        """Создание релиза"""
        # Увеличиваем версию
        new_version = self.bump_version(release_type)
        
        # Получаем изменения из git
        changes = self._get_git_changes()
        
        # Создаем информацию о релизе
        release_info = ReleaseInfo(
            version=str(new_version),
            title=title or f"Release v{new_version}",
            description=description or f"Release version {new_version}",
            changes=changes,
            date=datetime.now().strftime("%Y-%m-%d"),
            tag_name=f"v{new_version}",
            draft=draft,
            prerelease=prerelease or new_version.is_prerelease()
        )
        
        # Обновляем changelog
        self._update_changelog(release_info)
        
        # Создаем git tag
        self._create_git_tag(release_info.tag_name)
        
        # Создаем GitHub release если есть токен
        if self.github_token:
            self._create_github_release(release_info)
        
        # Генерируем документацию
        self.generate_documentation()
        
        return release_info
    
    def _get_git_changes(self) -> List[str]:
        """Получение изменений из git"""
        try:
            # Получаем последний тег
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True, text=True, cwd=self.project_root
            )
            last_tag = result.stdout.strip() if result.returncode == 0 else None
            
            # Получаем коммиты с последнего тега
            if last_tag:
                result = subprocess.run(
                    ['git', 'log', f'{last_tag}..HEAD', '--oneline', '--no-merges'],
                    capture_output=True, text=True, cwd=self.project_root
                )
            else:
                result = subprocess.run(
                    ['git', 'log', '--oneline', '--no-merges'],
                    capture_output=True, text=True, cwd=self.project_root
                )
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                return [commit for commit in commits if commit.strip()]
            
        except Exception as e:
            print(f"⚠️ Ошибка получения git изменений: {e}")
        
        return ["Initial release"]
    
    def _update_changelog(self, release_info: ReleaseInfo) -> None:
        """Обновление changelog"""
        if not self.changelog_file.exists():
            # Создаем новый changelog
            content = f"""# Changelog

Все важные изменения в проекте документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
и проект следует [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

## [{release_info.version}] - {release_info.date}

### Added
- Initial release

"""
        else:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Добавляем новую версию после [Unreleased]
            unreleased_pattern = r'## \[Unreleased\]'
            new_entry = f"""## [Unreleased]

## [{release_info.version}] - {release_info.date}

### Added
"""
            
            for change in release_info.changes:
                new_entry += f"- {change}\n"
            
            new_entry += "\n"
            
            content = re.sub(unreleased_pattern, new_entry, content)
        
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_git_tag(self, tag_name: str) -> None:
        """Создание git тега"""
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.project_root, check=True)
            subprocess.run(['git', 'commit', '-m', f'Release {tag_name}'], cwd=self.project_root, check=True)
            subprocess.run(['git', 'tag', tag_name], cwd=self.project_root, check=True)
            subprocess.run(['git', 'push', '--tags'], cwd=self.project_root, check=True)
            print(f"✅ Git тег {tag_name} создан и отправлен")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка создания git тега: {e}")
    
    def _create_github_release(self, release_info: ReleaseInfo) -> None:
        """Создание GitHub release"""
        if not self.github_token:
            print("⚠️ GitHub токен не найден, пропускаем создание release")
            return
        
        url = f"{self.github_api_base}/repos/{self.repo_owner}/{self.repo_name}/releases"
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'tag_name': release_info.tag_name,
            'name': release_info.title,
            'body': self._format_release_body(release_info),
            'draft': release_info.draft,
            'prerelease': release_info.prerelease
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            print(f"✅ GitHub release создан: {response.json()['html_url']}")
        except requests.RequestException as e:
            print(f"❌ Ошибка создания GitHub release: {e}")
    
    def _format_release_body(self, release_info: ReleaseInfo) -> str:
        """Форматирование тела release"""
        body = f"{release_info.description}\n\n"
        body += "## Changes\n\n"
        
        for change in release_info.changes:
            body += f"- {change}\n"
        
        return body
    
    def generate_documentation(self, config: Optional[DocumentationConfig] = None) -> None:
        """Генерация документации"""
        if config:
            self.docs_config = config
        
        # Создаем директорию для документации
        self.docs_dir.mkdir(exist_ok=True)
        
        # Генерируем основные страницы
        self._generate_index_page()
        self._generate_api_docs()
        self._generate_architecture_docs()
        self._generate_database_docs()
        self._generate_changelog_page()
        
        # Копируем статические файлы
        self._copy_static_files()
        
        print(f"✅ Документация сгенерирована в {self.docs_dir}")
    
    def _generate_index_page(self) -> None:
        """Генерация главной страницы документации"""
        template = """# {{ title }}

{{ description }}

## Быстрый старт

1. **Установка**
   ```bash
   git clone https://github.com/{{ repo_owner }}/{{ repo_name }}.git
   cd {{ repo_name }}
   ```

2. **Запуск с Docker**
   ```bash
   docker-compose up -d
   ```

3. **Открыть в браузере**
   ```
   http://localhost:3000
   ```

## Документация

- [API Documentation](api.md)
- [Архитектура](architecture.md)
- [База данных](database.md)
- [Changelog](changelog.md)

## Версия

Текущая версия: **{{ version }}**

## Поддержка

Если у вас есть вопросы или проблемы, создайте issue в GitHub.
"""
        
        content = Template(template).render(
            title=self.docs_config.title,
            description=self.docs_config.description,
            repo_owner=self.repo_owner,
            repo_name=self.repo_name,
            version=str(self.get_current_version())
        )
        
        with open(self.docs_dir / "index.md", 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_api_docs(self) -> None:
        """Генерация API документации"""
        if not self.docs_config.include_api_docs:
            return
        
        # Здесь можно добавить автоматическое извлечение API из FastAPI
        template = """# API Documentation

## Endpoints

### Health Check
- **GET** `/health` - Проверка состояния сервиса

### WordPress Analysis
- **POST** `/api/analyze` - Анализ WordPress сайта
- **GET** `/api/history` - История анализов
- **GET** `/api/recommendations` - SEO рекомендации

### Authentication
- **POST** `/api/auth/login` - Вход в систему
- **POST** `/api/auth/logout` - Выход из системы

## Примеры запросов

### Анализ сайта
```bash
curl -X POST "http://localhost:8000/api/analyze" \\
     -H "Content-Type: application/json" \\
     -d '{"url": "https://example.com"}'
```

### Получение истории
```bash
curl -X GET "http://localhost:8000/api/history" \\
     -H "Authorization: Bearer YOUR_TOKEN"
```
"""
        
        with open(self.docs_dir / "api.md", 'w', encoding='utf-8') as f:
            f.write(template)
    
    def _generate_architecture_docs(self) -> None:
        """Генерация документации по архитектуре"""
        if not self.docs_config.include_architecture:
            return
        
        template = """# Архитектура системы

## Общая схема

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Ollama        │    │   ChromaDB      │
│   (Proxy)       │    │   (LLM)         │    │   (Vector DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Компоненты

### Frontend (React + TypeScript)
- **Технологии**: React 18, TypeScript, Tailwind CSS
- **Функции**: Пользовательский интерфейс, визуализация данных
- **Особенности**: Темная тема, адаптивный дизайн

### Backend (FastAPI + Python)
- **Технологии**: FastAPI, SQLAlchemy, Pydantic
- **Функции**: API, бизнес-логика, интеграция с LLM
- **Особенности**: Асинхронность, автоматическая документация

### Database (SQLite + ChromaDB)
- **Технологии**: SQLite (основная БД), ChromaDB (векторная БД)
- **Функции**: Хранение данных, векторный поиск
- **Особенности**: Встроенная БД, простота развертывания

### LLM Integration (Ollama)
- **Технологии**: Ollama, локальные модели
- **Функции**: Анализ контента, генерация рекомендаций
- **Особенности**: Работа без интернета, приватность

## Поток данных

1. **Пользователь** вводит URL сайта
2. **Frontend** отправляет запрос на Backend
3. **Backend** сканирует WordPress сайт
4. **Ollama** анализирует контент и генерирует рекомендации
5. **Database** сохраняет результаты анализа
6. **Frontend** отображает результаты пользователю

## Безопасность

- JWT токены для аутентификации
- Валидация входных данных
- Rate limiting
- CORS настройки
- Безопасные заголовки
"""
        
        with open(self.docs_dir / "architecture.md", 'w', encoding='utf-8') as f:
            f.write(template)
    
    def _generate_database_docs(self) -> None:
        """Генерация документации по базе данных"""
        if not self.docs_config.include_database:
            return
        
        template = """# База данных

## Схема базы данных

### Основные таблицы

#### users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### analyses
```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    url VARCHAR(500) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result_data TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### recommendations
```sql
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

## Индексы

```sql
-- Индекс для быстрого поиска по URL
CREATE INDEX idx_analyses_url ON analyses(url);

-- Индекс для поиска по пользователю
CREATE INDEX idx_analyses_user_id ON analyses(user_id);

-- Индекс для поиска по статусу
CREATE INDEX idx_analyses_status ON analyses(status);

-- Индекс для рекомендаций по анализу
CREATE INDEX idx_recommendations_analysis_id ON recommendations(analysis_id);
```

## Миграции

Проект использует Alembic для управления миграциями:

```bash
# Создание новой миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

## Векторная база данных (ChromaDB)

ChromaDB используется для хранения векторных представлений контента:

- **Embeddings**: Векторные представления текста
- **Metadata**: Метаданные документов
- **Collections**: Группировка связанных документов

### Пример использования

```python
import chromadb

# Создание клиента
client = chromadb.Client()

# Создание коллекции
collection = client.create_collection("seo_content")

# Добавление документов
collection.add(
    documents=["SEO оптимизированный контент"],
    metadatas=[{"source": "example.com", "type": "article"}],
    ids=["doc1"]
)

# Поиск похожих документов
results = collection.query(
    query_texts=["SEO рекомендации"],
    n_results=5
)
```
"""
        
        with open(self.docs_dir / "database.md", 'w', encoding='utf-8') as f:
            f.write(template)
    
    def _generate_changelog_page(self) -> None:
        """Генерация страницы changelog"""
        if not self.docs_config.include_changelog:
            return
        
        if not self.changelog_file.exists():
            return
        
        with open(self.changelog_file, 'r', encoding='utf-8') as f:
            changelog_content = f.read()
        
        with open(self.docs_dir / "changelog.md", 'w', encoding='utf-8') as f:
            f.write(changelog_content)
    
    def _copy_static_files(self) -> None:
        """Копирование статических файлов"""
        static_dir = self.docs_dir / "static"
        static_dir.mkdir(exist_ok=True)
        
        # Здесь можно добавить копирование CSS, JS, изображений
        # shutil.copy2("path/to/style.css", static_dir / "style.css")
    
    def extract_version(self) -> str:
        """Извлечение текущей версии (для CLI)"""
        return str(self.get_current_version())
    
    def update_version(self) -> bool:
        """Обновление версии во всех файлах (для CLI)"""
        try:
            current_version = self.get_current_version()
            self.set_version(current_version)
            return True
        except Exception as e:
            print(f"❌ Ошибка обновления версии: {e}")
            return False
    
    def sync_from_readme(self) -> bool:
        """Синхронизация версии из README (для CLI)"""
        try:
            readme_version = self._extract_version_from_readme()
            if not readme_version:
                print("❌ Не удалось извлечь версию из README")
                return False
            
            version = Version.parse(readme_version)
            self.set_version(version)
            print(f"✅ Версия синхронизирована: {version}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка синхронизации: {e}")
            return False


def main():
    """Основная функция CLI"""
    parser = argparse.ArgumentParser(description="Менеджер версий reLink")
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда extract
    extract_parser = subparsers.add_parser('extract', help='Извлечь текущую версию')
    extract_parser.add_argument('--readme', help='Путь к README файлу')
    
    # Команда update
    update_parser = subparsers.add_parser('update', help='Обновить версию во всех файлах')
    update_parser.add_argument('--project-root', default='.', help='Корень проекта')
    
    # Команда sync
    sync_parser = subparsers.add_parser('sync', help='Синхронизировать версию из README')
    sync_parser.add_argument('--project-root', default='.', help='Корень проекта')
    
    # Команда bump
    bump_parser = subparsers.add_parser('bump', help='Увеличить версию')
    bump_parser.add_argument('type', choices=['major', 'minor', 'patch'], help='Тип увеличения')
    bump_parser.add_argument('--prerelease', help='Prerelease суффикс')
    bump_parser.add_argument('--project-root', default='.', help='Корень проекта')
    
    # Команда release
    release_parser = subparsers.add_parser('release', help='Создать релиз')
    release_parser.add_argument('type', choices=['major', 'minor', 'patch'], help='Тип релиза')
    release_parser.add_argument('--title', help='Заголовок релиза')
    release_parser.add_argument('--description', help='Описание релиза')
    release_parser.add_argument('--draft', action='store_true', help='Создать как черновик')
    release_parser.add_argument('--prerelease', action='store_true', help='Создать как prerelease')
    release_parser.add_argument('--project-root', default='.', help='Корень проекта')
    
    # Команда docs
    docs_parser = subparsers.add_parser('docs', help='Сгенерировать документацию')
    docs_parser.add_argument('--project-root', default='.', help='Корень проекта')
    docs_parser.add_argument('--output-dir', help='Директория для документации')
    docs_parser.add_argument('--theme', help='Тема документации')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Создаем менеджер версий
    manager = VersionManager(args.project_root)
    
    if args.command == 'extract':
        version = manager.extract_version()
        print(version)
    
    elif args.command == 'update':
        success = manager.update_version()
        sys.exit(0 if success else 1)
    
    elif args.command == 'sync':
        success = manager.sync_from_readme()
        sys.exit(0 if success else 1)
    
    elif args.command == 'bump':
        new_version = manager.bump_version(args.type, args.prerelease)
        print(f"✅ Версия увеличена до {new_version}")
    
    elif args.command == 'release':
        release_info = manager.create_release(
            release_type=args.type,
            title=args.title,
            description=args.description,
            draft=args.draft,
            prerelease=args.prerelease
        )
        print(f"✅ Релиз {release_info.version} создан")
    
    elif args.command == 'docs':
        config = DocumentationConfig()
        if args.output_dir:
            config.output_dir = args.output_dir
        if args.theme:
            config.theme = args.theme
        
        manager.generate_documentation(config)


if __name__ == "__main__":
    main() 