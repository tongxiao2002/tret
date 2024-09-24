import os
from .data_backup import backup_data
from .code_backup_and_restore import (
    backup_codes,
    restore_codes,
)


class TretWorkspace:
    def __init__(self, workspace_dir: str = None):
        pass

    def restore(self, workspace_dir: str):
        """
        Restores the codes from the specified workspace directory.

        Args:
            workspace_dir (str): The directory where the workspace will be restored from.
        """
        assert os.path.isdir(workspace_dir), f"{workspace_dir} is not a valid directory."
        restore_codes(workspace_dir)
        # TODO: check the modified time of linked data files and symlinks
        # if the linked data files is newer than symlinks, raise a warning that the raw data has been changed.

    def save(self, workspace_dir: str, datafiles: list[str], data_use_symlinks: bool = True):
        """
        Saves the current workspace to the specified directory.

        Args:
            workspace_dir (str): The directory where the workspace will be saved.
            use_symlinks (bool): If True, the data will be saved as symlinks. Otherwise, the data will be saved as a tarball.
        """
        assert os.path.isdir(workspace_dir), f"{workspace_dir} is not a valid directory."
        backup_codes(workspace_dir)
        backup_data(
            filepaths=datafiles,
            workspace_dir=workspace_dir,
            use_symlinks=data_use_symlinks,
        )
