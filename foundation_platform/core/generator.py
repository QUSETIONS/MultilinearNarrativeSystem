from abc import ABC, abstractmethod
import os
import json
import base64
import requests
from typing import Dict, Type, Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "models.json")

def _load_model_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

class BaseGenerator(ABC):
    """
    Abstract base class for all asset generators (Foundation Model Providers).
    """
    @abstractmethod
    def generate(self, description: str, output_path: str) -> bool:
        """
        Generate an asset based on description and save it to output_path.
        Returns True if successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement generate()")

class GeneratorRegistry:
    """
    Registry for managing multiple model providers (Foundation Bases).
    """
    _generators: Dict[str, Type[BaseGenerator]] = {}

    @classmethod
    def register(cls, name: str, generator_cls: Type[BaseGenerator]):
        cls._generators[name.lower()] = generator_cls

    @classmethod
    def get_generator(cls, name: str) -> Optional[BaseGenerator]:
        gen_cls = cls._generators.get(name.lower())
        if gen_cls:
            return gen_cls()
        return None

    @classmethod
    def list_providers(cls) -> list:
        return list(cls._generators.keys())

class MockGenerator(BaseGenerator):
    def generate(self, description: str, output_path: str) -> bool:
        print(f"Mock generating asset: {description[:60]}... -> {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Placeholder for asset generation\n")
                f.write(f"Description: {description}\n")
            return True
        except Exception as e:
            print(f"Error during mock generation: {e}")
            return False


class SiliconFlowGenerator(BaseGenerator):
    """
    Phase 24: Real image generation via SiliconFlow (硅基流动) free SDXL API.
    Endpoint: https://api.siliconflow.cn/v1/images/generations
    """
    def generate(self, description: str, output_path: str) -> bool:
        config = _load_model_config().get("siliconflow", {})
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "https://api.siliconflow.cn/v1")
        model = config.get("model", "stabilityai/stable-diffusion-xl-base-1.0")
        image_size = config.get("image_size", "1024x1024")
        
        if not api_key:
            print("[SiliconFlow] No API key configured in models.json. Using mock fallback.")
            return MockGenerator().generate(description, output_path)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            print(f"[SiliconFlow] Generating: {description[:80]}...")
            response = requests.post(
                f"{base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "prompt": description,
                    "image_size": image_size,
                    "batch_size": 1,
                    "num_inference_steps": 30
                },
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"[SiliconFlow] API Error {response.status_code}: {response.text[:200]}")
                return False
            
            data = response.json()
            images = data.get("images", data.get("data", []))
            
            if not images:
                print("[SiliconFlow] No images returned.")
                return False
            
            # Handle both base64 and URL responses
            img_data = images[0]
            if isinstance(img_data, dict):
                if "b64_json" in img_data:
                    img_bytes = base64.b64decode(img_data["b64_json"])
                elif "url" in img_data:
                    img_resp = requests.get(img_data["url"], timeout=30)
                    img_bytes = img_resp.content
                else:
                    print(f"[SiliconFlow] Unknown response format: {list(img_data.keys())}")
                    return False
            elif isinstance(img_data, str):
                # Direct base64
                img_bytes = base64.b64decode(img_data)
            else:
                return False
            
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            
            print(f"[SiliconFlow] Saved to {output_path} ({len(img_bytes)} bytes)")
            return True
            
        except Exception as e:
            print(f"[SiliconFlow] Error: {e}")
            return False


class CozeGenerator(BaseGenerator):
    """Future implementation for Coze AI Agent integration."""
    def generate(self, description: str, output_path: str) -> bool:
        print(f"CozeGenerator (BETA): Not yet implemented. Use 'siliconflow' instead.")
        return False

# Register Providers
GeneratorRegistry.register("mock", MockGenerator)
GeneratorRegistry.register("siliconflow", SiliconFlowGenerator)
GeneratorRegistry.register("coze", CozeGenerator)
