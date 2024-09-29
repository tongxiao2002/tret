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


def string_to_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError(
            f"Truthy value expected: got {v} but expected one of yes/no, true/false, t/f, y/n, 1/0 (case insensitive)."
        )


def make_choice_type_function(choices: list) -> Callable[[str], Any]:
    """
    Creates a mapping function from each choices string representation to the actual value. Used to support multiple
    value types for a single argument.

    Args:
        choices (list): List of choices.

    Returns:
        Callable[[str], Any]: Mapping function from string representation to actual value for each choice.
    """
    str_to_choice = {str(choice): choice for choice in choices}
    return lambda arg: str_to_choice.get(arg, arg)


def _parse_dataclass_field(parser: argparse.ArgumentParser, field: dataclasses.Field):
    """excerpt from transformers.HfArgumentParser
    """
    field_name = f"--{field.name}"
    kwargs = field.metadata.copy()
    # field.metadata is not used at all by Data Classes,
    # it is provided as a third-party extension mechanism.
    if isinstance(field.type, str):
        raise RuntimeError(
            "Unresolved type detected, which should have been done with the help of "
            "`typing.get_type_hints` method by default"
        )
    aliases = kwargs.pop("aliases", [])

    if isinstance(aliases, str):
        aliases = [aliases]
    origin_type = getattr(field.type, "__origin__", field.type)

    if origin_type is Union or (hasattr(types, "UnionType") and isinstance(origin_type, types.UnionType)):
        if str not in field.type.__args__ and (
            len(field.type.__args__) != 2 or type(None) not in field.type.__args__
        ):
            raise ValueError(
                "Only `Union[X, NoneType]` (i.e., `Optional[X]`) is allowed for `Union` because"
                " the argument parser only supports one type per argument."
                f" Problem encountered in field '{field.name}'."
            )
        if type(None) not in field.type.__args__:
            # filter `str` in Union
            field.type = field.type.__args__[0] if field.type.__args__[1] == str else field.type.__args__[1]
            origin_type = getattr(field.type, "__origin__", field.type)
        elif bool not in field.type.__args__:
            # filter `NoneType` in Union (except for `Union[bool, NoneType]`)
            field.type = (
                field.type.__args__[0] if isinstance(None, field.type.__args__[1]) else field.type.__args__[1]
            )
            origin_type = getattr(field.type, "__origin__", field.type)

    # A variable to store kwargs for a boolean field, if needed
    # so that we can init a `no_*` complement argument (see below)
    bool_kwargs = {}
    if origin_type is Literal or (isinstance(field.type, type) and issubclass(field.type, Enum)):
        if origin_type is Literal:
            kwargs["choices"] = field.type.__args__
        else:
            kwargs["choices"] = [x.value for x in field.type]
        kwargs["type"] = make_choice_type_function(kwargs["choices"])
        if field.default is not dataclasses.MISSING:
            kwargs["default"] = field.default
        else:
            kwargs["required"] = True

    elif field.type is bool or field.type == Optional[bool]:
        # Copy the currect kwargs to use to instantiate a `no_*` complement argument below.
        # We do not initialize it here because the `no_*` alternative must be instantiated after the real argument
        bool_kwargs = copy(kwargs)
        # Hack because type=bool in argparse does not behave as we want.
        kwargs["type"] = string_to_bool
        if field.type is bool or (field.default is not None and field.default is not dataclasses.MISSING):
            # Default value is False if we have no default when of type bool.
            default = False if field.default is dataclasses.MISSING else field.default
            # This is the value that will get picked if we don't include --field_name in any way
            kwargs["default"] = default
            # This tells argparse we accept 0 or 1 value after --field_name
            kwargs["nargs"] = "?"
            # This is the value that will get picked if we do --field_name (without value)
            kwargs["const"] = True

    elif inspect.isclass(origin_type) and issubclass(origin_type, list):
        kwargs["type"] = field.type.__args__[0]
        kwargs["nargs"] = "+"
        if field.default_factory is not dataclasses.MISSING:
            kwargs["default"] = field.default_factory()
        elif field.default is dataclasses.MISSING:
            kwargs["required"] = True

    else:
        kwargs["type"] = field.type
        if field.default is not dataclasses.MISSING:
            kwargs["default"] = field.default
        elif field.default_factory is not dataclasses.MISSING:
            kwargs["default"] = field.default_factory()
        else:
            kwargs["required"] = True
    parser.add_argument(field_name, *aliases, **kwargs)

    # Add a complement `no_*` argument for a boolean field AFTER the initial field has already been added.
    # Order is important for arguments with the same destination!
    # We use a copy of earlier kwargs because the original kwargs have changed a lot before reaching down
    # here and we do not need those changes/additional keys.
    if field.default is True and (field.type is bool or field.type == Optional[bool]):
        bool_kwargs["default"] = False
        parser.add_argument(f"--no_{field.name}", action="store_false", dest=field.name, **bool_kwargs)


def parse_args(cfg_file: str = None) -> TretArguments:
    if cfg_file is not None:
        if cfg_file.lower().endswith(".yaml") or cfg_file.lower().endswith(".yml"):
            import yaml
            arguments = TretArguments(
                **yaml.full_load(open(cfg_file, "r", encoding="utf-8"))
            )
        elif cfg_file.lower().endswith(".json"):
            import json
            arguments = TretArguments(
                **json.load(open(cfg_file, "r", encoding="utf-8"))
            )
        else:
            raise ValueError("'cfg_file' should only be YAML file or JSON file.")
        return arguments
    else:
        parser = argparse.ArgumentParser(description="llm-api-access argument parser")
        for field in dataclasses.fields(TretArguments):
            _parse_dataclass_field(parser=parser, field=field)
        args = parser.parse_args()
        arguments = TretArguments(
            **vars(args)
        )
        return arguments
