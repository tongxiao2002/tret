import types
import inspect
import argparse
import dataclasses
from copy import copy
from enum import Enum
from typing import Callable, Any, Union, Literal, Optional
from .constants import DEFAULT_WORKSPACE_DIR


@dataclasses.dataclass
class TretArguments:
    # workspace path arguments
    workspace_basedir: str = dataclasses.field(
        default=DEFAULT_WORKSPACE_DIR,
        metadata={"help": f"The base directory for the workspace. Defaults to '{DEFAULT_WORKSPACE_DIR}'."},
    )
    workspace_name: str = dataclasses.field(
        default=None,
        metadata={"help": "The name of current workspace. Defaults to current datetime."},
    )
    create_directory: bool = dataclasses.field(
        default=True,
        metadata={"help": "Whether to create workspace directory if not exists. Defaults to 'True'."},
    )

    # codes backup & restore arguments
    force_backup_codes_as_tarball: bool = dataclasses.field(
        default=False,
        metadata={"help": "Whether to forcely backup codes as a tarball regardless the existence of git. Defaults to 'False'."},
    )

    # data backup arguments
    append_data_to_existing_tarball: bool = dataclasses.field(
        default=True,
        metadata={"help": "If data tarball e.g, `data.tar.gz` already exists, "
                  "whether to append new data to this tarball, or just overwrite it."}
    )
