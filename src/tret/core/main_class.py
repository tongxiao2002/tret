import os
import json
import warnings
import datetime
from ..arguments import TretArguments
from ..constants import (
    REQUIREMENTS_TXT_FILENAME,
    TRET_ATTRIBUTES_FILENAME,
    CURRENT_CODES_TARBALL_FILENAME,
)
from .data_backup import backup_data
from .code_backup_and_restore import (
    backup_codes,
    restore_codes,
)
from ..utils.tarball_utils import restore_files_from_tarball


class TretWorkspace:
    """
    TretWorkspace is a class that manages the workspace for Tret projects,
    providing functionalities to back up and restore code and data.

    Attributes:
        arguments (TretArguments): The arguments provided for the workspace.
    """
    def __init__(
        self,
        arguments: TretArguments,
    ):
        self.arguments = arguments
        self.workspace_basedir = self.arguments.workspace_basedir
        self.force_backup_codes_as_tarball = self.arguments.force_backup_codes_as_tarball
        self.workspace_name = self.arguments.workspace_name
        self.append_data_to_existing_tarball = self.arguments.append_data_to_existing_tarball
        if self.workspace_name is None:
            self.workspace_name = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

        if os.path.isfile(self.workspace_dir):
            raise FileExistsError(f"'{self.workspace_dir}' is already a file, cannot work as a workspace.")
        if arguments.create_directory:
            os.makedirs(self.workspace_dir, exist_ok=True)
        self.tret_attributes_filepath = os.path.join(self.workspace_dir, TRET_ATTRIBUTES_FILENAME)

    @property
    def workspace_dir(self) -> str:
        return os.path.join(self.workspace_basedir, self.workspace_name)

    def restore_current_codes_from_tarball(self, remove_after_restore: bool = True):
        current_codes_tarball_filepath = os.path.join(self.workspace_dir, CURRENT_CODES_TARBALL_FILENAME)
        if not os.path.isfile(current_codes_tarball_filepath):
            warnings.warn(f"'{current_codes_tarball_filepath}' does not exist. Can not restores current codes.")
        restore_files_from_tarball(current_codes_tarball_filepath)
        if remove_after_restore:
            os.remove(current_codes_tarball_filepath)

        requirements_filepath = os.path.join(os.getcwd(), REQUIREMENTS_TXT_FILENAME)
        if os.path.isfile(requirements_filepath):
            os.remove(requirements_filepath)

    def restore(self) -> dict:
        """
        Restores the codes from the specified workspace directory.

        Args:
            workspace_dir (str): The directory where the workspace will be restored from.
        """
        assert os.path.isdir(self.workspace_dir), f"The workspace directory '{self.workspace_dir}' does not exist."

        # first restore from any `current-codes.tar.gz`
        current_codes_tarball_filepaths = []
        existing_workspace_names = os.listdir(self.workspace_basedir)
        for ws_name in existing_workspace_names:
            ws_dir = os.path.join(self.workspace_basedir, ws_name)
            tarball_filepath = os.path.join(ws_dir, CURRENT_CODES_TARBALL_FILENAME)
            if os.path.isfile(tarball_filepath):
                current_codes_tarball_filepaths.append(tarball_filepath)
        assert len(current_codes_tarball_filepaths) <= 1, "Multiple `current-codes.tar.gz` found in workspace base dir."

        if current_codes_tarball_filepaths:
            warnings.warn(
                f"Found existing 'current-codes.tar.gz' in {current_codes_tarball_filepaths[0]}. "
                f"Restoring from '{current_codes_tarball_filepaths[0]}' first."
            )
            restore_files_from_tarball(current_codes_tarball_filepaths[0])
            os.remove(current_codes_tarball_filepaths[0])

        restore_codes(self.workspace_dir)

        # check the modify time of symlink and the linked file
        # tret_attributes = json.load(open(self.tret_attributes_filepath, "r", encoding="utf-8"))
        symlink_data_dir = os.path.join(self.workspace_dir, "data", "symlinks")

        if not os.path.isdir(symlink_data_dir):
            # if no data are linked, just return
            return
        for filename in os.listdir(symlink_data_dir):
            symlink_datapath = os.path.join(symlink_data_dir, filename)
            symlink_file_stat = os.stat(symlink_datapath, follow_symlinks=False)
            raw_datafile_stat = os.stat(symlink_datapath, follow_symlinks=True)
            if raw_datafile_stat.st_mtime > symlink_file_stat.st_mtime:
                warnings.warn(
                    f"The target file has been modified more recently than the symlink: '{symlink_datapath}'. "
                    "The data may be outdated."
                )

        # load metadata
        tret_attributes = json.load(open(self.tret_attributes_filepath, "r", encoding="utf-8"))
        return tret_attributes['metadata']

    def backup(
        self,
        datafiles_to_backup: list[str] = None,
        datafiles_to_backup_as_tarball: list[str] = None,
        datafiles_to_backup_as_symlink: list[str] = None,
        additional_codefiles_to_backup: list[str] = [],
        metadata: dict = {},
    ):
        """
        Backs up specified files in different formats.
        Args:
            files_to_backup (list[str], optional): List of file paths to back up as regular files. Defaults to None.
            files_to_backup_as_tarball (list[str], optional): List of file paths to back up as tarballs. Defaults to None.
            files_to_backup_as_symlink (list[str], optional): List of file paths to back up as symbolic links. Defaults to None.
            additional_codefiles_to_backup (list[str], optional): List of additional code files to be backed up. Defaults to [].
        Returns:
            None
        """
        backup_codes(
            self.workspace_dir,
            additional_codefiles_to_backup=additional_codefiles_to_backup,
            backup_codes_as_tarball=self.force_backup_codes_as_tarball,
        )
        backup_data(
            workspace_dir=self.workspace_dir,
            files_to_backup=datafiles_to_backup,
            files_to_backup_as_tarball=datafiles_to_backup_as_tarball,
            files_to_backup_as_symlink=datafiles_to_backup_as_symlink,
            append_data_to_existing_tarball=self.append_data_to_existing_tarball,
        )
        # save attributes
        tret_attributes = {
            "backup_timestamp": datetime.datetime.now().timestamp(),
            "metadata": {**metadata},
        }

        json.dump(
            tret_attributes,
            open(self.tret_attributes_filepath, "w", encoding="utf-8"),
            ensure_ascii=False,
            indent=4,
        )
