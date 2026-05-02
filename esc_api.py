import sys
import json
import shutil
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

class FileDialogAPI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
    def save_file_dialog(self):
        """Диалог сохранения файла"""
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "Сохранить карту",
            "",
            "JSON files (*.json);;All files (*.*)"
        )
        return file_path if file_path else ""
    
    def load_file_dialog(self):
        """Диалог загрузки файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Загрузить карту",
            "",
            "JSON files (*.json);;All files (*.*)"
        )
        return file_path if file_path else ""
    
    def confirm_exit(self):
        """Диалог подтверждения выхода"""
        reply = QMessageBox.question(
            None,
            "Выход",
            "Сохранить изменения перед выходом?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            return "save_and_exit"
        elif reply == QMessageBox.No:
            return "exit"
        else:
            return "cancel"

def main():
    api = FileDialogAPI()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "save":
            result = api.save_file_dialog()
            print(result)
        elif mode == "load":
            result = api.load_file_dialog()
            print(result)
        elif mode == "confirm_exit":
            result = api.confirm_exit()
            print(result)
    
    sys.exit(0)

if __name__ == "__main__":
    main()