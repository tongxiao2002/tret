import os
from git.repo import Repo
from ..constants import DEFAULT_WORKSPACE_DIR
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
        # if git does not exist, save all the codes as a tarball.
        # Here, codes are defined as local modules imported by this experiment.
        files = [module.__file__ for module in classified_modules['local_modules']]
        working_directory = os.getcwd()
        rel_filepaths = [os.path.relpath(file, working_directory) for file in files]

        requirements_filepath = os.path.join(working_directory, "requirements.txt")
        with open(requirements_filepath, "w", encoding="utf-8") as fout:
            fout.write("\n".join(requirements))
        rel_filepaths += [os.path.relpath(requirements_filepath, working_directory)]

        tarball_filepath = os.path.join(workspace_dir, "codes.tar.gz")
        create_tarball_from_files(rel_filepaths, tarball_filepath)
        os.remove(requirements_filepath)
    else:
        # if git exists, save the current commit hash and the diff between current code and commit.
        requirements_filepath = os.path.join(workspace_dir, "requirements.txt")
        with open(requirements_filepath, "w", encoding="utf-8") as fout:
            fout.write("\n".join(requirements))

        repo = Repo(os.getcwd())
        commit_hash = repo.head.commit.hexsha
        diff = repo.git.diff(commit_hash)
        git_info_dir = os.path.join(workspace_dir, ".gitinfo")
        os.makedirs(git_info_dir, exist_ok=True)
        git_commit_hash_filepath = os.path.join(git_info_dir, "GIT_COMMIT_HASH")
        git_diff_info_filepath = os.path.join(git_info_dir, "GIT_DIFF_INFO")
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
    assert os.path.isdir(workspace_dir), f"{workspace_dir} is not a valid directory."
    if not is_git_exists():
        # if git does not exist, restore the tarball and requirements.txt
        # firstly save current codes, then restore from tarball in the workspace.
        current_codes_tarball_filepath = os.path.join(DEFAULT_WORKSPACE_DIR, "current-codes.tar.gz")
        if workspace_dir == DEFAULT_WORKSPACE_DIR:
            # if workspace_dir is the same as the base directory,
            # restore the current codes then remove the tarball.
            restore_files_from_tarball(current_codes_tarball_filepath, output_dir=os.getcwd())
            if not keep_requirements_txt:
                os.remove("requirements.txt")
            os.remove(current_codes_tarball_filepath)
            return
        elif not os.path.isfile(current_codes_tarball_filepath):
            # if current codes tarball does not exist, save all current codes,
            # on the other hand, if current codes tarball exists, we should not override it.
            classified_modules = detect_all_modules()
            files = [module.__file__ for module in classified_modules['local_modules']]
            working_directory = os.getcwd()
            rel_filepaths = [os.path.relpath(file, working_directory) for file in files]
            create_tarball_from_files(filepaths=rel_filepaths, output=current_codes_tarball_filepath)

        tarball_filepath = os.path.join(workspace_dir, "codes.tar.gz")
        restore_files_from_tarball(tarball_filepath, output_dir=os.getcwd())
        if not keep_requirements_txt:
            os.remove("requirements.txt")
    else:
        # if git exists, checkout to the stored commit,
        # then restore the unstaged changes from diff info.
        git_info_dir = os.path.join(workspace_dir, ".gitinfo")
        git_commit_hash_filepath = os.path.join(git_info_dir, "GIT_COMMIT_HASH")
        git_diff_info_filepath = os.path.join(git_info_dir, "GIT_DIFF_INFO")
        with open(git_commit_hash_filepath, "r", encoding="utf-8") as fin:
            commit_hash = fin.read()

        repo = Repo(os.getcwd())
        repo.git.checkout(commit_hash)
        repo.git.execute(["git", "apply", git_diff_info_filepath])
