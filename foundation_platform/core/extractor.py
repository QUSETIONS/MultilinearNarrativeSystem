import json
import os

class AssetExtractor:
    def __init__(self, json_path, project_root=None):
        self.json_path = json_path
        self.project_root = project_root
        self.data = {}
        self.load_data()

    def load_data(self):
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def extract_all(self):
        """
        Extracts asset definitions from the 'assets' field.
        Returns a dict: {type: {path: description}}
        """
        return self.data.get('assets', {})

    def get_missing_assets(self, base_dir):
        """
        Checks which assets from the JSON are missing on disk.
        """
        missing = []
        assets = self.extract_assets()
        for asset_type, items in assets.items():
            for path, desc in items.items():
                # Normalize path separators for Windows
                clean_path = path.replace('/', os.sep)
                full_path = os.path.join(base_dir, clean_path)
                if not os.path.exists(full_path):
                    missing.append({
                        'type': asset_type,
                        'path': path,
                        'description': desc
                    })
        return missing

    def get_node_asset_usage(self):
        """
        Scans nodes to see which backgrounds are used.
        """
        usage = set()
        for node in self.data.get('nodes', []):
            if 'bg' in node:
                usage.add(node['bg'])
        return usage
