# Totally Reproducible ExperimenTs (Tret)
⚠️ **This repository is still in development, and some modules have not been fully tested. Please use Tret with caution.** ⚠️

## Overview

Totally Reproducible ExperimenTs (Tret) is a **pure-python** tool that ensures the reproducibility of your experiments by automatically backing up and restoring your data, outputs, codes and dependencies for each experiment setup.

⚠️ **Before using Tret, I highly recommend reading the [Mechanism](#mechanism) section to avoid any potential misunderstandings.** ⚠️

## Installation

Clone this repository:

```shell
git clone https://github.com/tongxiao2002/tret
```

Then install from source:

```shell
cd tret
pip3 install .
```

## Usage

You can incorporate Tret into your project through just lines of code:

For backing up data and codes:

```python
import os
from tret import TretArguments, TretWorkspace

arguments = TretArguments(
    workspace_name=your_workspace_name,
)
workspace = TretWorkspace(arguments)

# Tret does not force the output results to a specified workspace.
# However, I strongly recommend that users manually change their output path to the workspace as shown below.
# This helps maintain better consistency between the codes and output results.
output_basedir = os.path.join(workspace.workspace_dir, your_output_basedir)

##### your codes #####

# Finally backup the codes and data to the workspace, the codes will be backed up automatically.
workspace.backup(
    datafiles_to_backup,                # the data to be backed up as regular files or directories.
    datafiles_to_backup_as_tarball,     # the data to be backed up as tarball, i.e., they well be compressed.
    datafiles_to_backup_as_symlink,     # the data to be backed up as symbolic links.
)
```

For restoring codes (Tret does not support restoring data since it's a complex and dangerous behavior, you can do it by yourself.😊):

```python
from tret import TretArguments, TretWorkspace

arguments = TretArguments(
    workspace_name=your_workspace_name,
)
workspace = TretWorkspace(arguments)
workspace.restore()
```

In the future, I plan to support command-line interfaces for more convenient restorage.

## Mechanism<a id="mechanism"></a>

### 🧐How does Tret backup your codes?
Firstly, Tret will detect all python modules you used in your program, then it will classify them into `built-in modules`, `local modules` and `external modules`. The only modules which need to be backed up are `local modules`, since `built-in modules` are bound python itself and `external modules` can be dumped into `requirements.txt`.

If you have initialized a git repository in your project, Tret will simply record current commit hash and backup all the unstaged changes (through `git-diff`) into the workspace.

Else Tret will pack all the `local modules` into a tarball (typically named `codes.tar.gz`) and save it in the workspace.

So you may have noticed that **Tret will only automatically backup python modules that will be used in your program**. For non-python code files, such as shell scripts that trigger python programs, Tret provides an interface to back them up into the tarball as well:

```python
from tret import TretArguments, TretWorkspace

arguments = TretArguments(
    workspace_name=your_workspace_name,
)
workspace = TretWorkspace(arguments)

##### your codes #####

workspace.backup(
    additional_codefiles_to_backup,     # you can list your non-python code files here for backing up
)
```

So if your project is not mainly written in python, maybe Tret is not the best choice for you.

### 🧐How does Tret backup your data?
Actually, Tret provides 3 choices for backing up your data:
- Directly backs up your data through copying.
- Backs up your data as symbolic links, which points to the original data files or directories.
- Backs up your data through copying, and then pack them into a tarball.

There is no default options, you must choose one of them for backing up your data, or Tret will not back up them automatically.

Note that when backing up data as symbolic links, the data may become outdated if the original files are modified. In such cases, Tret will issue a warning in the terminal when you attempt to restore from that workspace.

### 🧐How does Tret backup your outputs?
No, Tret does not require users to store their outputs in specific workspaces. You are free to place them wherever you want.

However, I strongly recommend manually setting the output path to the workspace. This helps maintain better consistency between your codes and output results, which is the core purpose of Tret’s development.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss any changes.

## License

This project is licensed under the GPLv3 License. See the [`LICENSE`](./LICENSE) file for details.

**If Tret helps you, please give my repo a star⭐️!**
