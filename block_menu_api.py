import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QGroupBox, QMessageBox, QCheckBox, 
                             QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class BlockEditorWindow(QMainWindow):
    def __init__(self, temp_file_path, block_index):
        super().__init__()
        self.temp_file_path = temp_file_path
        self.block_index = int(block_index)
        self.world_data = []
        self.block_data = None
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.setWindowTitle(f"Редактирование блока #{self.block_index}")
        self.setGeometry(300, 300, 550, 750)
        
        if not self.load_world_data():
            return
        
        self.init_ui()
        self.load_current_values()
    
    def convert_to_relative_path(self, absolute_path):
        """Преобразует абсолютный путь в относительный"""
        if not absolute_path:
            return ""
        
        absolute_path = os.path.normpath(absolute_path)
        current_dir = os.path.normpath(self.current_dir)
        
        if not os.path.isabs(absolute_path):
            return absolute_path
        
        try:
            rel_path = os.path.relpath(absolute_path, current_dir)
            rel_path = rel_path.replace('\\', '/')
            return rel_path
        except:
            return absolute_path
    
    def load_world_data(self):
        """Загружает данные мира из временного файла"""
        try:
            if not os.path.exists(self.temp_file_path):
                QMessageBox.critical(self, "Ошибка", f"Файл {self.temp_file_path} не найден!")
                return False
                
            with open(self.temp_file_path, 'r', encoding='utf-8') as f:
                self.world_data = json.load(f)
            
            if 0 <= self.block_index < len(self.world_data):
                self.block_data = self.world_data[self.block_index]
                return True
            else:
                QMessageBox.critical(self, "Ошибка", f"Блок с индексом {self.block_index} не найден!")
                return False
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")
            return False
    
    def init_ui(self):
        """Создает интерфейс редактора"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        info_label = QLabel(f"Редактирование блока #{self.block_index}")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)
        
        # ===== НОВАЯ ГРУППА: АНИМАЦИЯ =====
        animation_group = QGroupBox("Анимация (Animation)")
        animation_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        animation_layout = QVBoxLayout()
        
        # Радио-кнопки для выбора типа анимации
        self.animation_enabled = QRadioButton("Включить анимацию")
        self.animation_disabled = QRadioButton("Выключить анимацию")
        self.animation_disabled.setChecked(True)
        
        # Группа для радио-кнопок
        self.animation_group = QButtonGroup()
        self.animation_group.addButton(self.animation_enabled, 1)
        self.animation_group.addButton(self.animation_disabled, 0)
        
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.animation_enabled)
        radio_layout.addWidget(self.animation_disabled)
        animation_layout.addLayout(radio_layout)
        
        # Поля для ввода параметров анимации
        anim_params_layout = QVBoxLayout()
        
        # Тип анимации
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип анимации:"))
        self.anim_type = QLineEdit()
        self.anim_type.setPlaceholderText("SpriteSheetAnimation / Animation / Actor / FrameAnimation3D")
        type_layout.addWidget(self.anim_type)
        anim_params_layout.addLayout(type_layout)
        
        # Название/путь к анимации
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название/путь:"))
        self.anim_name = QLineEdit()
        self.anim_name.setPlaceholderText("Название анимации или путь к файлу (например: run, assets/animation.gif)")
        name_layout.addWidget(self.anim_name)
        anim_params_layout.addLayout(name_layout)
        
        # Скорость анимации
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Скорость:"))
        self.anim_speed = QLineEdit("1.0")
        self.anim_speed.setPlaceholderText("Скорость проигрывания (по умолчанию: 1.0)")
        speed_layout.addWidget(self.anim_speed)
        
        # Флаг зацикливания
        self.anim_loop = QCheckBox("Зациклить анимацию")
        self.anim_loop.setChecked(True)
        speed_layout.addWidget(self.anim_loop)
        
        anim_params_layout.addLayout(speed_layout)
        
        # Для SpriteSheetAnimation дополнительные параметры
        sprite_sheet_layout = QVBoxLayout()
        sprite_sheet_label = QLabel("Для SpriteSheetAnimation:")
        sprite_sheet_label.setStyleSheet("font-style: italic; color: gray;")
        sprite_sheet_layout.addWidget(sprite_sheet_label)
        
        cols_rows_layout = QHBoxLayout()
        cols_rows_layout.addWidget(QLabel("Колонки:"))
        self.sprite_cols = QLineEdit("1")
        cols_rows_layout.addWidget(self.sprite_cols)
        cols_rows_layout.addWidget(QLabel("Ряды:"))
        self.sprite_rows = QLineEdit("1")
        cols_rows_layout.addWidget(self.sprite_rows)
        sprite_sheet_layout.addLayout(cols_rows_layout)
        
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.sprite_fps = QLineEdit("12")
        fps_layout.addWidget(self.sprite_fps)
        sprite_sheet_layout.addLayout(fps_layout)
        
        anim_params_layout.addLayout(sprite_sheet_layout)
        
        animation_layout.addLayout(anim_params_layout)
        animation_group.setLayout(animation_layout)
        main_layout.addWidget(animation_group)
        
        # Подключаем сигналы для включения/выключения полей
        self.animation_enabled.toggled.connect(self.on_animation_toggled)
        
        # Группа для текстуры
        texture_group = QGroupBox("Текстура")
        texture_layout = QVBoxLayout()
        
        self.texture_preview = QLabel()
        self.texture_preview.setAlignment(Qt.AlignCenter)
        self.texture_preview.setFixedSize(128, 128)
        self.texture_preview.setStyleSheet("border: 1px solid gray; background-color: #2b2b2b;")
        texture_layout.addWidget(self.texture_preview, alignment=Qt.AlignCenter)
        
        texture_path_layout = QHBoxLayout()
        texture_path_layout.addWidget(QLabel("Путь:"))
        self.texture_path_edit = QLineEdit()
        self.texture_path_edit.setPlaceholderText("assets/textures/your_texture.png")
        texture_path_layout.addWidget(self.texture_path_edit)
        texture_layout.addLayout(texture_path_layout)
        
        btn_select_texture = QPushButton("Выбрать текстуру")
        btn_select_texture.clicked.connect(self.select_texture)
        texture_layout.addWidget(btn_select_texture)
        
        btn_reset_path = QPushButton("Сделать путь относительным")
        btn_reset_path.clicked.connect(self.make_path_relative)
        texture_layout.addWidget(btn_reset_path)
        
        texture_group.setLayout(texture_layout)
        main_layout.addWidget(texture_group)
        
        # Группа для позиции
        pos_group = QGroupBox("Позиция (Position)")
        pos_layout = QVBoxLayout()
        
        pos_x_layout = QHBoxLayout()
        pos_x_layout.addWidget(QLabel("X:"))
        self.pos_x = QLineEdit()
        pos_x_layout.addWidget(self.pos_x)
        pos_layout.addLayout(pos_x_layout)
        
        pos_y_layout = QHBoxLayout()
        pos_y_layout.addWidget(QLabel("Y:"))
        self.pos_y = QLineEdit()
        pos_y_layout.addWidget(self.pos_y)
        pos_layout.addLayout(pos_y_layout)
        
        pos_z_layout = QHBoxLayout()
        pos_z_layout.addWidget(QLabel("Z:"))
        self.pos_z = QLineEdit()
        pos_z_layout.addWidget(self.pos_z)
        pos_layout.addLayout(pos_z_layout)
        
        pos_group.setLayout(pos_layout)
        main_layout.addWidget(pos_group)
        
        # Группа для вращения
        rot_group = QGroupBox("Вращение (Rotation) в градусах")
        rot_layout = QVBoxLayout()
        
        rot_x_layout = QHBoxLayout()
        rot_x_layout.addWidget(QLabel("X:"))
        self.rot_x = QLineEdit()
        rot_x_layout.addWidget(self.rot_x)
        rot_layout.addLayout(rot_x_layout)
        
        rot_y_layout = QHBoxLayout()
        rot_y_layout.addWidget(QLabel("Y:"))
        self.rot_y = QLineEdit()
        rot_y_layout.addWidget(self.rot_y)
        rot_layout.addLayout(rot_y_layout)
        
        rot_z_layout = QHBoxLayout()
        rot_z_layout.addWidget(QLabel("Z:"))
        self.rot_z = QLineEdit()
        rot_z_layout.addWidget(self.rot_z)
        rot_layout.addLayout(rot_z_layout)
        
        rot_group.setLayout(rot_layout)
        main_layout.addWidget(rot_group)
        
        # Группа для масштаба
        scale_group = QGroupBox("Масштаб (Scale)")
        scale_layout = QVBoxLayout()
        
        scale_x_layout = QHBoxLayout()
        scale_x_layout.addWidget(QLabel("X:"))
        self.scale_x = QLineEdit()
        scale_x_layout.addWidget(self.scale_x)
        scale_layout.addLayout(scale_x_layout)
        
        scale_y_layout = QHBoxLayout()
        scale_y_layout.addWidget(QLabel("Y:"))
        self.scale_y = QLineEdit()
        scale_y_layout.addWidget(self.scale_y)
        scale_layout.addLayout(scale_y_layout)
        
        scale_z_layout = QHBoxLayout()
        scale_z_layout.addWidget(QLabel("Z:"))
        self.scale_z = QLineEdit()
        scale_z_layout.addWidget(self.scale_z)
        scale_layout.addLayout(scale_z_layout)
        
        scale_group.setLayout(scale_layout)
        main_layout.addWidget(scale_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.save_changes)
        btn_ok.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 5px;")
        
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.close)
        btn_cancel.setStyleSheet("font-size: 14px; padding: 5px;")
        
        buttons_layout.addWidget(btn_ok)
        buttons_layout.addWidget(btn_cancel)
        main_layout.addLayout(buttons_layout)
        
        main_layout.addStretch()
    
    def on_animation_toggled(self, checked):
        """Включает/выключает поля для анимации"""
        enabled = self.animation_enabled.isChecked()
        self.anim_type.setEnabled(enabled)
        self.anim_name.setEnabled(enabled)
        self.anim_speed.setEnabled(enabled)
        self.anim_loop.setEnabled(enabled)
        self.sprite_cols.setEnabled(enabled)
        self.sprite_rows.setEnabled(enabled)
        self.sprite_fps.setEnabled(enabled)
    
    def make_path_relative(self):
        """Преобразует текущий путь в относительный"""
        current_path = self.texture_path_edit.text()
        if current_path:
            rel_path = self.convert_to_relative_path(current_path)
            self.texture_path_edit.setText(rel_path)
            self.load_texture_preview(rel_path)
            print(f"Путь преобразован: {current_path} -> {rel_path}")
    
    def load_current_values(self):
        """Загружает текущие значения блока в поля ввода"""
        if not self.block_data:
            return
        
        # Загружаем настройки анимации
        anim_data = self.block_data.get('animation', None)
        if anim_data and anim_data.get('enabled', False):
            self.animation_enabled.setChecked(True)
            self.anim_type.setText(anim_data.get('type', ''))
            self.anim_name.setText(anim_data.get('name', ''))
            self.anim_speed.setText(str(anim_data.get('speed', 1.0)))
            self.anim_loop.setChecked(anim_data.get('loop', True))
            self.sprite_cols.setText(str(anim_data.get('cols', 1)))
            self.sprite_rows.setText(str(anim_data.get('rows', 1)))
            self.sprite_fps.setText(str(anim_data.get('fps', 12)))
        else:
            self.animation_disabled.setChecked(True)
        
        # Загружаем текстуру
        texture = self.block_data.get('texture', '')
        if texture:
            rel_texture = self.convert_to_relative_path(texture)
            if rel_texture != texture:
                self.block_data['texture'] = rel_texture
            self.texture_path_edit.setText(rel_texture)
            self.load_texture_preview(rel_texture)
        
        # Загружаем позицию
        pos = self.block_data.get('position', [0, 0, 0])
        self.pos_x.setText(str(pos[0]))
        self.pos_y.setText(str(pos[1]))
        self.pos_z.setText(str(pos[2]))
        
        # Загружаем вращение
        rot = self.block_data.get('rotation', [0, 0, 0])
        self.rot_x.setText(str(rot[0]))
        self.rot_y.setText(str(rot[1]))
        self.rot_z.setText(str(rot[2]))
        
        # Загружаем масштаб
        scale = self.block_data.get('scale', [1, 1, 1])
        self.scale_x.setText(str(scale[0]))
        self.scale_y.setText(str(scale[1]))
        self.scale_z.setText(str(scale[2]))
    
    def load_texture_preview(self, texture_path):
        """Загружает превью текстуры"""
        possible_paths = [
            texture_path,
            os.path.join(self.current_dir, texture_path),
            os.path.join(self.current_dir, 'assets', 'textures', os.path.basename(texture_path)),
        ]
        
        found_path = None
        for path in possible_paths:
            if path and os.path.exists(path):
                found_path = path
                break
        
        if found_path:
            pixmap = QPixmap(found_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.texture_preview.setPixmap(scaled_pixmap)
            else:
                self.texture_preview.setText("❌ Не удалось загрузить")
        else:
            self.texture_preview.setText("📁 Файл не найден")
    
    def select_texture(self):
        """Открывает диалог выбора текстуры"""
        start_dir = os.path.join(self.current_dir, 'assets', 'textures')
        if not os.path.exists(start_dir):
            start_dir = self.current_dir
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите текстуру",
            start_dir,
            "Image files (*.png *.jpg *.jpeg *.bmp);;All files (*.*)"
        )
        
        if file_path:
            rel_path = self.convert_to_relative_path(file_path)
            self.texture_path_edit.setText(rel_path)
            self.load_texture_preview(rel_path)
    
    def save_changes(self):
        """Сохраняет изменения во временный файл и создает маркер"""
        try:
            # Сохраняем настройки анимации
            if self.animation_enabled.isChecked():
                # Проверяем обязательные поля
                anim_type = self.anim_type.text().strip()
                anim_name = self.anim_name.text().strip()
                
                if not anim_type:
                    QMessageBox.warning(self, "Ошибка", "Укажите тип анимации!")
                    return
                if not anim_name:
                    QMessageBox.warning(self, "Ошибка", "Укажите название/путь к анимации!")
                    return
                
                self.block_data['animation'] = {
                    "enabled": True,
                    "type": anim_type,
                    "name": anim_name,
                    "speed": float(self.anim_speed.text() or "1.0"),
                    "loop": self.anim_loop.isChecked(),
                    "cols": int(self.sprite_cols.text() or "1"),
                    "rows": int(self.sprite_rows.text() or "1"),
                    "fps": int(self.sprite_fps.text() or "12")
                }
            else:
                self.block_data['animation'] = {"enabled": False}
            
            # Сохраняем текстуру
            texture_path = self.texture_path_edit.text()
            texture_path = self.convert_to_relative_path(texture_path)
            self.block_data['texture'] = texture_path if texture_path else None
            
            # Позиция
            self.block_data['position'] = [
                float(self.pos_x.text()),
                float(self.pos_y.text()),
                float(self.pos_z.text())
            ]
            
            # Вращение
            self.block_data['rotation'] = [
                float(self.rot_x.text()),
                float(self.rot_y.text()),
                float(self.rot_z.text())
            ]
            
            # Масштаб
            self.block_data['scale'] = [
                float(self.scale_x.text()),
                float(self.scale_y.text()),
                float(self.scale_z.text())
            ]
            
            # Сохраняем в файл
            with open(self.temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.world_data, f, indent=2, ensure_ascii=False)
            
            # Создаем маркерный файл
            marker_file = self.temp_file_path + '.changed'
            with open(marker_file, 'w') as f:
                f.write(str(self.block_index))
            
            QMessageBox.information(self, "Успех", "Изменения сохранены!\nМир будет автоматически обновлен. Анимация будет проигрываться на блоке!")
            self.close()
            
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", f"Некорректное числовое значение: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {str(e)}")

def main():
    if len(sys.argv) < 3:
        print("Usage: block_menu_api.py <temp_file_path> <block_index>")
        sys.exit(1)
    
    temp_file_path = sys.argv[1]
    block_index = sys.argv[2]
    
    app = QApplication(sys.argv)
    editor = BlockEditorWindow(temp_file_path, block_index)
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()