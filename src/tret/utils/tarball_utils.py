import os
import tarfile


def create_tarball_from_files(
    filepaths: list[str],
    output: str,
    arcpaths: list[str] = None,
    append_data_to_existing_tarball: bool = True
):
    """
    Create a tarball from a list of files.

    Args:
        filepaths (list[str]): List of file paths to include in the tarball.
        output (str): The output tarball file path.
        arcpaths (list[str], optional): List of archive paths for the files inside the tarball. Defaults to None.
        append_data_to_existing_tarball (bool, optional): If True, append data to an existing tarball if it exists. Defaults to True.

    Returns:
        None
    """
    def _filter_pycaches(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
        return tarinfo if "__pycache__" not in tarinfo.name else None

    compression = output.endswith(".gz") or output.endswith(".tgz")
    mode = "w:gz" if compression else "w"
    kwargs = {"compresslevel": 6} if compression else {}

    if arcpaths is None:
        arcpaths = [None] * len(filepaths)

    if not os.path.isfile(output) or not append_data_to_existing_tarball:
        with tarfile.open(output, mode, **kwargs) as tar:
            for filepath, arcpath in zip(filepaths, arcpaths):
                tar.add(name=filepath, arcname=arcpath, recursive=True, filter=_filter_pycaches)
    else:
        # append new data to existing tarball
        filename = os.path.basename(output)
        old_tarball_filepath = os.path.join(os.path.dirname(output), f"old-{filename}")
        os.replace(output, old_tarball_filepath)
        with tarfile.open(output, mode, **kwargs) as tar:
            with tarfile.open(old_tarball_filepath, "r") as old_tar:
                for member in old_tar.getmembers():
                    tar.addfile(member, old_tar.extractfile(member))

            for filepath, arcpath in zip(filepaths, arcpaths):
                tar.add(name=filepath, arcname=arcpath, recursive=True, filter=_filter_pycaches)
        os.remove(old_tarball_filepath)


def restore_files_from_tarball(tarball_path: str, output_dir: str):
    """
    Restore files from a tarball archive.

    Args:
        tarball_path (str): The path to the tarball archive.
        output_dir (str): The directory where the files will be extracted.

    Returns:
        None
    """
    with tarfile.open(tarball_path, "r:gz") as tar:
        tar.extractall(path=output_dir)
