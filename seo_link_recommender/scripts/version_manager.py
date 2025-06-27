#!/usr/bin/env python3
"""
Менеджер версий для SEO Link Recommender
Парсит версию из README.md и управляет Git тегами
"""

import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple


class VersionManager:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.readme_path = self.project_root / "README.md"
        
    def extract_version_from_readme(self) -> Optional[str]:
        """Извлекает версию из README.md"""
        try:
            with open(self.readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Ищем версию в заголовке
            header_match = re.search(r'# 🚀 SEO Link Recommender v(\d+\.\d+\.\d+)', content)
            if header_match:
                return header_match.group(1)
                
            # Ищем версию в поле версии
            version_match = re.search(r'\*\*Версия:\*\*\s*(\d+\.\d+\.\d+)', content)
            if version_match:
                return version_match.group(1)
                
            return None
        except Exception as e:
            print(f"❌ Ошибка чтения README: {e}")
            return None
    
    def update_version_in_readme(self, new_version: str) -> bool:
        """Обновляет версию в README.md"""
        try:
            with open(self.readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Обновляем заголовок
            content = re.sub(
                r'# 🚀 SEO Link Recommender v\d+\.\d+\.\d+',
                f'# 🚀 SEO Link Recommender v{new_version}',
                content
            )
            
            # Обновляем поле версии
            content = re.sub(
                r'\*\*Версия:\*\*\s*\d+\.\d+\.\d+',
                f'**Версия:** {new_version}',
                content
            )
            
            # Обновляем дату релиза
            current_date = datetime.now().strftime('%Y-%m-%d')
            content = re.sub(
                r'\*\*Дата релиза:\*\*\s*\d{4}-\d{2}-\d{2}',
                f'**Дата релиза:** {current_date}',
                content
            )
            
            with open(self.readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"✅ Версия обновлена в README: {new_version}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления README: {e}")
            return False
    
    def create_version_file(self, version: str) -> bool:
        """Создает файл с версией для использования в приложении"""
        try:
            version_file = self.project_root / "VERSION"
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(version)
            print(f"✅ Файл VERSION создан: {version}")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания VERSION: {e}")
            return False
    
    def create_git_tag(self, version: str, message: Optional[str] = None) -> bool:
        """Создает Git тег для версии"""
        try:
            if not message:
                message = f"Release v{version}"
            
            # Создаем тег
            subprocess.run([
                'git', 'tag', '-a', f'v{version}', '-m', message
            ], cwd=self.project_root, check=True)
            
            print(f"✅ Git тег создан: v{version}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка создания Git тега: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка Git: {e}")
            return False
    
    def push_git_tag(self, version: str) -> bool:
        """Пушит Git тег в удаленный репозиторий"""
        try:
            subprocess.run([
                'git', 'push', 'origin', f'v{version}'
            ], cwd=self.project_root, check=True)
            
            print(f"✅ Git тег отправлен: v{version}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка отправки Git тега: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка Git push: {e}")
            return False
    
    def get_version_info(self) -> Tuple[str, str]:
        """Получает информацию о версии и дате"""
        version = self.extract_version_from_readme()
        if not version:
            return "unknown", "unknown"
        
        try:
            with open(self.readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            date_match = re.search(r'\*\*Дата релиза:\*\*\s*(\d{4}-\d{2}-\d{2})', content)
            release_date = date_match.group(1) if date_match else "unknown"
            
            return version, release_date
        except Exception:
            return version, "unknown"
    
    def update_frontend_version(self, version: str) -> bool:
        """Обновляет версию в frontend package.json"""
        try:
            package_json_path = self.project_root / "frontend" / "package.json"
            if not package_json_path.exists():
                print("⚠️ package.json не найден")
                return False
            
            with open(package_json_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Обновляем версию в package.json
            content = re.sub(
                r'"version":\s*"[^"]*"',
                f'"version": "{version}"',
                content
            )
            
            with open(package_json_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Версия обновлена в package.json: {version}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления package.json: {e}")
            return False


def main():
    """Основная функция CLI"""
    if len(sys.argv) < 2:
        print("""
🚀 SEO Link Recommender - Version Manager

Использование:
  python version_manager.py <команда> [аргументы]

Команды:
  get                    - Показать текущую версию
  set <version>         - Установить новую версию
  tag [message]         - Создать Git тег
  push                  - Отправить Git тег
  release <version>     - Полный релиз (set + tag + push)
  
Примеры:
  python version_manager.py get
  python version_manager.py set 3.0.18
  python version_manager.py tag "Bug fixes and improvements"
  python version_manager.py release 3.0.18
        """)
        return
    
    manager = VersionManager()
    command = sys.argv[1]
    
    if command == "get":
        version, date = manager.get_version_info()
        print(f"📦 Текущая версия: {version}")
        print(f"📅 Дата релиза: {date}")
        
    elif command == "set":
        if len(sys.argv) < 3:
            print("❌ Укажите версию: python version_manager.py set <version>")
            return
        
        new_version = sys.argv[2]
        if not re.match(r'^\d+\.\d+\.\d+$', new_version):
            print("❌ Неверный формат версии. Используйте: X.Y.Z")
            return
        
        success = (
            manager.update_version_in_readme(new_version) and
            manager.create_version_file(new_version) and
            manager.update_frontend_version(new_version)
        )
        
        if success:
            print(f"🎉 Версия {new_version} успешно установлена!")
        else:
            print("❌ Ошибка установки версии")
            
    elif command == "tag":
        version = manager.extract_version_from_readme()
        if not version:
            print("❌ Не удалось определить версию")
            return
        
        message = sys.argv[2] if len(sys.argv) > 2 else f"Release v{version}"
        success = manager.create_git_tag(version, message)
        
        if success:
            print(f"🏷️ Тег v{version} создан с сообщением: {message}")
        else:
            print("❌ Ошибка создания тега")
            
    elif command == "push":
        version = manager.extract_version_from_readme()
        if not version:
            print("❌ Не удалось определить версию")
            return
        
        success = manager.push_git_tag(version)
        if success:
            print(f"🚀 Тег v{version} отправлен в репозиторий")
        else:
            print("❌ Ошибка отправки тега")
            
    elif command == "release":
        if len(sys.argv) < 3:
            print("❌ Укажите версию: python version_manager.py release <version>")
            return
        
        new_version = sys.argv[2]
        if not re.match(r'^\d+\.\d+\.\d+$', new_version):
            print("❌ Неверный формат версии. Используйте: X.Y.Z")
            return
        
        print(f"🚀 Начинаем релиз версии {new_version}...")
        
        # Устанавливаем версию
        if not manager.update_version_in_readme(new_version):
            print("❌ Ошибка обновления README")
            return
            
        if not manager.create_version_file(new_version):
            print("❌ Ошибка создания VERSION")
            return
            
        if not manager.update_frontend_version(new_version):
            print("❌ Ошибка обновления package.json")
            return
        
        # Создаем тег
        if not manager.create_git_tag(new_version, f"Release v{new_version}"):
            print("❌ Ошибка создания тега")
            return
        
        # Отправляем тег
        if not manager.push_git_tag(new_version):
            print("❌ Ошибка отправки тега")
            return
        
        print(f"🎉 Релиз версии {new_version} завершен успешно!")
        
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Используйте: get, set, tag, push, release")


if __name__ == "__main__":
    main() 