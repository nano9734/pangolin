from pathlib import Path
from typing import List
import importlib.util
import sys

class Strategy:
    def __init__(self, strategy_folder_path: str):
        self.strategy_folder_path = Path(strategy_folder_path)
        self.strategy_paths = list(self.strategy_folder_path.glob('*.py'))

    def loads(self, avg_prices: List[float]):
        file_name = self.strategy_paths[0].stem # The final path component, without its suffix
        module_name = file_name.replace("_", " ").title().replace(" ", "") # Convert snake case to pascal case

        # Dynamically load the strategy class from the strategy file
        strategy_class = self.get_strategy_class_from_file(
            module_name=module_name
        )

        print(f"[INFO] Strategy loaded successfully (Class: {module_name}, File: {file_name}.py)")

        return strategy_class(
            avg_prices=avg_prices
        )

    def get_strategy_class_from_file(self, module_name: str):
        spec = importlib.util.spec_from_file_location(module_name, self.strategy_paths[0])
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        strategy_class = getattr(module, module_name)
        return strategy_class
