import os
import json
import shutil
import pytest
import datetime
from unittest.mock import MagicMock, patch
from tret.core.main_class import TretWorkspace
from tret.arguments import TretArguments


@pytest.fixture(scope="module")
def temp_tret_arguments():
    args = TretArguments(
        workspace_basedir=os.path.join(os.path.dirname(__file__), "tret-workspace"),
        workspace_name="tests",
        create_directory=True,
    )
    return args


@pytest.fixture(scope="module")
def temp_tret_workspace(temp_tret_arguments):
    workspace = TretWorkspace(arguments=temp_tret_arguments)
    yield workspace
    shutil.rmtree(workspace.workspace_dir)


def test_init(temp_tret_workspace, temp_tret_arguments):
    assert temp_tret_workspace.arguments == temp_tret_arguments
    assert temp_tret_workspace.workspace_basedir == temp_tret_arguments.workspace_basedir
    assert temp_tret_workspace.force_backup_codes_as_tarball == temp_tret_arguments.force_backup_codes_as_tarball
    assert temp_tret_workspace.append_data_to_existing_tarball == temp_tret_arguments.append_data_to_existing_tarball
    assert temp_tret_workspace.workspace_name is not None
    assert os.path.isdir(temp_tret_workspace.workspace_dir)
