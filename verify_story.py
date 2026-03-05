import json
import os

def check_story():
    with open('东方快车谋杀案合并版.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    used_bgs = set()
    used_bgms = set()
    used_speakers = set()

    nodes = data.get('nodes', [])
    for n in nodes:
        if 'bg' in n and n['bg']:
            used_bgs.add(n['bg'])
        if 'music' in n and n['music']:
            used_bgms.add(n['music'])
        if n.get('type') == 'dialogue':
            speaker = n.get('speaker', '')
            if speaker and speaker != 'narrator':
                used_speakers.add(speaker)
        if 'choices' in n and isinstance(n['choices'], list):
            for ch in n['choices']:
                pass # choices usually don't have bg

    bgs = set(os.listdir('assets/backgrounds')) if os.path.exists('assets/backgrounds') else set()
    bgms = set(os.listdir('assets/bgm')) if os.path.exists('assets/bgm') else set()
    ports = set(os.listdir('assets/portraits')) if os.path.exists('assets/portraits') else set()

    missing_bgs = []
    for bg in sorted(used_bgs):
        clean_bg = bg.replace('assets/backgrounds/', '').replace('res://assets/backgrounds/', '')
        if clean_bg not in bgs and clean_bg+'.png' not in bgs and bg not in bgs:
            missing_bgs.append(bg)

    missing_ports = []
    for s in sorted(used_speakers):
        if s + '.png' not in ports:
            missing_ports.append(s)

    end_nodes = [n for n in nodes if n.get('type') == 'chapter' and n.get('next') is None]

    with open('verify_output.txt', 'w', encoding='utf-8') as f:
        f.write(f"Missing Backgrounds ({len(missing_bgs)}):\n")
        f.write("\n".join(missing_bgs) + "\n\n")
        f.write(f"Missing Portraits ({len(missing_ports)}):\n")
        f.write("\n".join(missing_ports) + "\n\n")
        f.write(f"Story End Nodes:\n")
        f.write("\n".join([n['id'] for n in end_nodes]) + "\n\n")
        f.write(f"Total Nodes: {len(nodes)}\n")

if __name__ == '__main__':
    check_story()
