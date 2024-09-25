from dataclasses import (
    dataclass,
    field,
    fields,
)
from .constants import DEFAULT_WORKSPACE_DIR


@dataclass
class TretArguments:
    # workspace path arguments
    workspace_basedir: str = field(
        default=DEFAULT_WORKSPACE_DIR,
        metadata={"help": f"The base directory for the workspace. Defaults to '{DEFAULT_WORKSPACE_DIR}'."},
    )
    workspace_name: str = field(
        default=None,
        metadata={"help": "The name of current workspace. Defaults to current datetime."},
    )

    # codes backup & restore arguments
    force_backup_codes_as_tarball: bool = field(
        default=False,
        metadata={"help": "Whether to forcely backup codes as a tarball regardless the existence of git. Defaults to 'False'."},
    )

    # data backup arguments
    backup_data_as_symlinks: bool = field(
        default=True,
        metadata={"help": "Whether backup data as symlinks, defaults to 'True'."}
    )
