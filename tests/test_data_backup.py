import os
import pytest
import tempfile
from unittest.mock import patch
from tret.core.data_backup import backup_data
from tret.constants import DATA_TARBALL_FILENAME

tempdir_kwargs = {
    "prefix": "tret-workspace-",
    "dir": os.path.dirname(__file__),
}


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.TemporaryDirectory(**tempdir_kwargs)
    yield temp_dir
    temp_dir.cleanup()


def test_backup_data_files_to_backup(temp_workspace):
    workspace_dir = temp_workspace.name
    test_file = os.path.join(workspace_dir, "test_file.txt")

    with open(test_file, "w") as f:
        f.write("test content")

    backup_data(workspace_dir, files_to_backup=[test_file])
    backup_file = os.path.join(workspace_dir, "data", "test_file.txt")
    assert os.path.exists(backup_file)
    with open(backup_file, "r") as f:
        assert f.read() == "test content"


def test_backup_data_files_to_backup_as_symlink(temp_workspace):
    workspace_dir = temp_workspace.name
    test_file = os.path.join(workspace_dir, "test_file.txt")

    with open(test_file, "w") as f:
        f.write("test content")

    backup_data(workspace_dir, files_to_backup_as_symlink=[test_file])
    symlink_file = os.path.join(workspace_dir, "data", "symlinks", "test_file.txt")
    assert os.path.islink(symlink_file)
    assert os.readlink(symlink_file) == test_file


def test_backup_data_files_to_backup_as_tarball(temp_workspace):
    workspace_dir = temp_workspace.name
    test_file = os.path.join(workspace_dir, "test_file.txt")

    with open(test_file, "w") as f:
        f.write("test content")

    with patch("tret.core.data_backup.create_tarball_from_files") as mock_create_tarball:
        backup_data(workspace_dir, files_to_backup_as_tarball=[test_file])
        data_tarball_filepath = os.path.join(workspace_dir, "data", DATA_TARBALL_FILENAME)
        mock_create_tarball.assert_called_once_with(
            filepaths=[test_file],
            output=data_tarball_filepath,
            append_data_to_existing_tarball=True,
        )


def test_backup_data_file_not_found(temp_workspace):
    workspace_dir = temp_workspace.name
    non_existent_file = os.path.join(workspace_dir, "non_existent_file.txt")

    with pytest.raises(FileNotFoundError):
        backup_data(workspace_dir, files_to_backup=[non_existent_file])

    with pytest.raises(FileNotFoundError):
        backup_data(workspace_dir, files_to_backup_as_symlink=[non_existent_file])

    with pytest.raises(FileNotFoundError):
        backup_data(workspace_dir, files_to_backup_as_tarball=[non_existent_file])


def test_backup_data_directory_to_backup(temp_workspace):
    workspace_dir = temp_workspace.name
    test_dir = os.path.join(workspace_dir, "test_dir")
    os.makedirs(test_dir)
    test_file = os.path.join(test_dir, "test_file.txt")

    with open(test_file, "w") as f:
        f.write("test content")

    backup_data(workspace_dir, files_to_backup=[test_dir])
    backup_dir = os.path.join(workspace_dir, "data", "test_dir")
    backup_file = os.path.join(backup_dir, "test_file.txt")

    assert os.path.exists(backup_dir)
    assert os.path.isdir(backup_dir)
    assert os.path.exists(backup_file)
    with open(backup_file, "r") as f:
        assert f.read() == "test content"
