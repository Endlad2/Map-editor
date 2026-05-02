import subprocess
import sys
import os

def edit_block(temp_file_path, block_index):
    """
    Открывает редактор блока
    
    Args:
        temp_file_path (str): Путь к временному JSON файлу с данными мира
        block_index (int): Индекс редактируемого блока
    """
    try:
        # Получаем путь к текущей директории
        current_dir = os.path.dirname(os.path.abspath(__file__))
        api_script = os.path.join(current_dir, 'block_menu_api.py')
        
        # Проверяем существование файла API
        if not os.path.exists(api_script):
            print(f"Ошибка: Файл {api_script} не найден!")
            return
        
        # Проверяем существование временного файла
        if not os.path.exists(temp_file_path):
            print(f"Ошибка: Файл {temp_file_path} не найден")
            return
        
        # Запускаем PyQt5 диалог редактирования
        process = subprocess.Popen([
            sys.executable, 
            api_script, 
            temp_file_path, 
            str(block_index)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"Редактор блока #{block_index} запущен")
        
    except Exception as e:
        print(f"Ошибка при открытии редактора блока: {e}")

if __name__ == "__main__":
    # Если скрипт запущен напрямую
    if len(sys.argv) >= 3:
        edit_block(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python block_menu.py <temp_file_path> <block_index>")