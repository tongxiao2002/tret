import os
from git.repo import Repo
from ..utils.module_detection import (
    detect_all_modules,
    generate_requirements_txt,
)
from ..utils.tarball_utils import create_tarball_from_files


def is_git_exists():
    try:
        _ = Repo(os.getcwd())
        return True
    except Exception:
        return False


def backup_codes(workspace_dir: str):
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
    if not is_git_exists():
        # if git does not exist, save all the codes as a tarball.
        # Here, codes are defined as local modules imported by this experiment.
        classified_modules = detect_all_modules()
        external_modules = classified_modules["external_modules"]
        requirements = generate_requirements_txt(external_modules)

        files = [module.__file__ for module in classified_modules['local_modules']]
        working_directory = os.getcwd()
        rel_filepaths = [os.path.relpath(file, working_directory) for file in files]
        requirements_filepath = os.path.join(workspace_dir, "requirements.txt")

        tarball_filepath = os.path.join(workspace_dir, "codes.tar.gz")
        create_tarball_from_files(rel_filepaths, tarball_filepath)
        with open(requirements_filepath, "w", encoding="utf-8") as fout:
            fout.write("\n".join(requirements))
    else:
        # if git exists, save the current commit hash and the diff between current code and commit.
        repo = Repo(os.getcwd())
        commit_hash = repo.head.commit.hexsha
        diff = repo.git.diff(commit_hash)
        git_info_filepath = os.path.join(workspace_dir, "GIT_DIFF_INFO")
        with open(git_info_filepath, "w", encoding="utf-8") as fout:
            fout.write("\n\n".join([commit_hash, diff]))


def restore_codes(workspace_dir: str):
    assert os.path.isdir(workspace_dir), f"{workspace_dir} is not a valid directory."
