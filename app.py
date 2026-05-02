import os
import sys
import zipfile
import urllib.request
import subprocess
import shutil
import tempfile

def main():
    # Определяем путь к папке %APPDATA%/.editor/
    appdata = os.environ.get('APPDATA')
    if not appdata:
        print("Ошибка: не найдена переменная окружения APPDATA")
        sys.exit(1)
    
    editor_dir = os.path.join(appdata, '.editor')
    
    # Создаем папку .editor, если она не существует
    if not os.path.exists(editor_dir):
        os.makedirs(editor_dir)
        print(f"Создана папка: {editor_dir}")
    else:
        print(f"Папка уже существует: {editor_dir}")
    
    # Временная папка для скачивания
    temp_dir = tempfile.gettempdir()
    zip_path = os.path.join(temp_dir, 'main.zip')
    
    # URL архива
    url = 'https://github.com/Endlad2/Backrooms-Infinity-editor/archive/refs/heads/main.zip'
    
    # Удаляем старый архив из Temp, если он существует
    if os.path.exists(zip_path):
        print("Удаление старого архива из Temp...")
        os.remove(zip_path)
    
    # Скачиваем архив в Temp
    print(f"Скачивание архива из {url}...")
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("Архив успешно скачан в Temp")
    except Exception as e:
        print(f"Ошибка при скачивании архива: {e}")
        sys.exit(1)
    
    # Распаковываем архив прямо в %APPDATA%/.editor/ с перезаписью
    print(f"Распаковка архива в {editor_dir} с перезаписью...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Распаковываем все файлы, перезаписывая существующие
            for file_info in zip_ref.infolist():
                # Убираем корневую папку "Backrooms-Infinity-editor-main/" из пути
                target_path = os.path.join(editor_dir, file_info.filename.replace('Backrooms-Infinity-editor-main/', '', 1))
                
                if file_info.is_dir():
                    if target_path:  # Создаем папку, если она не пустая
                        os.makedirs(target_path, exist_ok=True)
                else:
                    # Создаем родительские папки, если нужно
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    # Распаковываем файл (перезаписываем, если существует)
                    with zip_ref.open(file_info) as source, open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
        print("Архив успешно распакован в .editor с перезаписью")
    except Exception as e:
        print(f"Ошибка при распаковке архива: {e}")
        sys.exit(1)
    
    # Путь к editor.py (теперь он находится прямо в .editor)
    editor_script = os.path.join(editor_dir, 'editor.py')
    
    if not os.path.exists(editor_script):
        print(f"Ошибка: не найден файл {editor_script}")
        print("Проверьте структуру распакованных файлов")
        sys.exit(1)
    
    # Запускаем editor.py
    print(f"Запуск {editor_script}...")
    try:
        subprocess.run([sys.executable, editor_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске editor.py: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()