import os
import click
from .core import TretWorkspace
from .arguments import TretArguments

RESTORE_OPTION_NAME_DOC = r"""Name of the workspace you want to restore from.
Note that this option is used only when the workspace is stored in the DEFAULT workspace base directory (`tret-workspaces`).
"""

RESTORE_OPTION_DIR_DOC = r"""Directory path of the workspace you want to restore from.
"""

RESTORE_OPTION_CURRENT = r"""If restore codes in `current-codes.tar.gz` from the workspace.
If `--current` flag is set, tret will restore `current-codes.tar.gz`, else restore `codes.tar.gz`.
"""


@click.group(name="tret")
def main_cli():
    pass


@main_cli.command()
@click.option("-n", "--wsname", metavar='WORKSPACE-NAME', help=RESTORE_OPTION_NAME_DOC)
@click.option("-d", "--wsdir", metavar="WORKSPACE-DIR", help=RESTORE_OPTION_DIR_DOC)
@click.option("--current", is_flag=True, help=RESTORE_OPTION_CURRENT)
def restore(wsname: str = None, wsdir: str = None, current: bool = None):
    workspace_name, workspace_dir = wsname, wsdir
    if workspace_name is None and workspace_dir is None:
        click.echo(click.get_current_context().get_help())
        return

    assert not (workspace_name is not None and workspace_dir is not None), "Only one of `-d` or `-n` can be provided."

    if workspace_name is not None:
        arguments = TretArguments(
            workspace_name=workspace_name,
            create_directory=False,
        )
    else:
        arguments = TretArguments(
            workspace_basedir=os.path.dirname(workspace_dir),
            workspace_name=os.path.basename(workspace_dir),
            create_directory=False,
        )
    workspace = TretWorkspace(arguments)

    click.echo(f"Restoring from Workspace {workspace_dir}.", err=True)
    if current:
        workspace.restore_current_codes_from_tarball(remove_after_restore=True)
    else:
        workspace.restore()
