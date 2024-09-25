import os
import datetime
from ..arguments import TretArguments
from .data_backup import backup_data
from .code_backup_and_restore import (
    backup_codes,
    restore_codes,
)


class TretWorkspace:
    def __init__(
        self,
        arguments: TretArguments,
    ):
        self.arguments = arguments
        self.workspace_basedir = self.arguments.workspace_basedir
        self.force_backup_codes_as_tarball = self.arguments.force_backup_codes_as_tarball
        self.backup_data_as_symlinks = self.arguments.backup_data_as_symlinks
        self.workspace_name = self.arguments.workspace_name
        if self.workspace_name is None:
            self.workspace_name = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        self.workspace_dir = os.path.join(self.workspace_basedir, self.workspace_name)
        if os.path.isfile(self.workspace_dir):
            raise FileExistsError(f"'{self.workspace_dir}' is already a file, cannot work as a workspace.")
        os.makedirs(self.workspace_dir, exist_ok=True)

    def restore(self):
        """
        Restores the codes from the specified workspace directory.

        Args:
            workspace_dir (str): The directory where the workspace will be restored from.
        """
        restore_codes(self.workspace_dir)
        # TODO: check the modified time of linked data files and symlinks
        # if the linked data files is newer than symlinks, raise a warning that the raw data has been changed.

    def save(self, datafiles: list[str] = None):
        """
        Saves the current workspace to the specified directory.

        Args:
            workspace_dir (str): The directory where the workspace will be saved.
            use_symlinks (bool): If True, the data will be saved as symlinks. Otherwise, the data will be saved as a tarball.
        """
        backup_codes(self.workspace_dir, backup_codes_as_tarball=self.force_backup_codes_as_tarball)
        if datafiles is not None:
            backup_data(
                filepaths=datafiles,
                workspace_dir=self.workspace_dir,
                use_symlinks=self.backup_data_as_symlinks,
            )
