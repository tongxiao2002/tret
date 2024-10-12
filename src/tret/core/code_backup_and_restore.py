import os
import json
import tempfile
from git.repo import Repo
from ..constants import (
    REQUIREMENTS_TXT_FILENAME,
    CODES_TARBALL_FILENAME,
    CURRENT_CODES_TARBALL_FILENAME,
    GIT_INFO_FILENAME,
    GIT_REPO_PATH_KEYNAME,
    GIT_DIFF_INFO_KEYNAME,
    GIT_COMMIT_HASH_KEYNAME,
)
from ..utils.tarball_utils import (
    create_tarball_from_files,
    restore_files_from_tarball,
    get_filepaths_in_tarball,
)
from ..utils.module_detection import (
    detect_all_modules,
    generate_requirements_txt,
)


def get_git_repo_path(path: str):
    """
    Recursively finds the path to the root of a Git repository starting from the given path until reaching current working directory.

    Args:
        path (str): The starting path to search for the Git repository.

    Returns:
        str: The path to the Git repository if found, otherwise None.
    """
    working_directory = os.getcwd()
    try:
        _ = Repo(path)
        return path
    except Exception:
        dirname = os.path.basename(path)
        # if working directory is inside `dirname`, it means there does not exist any git repository inside the workspace directory.
        if dirname != working_directory and working_directory.startswith(dirname):
            return None
        else:
            return get_git_repo_path(os.path.dirname(path))


def _start_point_for_finding_git_repo(workspace_dir: str):
    working_directory = os.getcwd()
    if os.path.abspath(workspace_dir).startswith(working_directory):
        return os.path.abspath(workspace_dir)
    else:
        return working_directory


def backup_codes(
    workspace_dir: str,
    additional_codefiles_to_backup: list[str] = [],
    backup_codes_as_tarball: bool = False,
):
    """
    Backs up code files from the current workspace.

    This function detects all modules in the current workspace, generates a requirements.txt file for external modules,
    and backs up code files either as a tarball or using Git,
    depending on the presence of a Git repository and the `backup_codes_as_tarball` flag.

    Args:
        workspace_dir (str): The directory where the backup files will be stored.
        additional_codefiles_to_backup (list[str], optional): Additional code files to include in the backup. Defaults to [].
        backup_codes_as_tarball (bool, optional): If True, backs up all code files as a tarball regardless of Git presence. Defaults to False.

    Raises:
        FileNotFoundError: If any of the specified code files do not exist.
        OSError: If there is an error creating or writing to the backup files.

    Returns:
        None
    """
    working_directory = os.getcwd()
    classified_modules = detect_all_modules()
    external_modules = classified_modules["external_modules"]
    requirements = generate_requirements_txt(external_modules)

    start_point = _start_point_for_finding_git_repo(workspace_dir)
    git_repo_path = get_git_repo_path(start_point)

    all_codesfiles_backup = additional_codefiles_to_backup + [module.__file__ for module in classified_modules['local_modules']]
    all_codesfiles_backup = [os.path.abspath(file) for file in all_codesfiles_backup]
    # deduplication
    all_codesfiles_backup = list(set(all_codesfiles_backup))
    if not git_repo_path or backup_codes_as_tarball:
        # if git does not exist, backup all the codes as a tarball.
        # Here, codes are defined as local modules imported by this experiment and user-defined additional codefiles.
        rel_filepaths = [os.path.relpath(file, working_directory) for file in all_codesfiles_backup]

        requirements_filepath = os.path.join(working_directory, REQUIREMENTS_TXT_FILENAME)
        with open(requirements_filepath, "w", encoding="utf-8") as fout:
            fout.write("\n".join(requirements))
        rel_filepaths += [os.path.relpath(requirements_filepath, working_directory)]

        codes_tarball_filepath = os.path.join(workspace_dir, CODES_TARBALL_FILENAME)
        create_tarball_from_files(
            filepaths=rel_filepaths,
            output=codes_tarball_filepath,
            append_data_to_existing_tarball=False,
        )
        os.remove(requirements_filepath)
    else:
        def _get_gitrepo_tracked_files(repo: Repo):
            tracked_files = []
            for key in repo.index.entries.keys():
                tracked_files.append(key[0])
            return tracked_files

        # if git exists, save the current commit hash and the diff between current code and commit.
        requirements_filepath = os.path.join(workspace_dir, REQUIREMENTS_TXT_FILENAME)
        with open(requirements_filepath, "w", encoding="utf-8") as fout:
            fout.write("\n".join(requirements))

        repo = Repo(git_repo_path)
        # get not tracked codefiles, which will be backed up as a tarball
        git_tracked_files = _get_gitrepo_tracked_files(repo)
        git_tracked_files = [os.path.abspath(file) for file in git_tracked_files]
        git_not_tracked_codefiles = [
            os.path.relpath(item, working_directory)
            for item in all_codesfiles_backup if item not in git_tracked_files
        ]
        if len(git_not_tracked_codefiles) > 0:
            codes_tarball_filepath = os.path.join(workspace_dir, CODES_TARBALL_FILENAME)
            create_tarball_from_files(
                filepaths=git_not_tracked_codefiles,
                output=codes_tarball_filepath,
                append_data_to_existing_tarball=False,
            )

        # for git-tracked files, just backup current git commit hash and diff-results for restorage
        commit_hash = repo.head.commit.hexsha
        diff = repo.git.diff(commit_hash)
        git_info_filepath = os.path.join(workspace_dir, GIT_INFO_FILENAME)
        gitinfo = {
            GIT_REPO_PATH_KEYNAME: repo.git_dir,
            GIT_COMMIT_HASH_KEYNAME: commit_hash,
            GIT_DIFF_INFO_KEYNAME: diff,
        }
        json.dump(
            gitinfo,
            open(git_info_filepath, "w", encoding="utf-8"),
            ensure_ascii=False,
            indent=4,
        )


def restore_codes(workspace_dir: str):
    """
    Restores the code files in the specified workspace directory.

    This function performs the following steps:
    1. Checks if the workspace directory contains either a git information directory or a code tarball file.
    2. If a code tarball file exists, backs up the current codes to another tarball `current-codes.tar.gz`.
    3. Restores codes tracked by git by checking out to the stored commit and applying unstaged changes from diff info.
    4. Restores codes from the tarball, potentially overwriting git-tracked codes.

    Args:
        workspace_dir (str): The path to the workspace directory.

    Raises:
        AssertionError: If neither the git information directory nor the code tarball file exists in the workspace directory.
    """
    working_directory = os.getcwd()
    git_info_filepath = os.path.join(workspace_dir, GIT_INFO_FILENAME)
    codes_tarball_filepath = os.path.join(workspace_dir, CODES_TARBALL_FILENAME)
    assert os.path.isfile(git_info_filepath) or os.path.isfile(codes_tarball_filepath), \
        f"Codes in Workspace '{workspace_dir}' have corrupted."

    if os.path.isfile(codes_tarball_filepath):
        # if there are codes in the codes.tar.gz, which means these codes are not tracked by git,
        # we need to backup them to another tarball `current-codes.tar.gz` first.
        current_codes_tarball_filepath = os.path.join(workspace_dir, CURRENT_CODES_TARBALL_FILENAME)
        if not os.path.isfile(current_codes_tarball_filepath):
            filepaths_in_codes_tarball = get_filepaths_in_tarball(codes_tarball_filepath)
            filepaths_in_codes_tarball = [filepath for filepath in filepaths_in_codes_tarball if os.path.exists(filepath)]
            create_tarball_from_files(
                filepaths=filepaths_in_codes_tarball,
                output=current_codes_tarball_filepath,
                append_data_to_existing_tarball=False,
            )
            print(
                f"Backup current codes into {current_codes_tarball_filepath}, "
                "you can restore it through `TretWorkspace.restore_current_codes_from_tarball()`."
            )

    # we first restore codes which can be restore through git,
    # then restore codes that are stored in the tarball.
    # That's because there may be some duplication between git tracked codes and codes in the tarball.
    # In the case of git tracked codes can be restored easier and are not afraid of overwriting,
    # we firstly restore the codes from git, then restore the codes from tarball which may overwrite the codes from git.
    if os.path.isfile(git_info_filepath):
        # if git exists, checkout to the stored commit,
        # then restore the unstaged changes from diff info.
        gitinfo = json.load(open(git_info_filepath, "r", encoding="utf-8"))
        commit_hash = gitinfo[GIT_COMMIT_HASH_KEYNAME]

        repo = Repo(gitinfo[GIT_REPO_PATH_KEYNAME])
        repo.git.checkout(commit_hash)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix="git-diff-info") as fout:
            fout.write(gitinfo[GIT_DIFF_INFO_KEYNAME])
            fout.flush()
            repo.git.apply(fout.name, allow_empty=True)

    if os.path.isfile(codes_tarball_filepath):
        restore_files_from_tarball(codes_tarball_filepath, output_dir=working_directory)
        requirements_filepath = os.path.join(working_directory, REQUIREMENTS_TXT_FILENAME)
        if os.path.isfile(requirements_filepath):
            os.remove(requirements_filepath)
