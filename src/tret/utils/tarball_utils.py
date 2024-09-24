import tarfile


def tar_files(filepaths: list[str], output: str):
    """
    Create a tarball archive from a list of file paths.

    This function takes a list of file paths and creates a tarball archive
    at the specified output location. If the output file name ends with
    ".gz" or ".tgz", the tarball will be compressed using gzip.
    Only support gzip for compression.

    Args:
        filepaths (list[str]): A list of file paths to include in the tarball.
        output (str): The output file path for the tarball. If the file name
                      ends with ".gz" or ".tgz", the tarball will be compressed.

    Returns:
        None

    Notes:
        - Files and directories containing "__pycache__" in their names will
          be excluded from the tarball.
        - The gzip compression level is set to 6 by default if compression is used.
    """
    def _filter_pycaches(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
        return tarinfo if "__pycache__" not in tarinfo.name else None

    compression = output.endswith(".gz") or output.endswith(".tgz")
    mode = "w:gz" if compression else "w"
    kwargs = {"compresslevel": 6} if compression else {}

    with tarfile.open(output, mode, **kwargs) as tar:
        for filepath in filepaths:
            tar.add(filepath, recursive=True, filter=_filter_pycaches)


if __name__ == "__main__":
    import os
    files = ["src/tret/utils/tarball_utils.py", "src/tret/utils/module_detection.py", "src/tret/utils/__pycache__"]
    files = [os.path.abspath(file) for file in files]
    files = [os.path.relpath(file, os.getcwd()) for file in files]
    tar_files(files, "tret_utils.tar.gz")
