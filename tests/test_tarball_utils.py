import os
import pytest
import tarfile
import tempfile
from tret.utils.tarball_utils import (
    create_tarball_from_files,
    restore_files_from_tarball,
    get_filepaths_in_tarball,
)

tempdir_kwargs = {
    "prefix": "tret-tests-",
    "dir": os.path.dirname(__file__),
}


@pytest.fixture(scope="module")
def temp_directory():
    temp_dir = tempfile.TemporaryDirectory(**tempdir_kwargs)
    yield temp_dir
    temp_dir.cleanup()


@pytest.fixture(scope="module")
def temp_files(temp_directory):
    filepaths = []
    for i in range(3):
        filepath = os.path.join(temp_directory.name, f"file{i}.txt")
        with open(filepath, "w") as f:
            f.write(f"Content of file {i}")
        filepaths.append(os.path.relpath(filepath, start=os.getcwd()))
    yield filepaths


@pytest.fixture
def temp_tarball_filepath(temp_directory):
    tarball_path = os.path.join(temp_directory.name, "test.tar.gz")
    yield tarball_path


def test_create_tarball_from_files(temp_files, temp_tarball_filepath):
    arcpaths = [os.path.basename(file) for file in temp_files]

    create_tarball_from_files(temp_files, temp_tarball_filepath, arcpaths=arcpaths)
    assert os.path.isfile(temp_tarball_filepath)

    with tarfile.open(temp_tarball_filepath, "r") as tar:
        tar_members = tar.getnames()
        for filepath in temp_files:
            assert os.path.basename(filepath) in tar_members


def test_restore_files_from_tarball(temp_files, temp_tarball_filepath):
    create_tarball_from_files(temp_files, temp_tarball_filepath)
    restore_dir = tempfile.TemporaryDirectory(**tempdir_kwargs)

    restore_files_from_tarball(temp_tarball_filepath, restore_dir.name)
    for filepath in temp_files:
        restored_filepath = os.path.join(restore_dir.name, os.path.basename(filepath))
        assert os.path.isfile(restored_filepath)
        with open(restored_filepath, "r") as f:
            assert f.read() == f"Content of file {os.path.basename(filepath)[4]}"

    restore_dir.cleanup()


def test_get_filepaths_in_tarball(temp_files, temp_tarball_filepath):
    arcpaths = [os.path.basename(file) for file in temp_files]

    create_tarball_from_files(temp_files, temp_tarball_filepath, arcpaths=arcpaths)
    filepaths_in_tarball = get_filepaths_in_tarball(temp_tarball_filepath)
    for filepath in temp_files:
        assert os.path.basename(filepath) in filepaths_in_tarball


def test_append_to_existing_tarball(temp_files, temp_tarball_filepath):
    arcpaths = [os.path.basename(file) for file in temp_files]

    create_tarball_from_files(temp_files[:2], temp_tarball_filepath, arcpaths=arcpaths[:2])
    create_tarball_from_files(temp_files[:2], temp_tarball_filepath)
    create_tarball_from_files([temp_files[2]], temp_tarball_filepath, arcpaths=[arcpaths[2]], append_data_to_existing_tarball=True)

    with tarfile.open(temp_tarball_filepath, "r") as tar:
        tar_members = tar.getnames()
        for filepath in temp_files:
            assert os.path.basename(filepath) in tar_members
