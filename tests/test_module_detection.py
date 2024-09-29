import os
import sys
import json
import types
import pytest
from tret.utils.module_detection import (
    is_standard_lib_or_builtin_lib,
    is_local_module,
    get_external_module_version,
    detect_all_modules,
    generate_requirements_txt
)


def test_is_standard_lib_or_builtin_lib():
    assert is_standard_lib_or_builtin_lib(os) is True
    assert is_standard_lib_or_builtin_lib(json) is True

    assert is_standard_lib_or_builtin_lib(pytest) is False


def test_is_local_module():
    # Create a dummy local module
    dummy_local_module = types.ModuleType('dummy_local_module')
    dummy_local_module.__file__ = os.path.join(os.getcwd(), 'dummy_local_module.py')
    assert is_local_module(dummy_local_module) is True

    # Create a dummy external module
    dummy_external_module = types.ModuleType('dummy_external_module')
    dummy_external_module.__file__ = '/usr/local/lib/python3.9/site-packages/dummy_external_module.py'

    assert is_local_module(dummy_external_module) is False

    # Test with a built-in module (which should not be considered local)
    assert is_local_module(os) is False


def test_get_external_module_version():
    version = get_external_module_version(pytest)
    assert version is not None
    assert isinstance(version, str)

    # Test with a non-existent module
    non_existent_module = types.ModuleType('non_existent_module')
    assert get_external_module_version(non_existent_module) is None


def test_detect_all_modules():
    classified_modules = detect_all_modules()
    assert 'standard_libs' in classified_modules
    assert 'local_modules' in classified_modules
    assert 'external_modules' in classified_modules

    # Check that the standard library contains some known modules
    assert os in classified_modules['standard_libs']

    # Check that pytest is classified as an external module
    assert pytest in classified_modules['external_modules']


def test_generate_requirements_txt():
    external_modules = [pytest]
    requirements = generate_requirements_txt(external_modules)
    assert len(requirements) > 0
    assert any(req.startswith('pytest==') for req in requirements)

    # Test with an empty list
    requirements = generate_requirements_txt([])
    assert requirements == []
