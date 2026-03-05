import json

d = json.load(open('东方快车谋杀案.json', 'r', encoding='utf-8'))
nodes = d['nodes']

# Find all segments
segs = []
for i, n in enumerate(nodes):
    if n['type'] == 'segment':
        segs.append((i, n['id'], n.get('title', '')))

print(f'Total nodes: {len(nodes)}')
print(f'Total segments: {len(segs)}')
print()

# Show chapter boundaries
for j, (idx, sid, title) in enumerate(segs):
    start = idx
    end = segs[j+1][0] - 1 if j+1 < len(segs) else len(nodes) - 1
    node_count = end - start
    print(f'Chapter {j+1}: "{title}" (segment_id={sid})')
    print(f'  Nodes: [{start}..{end}] ({node_count} nodes)')
    
    # Count types within this chapter
    types = {}
    for k in range(start+1, end+1):
        t = nodes[k]['type']
        types[t] = types.get(t, 0) + 1
    print(f'  Types: {types}')
    print()
