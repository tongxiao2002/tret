import tarfile


def create_tarball_from_files(filepaths: list[str], output: str, arcpaths: list[str] = None):
    """
    Create a tarball archive from a list of file paths.

    Args:
        filepaths (list[str]): List of file paths to include in the tarball.
        output (str): The output tarball file path. If it ends with ".gz" or ".tgz",
            the tarball will be compressed using gzip.
        arcpaths (list[str], optional): List of archive paths corresponding to the
            file paths. If None, the file paths will be used as archive paths. Defaults to None.

    Returns:
        None

    Notes:
        - Files and directories containing "__pycache__" in their names will be excluded from the tarball.
        - Compression level for gzip is set to 6 by default.
    """
    def _filter_pycaches(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
        return tarinfo if "__pycache__" not in tarinfo.name else None

    compression = output.endswith(".gz") or output.endswith(".tgz")
    mode = "w:gz" if compression else "w"
    kwargs = {"compresslevel": 6} if compression else {}

    if arcpaths is None:
        arcpaths = [None] * len(filepaths)
    with tarfile.open(output, mode, **kwargs) as tar:
        for filepath, arcpath in zip(filepaths, arcpaths):
            tar.add(name=filepath, arcname=arcpath, recursive=True, filter=_filter_pycaches)


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


if __name__ == "__main__":
    import os
    files = ["src/tret/utils/tarball_utils.py", "src/tret/utils/module_detection.py", "src/tret/utils/__pycache__"]
    files = [os.path.abspath(file) for file in files]
    files = [os.path.relpath(file, os.getcwd()) for file in files]
    create_tarball_from_files(files, "tret_utils.tar.gz")
