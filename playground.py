from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import basic_lighting_shader
import os
import json
import tempfile
import zipfile
import shutil
import sys
import subprocess
import math
import random

app = Ursina(title='Backrooms: Infinity - Playground', vsync=True)

Entity.default_shader = basic_lighting_shader
scene.fog_density = (0, 0.02)
scene.fog_color = color.rgb(135, 206, 235)

player = FirstPersonController(shader=basic_lighting_shader, speed=8, jump_height=2, jump_duration=0.3)

sky_texture = load_texture('assets/sky_texture.png') if os.path.exists('assets/sky_texture.png') else None
sky = Sky(shader=basic_lighting_shader, texture=sky_texture)

sun_light = DirectionalLight(shadow_map_resolution=(512, 512))
sun_light.look_at(Vec3(1, -1, -1))
sun_light.color = color.rgb(255, 255, 200)

sun_visual = Entity(
    model='sphere',
    color=color.rgba(255, 200, 100, 50),
    scale=2,
    shader=basic_lighting_shader,
    position=(50, 100, -50),
    double_sided=True
)
scene.ambient_light = color.rgba(50, 50, 70, 0)

loaded_zip_path = None
temp_dir = None
settings = {}
chunks_data = {}
chunks_info = {}
chunk_width = None
chunk_depth = None
non_random_axis = None
non_random_chunk = None
chunk_chances = {}
is_infinity = False
auto_gluing = False
level_loaded = False
noclip_active = False
render_distance = 3

loaded_chunks = {}

def select_zip_file():
    try:
        result = subprocess.run(
            [sys.executable, 'select_api.py', 'select_zip'],
            capture_output=True,
            text=True,
            timeout=30
        )
        file_path = result.stdout.strip()
        if file_path and os.path.exists(file_path):
            return file_path
        else:
            print("Файл не выбран или не существует")
            return None
    except Exception as e:
        print(f"Ошибка вызова диалога: {e}")
        return None

def get_chunk_bounds(world_data):
    if not world_data:
        return 0, 0, 0, 0
    positions = [block['position'] for block in world_data]
    xs = [p[0] for p in positions]
    zs = [p[2] for p in positions]
    return min(xs), max(xs), min(zs), max(zs)

def get_chunk_width_depth(world_data):
    min_x, max_x, min_z, max_z = get_chunk_bounds(world_data)
    return max_x - min_x + 1, max_z - min_z + 1

def find_highest_block_y(world_data, offset_x=0, offset_z=0):
    highest_y = -9999
    for block in world_data:
        block_y = block['position'][1]
        scale_y = block.get('scale', [1,1,1])[1]
        block_top = block_y + scale_y
        
        if block_top > highest_y:
            highest_y = block_top
    
    return highest_y if highest_y != -9999 else 0

def load_zip_and_settings(zip_path):
    global temp_dir, settings, chunks_data, chunks_info, chunk_width, chunk_depth, non_random_axis, non_random_chunk, is_infinity, chunk_chances, auto_gluing
    
    temp_dir = tempfile.mkdtemp()
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    settings_path = os.path.join(temp_dir, 'settings.json')
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    else:
        print("Ошибка: settings.json не найден!")
        return False
    
    is_infinity = settings.get('infinity', False)
    auto_gluing = settings.get('auto_gluing', False)
    non_random_axis = settings.get('non_random_axis', 'None')
    non_random_chunk = settings.get('non_random_chunk', None)
    chunk_chances = settings.get('chunk_chances', {})
    
    chunks_dir = os.path.join(temp_dir, 'chunks')
    if not os.path.exists(chunks_dir):
        print("Ошибка: папка chunks не найдена!")
        return False
    
    for chunk_file in os.listdir(chunks_dir):
        if chunk_file.endswith('.json'):
            chunk_path = os.path.join(chunks_dir, chunk_file)
            with open(chunk_path, 'r', encoding='utf-8') as f:
                world_data = json.load(f)
                chunks_data[chunk_file] = world_data
                width, depth = get_chunk_width_depth(world_data)
                chunks_info[chunk_file] = {
                    'width': width,
                    'depth': depth,
                    'world_data': world_data
                }
    
    if chunks_data:
        first_chunk = list(chunks_data.values())[0]
        chunk_width, chunk_depth = get_chunk_width_depth(first_chunk)
    
    print(f"Загружено {len(chunks_data)} чанков")
    print(f"Размер чанка: {chunk_width} x {chunk_depth}")
    print(f"Auto-gluing: {auto_gluing}")
    
    assets_zip = os.path.join(temp_dir, 'level_assets.zip')
    if os.path.exists(assets_zip):
        with zipfile.ZipFile(assets_zip, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        print("Ассеты распакованы")
    
    return True

def get_random_chunk_by_chance():
    if not chunk_chances:
        available = [chunk for chunk in chunks_data.keys()]
        return random.choice(available) if available else None
    
    total_chance = sum(chunk_chances.values())
    if total_chance == 0:
        available = [chunk for chunk in chunks_data.keys()]
        return random.choice(available) if available else None
    
    roll = random.randint(1, total_chance)
    cumulative = 0
    for chunk_name, chance in chunk_chances.items():
        cumulative += chance
        if roll <= cumulative and chunk_name in chunks_data:
            return chunk_name
    
    available = [chunk for chunk in chunks_data.keys()]
    return random.choice(available) if available else None

def get_chunk_by_position(chunk_x, chunk_z):
    if not is_infinity:
        return None
    
    if non_random_axis != 'None':
        if (non_random_axis == 'X' and chunk_x == 0) or \
           (non_random_axis == 'Z' and chunk_z == 0):
            if non_random_chunk and non_random_chunk in chunks_data:
                return non_random_chunk
    
    return get_random_chunk_by_chance()

def create_block(block_data, offset_x=0, offset_z=0):
    texture_path = block_data.get('texture')
    texture = None
    if texture_path and os.path.exists(texture_path):
        texture = load_texture(texture_path)
    
    model_name = block_data.get('model', 'cube')
    
    block = Entity(
        model=model_name,
        texture=texture,
        position=(
            block_data['position'][0] + offset_x,
            block_data['position'][1],
            block_data['position'][2] + offset_z
        ),
        rotation=tuple(block_data.get('rotation', [0,0,0])),
        scale=tuple(block_data.get('scale', [1,1,1])),
        collider='box',
        shader=basic_lighting_shader
    )
    
    if block_data.get('animation', {}).get('enabled', False):
        anim_data = block_data['animation']
        try:
            if 'sprite' in anim_data.get('type', '').lower():
                anim_path = anim_data.get('name', '')
                if anim_path and os.path.exists(anim_path):
                    animation = SpriteSheetAnimation(
                        parent=block,
                        texture=anim_path,
                        tiles=Vec2(anim_data.get('cols', 1), anim_data.get('rows', 1)),
                        fps=anim_data.get('fps', 12),
                        loop=anim_data.get('loop', True),
                        autoplay=True
                    )
                    animation.scale = (2, 2)
        except Exception as e:
            print(f"Ошибка загрузки анимации: {e}")
    
    return block

def load_chunk(chunk_x, chunk_z):
    if (chunk_x, chunk_z) in loaded_chunks:
        return
    
    chunk_name = get_chunk_by_position(chunk_x, chunk_z)
    if not chunk_name or chunk_name not in chunks_data:
        return
    
    chunk_info = chunks_info[chunk_name]
    world_data = chunk_info['world_data']
    
    offset_x = chunk_x * chunk_width
    offset_z = chunk_z * chunk_depth
    
    blocks = []
    for block_data in world_data:
        block = create_block(block_data, offset_x, offset_z)
        blocks.append(block)
    
    loaded_chunks[(chunk_x, chunk_z)] = {
        'name': chunk_name,
        'blocks': blocks,
        'offset_x': offset_x,
        'offset_z': offset_z
    }
    
    print(f"Загружен чанк {chunk_name} на ({chunk_x}, {chunk_z}) с offset ({offset_x}, {offset_z})")

def unload_chunk(chunk_x, chunk_z):
    if (chunk_x, chunk_z) not in loaded_chunks:
        return
    
    chunk_data = loaded_chunks[(chunk_x, chunk_z)]
    for block in chunk_data['blocks']:
        destroy(block)
    
    del loaded_chunks[(chunk_x, chunk_z)]
    print(f"Выгружен чанк ({chunk_x}, {chunk_z})")

def update_chunks():
    if not is_infinity:
        return
    
    player_chunk_x = int(player.x // chunk_width)
    player_chunk_z = int(player.z // chunk_depth)
    
    if player.x < 0 and player.x % chunk_width != 0:
        player_chunk_x -= 1
    if player.z < 0 and player.z % chunk_depth != 0:
        player_chunk_z -= 1
    
    needed_chunks = set()
    for dx in range(-render_distance, render_distance + 1):
        for dz in range(-render_distance, render_distance + 1):
            needed_chunks.add((player_chunk_x + dx, player_chunk_z + dz))
    
    for chunk_pos in list(loaded_chunks.keys()):
        if chunk_pos not in needed_chunks:
            unload_chunk(chunk_pos[0], chunk_pos[1])
    
    for chunk_pos in needed_chunks:
        if chunk_pos not in loaded_chunks:
            if chunk_pos != (0, 0):
                load_chunk(chunk_pos[0], chunk_pos[1])

def load_main_chunk():
    main_chunk_name = settings.get('main_chunk')
    if not main_chunk_name:
        print("Ошибка: main_chunk не указан в settings.json!")
        return False
    
    if main_chunk_name not in chunks_data:
        print(f"Ошибка: чанк {main_chunk_name} не найден!")
        return False
    
    chunk_info = chunks_info[main_chunk_name]
    world_data = chunk_info['world_data']
    
    for block_data in world_data:
        create_block(block_data, 0, 0)
    
    loaded_chunks[(0, 0)] = {
        'name': main_chunk_name,
        'blocks': [],
        'offset_x': 0,
        'offset_z': 0
    }
    
    highest_y = find_highest_block_y(world_data, 0, 0)
    
    if highest_y > -9999:
        player.position = (0.5, highest_y + 2, 0.5)
        player.y = highest_y + 2
        print(f"Игрок спавнится на Y={highest_y + 2}")
    else:
        player.position = (0.5, 5, 0.5)
        print("Блоки не найдены, игрок на Y=5")
    
    if is_infinity:
        for x in range(-render_distance, render_distance + 1):
            for z in range(-render_distance, render_distance + 1):
                if x != 0 or z != 0:
                    load_chunk(x, z)
    
    return True

def start_game():
    global level_loaded
    if not loaded_zip_path or not os.path.exists(loaded_zip_path):
        print("Ошибка: файл не выбран или не существует")
        return
    
    print("Загрузка уровня...")
    if load_zip_and_settings(loaded_zip_path):
        if load_main_chunk():
            print("=" * 60)
            print("Уровень успешно загружен!")
            print("Управление: WASD - движение, мышь - осмотр, ESC - выход")
            print("N - Noclip (вкл/выкл)")
            if is_infinity:
                print(f"Режим: бесконечный (дистанция прорисовки {render_distance} чанков)")
            else:
                print("Режим: обычный (только main чанк)")
            print("=" * 60)
            
            level_loaded = True
            return
    
    print("Ошибка загрузки уровня!")

def select_and_load():
    global loaded_zip_path
    loaded_zip_path = select_zip_file()
    if loaded_zip_path:
        start_game()
    else:
        print("Файл не выбран. Выход...")
        application.quit()

def toggle_noclip():
    global noclip_active
    
    noclip_active = not noclip_active
    
    if noclip_active:
        player.gravity = 0
        player.collider = None
        player.speed = 15
        print("Noclip: ВКЛ")
    else:
        player.gravity = 1
        player.collider = 'box'
        player.speed = 8
        print("Noclip: ВЫКЛ")

def update():
    if not level_loaded:
        return
    
    if noclip_active:
        speed = player.speed * time.dt
        if held_keys['w']: player.position += player.forward * speed
        if held_keys['s']: player.position -= player.forward * speed
        if held_keys['a']: player.position -= player.right * speed
        if held_keys['d']: player.position += player.right * speed
        if held_keys['space']: player.y += speed * 2
        if held_keys['left control']: player.y -= speed * 2
    else:
        update_chunks()
    
    time_of_day = (time.time() * 0.03) % (2 * math.pi)
    sun_x = 40 * math.cos(time_of_day)
    sun_z = 40 * math.sin(time_of_day)
    sun_visual.position = (sun_x, 25, sun_z)
    sun_light.look_at(Vec3(-sun_x, -25, -sun_z))

def input(key):
    if key == 'escape':
        if level_loaded and temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        application.quit()
    
    if key == 'n' and level_loaded:
        toggle_noclip()

print("=" * 60)
print("Backrooms: Infinity - Playground")
print("Открывается диалог выбора ZIP файла...")
print("=" * 60)

invoke(select_and_load, delay=0.1)

app.run()