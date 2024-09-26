import os
import sys
import types
python_version = sys.version_info
assert python_version.major == 3, "Tret only supports Python3."
if python_version.minor < 10:
    try:
        from stdlib_list import stdlib_list
        stdlibs = stdlib_list(f"{python_version.major}.{python_version.minor}") + list(sys.builtin_module_names)
    except ImportError:
        raise ImportError(
            "The stdlib_list package is required for Python versions < 3.10. "
            "Please install it via `pip install stdlib-list`."
        )
else:
    stdlibs = list(sys.stdlib_module_names) + list(sys.builtin_module_names)

import importlib
import importlib.metadata
# import pipdeptree


def is_standard_lib_or_builtin_lib(module: types.ModuleType):
    """check if a module is part of the standard library or python builtin library
    """
    module_name = module.__name__
    # stdlibs contains all python standard library
    # modules without __file__ attribute are python builtin modules
    return module_name in stdlibs or (not hasattr(module, "__file__")) or not module.__file__


def is_local_module(module: types.ModuleType):
    """check if a module is part of the local module (i.e., not installed via pip or conda)
    """
    module_path = module.__file__
    return os.path.abspath(module_path).startswith(os.getcwd())


def get_external_module_version(module: types.ModuleType):
    """get the version of an external module
    """
    try:
        module_version = importlib.metadata.version(module.__name__)
    except Exception:
        return None
    return module_version


def detect_all_modules():
    """
    Detect and classify all currently loaded modules into standard libraries, local modules, and external modules.

    Returns:
        dict: A dictionary with three keys:
            - "standard_libs": A list of modules that are part of the Python standard library or built-in modules.
            - "local_modules": A list of modules that are part of the local project (i.e., not installed via pip or conda).
            - "external_modules": A list of modules that are installed via pip or conda.
    """
    modules = sys.modules
    classified_modules = {
        "standard_libs": [],
        "local_modules": [],
        "external_modules": [],
    }
    for module_name, module in modules.items():
        # only classify root modules
        splitted_module_name = module.__name__.split('.')
        if is_standard_lib_or_builtin_lib(module) or is_standard_lib_or_builtin_lib(modules[splitted_module_name[0]]):
            classified_modules["standard_libs"].append(module)
        elif is_local_module(module):
            classified_modules["local_modules"].append(module)
        else:
            classified_modules["external_modules"].append(module)
    # deduplication
    for class_name, modules in classified_modules.items():
        classified_modules[class_name] = list(set(modules))
    return classified_modules


def generate_requirements_txt(external_modules: list[types.ModuleType]):
    """
    Generate a requirements.txt file for the external modules used in the current project.
    TODO: shrink the size of requirement.txt, only records modules who are on the top of dependency tree.
    """
    requirements = []
    for module in external_modules:
        version = get_external_module_version(module)
        if version:
            requirements.append(f"{module.__name__}=={version}")
    return requirements
