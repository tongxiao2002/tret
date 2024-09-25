import os
from ..utils.tarball_utils import (
    create_tarball_from_files,
)


def backup_data(filepaths: list[str], workspace_dir: str, use_symlinks: bool = True):
    assert os.path.isdir(workspace_dir), f"{workspace_dir} is not a valid directory."
    if use_symlinks:
        symlink_savedir = os.path.join(workspace_dir, "data")
        os.makedirs(symlink_savedir, exist_ok=True)
        for filepath in filepaths:
            os.symlink(
                src=filepath,
                dst=os.path.join(symlink_savedir, os.path.basename(filepath)),
                target_is_directory=os.path.isdir(filepath),
            )
    else:
        tarball_filepath = os.path.join(workspace_dir, "data.tar.gz")
        create_tarball_from_files(filepaths, tarball_filepath)
