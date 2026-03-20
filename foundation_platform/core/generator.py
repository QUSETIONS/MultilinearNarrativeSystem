from abc import ABC, abstractmethod
import os
from typing import Dict, Type, Optional

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
        print(f"Mock generating asset: {description} -> {output_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create a tiny placeholder file (simulating generation)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Placeholder for asset generation\n")
                f.write(f"Description: {description}\n")
            return True
        except Exception as e:
            print(f"Error during mock generation: {e}")
            return False

class CozeGenerator(BaseGenerator):
    """
    Future implementation for Coze AI Agent integration.
    """
    def generate(self, description: str, output_path: str) -> bool:
        # TODO: Implement Coze API call
        print(f"CozeGenerator (BETA): Generating '{description}'")
        return False

# Register Providers
GeneratorRegistry.register("mock", MockGenerator)
GeneratorRegistry.register("coze", CozeGenerator)
