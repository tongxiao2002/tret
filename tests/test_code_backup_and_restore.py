import os
import shutil
import pytest
import tempfile
import importlib
from git import Repo
from tret.core.code_backup_and_restore import (
    backup_codes,
    restore_codes,
    get_git_repo_path,
    _start_point_for_finding_git_repo,
)
from tret.constants import (
    CODES_TARBALL_FILENAME,
    GIT_INFO_FILENAME,
)

tempdir_kwargs = {
    "prefix": "tret-workspace-",
    "dir": os.path.dirname(__file__),
}


def test_get_git_repo_path_None():
    assert get_git_repo_path("/") is None


def test_start_point_for_finding_git_repo():
    assert _start_point_for_finding_git_repo("/") == os.getcwd()


@pytest.fixture
def temp_git_repo():
    git_repo_dir = os.path.dirname(__file__)
    if os.path.exists(os.path.join(git_repo_dir, ".git")):
        raise FileExistsError(f"Directory '{git_repo_dir}' is already a git repository.")

    tmp_repo = Repo.init(git_repo_dir)
    yield tmp_repo
    tmp_repo.close()
    shutil.rmtree(tmp_repo.git_dir)


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.TemporaryDirectory(**tempdir_kwargs)
    yield temp_dir.name
    temp_dir.cleanup()


@pytest.fixture(scope="module")
def temp_local_module():
    temp_dir = os.path.join(os.path.dirname(__file__), "local_module")
    os.makedirs(temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_backup_codes_with_git(temp_git_repo, temp_workspace, temp_local_module):
    workspace_dir = temp_workspace

    # create __init__.py file
    with open(os.path.join(temp_local_module, "__init__.py"), "w", encoding="utf-8") as fout:
        fout.close()

    test_file = os.path.join(temp_local_module, "test_file.py")
    with open(test_file, "w", encoding="utf-8") as fout:
        fout.write("print('Hello, World!')")

    temp_git_repo.index.add([test_file])
    temp_git_repo.index.commit("Initial commit")

    backup_codes(workspace_dir=workspace_dir)

    assert os.path.isfile(os.path.join(workspace_dir, GIT_INFO_FILENAME))


def test_backup_codes_without_git(temp_workspace, temp_local_module):
    workspace_dir = temp_workspace

    # create __init__.py file
    with open(os.path.join(temp_local_module, "__init__.py"), "w", encoding="utf-8") as fout:
        fout.close()

    test_file = os.path.join(temp_local_module, "test_file.py")
    with open(test_file, "w", encoding="utf-8") as fout:
        fout.write("print('Hello, World!')")

    backup_codes(workspace_dir=workspace_dir, backup_codes_as_tarball=True)
    assert os.path.isfile(os.path.join(workspace_dir, CODES_TARBALL_FILENAME))
    assert not os.path.isfile(os.path.join(workspace_dir, GIT_INFO_FILENAME))


def test_restore_codes_with_git(temp_git_repo, temp_workspace, temp_local_module):
    workspace_dir = temp_workspace

    # create __init__.py file
    with open(os.path.join(temp_local_module, "__init__.py"), "w", encoding="utf-8") as fout:
        fout.close()

    test_file = os.path.join(temp_local_module, "test_file.py")
    with open(test_file, "w", encoding="utf-8") as fout:
        fout.write("print('Hello, World!')")

    temp_git_repo.index.add([test_file])
    temp_git_repo.index.commit("Initial commit")

    with open(test_file, "w", encoding="utf-8") as fout:
        fout.write("print('Hello, Universe!')")

    backup_codes(workspace_dir)

    temp_git_repo.index.add([test_file])
    temp_git_repo.index.commit("Second commit")

    restore_codes(workspace_dir)
    with open(test_file, "r", encoding="utf-8") as fin:
        assert fin.read() == "print('Hello, Universe!')"


def test_restore_codes_without_git(temp_workspace, temp_local_module):
    workspace_dir = temp_workspace

    # create __init__.py file
    with open(os.path.join(temp_local_module, "__init__.py"), "w", encoding="utf-8") as fout:
        fout.close()

    test_file = os.path.join(temp_local_module, "test_file.py")
    with open(test_file, "w", encoding="utf-8") as fout:
        fout.write("print('Hello, World!')")
    importlib.import_module("local_module")
    importlib.import_module("local_module.test_file")

    backup_codes(workspace_dir, backup_codes_as_tarball=True)
    with open(test_file, "w", encoding="utf-8") as fout:
        fout.write("print('Hello, Universe!')")

    restore_codes(workspace_dir)
    with open(test_file, "r", encoding="utf-8") as fin:
        assert fin.read() == "print('Hello, World!')"


def test_backup_and_restore_additional_files(temp_workspace, temp_local_module):
    workspace_dir = temp_workspace

    # create __init__.py file
    with open(os.path.join(temp_local_module, "__init__.py"), "w", encoding="utf-8") as fout:
        fout.close()

    test_file = os.path.join(temp_local_module, "test_file.py")
    additional_file = os.path.join(temp_local_module, "additional_file.py")

    with open(test_file, "w", encoding="utf-8") as fout:
        fout.write("print('Hello, World!')")

    with open(additional_file, "w", encoding="utf-8") as fout:
        fout.write("print('Additional file')")

    backup_codes(
        workspace_dir=workspace_dir,
        additional_codefiles_to_backup=[additional_file],
        backup_codes_as_tarball=True
    )

    with open(test_file, "w", encoding="utf-8") as fout:
        fout.write("print('Hello, Universe!')")

    with open(additional_file, "w", encoding="utf-8") as fout:
        fout.write("print('Modified additional file')")

    restore_codes(workspace_dir)
    with open(test_file, "r", encoding="utf-8") as fin:
        assert fin.read() == "print('Hello, World!')"

    with open(additional_file, "r", encoding="utf-8") as fin:
        assert fin.read() == "print('Additional file')"
