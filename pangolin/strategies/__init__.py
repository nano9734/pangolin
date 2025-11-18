from pathlib import Path
import string
import os
import sys
import importlib

# load strategy modules from pangolin/strategies
class GetStrategy:
    def __init__(self):
        print('*** GetStrategy Class ***')

        # collect all strategy files ending with '.py'
        files = list(Path("pangolin/strategies").glob("*.py"))

        # build name arrays
        file_names = []
        module_names = []
        for file_path in files:
            if not file_path.stem == '__init__':
                # extract filename components
                file_name = os.path.basename(file_path)
                name = os.path.splitext(file_name)[0]
                ext  = os.path.splitext(file_name)[1]

                # convert snake case to pascal case
                module_name = ''.join(word.capitalize() for word in name.split('_'))
                module_names.append(module_name)
                self._import_from_path(module_name, file_path)

    # dynamically import a module from a file path
    def _import_from_path(self, module_name, file_path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # instantiate the class if it exists in the module
        if hasattr(module, module_name):
            cls = getattr(module, module_name)
            instance = cls()
            return instance
