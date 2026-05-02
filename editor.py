from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import basic_lighting_shader
import os, json, tempfile, shutil, subprocess, sys, copy, math, zipfile

app = Ursina(title='Backrooms : Infinity', vsync=True)

Entity.default_shader = basic_lighting_shader
scene.fog_density = (0, 0.02)
scene.fog_color = color.rgb(135, 206, 235)

player = FirstPersonController(shader=basic_lighting_shader)

sky_texture = load_texture('assets/sky_texture.png') if os.path.exists('assets/sky_texture.png') else None
sky = Sky(shader=basic_lighting_shader, texture=sky_texture)

sun_light = DirectionalLight(shadow_map_resolution=(1024, 1024))
sun_light.look_at(Vec3(1, -1, -1))
sun_light.color = color.rgb(255, 255, 200)

sun_visual = Entity(
    model='sphere',
    color=color.rgba(255, 200, 100, 100),
    scale=3,
    shader=basic_lighting_shader,
    position=(50, 100, -50),
    double_sided=True
)

scene.ambient_light = color.rgba(50, 50, 70, 0)

noclip = False
pause_menu = None
is_paused = False

temp_file = os.path.join(tempfile.gettempdir(), 'map.json')
world_data = []
unsaved_changes = False

undo_stack = []
redo_stack = []

def snapshot():
    undo_stack.append(copy.deepcopy(world_data))
    redo_stack.clear()

def create_default_world():
    global world_data
    world_data = []
    for x in range(10):
        for z in range(10):
            world_data.append({
                "model": "cube",
                "texture": "assets/textures/grass.png",
                "position": [x, 0, z],
                "rotation": [0, 0, 0],
                "scale": [1, 1, 1],
                "animation": {"enabled": False}
            })

def save_temp():
    global unsaved_changes
    with open(temp_file, 'w') as f:
        json.dump(world_data, f, indent=2)
    unsaved_changes = False

def load_temp():
    global world_data
    if os.path.exists(temp_file):
        with open(temp_file, 'r') as f:
            world_data = json.load(f)
            for obj in world_data:
                if 'animation' not in obj:
                    obj['animation'] = {"enabled": False}
    else:
        create_default_world()
        save_temp()

base_model_list = ['cube', 'sphere', 'quad', 'plane']
custom_models = []

model_path = 'assets/models'
texture_path = 'assets/textures'

if os.path.exists(model_path):
    for f in os.listdir(model_path):
        if f.endswith(('.obj', '.glb', '.gltf', '.bam','.blend')):
            custom_models.append(f)

model_list = base_model_list + custom_models
texture_list = []

if os.path.exists(texture_path):
    for f in os.listdir(texture_path):
        if f.endswith(('.png', '.jpg', '.jpeg')):
            texture_list.append(f)

model_index = 0
texture_index = 0
saved_blocks_index = 0

default_rotation = [0, 0, 0]
default_scale = [1, 1, 1]

current_spawn_rotation = default_rotation.copy()
current_spawn_scale = default_scale.copy()

saved_templates = []

def get_model(): 
    return model_list[model_index]

def get_texture():
    return f'{texture_path}/{texture_list[texture_index]}' if texture_list else None

def save_current_block_as_template():
    global hovered, saved_blocks_index, saved_templates
    if hovered:
        texture_path_val = None
        if hovered.texture:
            if hasattr(hovered.texture, 'name'):
                texture_path_val = hovered.texture.name
            else:
                texture_path_val = str(hovered.texture)
        
        template = {
            "model": hovered.model,
            "texture": texture_path_val,
            "scale": list(hovered.scale),
            "rotation": list(hovered.rotation)
        }
        
        saved_templates.append(template)
        saved_blocks_index = len(saved_templates) - 1
        print(f"✅ Шаблон сохранен!")

def use_saved_template():
    global model_index, texture_index, current_spawn_scale, current_spawn_rotation, saved_blocks_index, saved_templates
    if saved_templates and 0 <= saved_blocks_index < len(saved_templates):
        template = saved_templates[saved_blocks_index]
        if template['model'] in model_list:
            model_index = model_list.index(template['model'])
        if template.get('texture') and isinstance(template['texture'], str):
            texture_name = os.path.basename(template['texture'])
            if texture_name in texture_list:
                texture_index = texture_list.index(texture_name)
            else:
                for i, tex in enumerate(texture_list):
                    if tex == template['texture'] or tex == texture_name:
                        texture_index = i
                        break
        current_spawn_scale = template['scale'].copy()
        current_spawn_rotation = template['rotation'].copy()

def reset_to_default_spawn():
    global current_spawn_scale, current_spawn_rotation
    current_spawn_scale = default_scale.copy()
    current_spawn_rotation = default_rotation.copy()

blocks = []

def rebuild_world():
    global blocks
    for b in blocks:
        if hasattr(b, 'animation_obj') and b.animation_obj:
            if hasattr(b.animation_obj, 'stop'):
                b.animation_obj.stop()
            destroy(b.animation_obj)
        destroy(b)
    blocks.clear()

    for i, obj in enumerate(world_data):
        anim_data = obj.get('animation', {"enabled": False})
        has_animation = anim_data.get('enabled', False)
        
        if has_animation:
            try:
                b = Entity(
                    model='cube',
                    position=tuple(obj['position']),
                    rotation=tuple(obj.get('rotation', [0,0,0])),
                    scale=tuple(obj.get('scale', [1,1,1])),
                    collider='box',
                    shader=basic_lighting_shader
                )
                
                anim_type = anim_data.get('type', '')
                anim_name = anim_data.get('name', '')
                anim_loop = anim_data.get('loop', True)
                cols = anim_data.get('cols', 1)
                rows = anim_data.get('rows', 1)
                fps = anim_data.get('fps', 12)
                
                if 'sprite' in anim_type.lower():
                    try:
                        b.animation_obj = SpriteSheetAnimation(
                            parent=b,
                            texture=anim_name,
                            tiles=Vec2(cols, rows),
                            fps=fps,
                            loop=anim_loop,
                            autoplay=True
                        )
                        b.animation_obj.scale = (2, 2)
                    except Exception as e:
                        print(f"⚠️ Ошибка: {e}")
                        
                elif 'animation' in anim_type.lower():
                    try:
                        b.animation_obj = Animation(
                            parent=b,
                            animation=anim_name,
                            fps=fps,
                            loop=anim_loop,
                            autoplay=True
                        )
                        b.animation_obj.scale = (2, 2)
                    except Exception as e:
                        print(f"⚠️ Ошибка: {e}")
                        
                elif 'actor' in anim_type.lower():
                    try:
                        from direct.actor.Actor import Actor
                        model_file = anim_data.get('model_file', anim_name)
                        b.actor = Actor(model_file)
                        b.actor.reparentTo(b)
                        b.actor.setScale(1)
                        if anim_name:
                            b.actor.loop(anim_name)
                        b.animation_obj = b.actor
                    except Exception as e:
                        print(f"⚠️ Ошибка: {e}")
                        
                elif 'frame' in anim_type.lower():
                    try:
                        from ursina import FrameAnimation3d
                        b.animation_obj = FrameAnimation3d(
                            parent=b,
                            path=anim_name,
                            fps=fps,
                            loop=anim_loop,
                            autoplay=True
                        )
                    except Exception as e:
                        print(f"⚠️ Ошибка: {e}")
                        
                b.has_animation = True
                b.index = i
                blocks.append(b)
                
            except Exception as e:
                b = Entity(
                    model=obj['model'],
                    texture=obj.get('texture'),
                    position=tuple(obj['position']),
                    rotation=tuple(obj.get('rotation', [0,0,0])),
                    scale=tuple(obj.get('scale', [1,1,1])),
                    collider='box',
                    shader=basic_lighting_shader
                )
                b.index = i
                blocks.append(b)
        else:
            b = Entity(
                model=obj['model'],
                texture=obj.get('texture'),
                position=tuple(obj['position']),
                rotation=tuple(obj.get('rotation', [0,0,0])),
                scale=tuple(obj.get('scale', [1,1,1])),
                collider='box',
                shader=basic_lighting_shader
            )
            b.index = i
            blocks.append(b)

def add_block(pos):
    snapshot()
    block_data = {
        "model": get_model(),
        "texture": get_texture(),
        "position": list(pos),
        "rotation": current_spawn_rotation.copy(),
        "scale": current_spawn_scale.copy(),
        "animation": {"enabled": False}
    }
    world_data.append(block_data)
    save_temp()
    rebuild_world()

def remove_block(i):
    snapshot()
    world_data.pop(i)
    for new_i, b in enumerate(blocks):
        if b.index > i:
            b.index = new_i
    save_temp()
    rebuild_world()

highlight = Entity(
    model='cube',
    color=color.rgba(255,255,255,80),
    scale=1.02,
    enabled=False,
    wireframe=True,
    unlit=True
)

hovered = None

def update_hover():
    global hovered
    hit = raycast(camera.world_position, camera.forward, distance=6)
    if hit.hit and hit.entity in blocks:
        hovered = hit.entity
        highlight.enabled = True
        highlight.position = hovered.position
        highlight.rotation = hovered.rotation
        highlight.scale = tuple(s * 1.02 for s in hovered.scale)
    else:
        hovered = None
        highlight.enabled = False

def modify_selected_block(axis, direction, modify_type):
    global hovered, world_data, blocks
    if not hovered:
        return
    snapshot()
    block_index = hovered.index
    block_data = world_data[block_index]
    axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
    
    if modify_type == 'position':
        change = 0.05 if direction == 'up' else -0.05
        block_data['position'][axis_index] += change
        hovered.position = tuple(block_data['position'])
    elif modify_type == 'scale':
        change = 0.05 if direction == 'right' else -0.05
        new_scale = block_data['scale'][axis_index] + change
        if new_scale >= 0.1:
            block_data['scale'][axis_index] = new_scale
            hovered.scale = tuple(block_data['scale'])
            highlight.scale = tuple(s * 1.02 for s in hovered.scale)
    save_temp()

def open_file_dialog(mode):
    try:
        result = subprocess.run(
            [sys.executable, 'esc_api.py', mode],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Ошибка: {e}")
        return ""

def save_world_to_file():
    path = open_file_dialog("save")
    if path:
        shutil.copy(temp_file, path)
        return True
    return False

def load_world_from_file():
    path = open_file_dialog("load")
    if path and os.path.exists(path):
        shutil.copy(path, temp_file)
        load_temp()
        rebuild_world()
        return True
    return False

def confirm_exit():
    result = open_file_dialog("confirm_exit")
    if result == "save_and_exit":
        save_world_to_file()
        return True
    elif result == "exit":
        return True
    return False

def check_for_block_changes():
    marker_file = temp_file + '.changed'
    if os.path.exists(marker_file):
        try:
            with open(marker_file, 'r') as f:
                block_index = f.read().strip()
            os.remove(marker_file)
            load_temp()
            rebuild_world()
        except Exception as e:
            print(f"Ошибка: {e}")

def open_block_menu(block_index):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        api_script = os.path.join(current_dir, 'block_menu_api.py')
        if not os.path.exists(api_script):
            print(f"ОШИБКА: Файл {api_script} не найден!")
            return
        subprocess.Popen([sys.executable, api_script, temp_file, str(block_index)])
    except Exception as e:
        print(f"Ошибка: {e}")

def export_level():
    try:
        from PyQt5.QtWidgets import (QApplication, QFileDialog, QDialog, QVBoxLayout, 
                                     QRadioButton, QLineEdit, QComboBox, QPushButton, 
                                     QLabel, QButtonGroup, QHBoxLayout, QWidget, QCheckBox)
        
        temp_app = QApplication.instance()
        if not temp_app:
            temp_app = QApplication([])
        
        folder_path = QFileDialog.getExistingDirectory(None, "Выберите папку с JSON файлами карт")
        if not folder_path:
            return
        
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        if not json_files:
            print("Нет JSON файлов в выбранной папке")
            return
        
        used_textures = set()
        used_models = set()
        
        for json_file in json_files:
            file_path = os.path.join(folder_path, json_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for block in data:
                            if 'texture' in block and block['texture']:
                                texture_path = block['texture']
                                if texture_path and texture_path.startswith('assets/textures/'):
                                    used_textures.add(texture_path)
                            if 'model' in block and block['model']:
                                model_name = block['model']
                                if model_name and model_name not in base_model_list:
                                    for ext in ['.obj', '.glb', '.gltf', '.bam', '.blend']:
                                        model_path_full = f'assets/models/{model_name}{ext}'
                                        if os.path.exists(model_path_full):
                                            used_models.add(model_path_full)
                                            break
            except Exception as e:
                print(f"Ошибка чтения {json_file}: {e}")
        
        temp_dir = tempfile.mkdtemp()
        
        zip_path = os.path.join(temp_dir, 'level_assets.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for texture in used_textures:
                if os.path.exists(texture):
                    arcname = texture
                    zipf.write(texture, arcname)
            for model in used_models:
                if os.path.exists(model):
                    arcname = model
                    zipf.write(model, arcname)
        
        chunks_dir = os.path.join(temp_dir, 'chunks')
        os.makedirs(chunks_dir, exist_ok=True)
        for json_file in json_files:
            shutil.copy(os.path.join(folder_path, json_file), os.path.join(chunks_dir, json_file))
        
        dialog = QDialog()
        dialog.setWindowTitle("Параметры уровня")
        dialog.setModal(True)
        layout = QVBoxLayout()
        
        infinity_group = QButtonGroup(dialog)
        infinity_radio = QRadioButton("Infinity")
        not_infinity_radio = QRadioButton("Not Infinity")
        not_infinity_radio.setChecked(True)
        layout.addWidget(infinity_radio)
        layout.addWidget(not_infinity_radio)
        infinity_group.addButton(infinity_radio)
        infinity_group.addButton(not_infinity_radio)
        
        auto_gluing_checkbox = QCheckBox("Auto-gluing (автоматическая стыковка чанков)")
        auto_gluing_checkbox.setChecked(False)
        layout.addWidget(auto_gluing_checkbox)
        
        entities_label = QLabel("Entities (через пробел):")
        entities_input = QLineEdit()
        layout.addWidget(entities_label)
        layout.addWidget(entities_input)
        
        level_name_label = QLabel("Level Name:")
        level_name_input = QLineEdit()
        layout.addWidget(level_name_label)
        layout.addWidget(level_name_input)
        
        exit_chunk_label = QLabel("Select exit chunk:")
        exit_chunk_combo = QComboBox()
        exit_chunk_combo.addItems(json_files)
        layout.addWidget(exit_chunk_label)
        layout.addWidget(exit_chunk_combo)
        
        main_chunk_label = QLabel("Select Main Chunk:")
        main_chunk_combo = QComboBox()
        main_chunk_combo.addItems(json_files)
        layout.addWidget(main_chunk_label)
        layout.addWidget(main_chunk_combo)
        
        items_label = QLabel("Items (через пробел):")
        items_input = QLineEdit()
        layout.addWidget(items_label)
        layout.addWidget(items_input)
        
        non_random_axis_combo = QComboBox()
        non_random_chunk_combo = QComboBox()
        non_random_axis_combo.setVisible(False)
        non_random_chunk_combo.setVisible(False)
        
        chunk_chances_widget = None
        chance_inputs = {}
        
        def on_infinity_toggled():
            is_inf = infinity_radio.isChecked()
            non_random_axis_combo.setVisible(is_inf)
            non_random_chunk_combo.setVisible(is_inf)
            
            nonlocal chunk_chances_widget
            if chunk_chances_widget:
                chunk_chances_widget.setVisible(is_inf)
        
        infinity_radio.toggled.connect(on_infinity_toggled)
        
        non_random_axis_label = QLabel("Non-random chunks axis (X/Z/Y/None):")
        non_random_axis_combo.addItems(['None', 'X', 'Z', 'Y'])
        layout.addWidget(non_random_axis_label)
        layout.addWidget(non_random_axis_combo)
        
        non_random_chunk_label = QLabel("Non-random chunk:")
        non_random_chunk_combo.addItems(json_files)
        layout.addWidget(non_random_chunk_label)
        layout.addWidget(non_random_chunk_combo)
        
        chunk_chances_widget = QWidget()
        chances_layout = QVBoxLayout()
        chances_label = QLabel("Spawn Chance (0-100%):")
        chances_layout.addWidget(chances_label)
        
        for json_file in json_files:
            chance_layout = QHBoxLayout()
            chance_label = QLabel(f"{json_file}:")
            chance_input = QLineEdit("100")
            chance_layout.addWidget(chance_label)
            chance_layout.addWidget(chance_input)
            chances_layout.addLayout(chance_layout)
            chance_inputs[json_file] = chance_input
        
        chunk_chances_widget.setLayout(chances_layout)
        layout.addWidget(chunk_chances_widget)
        chunk_chances_widget.setVisible(False)
        
        non_random_axis_combo.setVisible(False)
        non_random_chunk_combo.setVisible(False)
        
        save_button = QPushButton("Создать уровень")
        layout.addWidget(save_button)
        
        dialog.setLayout(layout)
        
        result_data = {}
        
        def on_save():
            nonlocal result_data
            result_data = {
                'infinity': infinity_radio.isChecked(),
                'auto_gluing': auto_gluing_checkbox.isChecked(),
                'entities': entities_input.text().split() if entities_input.text() else [],
                'level_name': level_name_input.text(),
                'exit_chunk': exit_chunk_combo.currentText(),
                'main_chunk': main_chunk_combo.currentText(),
                'items': items_input.text().split() if items_input.text() else []
            }
            
            if infinity_radio.isChecked():
                result_data['non_random_axis'] = non_random_axis_combo.currentText()
                result_data['non_random_chunk'] = non_random_chunk_combo.currentText()
                
                chunk_chances_dict = {}
                for chunk_name, input_field in chance_inputs.items():
                    try:
                        chance = int(input_field.text())
                        chance = max(0, min(100, chance))
                        if chance > 0:
                            chunk_chances_dict[chunk_name] = chance
                    except:
                        chunk_chances_dict[chunk_name] = 0
                
                if chunk_chances_dict:
                    result_data['chunk_chances'] = chunk_chances_dict
            
            dialog.accept()
        
        save_button.clicked.connect(on_save)
        dialog.exec_()
        
        if result_data:
            settings_path = os.path.join(temp_dir, 'settings.json')
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            final_zip_name = f"{result_data.get('level_name', 'level')}.zip"
            final_zip_path = os.path.join(temp_dir, final_zip_name)
            
            with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file != final_zip_name:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
            
            save_path, _ = QFileDialog.getSaveFileName(None, "Сохранить уровень", "", "ZIP files (*.zip)")
            if save_path:
                shutil.copy(final_zip_path, save_path)
                print(f"Уровень сохранен: {save_path}")
            
            shutil.rmtree(temp_dir)
    
    except Exception as e:
        print(f"Ошибка экспорта: {e}")

class PauseMenu:
    def __init__(self):
        self.entity = None
        self.buttons = []
        self.notification = None
        
    def create(self):
        self.entity = Entity(parent=camera.ui)
        self.panel = Panel(
            parent=self.entity,
            scale=(0.5, 0.7),
            color=color.rgba(0,0,0,200),
            position=(0, 0)
        )
        Text(
            parent=self.entity,
            text="ПАУЗА",
            y=0.35,
            scale=2,
            color=color.white,
            origin=(0,0)
        )
        
        buttons_data = [
            ("Сохранить мир", 0.2, self.save_world),
            ("Загрузить мир", 0.05, self.load_world),
            ("Экспорт", -0.1, self.export_level),
            ("Сохранить и выйти", -0.25, self.save_and_exit),
            ("Выйти", -0.4, self.exit_game),
            ("Продолжить", -0.55, self.resume_game)
        ]
        
        for text, y_pos, callback in buttons_data:
            btn = Button(
                parent=self.entity,
                text=text,
                scale=(0.4, 0.07),
                position=(0, y_pos),
                color=color.rgb(50,50,50),
                highlight_color=color.rgb(80,80,80),
                text_color=color.white,
                highlight_text_color=color.yellow,
                on_click=callback
            )
            self.buttons.append(btn)
    
    def save_world(self):
        if save_world_to_file():
            self.show_notification("Мир сохранен!", color.green)
    
    def load_world(self):
        if load_world_from_file():
            self.show_notification("Мир загружен!", color.green)
    
    def export_level(self):
        self.show_notification("Экспорт уровня...", color.yellow)
        invoke(export_level, delay=0.1)
    
    def save_and_exit(self):
        if save_world_to_file():
            self.show_notification("Мир сохранен, выход...", color.yellow)
            invoke(application.quit, delay=0.5)
    
    def exit_game(self):
        self.show_notification("Выход из игры...", color.red)
        invoke(application.quit, delay=0.5)
    
    def resume_game(self):
        toggle_pause()
    
    def show_notification(self, message, text_color):
        if self.notification:
            destroy(self.notification)
        self.notification = Text(
            text=message,
            position=(0, -0.65),
            origin=(0,0),
            color=text_color,
            parent=self.entity,
            scale=1.5,
            background=True
        )
        invoke(self.hide_notification, delay=1.5)
    
    def hide_notification(self):
        if self.notification:
            destroy(self.notification)
            self.notification = None
    
    def destroy(self):
        for btn in self.buttons:
            if btn:
                destroy(btn)
        self.buttons.clear()
        if self.notification:
            destroy(self.notification)
            self.notification = None
        if self.panel:
            destroy(self.panel)
        if self.entity:
            destroy(self.entity)
        self.entity = None

pause_menu_system = None

def toggle_pause():
    global is_paused, pause_menu_system
    is_paused = not is_paused
    mouse.locked = not is_paused
    mouse.visible = is_paused
    player.enabled = not is_paused
    
    if is_paused:
        pause_menu_system = PauseMenu()
        pause_menu_system.create()
    else:
        if pause_menu_system:
            pause_menu_system.destroy()
            pause_menu_system = None

last_check_time = 0
last_modify_frame = 0
time_of_day = 0

def update():
    global last_check_time, last_modify_frame, time_of_day
    
    if not is_paused:
        update_hover()
        
        time_of_day += time.dt * 0.05
        sun_x = 50 * math.cos(time_of_day)
        sun_z = 50 * math.sin(time_of_day)
        sun_visual.position = (sun_x, 30, sun_z)
        sun_light.look_at(Vec3(-sun_x, -30, -sun_z))
        
        if time_of_day % (2*math.pi) < math.pi:
            intensity = math.sin(time_of_day)
            sun_light.color = color.rgb(255, 200 + int(55 * intensity), 150 + int(105 * intensity))
        else:
            sun_light.color = color.rgb(20, 40, 80)
            scene.ambient_light = color.rgb(30, 30, 50)

        if time.time() - last_check_time > 0.5:
            check_for_block_changes()
            last_check_time = time.time()
        
        if hovered and time.time() - last_modify_frame > 0.1:
            axis_keys = {'x': held_keys['x'], 'y': held_keys['y'], 'z': held_keys['z']}
            for axis, is_pressed in axis_keys.items():
                if is_pressed:
                    if held_keys['up arrow']:
                        modify_selected_block(axis, 'up', 'position')
                        last_modify_frame = time.time()
                        break
                    elif held_keys['down arrow']:
                        modify_selected_block(axis, 'down', 'position')
                        last_modify_frame = time.time()
                        break
                    elif held_keys['right arrow']:
                        modify_selected_block(axis, 'right', 'scale')
                        last_modify_frame = time.time()
                        break
                    elif held_keys['left arrow']:
                        modify_selected_block(axis, 'left', 'scale')
                        last_modify_frame = time.time()
                        break
        
        if noclip:
            speed = 10 * time.dt
            if held_keys['w']: player.position += player.forward * speed
            if held_keys['s']: player.position -= player.forward * speed
            if held_keys['a']: player.position -= player.right * speed
            if held_keys['d']: player.position += player.right * speed
            if held_keys['space']: player.y += speed * 3
            if held_keys['left control']: player.y -= speed * 3

def input(key):
    global model_index, texture_index, noclip, saved_blocks_index
    
    if key == 'escape':
        toggle_pause()
        return
    
    if is_paused:
        return
    
    if held_keys['control'] and key == 'i':
        save_current_block_as_template()
        return
    
    if held_keys['control'] and key == 'r':
        load_temp()
        rebuild_world()
        return
    
    if key == 'n':
        noclip = not noclip
        player.gravity = 0 if noclip else 1
        player.collider = None if noclip else 'box'
    
    if held_keys['control'] and key == 'z' and undo_stack:
        redo_stack.append(copy.deepcopy(world_data))
        world_data.clear()
        world_data.extend(undo_stack.pop())
        rebuild_world()
        save_temp()
        return

    if held_keys['control'] and key == 'y' and redo_stack:
        undo_stack.append(copy.deepcopy(world_data))
        world_data.clear()
        world_data.extend(redo_stack.pop())
        rebuild_world()
        save_temp()
        return
    
    if held_keys['1']:
        if key == 'scroll up': 
            model_index = (model_index + 1) % len(model_list)
            reset_to_default_spawn()
        if key == 'scroll down': 
            model_index = (model_index - 1) % len(model_list)
            reset_to_default_spawn()
        return
    
    if held_keys['2'] and texture_list:
        if key == 'scroll up': 
            texture_index = (texture_index + 1) % len(texture_list)
        if key == 'scroll down': 
            texture_index = (texture_index - 1) % len(texture_list)
        return
    
    if held_keys['3'] and saved_templates:
        if key == 'scroll up': 
            saved_blocks_index = (saved_blocks_index + 1) % len(saved_templates)
            use_saved_template()
        if key == 'scroll down': 
            saved_blocks_index = (saved_blocks_index - 1) % len(saved_templates)
            use_saved_template()
        return
    
    if key == 'middle mouse down' and hovered:
        open_block_menu(hovered.index)
        return
    
    if hovered:
        if key == 'right mouse down':
            add_block(hovered.position + mouse.normal)
        if key == 'left mouse down':
            remove_block(hovered.index)

load_temp()
if not world_data:
    create_default_world()
    save_temp()

rebuild_world()

app.run()