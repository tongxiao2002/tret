import os
from git.repo import Repo
from ..constants import (
    REQUIREMENTS_TXT_FILENAME,
    CODES_TARBALL_FILENAME,
    CURRENT_CODES_TARBALL_FILENAME,
    GIT_INFO_DIRNAME,
    GIT_DIFF_INFO_FILENAME,
    GIT_COMMIT_HASH_FILENAME,
)
from ..utils.tarball_utils import (
    create_tarball_from_files,
    restore_files_from_tarball,
)
from ..utils.module_detection import (
    detect_all_modules,
    generate_requirements_txt,
)


def is_git_exists():
    try:
        _ = Repo(os.getcwd())
        return True
    except Exception:
        return False


def backup_codes(workspace_dir: str, backup_codes_as_tarball: bool = False):
    """
    Backs up the current code in the specified workspace directory.

    If a Git repository exists in the current working directory, this function saves the current commit hash
    and the diff between the current code and the commit. If no Git repository is found, it saves all the local
    modules as a tarball and generates a requirements.txt file for the external modules.

    Args:
        workspace_dir (str): The directory where the backup will be stored.

    Raises:
        AssertionError: If the provided workspace_dir is not a valid directory.
    """
    assert os.path.isdir(workspace_dir), f"{workspace_dir} is not a valid directory."
    classified_modules = detect_all_modules()
    external_modules = classified_modules["external_modules"]
    requirements = generate_requirements_txt(external_modules)
    if not is_git_exists() or backup_codes_as_tarball:
        # if git does not exist, backup all the codes as a tarball.
        # Here, codes are defined as local modules imported by this experiment.
        files = [module.__file__ for module in classified_modules['local_modules']]
        working_directory = os.getcwd()
        rel_filepaths = [os.path.relpath(file, working_directory) for file in files]

        requirements_filepath = os.path.join(working_directory, REQUIREMENTS_TXT_FILENAME)
        with open(requirements_filepath, "w", encoding="utf-8") as fout:
            fout.write("\n".join(requirements))
        rel_filepaths += [os.path.relpath(requirements_filepath, working_directory)]

        tarball_filepath = os.path.join(workspace_dir, CODES_TARBALL_FILENAME)
        create_tarball_from_files(rel_filepaths, tarball_filepath)
        os.remove(requirements_filepath)
    else:
        # if git exists, save the current commit hash and the diff between current code and commit.
        requirements_filepath = os.path.join(workspace_dir, REQUIREMENTS_TXT_FILENAME)
        with open(requirements_filepath, "w", encoding="utf-8") as fout:
            fout.write("\n".join(requirements))

        repo = Repo(os.getcwd())
        commit_hash = repo.head.commit.hexsha
        diff = repo.git.diff(commit_hash)
        git_info_dir = os.path.join(workspace_dir, GIT_INFO_DIRNAME)
        os.makedirs(git_info_dir, exist_ok=True)
        git_commit_hash_filepath = os.path.join(git_info_dir, GIT_COMMIT_HASH_FILENAME)
        git_diff_info_filepath = os.path.join(git_info_dir, GIT_DIFF_INFO_FILENAME)
        with open(git_commit_hash_filepath, "w", encoding="utf-8") as fout:
            fout.write(commit_hash)
        with open(git_diff_info_filepath, "w", encoding="utf-8") as fout:
            fout.write(diff)


def restore_codes(workspace_dir: str, keep_requirements_txt: bool = False):
    """
    Restores code files from a specified workspace directory.

    This function handles two scenarios:
    1. If Git is not available:
        - Restores code files from a tarball located in the workspace directory.
        - Optionally removes the `requirements.txt` file.
        - If the workspace directory is the default workspace directory, it restores the current codes and removes the tarball.
        - If the current codes tarball does not exist, it creates one from the current code files for saving.
    2. If Git is available:
        - Checks out to the stored commit.
        - Restores unstaged changes from the diff information.

    Args:
        workspace_dir (str): The directory from which to restore code files.
        keep_requirements_txt (bool, optional): If True, retains the `requirements.txt` file. Defaults to False.

    Raises:
        AssertionError: If the provided workspace directory is not a valid directory.
    """
    git_info_dir = os.path.join(workspace_dir, GIT_INFO_DIRNAME)
    codes_tarball_filepath = os.path.join(workspace_dir, CODES_TARBALL_FILENAME)
    assert os.path.isdir(git_info_dir) or os.path.isfile(codes_tarball_filepath), f"Workspace '{workspace_dir}' corrupted."

    if not is_git_exists() or (not os.path.isdir(git_info_dir) and os.path.isfile(codes_tarball_filepath)):
        # if git does not exist, restore the tarball and requirements.txt
        # firstly backup current codes, then restore from tarball in the workspace.
        # TODO: Find a better place to backup & restore current-codes.tar.gz

        current_codes_tarball_filepath = os.path.join(workspace_dir, CURRENT_CODES_TARBALL_FILENAME)
        if not os.path.isfile(current_codes_tarball_filepath):
            # if current codes tarball does not exist, backup all current codes,
            # on the other hand, if current codes tarball exists, we should not override it.
            classified_modules = detect_all_modules()
            files = [module.__file__ for module in classified_modules['local_modules']]
            working_directory = os.getcwd()
            rel_filepaths = [os.path.relpath(file, working_directory) for file in files]
            create_tarball_from_files(filepaths=rel_filepaths, output=current_codes_tarball_filepath)
            print(
                f"Backup current codes into {current_codes_tarball_filepath}, "
                "you can restore it through `TretWorkspace.restore_current_codes_from_tarball()`."
            )

        restore_files_from_tarball(codes_tarball_filepath, output_dir=os.getcwd())
        if not keep_requirements_txt:
            os.remove(REQUIREMENTS_TXT_FILENAME)
    else:
        # if git exists, checkout to the stored commit,
        # then restore the unstaged changes from diff info.
        git_info_dir = os.path.join(workspace_dir, GIT_INFO_DIRNAME)
        git_commit_hash_filepath = os.path.join(git_info_dir, GIT_COMMIT_HASH_FILENAME)
        git_diff_info_filepath = os.path.join(git_info_dir, GIT_DIFF_INFO_FILENAME)
        with open(git_commit_hash_filepath, "r", encoding="utf-8") as fin:
            commit_hash = fin.read()

        repo = Repo(os.getcwd())
        repo.git.checkout(commit_hash)
        repo.git.execute(["git", "apply", git_diff_info_filepath])
