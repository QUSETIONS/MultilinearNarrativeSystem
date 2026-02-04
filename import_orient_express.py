import json
import os

# 配置
JSON_FILE = '东方快车谋杀案.json'
OUTPUT_DIR_TIMELINES = 'dialogic/timelines'
OUTPUT_DIR_CHARACTERS = 'dialogic/characters'
OUTPUT_FILENAME = 'orient_express.dtl'
ASSETS_DIR_BG = 'assets/backgrounds'
ASSETS_DIR_PORTRAITS = 'assets/portraits'

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_character_files(characters, output_dir):
    ensure_directory(output_dir)
    print(f"Generating {len(characters)} characters...")
    
    for char in characters:
        char_id = char['id']
        display_name = char['name']
        file_path = os.path.join(output_dir, f"{char_id}.dch")
        
        # 检查是否有对应的头像文件
        portrait_path = os.path.join(ASSETS_DIR_PORTRAITS, f"{char_id}.png")
        has_portrait = os.path.exists(portrait_path)
        
        default_portrait = char_id if has_portrait else ""
        portraits_str = "{}"
        
        if has_portrait:
            # 构建 Godot Variant 格式的 portraits 字典字符串
            # 注意: image 路径需要是 Godot资源路径 string
            portraits_str = f"""{{
"{char_id}": {{
"export_overrides": {{
"image": "res://assets/portraits/{char_id}.png"
}},
"mirror": false,
"offset": Vector2(0, 0),
"scale": 1,
"scene": ""
}}
}}"""
        
        # Dialogic 使用 dict_to_inst 加载 .dch，必须是 Godot Variant 格式的字典
        content = f"""{{
"class_name": "DialogicCharacter",
"@path": "res://addons/dialogic/Resources/character.gd",
"@subpath": NodePath(""),
"_translation_id": "",
"color": Color(1, 1, 1, 1),
"custom_info": {{
}},
"default_portrait": "{default_portrait}",
"description": "",
"display_name": "{display_name}",
"mirror": false,
"nicknames": ["{display_name}"],
"offset": Vector2(0, 0),
"portraits": {portraits_str},
"scale": 1.0
}}"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Created {file_path}")

def generate_timeline(data, output_dir, filename):
    ensure_directory(output_dir)
    nodes = data['nodes']
    file_path = os.path.join(output_dir, filename)
    
    # Map node ID to index
    node_map = {node['id']: i for i, node in enumerate(nodes)}
    
    # 识别跳转目标
    jump_targets = set()
    
    # Pass 1: Identify targets from choices and non-linear 'next' flows
    for i, node in enumerate(nodes):
        if node['type'] == 'choice':
            for choice in node['choices']:
                jump_targets.add(choice['next'])
        elif 'next' in node and node['next']:
            next_id = node['next']
            # If next node is NOT the immediate next one in the list, we need a jump
            if i + 1 >= len(nodes) or nodes[i+1]['id'] != next_id:
                jump_targets.add(next_id)
    
    lines = []
    
    for i, node in enumerate(nodes):
        node_id = node['id']
        
        if node_id in jump_targets:
            lines.append(f"label {node_id}")
        
        if node['type'] == 'segment':
            lines.append(f"# --- Segment: {node.get('title', 'Unknown')} ---")
            
        elif node['type'] == 'dialogue':
            # Background
            if 'bg' in node and node['bg']:
                bg_file = node['bg']
                # 检查背景文件是否存在
                if os.path.exists(os.path.join(ASSETS_DIR_BG, bg_file)):
                    lines.append(f"[background arg=\"res://assets/backgrounds/{bg_file}\" fade=\"1.0\"]")
                else:
                    lines.append(f"# [background arg=\"{bg_file}\"]")
            
            text = node.get('text', '')
            speaker = node.get('speaker')
            
            # Clear previous portraits (User request: Disappear after talking)
            lines.append("leave --All--")

            if speaker:
                if speaker != 'narrator':
                    # Add simple join command to ensure portrait is visible
                    # Position 1 is typically LEFT (User requested left position)
                    lines.append(f"join {speaker} 1")
                
                lines.append(f"{speaker}: {text}")
            else:
                if 'narrator' in text or not speaker: 
                     lines.append(f"narrator: {text}")
                else:
                     lines.append(f"{text}")

            # Check for Flow Control (Jump)
            if 'next' in node and node['next']:
                next_id = node['next']
                if i + 1 >= len(nodes) or nodes[i+1]['id'] != next_id:
                    lines.append(f"\tjump {next_id}")
                     
        elif node['type'] == 'choice':
            bg = node.get('bg')
            if bg:
                if os.path.exists(os.path.join(ASSETS_DIR_BG, bg)):
                    lines.append(f"[background arg=\"res://assets/backgrounds/{bg}\" fade=\"1.0\"]")
                else:
                    lines.append(f"# [background arg=\"{bg}\"]")
                
            for choice in node['choices']:
                choice_text = choice['text']
                next_id = choice['next']
                
                lines.append(f"- {choice_text}")
                lines.append(f"\tjump {next_id}")
        
        lines.append("") 

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"Generated timeline: {file_path}")

def main():
    if not os.path.exists(JSON_FILE):
        print(f"Error: File {JSON_FILE} not found.")
        return

    data = load_json(JSON_FILE)
    
    create_character_files(data['characters'], OUTPUT_DIR_CHARACTERS)
    generate_timeline(data, OUTPUT_DIR_TIMELINES, OUTPUT_FILENAME)
    print("Done!")

if __name__ == "__main__":
    main()
