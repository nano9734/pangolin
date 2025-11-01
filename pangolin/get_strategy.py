from pathlib import Path
import importlib.util
import sys
import os

class GetStrategy:
    def __init__(self):
        self.path = Path('.')
        self.files = list(self.path.glob('**/strategies/*.py'))
        self.file_names = []
        self._get_file_names(self.files, self.file_names)
        self._import_from_path(self.file_names)

    def _get_file_names(self, files, file_names):
        for file_name in files:
            if file_name == '__init__.py':
                pass
            else:
                file_name = file_name.stem
                file_names.append(file_name)

    def _import_from_path(self, file_names):
        modules = []
        for file_name in file_names:
            path = os.path.join('pangolin', 'strategies')
            path = os.path.join(path, file_name + '.py')
            # Convert snake case to pascal case
            module_name = file_name.replace('_', ' ').title()
            module_name = module_name.replace(' ', '')
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            modules.append(module)
        return modules
