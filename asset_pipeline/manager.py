import os
import sys
import io

# Handle Windows terminal encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ensure we can import from the current package structure
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from core.extractor import AssetExtractor
    from core.generator import MockGenerator, CozeGenerator
except ImportError:
    # Fallback for different execution contexts
    from .core.extractor import AssetExtractor
    from .core.generator import MockGenerator, CozeGenerator

class AssetManager:
    def __init__(self, json_path, root_dir):
        self.extractor = AssetExtractor(json_path)
        self.root_dir = root_dir
        self.generator = MockGenerator() # Default to mock for safety

    def use_coze(self):
        self.generator = CozeGenerator()

    def run_sync(self, dry_run=True, limit=None):
        """
        Sync assets between JSON definition and local files.
        """
        print("="*60)
        print(" ASSET EXTRACTION & GENERATION PLATFORM")
        print("="*60)
        print(f"Target JSON: {self.extractor.json_path}")
        print(f"Root Dir:    {self.root_dir}\n")

        missing = self.extractor.get_missing_assets(self.root_dir)
        
        if not missing:
            print("DONE: All assets are present. Nothing to do!")
            return

        print(f"INFO: Found {len(missing)} missing assets to be generated:\n")
        
        for i, item in enumerate(missing, 1):
            print(f"  {i}. [{item['type']}] {item['path']}")
            print(f"     Prompt: {item['description']}")
        
        print("\n" + "="*60)
        
        if dry_run:
            print("WARNING: DRY RUN ENABLED - No files were created.")
            return

        print("START: Starting Generation...")
        count = 0
        for item in missing:
            if limit and count >= limit:
                print(f"\nINFO: Limit of {limit} reached. Stopping.")
                break
            
            # Normalize path for the OS
            clean_path = item['path'].replace('/', os.sep)
            output_path = os.path.join(self.root_dir, clean_path)
            
            print(f"PROCESSING: Generating {item['path']}...")
            success = self.generator.generate(item['description'], output_path)
            if success:
                print(f"   SUCCESS: Done.")
            else:
                print(f"   FAILED.")

if __name__ == "__main__":
    # Default execution for testing
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_name = "东方快车谋杀案合并版.json"
    json_path = os.path.join(project_root, json_name)
    
    if not os.path.exists(json_path):
        print(f"Error: Could not find {json_name} in {project_root}")
        sys.exit(1)

    manager = AssetManager(json_path, project_root)
    # Run a test sync with a limit of 3 for the first batch
    manager.run_sync(dry_run=False, limit=3)
