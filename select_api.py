import sys
import os
from PyQt5.QtWidgets import QApplication, QFileDialog

class FileSelectAPI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
    def select_zip_file(self):
        """Диалог выбора ZIP файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Выберите ZIP файл уровня",
            os.path.expanduser("~"),
            "ZIP files (*.zip);;All files (*.*)"
        )
        return file_path if file_path else ""

def main():
    api = FileSelectAPI()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "select_zip":
            result = api.select_zip_file()
            print(result)
    
    sys.exit(0)

if __name__ == "__main__":
    main()