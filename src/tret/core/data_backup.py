import os
import shutil
from ..utils.tarball_utils import (
    create_tarball_from_files,
)


def backup_data(
    workspace_dir: str,
    files_to_backup: list[str] = None,
    files_to_backup_as_tarball: list[str] = None,
    files_to_backup_as_symlink: list[str] = None,
):
    """
    Backs up specified files and directories from the workspace to a backup directory.

    Args:
        workspace_dir (str): The directory where the backup will be stored.
        files_to_backup (list[str], optional): List of file or directory paths to copy to the backup directory.
        files_to_backup_as_tarball (list[str], optional): List of file or directory paths to include in a tarball.
        files_to_backup_as_symlink (list[str], optional): List of file or directory paths to create symbolic links for in the backup directory.

    Raises:
        FileNotFoundError: If any path is not a file or directory.
    """
    data_backup_dir = os.path.join(workspace_dir, "data")
    if files_to_backup:
        os.makedirs(data_backup_dir, exist_ok=True)
        for filepath in files_to_backup:
            src = filepath
            dst = os.path.join(data_backup_dir, os.path.basename(src))
            if os.path.isdir(filepath):
                shutil.copytree(
                    src=src,
                    dst=dst,
                )
            elif os.path.isfile(filepath) or os.path.islink(filepath):
                shutil.copyfile(
                    src=src,
                    dst=dst,
                    follow_symlinks=False,
                )
            else:
                raise FileNotFoundError(f"'{src}' is not a file or directory, cannot be copied.")

    if files_to_backup_as_symlink:
        symlink_savedir = os.path.join(data_backup_dir, "symlinks")
        os.makedirs(symlink_savedir, exist_ok=True)
        for filepath in files_to_backup_as_symlink:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"'{filepath}' does not exists.")

            os.symlink(
                src=filepath,
                dst=os.path.join(symlink_savedir, os.path.basename(filepath)),
                target_is_directory=os.path.isdir(filepath),
            )

    if files_to_backup_as_tarball:
        for filepath in files_to_backup_as_tarball:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"'{filepath}' does not exists.")

        os.makedirs(data_backup_dir, exist_ok=True)
        data_tarball_filepath = os.path.join(data_backup_dir, "data.tar.gz")
        create_tarball_from_files(files_to_backup_as_tarball, data_tarball_filepath)
