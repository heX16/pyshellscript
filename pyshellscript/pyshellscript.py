# coding: utf-8
# about: Library for shell scripting in Python
# author: heX
# url: https://github.com/heX16

import os
import sys
import io
import shutil
import subprocess
import platform
import re
import stat
import typing
from pathlib import Path
from time import sleep
from datetime import datetime, time, date, timedelta
from subprocess import CompletedProcess, Popen
from typing import Any, Callable, Dict, Set, List, Optional, Union, Iterable

try:
    import psutil  # pip install psutil
except ImportError:
    psutil = None


# Base ################################################################

def pyshellscript_version():
    return '0.3.3'


# Global variable ################################################################

# Error code after function call `run_command` or `sh`.
# This variable is used after invoking `run_command` or `sh`.
returncode = None


# OS ################################################################


def get_current_script_name() -> Path:
    """
    Get the name of the current script file with extension.
    """
    # Note: Using `sys.argv[0]` instead of `__file__`
    #   for better compatibility with command-line execution
    return Path(os.path.basename(sys.argv[0]))


def is_wnd() -> bool:
    """Check if the operating system is Windows."""
    return platform.system().lower() == 'windows'


def is_linux() -> bool:
    """Check if the operating system is Linux."""
    return platform.system().lower() == 'linux'


def _get_wnd_version() -> str:
    """Retrieve the Windows version."""
    if not is_wnd():
        raise RuntimeError("Not running on Windows.")
    return platform.version()


def _get_wnd_name() -> str:
    if not is_wnd():
        raise RuntimeError("Not running on Windows.")

    version = platform.version()
    release = platform.release()
    # Attempt to directly use the release for well-known names
    if release in ["XP", "7", "8", "10", "Vista"]:
        return "Windows " + release

    # For Windows 10 and later, platform.release() returns '10', but we might want to distinguish between 10 and 11+
    # This requires more sophisticated checking, potentially using registry or other version-specific methods,
    # which are not straightforward with platform.version() or platform.release() alone.

    # Starting with Windows 10, Microsoft moved to a more service-oriented versioning scheme,
    # making it harder to distinguish between major versions like Windows 10 and Windows 11
    # purely based on the version number returned by platform.version().
    # The version numbers returned can vary significantly based on updates.

    # A simple approach for demonstration purposes:
    # Use a regex match to look for specific version patterns in the detailed version number.
    # This is a basic and not future-proof method.
    version_match = re.search(r"10\.0\.(\d+)", version)
    if version_match:
        build_number = int(version_match.group(1))
        if build_number >= 22000:  # This is an approximation for Windows 11 initial builds.
            return "Windows 11"
        return "Windows 10"

    # Fallback if none of the above conditions are met
    return f"Windows (Unknown Version: {version})"


def _get_linux_kernel_version() -> str:
    """Retrieve the Linux kernel version using a shell command."""
    if not is_linux():
        raise RuntimeError("Not running on Linux.")
    r = sh("uname -r", capture_output=True)
    return r.stdout.strip()


def _get_linux_distributive_name() -> str:
    """Retrieve the name of the Linux distribution using a shell command."""
    if not is_linux():
        raise RuntimeError("Not running on Linux.")
    # This command attempts to read the distribution name from various standard files
    r = sh("cat /etc/*release | grep PRETTY_NAME | cut -d '=' -f2", capture_output=True)
    distrib_name = r.stdout.strip().strip('"')
    return distrib_name if distrib_name else "Linux Distribution Name Unknown"


def get_os_version() -> str:
    """
    Retrieve the version of the operating system.
    """
    if is_wnd():
        return _get_wnd_version()
    elif is_linux():
        return _get_linux_kernel_version()
    else:
        return "Unsupported operating system."


def get_os_name() -> str:
    """
    Retrieve the name of the operating system.
    """
    if is_wnd():
        return _get_wnd_name()
    elif is_linux():
        return _get_linux_distributive_name()
    else:
        return "Unknown operating system."


# Files data ################################################################

def get_file_content(file_name: str | Path, encoding='utf-8', ignore_io_error=False) -> str:
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_name (str | Path): The name or path of the file to read.
        encoding (str): The encoding to use when reading the file. Defaults to 'utf-8'.
        ignore_io_error (bool): If True, returns an empty string on IOError. Defaults to False.

    Returns:
        str: The content of the file, or an empty string if an IOError occurs and ignore_io_error is True.

    Note:
        If the file is too large, calling this function will consume a lot of memory.
    """
    try:
        with open(file_name, 'r', encoding=encoding) as f:
            return str(f.read())
    except IOError:
        if ignore_io_error:
            return ''
        else:
            raise


def save_file_content(file_name: str | Path, content: str | List[str] | Iterable[str], encoding='utf-8', ignore_io_error=False) -> None:
    """
    Saves the given content to a file.

    Args:
        file_name (str | Path): The name or path of the file to write to.
        content (str | Iterable[str]): The content to write into the file. Can be a string or a list of strings.
        encoding (str): The encoding to use when writing to the file. Defaults to 'utf-8'.
        ignore_io_error (bool): If True, suppresses IOError. Defaults to False.

    Raises:
        IOError: If there is an error writing to the file and ignore_io_error is False.
        ValueError: If the content is not of type str or list[str].

    Returns:
        None
    """
    try:
        with open(file_name, 'w', encoding=encoding) as f:
            if isinstance(content, str):
                f.write(content)
            elif isinstance(content, Iterable):
                f.writelines(content)
            else:
                raise TypeError("Content must be a string or a list of strings.")
    except IOError:
        if not ignore_io_error:
            raise


def split_file(file_path: Path | str, chunk_size, remove_on_failure=True):
    """
    Splits a file into multiple chunks of equal size (except for the last chunk).

    Parameters:
    file_path (Path): Path to the input file.
    chunk_size (int): Size of each chunk in bytes.
    remove_on_failure (bool): If True, removes created chunks if an error occurs. Default is True.

    Returns:
    bool: True if the operation is successful, False if an error occurs.

    See Also:
        split_file, combine_files, split_files_get_list, file_list_calc_total_size

    Example:
        ```
        success = split_file(Path('test.txt'), 10000)
        if success:
            print("File successfully split into chunks.")
        else:
            print("An error occurred while splitting the file.")
        ```
    """
    file_path = Path(file_path)
    block_size = 64 * 1024  # 64 KB
    created_files = []
    try:
        with file_path.open('rb') as file:
            chunk_num = 1
            while True:
                chunk_file_name = file_path.with_suffix(f".{chunk_num:03d}")
                created_files.append(chunk_file_name)
                with chunk_file_name.open('wb') as chunk_file:
                    remaining_size = chunk_size
                    while remaining_size > 0:
                        block = file.read(min(block_size, remaining_size))
                        if not block:
                            break
                        chunk_file.write(block)
                        remaining_size -= len(block)
                    if remaining_size > 0:
                        break
                chunk_num += 1
        return True
    except IOError:
        if remove_on_failure:
            for file_name in created_files:
                try:
                    file_name.unlink()
                except OSError:
                    pass
        return False


def combine_files(output_file_path: Path, chunk_files: List[Path]) -> bool:
    """
    Combines chunk files into a single output file.

    Parameters:
    output_file_path (Path): Path to the output file.
    chunk_files (List[Path]): List of Path objects representing the chunk files.

    Returns:
    bool: True if the operation is successful, False if an error occurs.

    See Also:
        split_file, combine_files, split_files_get_list, file_list_calc_total_size

    Example usage:
    >>> from pathlib import Path
    >>> files = [Path('file.txt.001'), Path('file.txt.002'), Path('file.txt.003'), Path('file.txt.004')]
    >>> success = combine_files(Path('combined_file.txt'), files)
    >>> if success:
    >>>     print("Files successfully combined into one.")
    >>> else:
    >>>     print("An error occurred while combining the files.")
    """
    block_size = 64 * 1024  # 64 KB
    try:
        with output_file_path.open('wb') as output_file:
            for chunk_file in chunk_files:
                with chunk_file.open('rb') as file:
                    while True:
                        block = file.read(block_size)
                        if not block:
                            break
                        output_file.write(block)
        return True
    except IOError:
        return False


# Files ################################################################

def rmdir(path: str | Path, must_be_empty: bool = False, recursive: bool = True):
    """
    Removes a directory from the filesystem.

    :param path: Path to the directory to be removed.
    :param must_be_empty: If True, checks if the directory is empty before removing.
    :param recursive: If True, allows for recursive deletion of the directory and its contents.

    :raises IsADirectoryError: If the path is not a directory.
    :raises OSError: If must_be_empty is True and the directory is not empty.
    """

    def rmdir_recursion(path_recur: Path):
        # Delete files in this directory (recursively)
        for item in path_recur.iterdir():
            if item.is_dir():
                # Recursively remove subdirectories
                rmdir_recursion(item)  # >> RECURSION

                # NOTE: I know about: `shutil.rmtree(item)`.
                #       But I want more control here, it might come in handy in the future.
            else:
                item.unlink()  # Remove files
        path_recur.rmdir()  # Finally remove the directory itself

    # Main function:

    path = Path(path)

    if not recursive and not must_be_empty:
        raise ValueError('When `recursion=False`, then must be: `must_be_empty=True`')
    elif recursive and must_be_empty:
        raise ValueError('When `recursion=True`, then must be: `must_be_empty=False`')
    elif not path.is_dir():
        raise IsADirectoryError(f'Cannot remove {path} because it is not a directory.')

    # Check if the directory must be empty
    if must_be_empty:
        # Directory is not empty, raise an error
        if any(path.iterdir()):  # `iterdir` returns an iterator of directory contents
            raise OSError(f'Cannot remove {path} because it is not empty.')

    if recursive:
        rmdir_recursion(path)
    else:
        path.rmdir()  # Non-recursive removal, only works if the directory is empty


def rm(path: str | Path, recursive=False):
    """
    Remove a file or directory.

    Parameters:
    - path (str or Path): The path to the file or directory to be removed.
    - recursive (bool): If True - remove directory. If False - remove one file. If None - remove one file or dir.

    Raises:
    - FileNotFoundError: If the specified path does not exist.
    - IsADirectoryError: If the specified path is a directory and recursive is not set to True.
    - PermissionError: If the user has insufficient permissions to remove the specified path.
    - Exception: If an unspecified error occurs during the removal operation.

    Example:
    >>> rm("file.txt")
    Successfully removed file.txt

    >>> rm("directory/", recursive=True)
    Successfully removed directory and its contents recursively.

    """
    # TODO: double check with a symlink
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f'The specified path {path} does not exist.')
    if recursive is None:
        recursive = path_obj.is_dir()

    if recursive and path_obj.is_dir():
        path_obj.rmdir()
        # log(f'Successfully removed directory {path}')
    elif not recursive and path_obj.is_file():
        path_obj.unlink()
        # log(f'Successfully removed {path}')
    elif recursive and not path_obj.is_dir():
        raise IsADirectoryError(f'Cannot remove {path} recursively because it is not a directory.')
    elif not recursive and not path_obj.is_file():
        raise IsADirectoryError(f'Cannot remove {path} because it is not a file.')
    else:
        raise Exception(f'An unspecified error occurred during the removal operation.')


def copy_files(source_dir: Path | str, destination_dir: Path | str):
    """
    Copy all files from the source directory to the destination directory.

    Parameters:
    - source_dir (Path or str): The path to the source directory containing files to be copied.
    - destination_dir (Path or str): The destination directory where files will be copied.

    Raises:
    - FileNotFoundError: If the source directory does not exist.
    - NotADirectoryError: If the source path is not a directory.
    - NotADirectoryError: If the destination path is not a directory.
    - PermissionError: If the user has insufficient permissions.
    - Exception: If an unspecified error occurs during the copy operation.

    Example:
    >>> copy_files("source_folder", "destination_folder")
    File source_folder/file1.txt copied to destination_folder/file1.txt
    File source_folder/file2.txt copied to destination_folder/file2.txt
    ...

    Note:
    This function recursively copies files from the source directory to the destination directory,
    preserving the directory structure.
    """

    source_path = Path(source_dir)
    destination_dir = Path(destination_dir)

    # Check if the source directory exists
    if not source_path.exists() or not source_path.is_dir():
        raise FileNotFoundError(f'The source directory {source_path} does not exist or is not a directory.')

    # Check if the destination path is a directory
    if not destination_dir.is_dir():
        raise NotADirectoryError(f'The destination path {destination_dir} is not a directory.')

    # Create the destination directory if it does not exist
    destination_dir.mkdir(parents=True, exist_ok=True)

    # Get a list of files in the source directory and its subdirectories
    files_to_copy_iter = source_path.rglob('*')

    # Copy files to the destination directory
    for file_to_copy in files_to_copy_iter:
        if file_to_copy.is_file():
            # Construct the destination path for each file
            destination_file = destination_dir / file_to_copy.name
            copy_file(file_to_copy, destination_file)
            # log(f'File {file_to_copy} copied to {destination_file}')


def copy_file(source_file: Path | str, destination_dir: Path | str):
    """
    Copy a file from the source path to the destination path.

    Parameters:
    - source_file (Path or str): The path to the source file to be copied.
    - destination_path (Path or str): The destination directory or file.

    Raises:
    - FileNotFoundError: If the source file does not exist.
    - PermissionError: If the user has insufficient permissions.
    - Exception: If an unspecified error occurs during the copy operation.

    Example:
    >>> copy_file("source.txt", "destination_folder")
    File source.txt copied to destination_folder/source.txt
    """

    source_path = Path(source_file)
    destination_path = Path(destination_dir)

    # Check if the source file exists and is a file
    if not source_path.is_file():
        raise FileNotFoundError(f'The source file {source_path} does not exist or is not a file.')

    # Check if the destination is a directory or a file
    if destination_path.is_dir():
        # If it's a directory, create the destination directory if it does not exist
        destination_path.mkdir(parents=True, exist_ok=True)
        # Append the original file name to the destination directory
        destination_path = destination_path / source_path.name

    # Copy the file to the destination directory
    shutil.copy2(source_path, destination_path)

    print('WARN: This function is not implemented yet.')
    print('      set_file_write_time(disk_h_file_backup, current_time)')
    # TODO: set_file_create_time(destination_path, get_file_create_time(source_path))
    # log(f'File {source_path} copied to {destination_path}')


def cp(source: Path | str, destination: Path | str):
    # TODO: documentation
    source = Path(source)
    destination = Path(destination)

    if source.is_dir():
        copy_files(source, destination)
    else:
        copy_file(source, destination)


class CopyFileProgressTracker:
    def __init__(self, file: typing.BinaryIO, file_size: int,
                 callback_print_progress: Callable,
                 callback_print_data: Optional[Dict] = None,
                 callback: Optional[Callable] = None,
                 callback_user_data: Optional[Any] = None):
        """
        A file wrapper that facilitates tracking and displaying copy progress, and executing callback functions.

        A file wrapper class used to intercept write operations to a file object,
        enabling progress tracking and custom callback execution during file copy operations.
        This class integrates functionality to update the progress based on
        the amount of data written and optionally calls a user-defined callback function
        with detailed progress information.

        :param file: File object to which data is written.
        :param file_size: Total size of the file being copied.
        :param callback_print_progress: Function to call for printing progress.
        :param callback_print_data: Data for the progress printing callback.
        :param callback: Optional user-defined callback function for additional processing.
        :param callback_user_data: Optional user data for the additional callback.
        """

        self._file = file
        self._file_size = file_size
        self._callback_print_progress = callback_print_progress
        self._callback = callback
        self._callback_print_data = callback_print_data
        self._callback_user_data = callback_user_data
        self._total_written = 0  # Total number of bytes written

    def write(self, data: bytes) -> None:
        self._file.write(data)

        self._total_written += len(data)

        # Print progress callback
        if self._callback_print_progress:
            self._callback_print_progress(data, len(data), self._total_written, self._file_size,
                                          self._callback_print_data, 0)

        # Additional custom user callback
        if self._callback:
            self._callback(data, len(data), self._total_written, self._file_size, self._callback_user_data, 0)

    def __getattr__(self, attr: str):
        return getattr(self._file, attr)


def print_copy_progress(data: bytes, data_len: int, copied_size: int, file_size: int,
                        user_data: Any, error_code: int) -> None:
    """
    Print progress to the console at most once per second.

    :param data: The latest chunk of data written to the file.
    :param data_len: The size of the latest data chunk.
    :param copied_size: Total size of data copied so far.
    :param file_size: Total size of the file being copied.
    :param user_data: Dictionary to store user data `Dict{'last_print_time': 0.0}`, like the time of the last print.
    :param error_code: Error codes (not working - under development).
    """
    if data is None:
        return
    current_time = get_datetime().timestamp()
    last_print_time = user_data.get('last_print_time', 0.0)
    if current_time != last_print_time:  # Print every second
        progress = int(copied_size / file_size * 100)
        progress_bar = progress // 2
        progress_left = 100 // 2 - progress_bar
        progress_bar_str = ('=' * progress_bar) + (' ' * progress_left)
        sys.stdout.write(f'\r[{progress_bar_str}] {progress:3}%  {format_bytes(copied_size)}/{format_bytes(file_size)}')
        sys.stdout.flush()
        user_data['last_print_time'] = current_time

    if error_code == 0 and data_len == 0:
        sys.stdout.write('\r\n')
        sys.stdout.flush()


def copy_file_with_progress(source_path: Path | str, destination_path: Path | str,
                            follow_symlinks: bool = True,
                            callback: Optional[Callable] = None,
                            callback_user_data: Optional[Dict] = None,
                            callback_print_progress: Optional[Callable] = None) -> None:
    """
    Copy a file from source to destination with progress tracking and optional callback execution.

    :param source_path: Path to the source file.
    :param destination_path: Path to the destination file.
    :param follow_symlinks: Whether to follow symlinks or copy them as symlinks.
    :param callback: Optional callback function for custom processing.
    :param callback_user_data: Data for the custom callback function.
    :param callback_print_progress: Optional callback for printing progress.

    callback propotype:
    `def print_copy_progress(data: bytes, data_len: int, copied_size: int, file_size: int,
                        user_data: Any, error_code: int) -> None`
    """
    source_path = Path(source_path)
    destination_path = Path(destination_path)

    if not follow_symlinks and source_path.is_symlink():
        destination_path.symlink_to(source_path.readlink())
    else:
        file_size = source_path.stat().st_size
        if callback_print_progress is None:
            callback_print_progress = print_copy_progress
        callback_print_data = {'last_print_time': 0}

        with source_path.open('rb') as source_file:
            try:
                with destination_path.open('wb') as destination_file:
                    progress_destination_file = CopyFileProgressTracker(destination_file,
                                                                        file_size,
                                                                        callback_print_progress,
                                                                        callback_print_data,
                                                                        callback,
                                                                        callback_user_data)
                    shutil.copyfileobj(source_file, progress_destination_file, length=1024 * 1024)
                    callback_print_progress(b'', 0, file_size, file_size, callback_print_data, 0)

            # Issue [shutil 43219], raise a less confusing exception (copy from shutil)
            except IsADirectoryError as e:
                if not destination_path.exists():
                    raise FileNotFoundError(f'Directory does not exist: {destination_path}') from e
                else:
                    raise

        shutil.copystat(source_path, destination_path, follow_symlinks=follow_symlinks)
        # TODO: set_file_create_time(destination_path, get_file_create_time(source_path))


def format_bytes(byte_count, kibi=False):
    level = ' B'
    i = '' if not kibi else 'i'
    divisor = 1024 if kibi else 1000
    if byte_count >= divisor:
        level = 'K'
        byte_count /= divisor
        if byte_count >= divisor:
            level = 'M'
            byte_count /= divisor
            if byte_count >= divisor:
                level = 'G'
                byte_count /= divisor
                if byte_count >= divisor:
                    level = 'T'
                    byte_count /= divisor
                    if byte_count >= divisor:
                        level = 'P'
                        byte_count /= divisor
    return f"{byte_count:,.0f} {level}{i}B"


def change_filename_ext_in_path(filename: Path, new_extension: str = '.txt') -> Path:
    """
    Changes in value the Path-file extension of a given filename to a new extension.
    WARNING: There is no real renaming of the file in the file system. Change only in the return value (in the memory).

    :param filename: A Path object representing the original filename.
    :param new_extension: A string representing the new file extension, starting with a dot.
    :return: A Path object with the new file extension.
    """
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension
    return filename.with_suffix(new_extension)


def rename_only(filename: Path | str, new_filename: Path | str):
    """
    Renames a file in the same directory. Renaming without moving.

    Args:
        filename: The current file's path or name.
        new_filename: The new name for the file.
            Must contain only the name, without the path to the new directory.

    The function renames the file located at the specified path by changing its name to new_filename,
    while ensuring
    that both the current file and the new name are in the same directory.
    If new_filename contains more than one path
    segment, the function raise exception.

    Example:
    >>> rename_only("path/file.txt", "new_file.txt")
    """
    filename = Path(filename)
    new_filename = Path(new_filename)
    if len(new_filename.parts) > 1:
        raise ValueError(f'"{new_filename}" contains more than one path segment')

    new_filename = filename.parent / new_filename.name
    filename.rename(new_filename)


def mv(source: Path | str, destination: Path | str):
    Path(source).rename(Path(destination))
    # log(f'Move: {filename} to {new_filename}')


def move_file_to_dir(source: Path | str, destination_dir: Path | str) -> None:
    """
    Move a file from the source location to the destination directory.

    Args:
        source (Path | str): The source file's path
        destination_dir (Path | str): The destination directory's path, must be directory

    This function takes the source file, renames it with its original name, and moves it to the destination directory.

    Example:
    ```
    >>> source_path = Path("path/to/source/file.txt")
    >>> destination_directory = Path("path/to/destination/")
    >>> move_file_to_dir(source_path, destination_directory)
    ```
    """
    source = Path(source)
    destination_dir = Path(destination_dir)
    destination_path = destination_dir / source.name

    source.rename(destination_path)
    # log(f'Moved: {filename} to {new_filename}')


def rename_files_recursively(directory_path: Path | str, search_filename: str, new_filename, rename_dir=False):
    """
    Recursively renames files (and optionally directories) in a specified directory
    that match a given filename.

    Parameters:
    directory_path (Path|str): The path of the directory to start the search.
    search_filename (str): The filename to search for.
    new_filename (str): The new filename to apply to matched items.
    rename_dir (bool): If False, only files are renamed. If True, directories are also renamed.

    Raises:
    FileNotFoundError: If the specified directory does not exist.
    PermissionError: If the script lacks necessary permissions to rename a file or directory.
    OSError: For other issues related to file renaming (e.g., file in use, invalid names).
    """
    directory_path = Path(directory_path)
    if not directory_path.exists():
        raise FileNotFoundError(f"The directory {directory_path} does not exist.")
    if not directory_path.is_dir():
        raise NotADirectoryError(f"The specified path {directory_path} is not a directory.")

    for item in directory_path.rglob(search_filename):
        if rename_dir or item.is_file():
            rename_only(item, new_filename)


def find(
        directory_path: Path | str = '.',
        search_mask: str = '*',
        recursively: bool = False):
    """
    Find files in the specified directory matching the given search mask.

    Args:
        directory_path (Path or str): The directory in which to search for files.
        search_mask (str): The search mask to filter files, e.g., "*.txt".
            You can use "**/" to search recursively (equivalent `recursively=True`).
        recursively (bool, optional): If True, search for files in subdirectories as well.
            If False, only search for files in the specified directory.

    Returns:
        Iterable of Path: An iterable of `Path` objects representing the found files.

    Raises:
        FileNotFoundError: If the specified directory does not exist.


    Example:
        ```
        for file in find('~/', '*', recursively=True):
            print(str(file))

        for file in find('~/', '*', recursively=True):
            if get_file_size(file) > 1024 * 1024:  # File size more 1 mb
                print(str(file))

        files = find('~/', '*', recursively=True)
        if files:
            print('File list:')
            for file in files:
                print(str(file))
        else:
            print('File not found')
        ```
    """
    directory_path = Path(directory_path).expanduser()
    if not directory_path.exists():
        raise FileNotFoundError(f'The directory {directory_path} does not exist.')

    if recursively:
        return Path(directory_path).rglob(search_mask)
    else:
        return Path(directory_path).glob(search_mask)


def find_dir(directory_path: Path | str = '.', search_mask: str = '*', recursively: bool = False):
    """
    Find directories in the specified directory matching the given search mask.

    Args:
        directory_path (Path or str): The directory in which to search for directories.
        search_mask (str): The search mask to filter directories, e.g., "subdir*".
            You can use "**/" to search recursively (equivalent to `recursively=True`).
        recursively (bool, optional): If True, search for directories in subdirectories as well.
            If False, only search for directories in the specified directory.

    Returns:
        Generator of Path: A generator of `Path` objects representing the found directories.

    Raises:
        FileNotFoundError: If the specified directory does not exist.

    Example:
        >>> for directory in find_dir('~/', 'subdir*', recursively=True):
        >>>     print(str(directory))

        >>> for directory in find_dir('~/', 'subdir*', recursively=True):
        >>>     # Skip directories starting with '.'
        >>>     if any(part.startswith('.') for part in directory.parts):
        >>>         continue
    """

    def find_dir_generator(path, mask, recursive):
        if recursive:
            for d in path.rglob(mask):
                if d.is_dir():
                    yield d
        else:
            for d in path.iterdir():
                if d.is_dir() and d.match(mask):
                    yield d

    directory_path = Path(directory_path).expanduser()
    if not directory_path.exists():
        raise FileNotFoundError(f'The directory {directory_path} does not exist.')

    return find_dir_generator(directory_path, search_mask, recursively)


def get_file_perm(p: Path | str) -> str:
    """
    Retrieves the file permissions of a given path in octal format, or returns
    a modified value if the operating system is Windows.

    On Linux systems, it extracts the permissions part of the file's status
    using the `stat()` method from the `Path` object and returns it as an octal string.
    On Windows systems, it checks if the file is read-only and returns '555' if true,
    implying read and execute permissions for user, group, and others. If not read-only,
    it returns '777', implying full permissions.

    Parameters:
    p (Path): The path of the file or directory for which to retrieve permissions.

    Returns:
    str: A string representing the file permissions in octal format on Linux.

    Example:
    >>> get_file_perm(Path('/path/to/file'))
    '755'  # On Linux
    '777'  # On Windows, not read-only file
    '555'  # On Windows, read-only file
    """
    p = Path(p)
    if os.name == 'nt':  # Checks if the operating system is Windows
        # Check if the file has the read-only attribute
        if os.stat(p).st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
            return '555'  # Read and execute permissions
        return '777'  # Full permissions

    return oct(p.stat().st_mode)[-3:]


def get_current_dir() -> Path:
    """
    Get the current working directory as a `Path` object.
    """
    return Path.cwd()


def current_dir() -> Path:
    """
    Alias for `get_current_dir()`
    """
    return get_current_dir()


def cwd() -> Path:
    """
    Alias for `get_current_dir()`
    """
    return get_current_dir()


def set_current_dir(new_directory: Path | str) -> None:
    """
    Set the current working directory to the specified path.

    Args:
        new_directory (Path or str): The new directory to set as the current working directory.

    Raises:
        FileNotFoundError: If the specified directory does not exist.
        NotADirectoryError: If the specified path is not a directory.
        PermissionError: If the script lacks necessary permissions to change the current directory.

    Example:
    >>> set_current_dir('/path/to/new/directory')  # Changes the current working directory
    """
    new_directory = Path(new_directory).expanduser()

    if not new_directory.exists():
        raise FileNotFoundError(f"The directory {new_directory} does not exist.")

    if not new_directory.is_dir():
        raise NotADirectoryError(f"The path {new_directory} is not a directory.")

    # Change the current working directory
    os.chdir(new_directory)


def chdir(new_directory: Path | str) -> None:
    """
    Alias for `set_current_dir()`
    """
    set_current_dir(new_directory)


def cd(new_directory: Path | str) -> None:
    """
    Alias for `set_current_dir()`
    """
    set_current_dir(new_directory)


def check_ext(f: Path | str, ext_list: list[str]) -> bool:
    """
    Check if a file's extension matches a list of allowed extensions.

    Args:
        f (Path | str): A Path object representing the file to be checked.
        ext_list (list[str]): A list of allowed file extensions.
            `ext_list = ['txt', 'md']` - accept *.txt and *.md files
            `ext_list = ['*']` - accept all files
            `ext_list = []` - ignore all files
            `ext_list = ['']` - accept files with empty extension

    Returns:
        bool: True if the file's extension matches one of the allowed extensions,
              False otherwise.

    Examples:
    >>> if check_ext(Path("example.txt"), ['txt', 'md']):
    >>>   print(f"Extension is allowed.")
    """
    ext_list = [i.lower() for i in ext_list]
    return (ext_list[0] == '*') or (Path(f).suffix.lower()[1:] in ext_list)


def get_file_size(file_path: Path | str) -> int:
    return file_path.stat().st_size


def get_file_write_time(file_path: Path | str) -> datetime:
    return datetime.fromtimestamp(Path(file_path).stat().st_mtime)


def set_file_write_time(file_path: Path | str, new_last_modified: datetime):
    file_path = Path(file_path)

    if not file_path.exists() or not file_path.is_file():
        print(f'The file {file_path} does not exist or is not a file.')
        return

    timestamp = new_last_modified.timestamp()

    # file_path.touch()
    os.utime(file_path, (timestamp, timestamp))


def get_file_create_time(file_path: Path | str) -> datetime:
    path = Path(file_path)
    # On Windows, `os.path.getctime()` returns the creation date.
    # On Unix-like systems, it returns the last metadata change on a file or directory.
    # For actual file creation date, this might not be accurate on Unix-like systems.
    # TODO: `Path.stat().birthtime`: Creation time(on some Unix systems in the FreeBSD family, including macOS)
    # TODO: This method normally follows symlinks;
    #  to stat a symlink add the argument follow_symlinks=False, or use lstat().
    creation_time = os.path.getctime(path)
    return datetime.fromtimestamp(creation_time)


def set_file_create_time(file_path: Path | str, new_create_date: datetime):
    """
    WARNING: This function is not implemented yet!

    Set the creation date of a file.
    Note: This function might not work as expected on Unix-like systems.

    Args:
    - file_path (str or Path): The path to the file.
    - new_create_date (datetime): The new creation date to set.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        print(f'The file {path} does not exist or is not a file.')
        return

    raise NotImplementedError('This function is not implemented yet.')

    # TODO: implementation for windows
    #  https://github.com/Delgan/win32-setctime
    #  https://github.com/kubinka0505/filedate
    #  https://stackoverflow.com/a/43047398

    """
    from ctypes import windll, wintypes, byref

    # Arbitrary example of a file and a date
    filepath = "my_file.txt"
    epoch = 1561675987.509

    # Convert Unix timestamp to Windows FileTime using some magic numbers
    # See documentation: https://support.microsoft.com/en-us/help/167296
    timestamp = int((epoch * 10000000) + 116444736000000000)
    ctime = wintypes.FILETIME(timestamp & 0xFFFFFFFF, timestamp >> 32)

    # Call Win32 API to modify the file creation date
    handle = windll.kernel32.CreateFileW(filepath, 256, 0, None, 3, 128, None)
    windll.kernel32.SetFileTime(handle, byref(ctime), None, None)
    windll.kernel32.CloseHandle(handle)

    //////////////////////////////

    def changeFileCreationTime(fname, newtime):
        wintime = pywintypes.Time(newtime)
        winfile = win32file.CreateFile(
            fname,
            win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None, win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL, None)

        win32file.SetFileTime(winfile, wintime, None, None)

        winfile.close()
    //////////////////////////

    from win32_setctime import setctime

    setctime("my_file.txt", 1561675987.509)

    from ctypes import windll, wintypes, byref

    # Arbitrary example of a file and a date
    filepath = "my_file.txt"
    epoch = 1561675987.509

    # Convert Unix timestamp to Windows FileTime using some magic numbers
    # See documentation: https://support.microsoft.com/en-us/help/167296
    timestamp = int((epoch * 10000000) + 116444736000000000)
    ctime = wintypes.FILETIME(timestamp & 0xFFFFFFFF, timestamp >> 32)

    # Call Win32 API to modify the file creation date
    handle = windll.kernel32.CreateFileW(filepath, 256, 0, None, 3, 128, None)
    windll.kernel32.SetFileTime(handle, byref(ctime), None, None)
    windll.kernel32.CloseHandle(handle)
    """

    # timestamp = new_create_date.timestamp()
    # On Windows, the first value of the tuple sets the creation date.
    # This operation is not guaranteed to change the creation date on Unix-like systems.
    # os.utime(path, (timestamp, path.stat().st_mtime))


def touch(file: Path | str, mode=None, exist_ok=True):
    """
    Create a new file at the specified path or update the modification time if the file already exists.

    Parameters:
    file (Path | str): The path of the file to be created or touched.
    mode (int, optional): The permissions to set on the newly created file. Defaults to None.
    exist_ok (bool): If False, raises a FileExistsError if the file already exists. Defaults to True.

    Note:
    This function uses Path.touch from the pathlib module to create the file. The mode parameter
    is only effective if the file is created; it does not change the permissions of an existing file.
    """
    file = Path(file)
    file.touch(mode=mode, exist_ok=exist_ok)


def chmod(path: Path | str, mode, follow_symlinks=True):
    """
    Change the permissions of a file or directory.

    Parameters: path (Path | str): The path of the file or directory. mode (int): The permissions to set. Should be
    an integer (e.g., 0o755). follow_symlinks (bool): If False, and the path is a symbolic link, chmod modifies the
    symbolic link itself instead of the file it points to. Defaults to True.
    """
    path = Path(path)
    path.chmod(mode=mode, follow_symlinks=follow_symlinks)


def chown(path: Path | str, user: str | int | None = None, group: str | int | None = None):
    """
    Change the owner and group of a file or directory.

    Parameters:
    path (Path | str): The path of the file or directory.
    user (str | int, optional): The name or ID of the user to set as the owner. Defaults to None.
    group (str | int, optional): The name or ID of the group to set. Defaults to None.

    Note:
    This function uses `os.chown` to change the file owner and group.
    If either user or group is None, the corresponding ownership is not changed.
    If a user or group name is provided, it will be resolved to the corresponding ID.
    This function only works on Linux systems.
    """
    if not is_linux():
        raise OSError('This function is only supported on Linux systems.')

    import pwd
    import grp

    path = Path(path)

    # Get current ownership
    stat_info = path.lstat()
    uid = stat_info.st_uid
    gid = stat_info.st_gid

    # Get new user ID if user is specified
    if user is not None:
        if isinstance(user, int):
            uid = user
        else:
            uid = pwd.getpwnam(user).pw_uid

    # Get new group ID if group is specified
    if group is not None:
        if isinstance(group, int):
            gid = group
        else:
            gid = grp.getgrnam(group).gr_gid

    os.chown(path, uid, gid)


def split_files_get_list(first_chunk_path: Path | str) -> List[Path]:
    """
    Verifies and lists chunk files in the directory of the given first chunk file.

    Parameters:
    first_chunk_path (Path): Path to the first chunk file. Must be '*.001' (e.g., 'file.txt.001').

    Returns:
    list: List of Path objects representing the chunk files if conditions are met, otherwise an empty list.

    See Also:
        split_file, combine_files, split_files_get_list, file_list_calc_total_size
    """
    first_chunk_path = Path(first_chunk_path)

    if first_chunk_path.suffix != '.001':
        return []

    directory = first_chunk_path.parent
    base_name = first_chunk_path.stem

    base_name_no_ext = base_name.rsplit('.', 1)[0]

    # Search, filtering and sorting files by numeric extension, ensuring three-digit extensions only
    chunk_files = directory.glob(f'{base_name_no_ext}.*')
    chunk_files = filter(lambda f: f.suffix[1:].isdigit() and len(f.suffix[1:]) == 3, chunk_files)
    chunk_files = sorted(chunk_files, key=lambda f: int(f.suffix[1:]))

    if not chunk_files:
        return []

    expected_size = first_chunk_path.stat().st_size
    for i, chunk_file in enumerate(chunk_files):
        current_size = chunk_file.stat().st_size
        expected_suffix = f'.{(i + 1):03d}'
        if chunk_file.suffix != expected_suffix:
            return []
        if i < len(chunk_files) - 1 and current_size != expected_size:
            return []
        elif i == len(chunk_files) - 1 and current_size > expected_size:
            return []

    return chunk_files


def file_list_calc_total_size(file_list: List[Union[Path, str]]) -> int:
    """
    Calculates the total size of all files in the given list.

    Parameters:
    file_list (List[Union[Path, str]]): List of Path objects or strings representing the files.

    Returns:
    int: Total size of the files in bytes.
    """
    return sum(Path(file).stat().st_size for file in file_list)


def file_list_filter_by_flags(
        file_list: Iterable[Union[Path, str]],
        existing=None,
        only_files=None,
        only_dir=None,
        readable=None,
        writable=None,
        executable=None,
        hidden=None,
        symlinks=None,
        size_greater_than=None,
        size_less_than=None,
        extension=None,
        file_type=None,
        mtime_before=None,
        mtime_after=None,
        atime_before=None,
        atime_after=None,
        ctime_before=None,
        ctime_after=None,
        empty=None,
        maxdepth=None,
        mindepth=None,
) -> List[Path]:
    """
    Filters the given list of files or directories based on specified criteria.
    
    This function is Python analog of the Linux 'find' command.
    Each parameter has a corresponding parameter in the 'find' command
    (see the 'Find analog:' line in the documentation).

    Parameters:
    file_list (Iterable[Union[Path, str]]):
        File and directory paths to filter.
        Array of strings. 
        Or array of `Path` objects (`Path` are recommended).
        Instead of arrays, can be iterators (such as `Path.iterdir()`).
        Find analog: PATH argument
    existing (bool, optional): 
        Filter by existing.
        Can be `True` or `False` or `None`. Default is None.
        If None, do not filter by existing.
        If True, include only existing files or directories. 
        If False, include only non-existing (useful for searching for files that do not exist).
        Find analog: no direct analog (find searches existing files by default)
    only_files (bool, optional):
        Filter by files.
        Can be `True` or `False` or `None`. Default is None.
        If None, do not filter by file type.
        If True, include only files.
        If False, include only non-files (directories, symlinks, etc.).
        Find analog: "-type f"
    only_dir (bool, optional):
        Filter by directories.
        Can be `True` or `False` or `None`. Default is None.
        If None, do not filter by directory type.
        If True, include only directories.
        If False, include only non-directories.
        Find analog: "-type d"
    readable (bool, optional):
        Filter by readable files or directories.
        If True, include only readable files or directories. Default is None.
        Find analog: "-readable"
    writable (bool, optional):
        Filter by writable files or directories.
        If True, include only writable files or directories. Default is None.
        Find analog: "-writable"
    executable (bool, optional):
        Filter by executable files or directories.
        If True, include only executable files or directories. Default is None.
        Find analog: "-executable"
    hidden (bool, optional):
        Filter by hidden files or directories.
        If True, include only hidden files or directories. Default is None.
        Find analog: "-name '.*'"
    symlinks (bool, optional):
        Filter by symbolic links.
        If True, include only symbolic links. Default is None.
        Find analog: "-type l"
    size_greater_than (int, optional):
        Filter by file size.
        Include only files larger than this size (in bytes). Default is None.
        Find analog: "-size +Nc"
    size_less_than (int, optional):
        Filter by file size.
        Include only files smaller than this size (in bytes). Default is None.
        Find analog: "-size -Nc"
    extension (str, optional):
        Filter by file extension.
        Include only files with this extension. Default is None.
        Find analog: "-name '*.ext'"
    file_type (str, optional):
        Filter by file type.
        Include only files of this type ('f' for files, 'd' for directories, 'l' for symlinks). Default is None.
        Find analog: "-type {f|d|l}"
    mtime_before (datetime, optional):
        Filter by modification time.
        Include only files modified before this date. Default is None.
        Find analog: "-mtime +N"
    mtime_after (datetime, optional):
        Filter by modification time.
        Include only files modified after this date. Default is None.
        Find analog: "-mtime -N"
    atime_before (datetime, optional):
        Filter by access time.
        Include only files accessed before this date. Default is None.
        Find analog: "-atime +N"
    atime_after (datetime, optional):
        Filter by access time.
        Include only files accessed after this date. Default is None.
        Find analog: "-atime -N"
    ctime_before (datetime, optional):
        Filter by change time.
        Include only files changed before this date. Default is None.
        Find analog: "-ctime +N"
    ctime_after (datetime, optional):
        Filter by change time.
        Include only files changed after this date. Default is None.
        Find analog: "-ctime -N"
    empty (bool, optional):
        Filter by empty files or directories.
        If True, include only empty files or directories. Default is None.
        Find analog: "-empty"

    maxdepth (int, optional): 
        Maximum depth of directories to include. 
        Default is None.
        Find analog: "-maxdepth N"
    mindepth (int, optional): 
        Minimum depth of directories to include. 
        Default is None.
        Find analog: "-mindepth N"

    Returns:
    List[Path]: List of Path objects that match the specified criteria.
    """
    res = []

    for file_path in file_list:
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if existing is not None and file_path.exists() != existing:
            continue

        if only_files is not None and file_path.is_file() != only_files:
            continue

        if only_dir is not None and file_path.is_dir() != only_dir:
            continue

        if readable is not None and os.access(file_path, os.R_OK) != readable:
            continue

        if writable is not None and os.access(file_path, os.W_OK) != writable:
            continue

        if executable is not None and os.access(file_path, os.X_OK) != executable:
            continue

        if hidden is not None and file_path.name.startswith('.') != hidden:
            continue

        if symlinks is not None and file_path.is_symlink() != symlinks:
            continue

        if size_greater_than is not None and file_path.is_file() and file_path.stat().st_size <= size_greater_than:
            continue

        if size_less_than is not None and file_path.is_file() and file_path.stat().st_size >= size_less_than:
            continue

        if extension is not None and file_path.suffix != extension:
            continue

        if file_type == 'f' and not file_path.is_file():
            continue
        elif file_type == 'd' and not file_path.is_dir():
            continue
        elif file_type == 'l' and not file_path.is_symlink():
            continue

        if mtime_before is not None and datetime.fromtimestamp(file_path.stat().st_mtime) >= mtime_before:
            continue

        if mtime_after is not None and datetime.fromtimestamp(file_path.stat().st_mtime) <= mtime_after:
            continue

        if atime_before is not None and datetime.fromtimestamp(file_path.stat().st_atime) >= atime_before:
            continue

        if atime_after is not None and datetime.fromtimestamp(file_path.stat().st_atime) <= atime_after:
            continue

        if ctime_before is not None and datetime.fromtimestamp(file_path.stat().st_ctime) >= ctime_before:
            continue

        if ctime_after is not None and datetime.fromtimestamp(file_path.stat().st_ctime) <= ctime_after:
            continue

        if empty and file_path.is_file() and file_path.stat().st_size != 0:
            continue

        if empty and file_path.is_dir() and any(file_path.iterdir()):
            continue

        # Check depth constraints
        if maxdepth is not None or mindepth is not None:
            depth = len(file_path.parts)
            
            if maxdepth is not None and depth > maxdepth:
                continue
                
            if mindepth is not None and depth < mindepth:
                continue

        res.append(file_path)
    return res


def file_list_filter_by_user_group_perm(
        file_list: List[Union[Path, str]],
        user: Union[str, int, None] = None,
        group: Union[str, int, None] = None,
        perm: str = None
) -> List[Path]:
    """
    Filters the given list of files or directories based on user, group, and permissions.

    Parameters:
    file_list (List[Union[Path, str]]): List of Path objects or strings representing the files or directories.
    user (str | int, optional): The user name or ID to filter by. Default is None.
    group (str | int, optional): The group name or ID to filter by. Default is None.
    perm (str, optional): The permission string to filter by (e.g., '755'). Default is None.

    Returns:
    List[Path]: List of Path objects that match the specified criteria.
    """
    import pwd
    import grp

    res = []

    for file_path in file_list:
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if user is not None:
            uid = file_path.stat().st_uid
            if isinstance(user, int):
                if uid != user:
                    continue
            else:
                if uid != pwd.getpwnam(user).pw_uid:
                    continue

        if group is not None:
            gid = file_path.stat().st_gid
            if isinstance(group, int):
                if gid != group:
                    continue
            else:
                if gid != grp.getgrnam(group).gr_gid:
                    continue

        if perm is not None:
            mode = oct(file_path.stat().st_mode)[-3:]
            if mode != perm:
                continue

        res.append(file_path)

    return res


def file_list_filter_by_substring(file_list: List[Union[Path, str]],
                                  substring: str, inverse: bool = False) -> List[Path]:
    """
    Filter a list of file paths by including only those that contain a given substring.
    If inverse is True, exclude paths that contain the substring.
    """
    return list(map(Path, filter(lambda x: str_present(str(x), substring) != inverse, file_list)))


def file_list_sort_by_date(file_list: List[Union[Path, str]], reverse=False) -> List[Path]:
    """ Function to sort files by modification date """
    return sorted(file_list, key=lambda x: Path(x).stat().st_mtime, reverse=reverse)


def file_list_sort_by_size(file_list: List[Union[Path, str]], reverse=False) -> List[Path]:
    """ Function to sort files by size """
    return sorted(file_list, key=lambda x: Path(x).stat().st_size, reverse=reverse)


def file_list_sort_by_name(file_list: List[Union[Path, str]], reverse=False) -> List[Path]:
    """ Function to sort files by name """
    return sorted(file_list, key=lambda x: Path(x).name.lower(), reverse=reverse)


def file_list_sort_by_ext(file_list: List[Union[Path, str]], reverse=False) -> List[Path]:
    """ Function to sort files by extension """
    return sorted(file_list, key=lambda x: Path(x).suffix.lower(), reverse=reverse)


# Run ################################################################

def get_last_error() -> int | None:
    """
    Returns the last error code.
    @see returncode, get_error_code
    """
    global returncode
    return returncode


def get_error_code() -> int | None:
    """
    Returns the last error code.
    @see returncode, get_last_error
    """
    global returncode
    return returncode


class RunOk(subprocess.CompletedProcess):

    def __init__(self, args, set_returncode, stdout: io.StringIO, stderr: io.StringIO):
        super().__init__(args, set_returncode, stdout, stderr)
        self.stdout: io.StringIO = stdout
        self.stderr: io.StringIO = stderr


class RunFail(subprocess.CompletedProcess):

    def __init__(self, args, exception):
        super().__init__(args, -1, None, None)
        self.exception = exception
        self.stdout = io.StringIO('')
        self.stderr = self.stdout


class RunFailProcessPresent(subprocess.CompletedProcess):

    def __init__(self, args):
        super().__init__(args, -1)


def run_command(command: str,
                capture_output=False,
                stdin_text: str | bytes = None,
                stdin=None,
                background=False,
                ensure_unique=False,
                raise_exception=False) -> subprocess.Popen | RunOk | RunFail | RunFailProcessPresent:
    """
    Executes a command with various options such as running in the background, capturing output, ensuring uniqueness,
    and handling custom stdin input.

    Parameters:
    - command (str): The shell command to execute.
    - capture_output (bool): Whether to capture the command's stdout and stderr. Defaults to False.
        If set to True, stdout and stderr are captured and can be accessed via the process object or RunOk instance.
    - stdin_text (str | bytes): Text or bytes to send to the stdin of the subprocess.
        This should not be used with 'stdin'.
    - stdin (subprocess.PIPE or similar): The stdin stream for the subprocess.
        This should not be used together with 'stdin_text'.
    - background (bool): Whether to run the command in the background. Defaults to False.
        If set to True, the function returns
      immediately with a subprocess.Popen object, and you will not receive captured output or a return code.
    - ensure_unique (bool): Ensure the command runs only if it's not already running. Defaults to False.
    - raise_exception (bool): Whether to raise an exception if the command is already running and ensure_unique is True.

    Returns:
    - subprocess.Popen | RunOk | RunFail | RunFailProcessPresent:
      If the `background=True` function return a `subprocess.Popen` object.
      If the `background=False` function return a RunOk instance with captured output,
      a `RunFail` instance with an exception if there was an exception and `raise_exception=False`,
      or a `RunFailProcessPresent` instance if the command is already running.

    Raises:
    - ValueError: If incompatible options are combined (e.g., both 'stdin_text' and 'stdin' are provided).

    Examples:
        ```
        # Example 1: Capturing output of a command
        output = run_command('cat test.txt', capture_output=True)
        if output.stdout:
            print(output.stdout.read())

        # Example 2: Using the function with background and unique process constraints
        process = run_command('long_running_task --option', background=True, ensure_unique=True)
        if isinstance(process, RunFailProcessPresent):
            print("Process is already running.")

        # Example 3: Pipe example (string version)
        output = run_command('cat test.txt', capture_output=True, raise_exception=True)
        grep_output = run_command('grep test_line', capture_output=True, stdin_text=output.stdout.getvalue(),
            raise_exception=True)
        out_str = grep_output.stdout.read()
        print(out_str)

        # Example 4: Pipe example (stdin version)
        output_process = run_command('cat test.txt', capture_output=True, background=True)
        grep_process = run_command('grep test_line', stdin=output_process.stdout)
        print(grep_process.stdout.read())
        ```

    Note:
      To redirect redirect the output of the first application to the second application.
      Ensure the first application is executed with `background=True` and `capture_output=True`.
      Then store returned value obtained after calling the first application to the `result`.
      And pass `result.stdout` to the `stdin` parameter when calling the second application.
    """

    # TODO: add argument `ensure_unique_check_param = True`
    # TODO: add argument `wait_time_if_found = -1`
    # TODO: add argument `timeout = -1`
    # TODO: add argument `print_result = False` or `print_stdout=False`

    global returncode

    if stdin_text is not None and stdin is not None:
        raise ValueError('Both `input` and `stdin` cannot be provided simultaneously.')
    if isinstance(stdin, io.StringIO):
        raise ValueError('Invalid `stdin`. Use `background=True`')

    returncode = None
    if ensure_unique:
        # TODO: [BUG] get_filename(command) - need add the trim of the param part
        proc_name = str(get_filename(command))
        if proc_present(proc_name):
            return RunFailProcessPresent(command)

    stdin_setting = None
    if stdin is not None:
        stdin_setting = stdin
    elif stdin_text is not None:
        stdin_setting = subprocess.PIPE

    stdout_setting = subprocess.PIPE if capture_output else None

    try:
        process = subprocess.Popen(
            command, shell=True,
            stdin=stdin_setting, stdout=stdout_setting, stderr=subprocess.PIPE, text=True, universal_newlines=True)
    except (OSError, ValueError, subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        if raise_exception:
            raise e
        else:
            return RunFail(command, e)

    if stdin_text is not None:
        if isinstance(stdin_text, bytes):
            stdin_text = stdin_text.decode('utf-8')
        if process.poll() is None:
            try:
                process.stdin.write(stdin_text)
                process.stdin.close()
            except (ValueError, OSError):
                pass

    if not background:
        stdout_io = None
        stderr_io = None
        if capture_output:
            stdout_str, stderr_str = process.communicate()
            # return result as `io` object (for compatible)
            # we can't return original `process.stdout` - because it is already empty (used and closed)
            stdout_io = io.StringIO(stdout_str)
            stderr_io = io.StringIO(stderr_str)
        else:
            process.wait()
        returncode = process.returncode
        # replace `process` object
        process = RunOk(command, process.returncode, stdout_io, stderr_io)

    return process


def sh(command_string: str, background=False, capture_output=False, ensure_unique=False):
    """
    Executes multiple shell commands provided in a single string, separated by newlines.

    Parameters:
    - command_string (str): A string containing multiple commands separated by newlines.
    - background (bool): Whether to run the commands in the background. Defaults to False.
    - capture_output (bool): Whether to capture the commands' stdout. Defaults to False.
    - ensure_unique (bool): Ensure each command runs only if it's not already running. Defaults to False.

    Returns:
    - If command is one - result of the `run_command` calls.
    - If command is multiline - list of results of the `run_command` calls.
    """
    # TODO: rename `sh` -> `run_multi()`
    # TODO: add `stop_on_error=False`
    # TODO: add `print_stdout=False`
    commands = command_string.strip().split('\n')
    results = []
    for command in commands:
        result = run_command(command, background=background, capture_output=capture_output, ensure_unique=ensure_unique)
        results.append(result)
    if len(results) == 1:
        results = results[0]
    return results


# Proc #


def proc_present(process_name: str, ignore_exe_extension: bool | typing.Any = None) -> bool:
    """
    Checks if a process with the specified name is currently running on the system.

    This function iterates over all processes running on the system using psutil.process_iter()
    and checks if any of those processes match the given process name.
    If `ignore_exe_extension` is True, it specifically ignores '.exe' extensions
    in process names during the comparison.

    Parameters:
    - proc_name (str): The name of the process to check for.
    - ignore_exe_extension (bool, optional): Whether to ignore '.exe' extensions in process names.
        Defaults to True (for OS Windows).

    Returns:
    - bool: True if a process with the specified name is found, False otherwise.

    Example:
    >>> proc_present("python")
    True  # This would return True if a 'python' or 'python.exe' process is running, False otherwise.
    """
    if psutil is None:
        raise ImportError('The psutil library is required but not installed. Install it using `pip install psutil`')

    if is_wnd() and ignore_exe_extension is None:
        ignore_exe_extension = True

    process_name = process_name.lower()
    if ignore_exe_extension and process_name.endswith('.exe'):
        process_name = process_name[:-4]

    for p in psutil.process_iter(attrs=['name']):
        current_process_name = p.name().lower()
        if ignore_exe_extension and current_process_name.endswith('.exe'):
            current_process_name = current_process_name[:-4]

        if current_process_name == process_name:
            return True
    return False


def get_proc_list(skip_system=True, skip_core=True, only_system=False) -> list:
    """
    Retrieves a list of running processes, with options to filter system, core, or user processes.

    This function iterates over all processes running on the system and optionally filters out system or
    core processes based on the given parameters. It can also be set to return only system processes.

    @param skip_system: bool -- If True, system processes are skipped. Defaults to True.
    @param skip_core: bool -- If True, core processes (those without a command line or associated user) are skipped.
        Defaults to True.
    @param only_system: bool -- If True, only system processes are returned. When set, `skip_system` is ignored.
        Defaults to False.
    @return: list[psutil.Process] -- A list of `psutil.Process` objects for the processes that meet the criteria
        specified by the parameters.

    @details:
    Each Process object in the list can provide various values.
    list of possible string values: 'cmdline', 'connections', 'cpu_affinity', 'cpu_num',
    'cpu_percent', 'cpu_times', 'create_time', 'cwd',
    'environ', 'exe', 'gids', 'io_counters', 'ionice',
    'memory_full_info', 'memory_info', 'memory_maps', 'memory_percent',
    'name', 'nice', 'num_ctx_switches', 'num_fds', 'num_handles', 'num_threads',
    'open_files', 'pid', 'ppid', 'status', 'terminal', 'threads', 'uids', 'username'`.
    See psutil documentation for more details on these attributes.
    https://psutil.readthedocs.io/en/latest/#psutil.Process.as_dict
    Examples:
        ```
        # Get a list of all processes
        process_list = get_proc_list()

        # Convert the process list to a dictionary with specified attributes
        ps = proc_list_to_dict(process_list, ['exe', 'pid'])

        # Create a dictionary mapping executable paths to process IDs
        ps_exec = dict()
        for p in ps:
            ps_exec.update({Path(p['exe']): p['pid']})

        print(ps_exec)
        ```
    """
    if psutil is None:
        raise ImportError("The psutil library is required but not installed. Install it using 'pip install psutil'")

    result = []
    if only_system:
        skip_system = False
    for p in psutil.process_iter():
        try:
            sys_proc = False
            u = p.username()
            if skip_core and (u is None):
                continue
            if (u == 'NT AUTHORITY\\SYSTEM' or
                    u == 'NT AUTHORITY\\LOCAL SERVICE' or
                    u == 'NT AUTHORITY\\SYSTEM'):
                sys_proc = True
            if skip_system and sys_proc:
                continue
            cmd = p.cmdline()
            if skip_core and (cmd is None or cmd == ''):
                continue
            if only_system and not sys_proc:
                continue

            result.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Ignore processes that could not be accessed or do not exist anymore
    return result


def proc_list_to_pid_list(proc_list):
    """Convert a list of psutil.Process objects to a list of process IDs (PIDs).

    @param proc_list: list[psutil.Process] -- List of process objects from the psutil library.
    @return: list[int] -- List of process IDs.
    """
    if psutil is None:
        raise ImportError('The psutil library is required but not installed. Install it using `pip install psutil`')
    result = []
    for p in proc_list:
        result.append(p.pid)
    return result


def proc_list_to_names_list(proc_list):
    """Convert a list of psutil.Process objects to a list of process names.

    @param proc_list: list[psutil.Process] -- List of process objects from the psutil library.
    @return: list[str] -- List of process names.
    """
    if psutil is None:
        raise ImportError('The psutil library is required but not installed. Install it using `pip install psutil`')
    result = []
    for p in proc_list:
        result.append(p.name())
    return result


def proc_list_to_dict(proc_list, attrs):
    """Convert a list of psutil.Process objects to a list of dictionaries representing process attributes.

    @param proc_list: list[psutil.Process] -- List of process objects from the psutil library.
    @param attrs: list[str] -- List of attributes to retrieve for each process.
    @return: list[dict] -- List of dictionaries with keys as attributes and
        values as the corresponding process information.
    """
    if psutil is None:
        raise ImportError('The psutil library is required but not installed. Install it using `pip install psutil`')

    result = []
    for process in proc_list:
        try:
            result.append(process.as_dict(attrs=attrs))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Ignore processes that could not be accessed or do not exist anymore

    return result


# Strings ################################################################


def str_present(target_str: str, find_substr: str) -> bool:
    if isinstance(target_str, str) and isinstance(find_substr, str):
        return find_substr in target_str
    else:
        raise TypeError("Unsupported type")


def get_filename(path: Path | str) -> Path:
    """ Extract filename (with extension) """
    return Path(Path(path).name)


# Date time ################################################################

def datetime_trim_ms(t: datetime | time) -> datetime | time:
    """
    Trims milliseconds from a datetime or time object.

    Parameters:
    - t (datetime | time): The datetime or time object from which milliseconds are to be trimmed.

    Returns:
    - datetime | time: A new datetime or time object without milliseconds.
    """
    if isinstance(t, datetime):
        return datetime(t.year, t.month, t.day, t.hour, t.minute, t.second)
    elif isinstance(t, time):
        return time(t.hour, t.minute, t.second)
    else:
        raise TypeError("Unsupported type for t. Expected datetime or time.")


def datetime_trim_second(t: datetime | time) -> datetime | time:
    """
    Trims seconds from a datetime or time object.

    Parameters:
    - t (datetime | time): The datetime or time object from which seconds are to be trimmed.

    Returns:
    - datetime | time: A new datetime or time object without seconds.
    """
    if isinstance(t, datetime):
        return datetime(t.year, t.month, t.day, t.hour, t.minute)
    elif isinstance(t, time):
        return time(t.hour, t.minute)
    else:
        raise TypeError("Unsupported type for t. Expected datetime or time.")


def datetime_trim_time(t: datetime) -> datetime:
    """
    Trims time from a datetime object.
    """
    if isinstance(t, datetime):
        return datetime(t.year, t.month, t.day)
    else:
        raise TypeError("Unsupported type for t. Expected datetime.")


def _datetime_format(
        strftime: str,
        time_value: Union[datetime, date],
        delimiter_date: str = '-',
        delimiter_time: str = ':',
        delimiter_date_time: str = ' ',
        delimiter: Union[str, None] = None
) -> str:
    if isinstance(time_value, (datetime, date)):
        d_t = delimiter_time
        d_d = delimiter_date
        d_dt = delimiter_date_time
        if delimiter is not None:
            d_t = delimiter
            d_d = delimiter
        # Convert delimiter variables to text
        strftime = strftime.format(d_d=d_d, d_t=d_t, d_dt=d_dt)
        return time_value.strftime(strftime)
    else:
        raise TypeError('Invalid type: expected datetime or date.')


def datetime_to_yyyy_mm_dd_hh_mm_ss(
        time_value: Union[datetime, date],
        delimiter_date: str = '-',
        delimiter_time: str = ':',
        delimiter_date_time: str = ' ',
        delimiter: Union[str, None] = None
) -> str:
    """
    Convert time to 'YYYY-MM-DD HH:MM:SS' format.
    """
    return _datetime_format(
        strftime='%Y{d_d}%m{d_d}%d{d_dt}%H{d_t}%M{d_t}%S',
        **locals()
    )


def datetime_to_yyyy_mm_dd_hh_mm(
        time_value: Union[datetime, date],
        delimiter_date: str = '-',
        delimiter_time: str = ':',
        delimiter_date_time: str = ' ',
        delimiter: Union[str, None] = None
) -> str:
    """
    Convert time to 'YYYY-MM-DD HH:MM' format.
    """
    return _datetime_format(
        strftime='%Y{d_d}%m{d_d}%d{d_dt}%H{d_t}%M',
        **locals()
    )


def datetime_to_yyyy_mm_dd(time_value: Union[datetime, date], delimiter: str = '-') -> str:
    """
    Convert time to 'YYYY-MM-DD' format.
    Example:
        > datetime_to_yyyy_mm_dd(now())
        > '2024-12-16'
    """
    if isinstance(time_value, (datetime, date)):
        return time_value.strftime(f'%Y{delimiter}%m{delimiter}%d')
    else:
        raise TypeError('Invalid type: expected datetime or date.')


def datetime_to_hh_mm_ss(time_value: Union[datetime, time], delimiter: str = '-') -> str:
    """
    Convert time to 'HH-MM-SS' format.
    Example:
        > datetime_to_hh_mm_ss(datetime.now(), delimiter=':')
        > '08:16:32'
    """
    if isinstance(time_value, (datetime, time)):
        return time_value.strftime(f'%H{delimiter}%M{delimiter}%S')
    else:
        raise TypeError('Invalid type: expected datetime or time.')


def datetime_to_hh_mm(time_value: Union[datetime, time], delimiter: str = '-') -> str:
    """
    Convert time to 'HH-MM' format.
    Example:
        > datetime_to_hh_mm(datetime.now(), delimiter=':')
        > '08:16'
    """
    if isinstance(time_value, (datetime, time)):
        return time_value.strftime(f'%H{delimiter}%M')
    else:
        raise TypeError('Invalid type: expected datetime or time.')


def get_datetime() -> datetime:
    """ Alias for the `now()` """
    return datetime.now()


def now() -> datetime:
    """ Return the current time """
    return datetime.now()


def delay(second: float):
    """ Alias for the `sleep()` """
    sleep(second)


def _regex_build_delimiter_pattern(delimiters: Union[str, List[str]], group_name) -> str:
    """ Helper function to construct regex pattern for delimiters """
    if isinstance(delimiters, str):
        delimiters = [delimiters]

    if isinstance(delimiters, list):
        escaped_delimiters = [re.escape(d) for d in delimiters]
        return f'(?P<{group_name}>' + '|'.join(escaped_delimiters) + ')'
    else:
        raise TypeError('Delimiter must be a string or a list of strings.')


def datetime_parse(
        s: str,
        raise_exception: bool = False,
        delimiter_date: Union[str, List[str]] = None,
        delimiter_time: Union[str, List[str]] = None,
        delimiter_date_time: Union[str, List[str]] = None,
        require_start: Union[str, bool] = False,
        require_end: Union[str, bool] = False,
        iso: bool = False,
        iso_basic: bool = False,
        no_time: bool = False,
) -> Union[datetime, None]:
    """
    Parses a string containing a date and time in various formats into a `datetime` object.

    :param s:
        The string to parse.
    :param raise_exception:
        If `True`, raises an exception on parsing errors. If `False`, returns `None` on failure. Default is `False`.
    :param delimiter_date:
        Delimiters used between date components (year, month, day). Can be a single string or a list of strings. Default is `['-', '/']`.
    :param delimiter_time:
        Delimiters used between time components (hour, minute, second). Can be a single string or a list of strings. Default is `['-', ':']`.
    :param delimiter_date_time:
        Delimiters used between the date and time parts. Can be a single string or a list of strings. Default is `[' ', '_', '-', 'T']`.
    :param require_start:
        If `True`, the date must be at the start of the string (adds `^` in regex). If `False`, no requirement. If a string, it is used as the starting pattern in regex. Default is `False`.
    :param require_end:
        If `True`, the date must be at the end of the string (adds `$` in regex). If `False`, no requirement. If a string, it is used as the ending pattern in regex. Default is `False`.
    :param iso:
        If `True`, only matches ISO 8601 format (`YYYY-MM-DD HH:MM[:SS]`). Default is `False`.
    :param iso_basic:
        If `True`, only matches basic ISO 8601 format without delimiters (`YYYYMMDDHHMMSS`). Default is `False`.
    :param no_time:
        If `True`, only matches date parts (no time required). Default is `False`.

    :return:
        A `datetime` object if parsing is successful, otherwise `None`.

    :raises ValueError:
        If the string does not match any expected format or contains invalid date/time, and `raise_exception` is `True`.
    :raises TypeError:
        If any of the delimiter parameters are neither strings nor lists of strings.

    .. note::
        The function attempts to parse the input string using multiple date and time formats.
        It returns the first successfully parsed `datetime` object.

        If `iso` is set to `True`, only the standard ISO 8601 format (`YYYY-MM-DD HH:MM[:SS]`) is considered during parsing.

        If `iso_basic` is set to `True`, only the basic ISO 8601 format without delimiters (`YYYYMMDDHHMMSS`) is considered.

        If `require_start` or `require_end` are strings, they are directly used in the regex patterns to enforce custom start or end conditions.

        Two-digit years are assumed to be in the 2000s. For example, `'21'` becomes `2021`.

        Delimiters can be customized to match various date and time formats.

    **Examples**:

    >>> datetime_parse("2022-12-31 23:59:59")
    datetime.datetime(2022, 12, 31, 23, 59, 59)

    >>> datetime_parse("2022/12/31_23-59", delimiter_date='/', delimiter_time='-')
    datetime.datetime(2022, 12, 31, 23, 59)

    >>> datetime_parse("2022-12-31 23:59 Log", require_end=True)
    None

    >>> datetime_parse("20221231T235959", delimiter_date_time='T', iso_basic=True)
    datetime.datetime(2022, 12, 31, 23, 59, 59)

    >>> datetime_parse("2022-12-31", no_time=True)
    datetime.datetime(2022, 12, 31, 0, 0)

    >>> datetime_parse("Invalid date", raise_exception=False)
    None
    """

    # Default values
    if delimiter_date is None:
        delimiter_date = ['-', '/']
    if delimiter_time is None:
        delimiter_time = ['-', ':']
    if delimiter_date_time is None:
        delimiter_date_time = [' ', '_', '-', 'T']

    # Define common regex patterns
    yyyy = r'(?P<year>\d{4})'
    yy = r'(?P<year>\d{2})'
    mm = r'(?P<month>[0-1][0-9])'
    dd = r'(?P<day>\d{2})'
    hh = r'(?P<hour>[0-2][0-9])'
    mn = r'(?P<minute>[0-5][0-9])'
    ss = r'(?P<second>\d{2})'

    # Build the regex patterns for each delimiter
    d_d = _regex_build_delimiter_pattern(delimiter_date, 'd_d')
    d_t = _regex_build_delimiter_pattern(delimiter_time, 'd_t')
    d_dt = _regex_build_delimiter_pattern(delimiter_date_time, 'd_dt')

    # Optionally enforce start and end of string
    if isinstance(require_start, str):
        start_pattern = require_start
    elif isinstance(require_start, bool):
        start_pattern = '^' if require_start else ''
    else:
        raise TypeError('require_start must be a string or bool.')

    if isinstance(require_end, str):
        end_pattern = require_end
    elif isinstance(require_end, bool):
        end_pattern = '$' if require_end else ''
    else:
        raise TypeError('require_end must be a string or bool.')

    datetime_regexes_iso_human = [
        # YYYY-MM-DD_HH:MM:SS   (iso, human version)
        f'{yyyy}{d_d}{mm}(?P=d_d){dd}{d_dt}{hh}{d_t}{mn}(?P=d_t){ss}',

        # YYYY-MM-DD_HH:MM   (iso, human version)
        f'{yyyy}{d_d}{mm}(?P=d_d){dd}{d_dt}{hh}{d_t}{mn}',
    ]

    datetime_regexes_iso_compact = [
        # YYYYMMDD_HHMMSS   (iso, timestamp, basic version)
        f'{yyyy}{mm}{dd}{d_dt}{hh}{mn}{ss}',

        # YYYYMMDD_HHMM   (iso, timestamp, basic version)
        f'{yyyy}{mm}{dd}{d_dt}{hh}{mn}',
    ]

    datetime_regexes_short_year = [
        # YY-MM-DD_HH:MM:SS
        f'{yy}{d_d}{mm}(?P=d_d){dd}{d_dt}{hh}{d_t}{mn}(?P=d_t){ss}',

        # YY-MM-DD_HH:MM
        f'{yy}{d_d}{mm}(?P=d_d){dd}{d_dt}{hh}{d_t}{mn}',
    ]

    datetime_regexes_day_first_strange_format = [
        # DD-MM-YYYY_HH:MM:SS
        f'{dd}{d_d}{mm}(?P=d_d){yyyy}{d_dt}{hh}{d_t}{mn}(?P=d_t){ss}',

        # DD-MM-YYYY_HH:MM
        f'{dd}{d_d}{mm}(?P=d_d){yyyy}{d_dt}{hh}{d_t}{mn}',
    ]

    datetime_regexes_date_only = [
        # YYYY-MM-DD   (date only)
        f'{yyyy}{d_d}{mm}(?P=d_d){dd}',

        # YYYYMMDD   (date only)
        f'{yyyy}{mm}{dd}',
    ]

    if no_time is False:
        datetime_regexes_date_only = []

    datetime_regexes = [
        *datetime_regexes_iso_human,

        *datetime_regexes_iso_compact,

        *datetime_regexes_short_year,

        *datetime_regexes_date_only,

        *datetime_regexes_day_first_strange_format,
    ]

    if iso:
        datetime_regexes = datetime_regexes_iso_human
        iso_basic = False

    if iso_basic:
        datetime_regexes = datetime_regexes_iso_compact

    for regex in datetime_regexes:
        match = re.search(start_pattern + regex + end_pattern, s)
        if match:
            try:
                groups = match.groupdict()
                # Extract components with default values
                year_str = groups.get('year')
                month = int(groups.get('month'))
                day = int(groups.get('day'))
                hour = int(groups.get('hour', '0'))
                minute = int(groups.get('minute', '0'))
                second = int(groups.get('second', '0'))

                # Adjust year based on length of the year string
                if len(year_str) == 2:
                    year = int(year_str) + 2000  # Adjust as needed
                else:
                    year = int(year_str)

                # Create and return the datetime object
                return datetime(year, month, day, hour, minute, second)

            except Exception as e:
                if raise_exception:
                    raise ValueError(f"Error parsing datetime: {e}")
                return None

    # If no regex matched
    if raise_exception:
        raise ValueError("No matching datetime format found.")
    return None


# Config ################################################################


def dict_cast_values(dict_values: Dict[str, Any], default_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively cast the dict values to the types of the default values.

    Parameters:
    dict_values (Dict[str, Any]): The values from the dict.
    default_values (Dict[str, Any]): The default values with types.

    Returns:
    Dict[str, Any]: The dict values with casted types.
    """
    dict_values_casted = {}
    for key, default_value in default_values.items():
        value = dict_values.get(key, default_value)
        if isinstance(default_value, bool):
            casted_value = bool(value)
        elif isinstance(default_value, int):
            casted_value = int(value)
        elif isinstance(default_value, float):
            casted_value = float(value)
        elif isinstance(default_value, Path):
            casted_value = Path(value)
        elif isinstance(default_value, dict) and isinstance(value, dict):
            casted_value = dict_cast_values(value, default_value)
        else:
            casted_value = value  # Keep as string or original type for other types
        dict_values_casted[key] = casted_value
    return dict_values_casted


def _set_global_variables(config: Dict[str, Any]) -> None:
    """
    Set global variables from config dictionary.
    
    Parameters:
    config (Dict[str, Any]): Configuration dictionary
    """
    for key, value in config.items():
        # Set the global variable
        globals()[key] = value


def load_config_from_yaml(config_file: Path, default_values: Dict[str, Any]) -> None:
    """
    Load config from YAML file or create with defaults. Set global variables.

    Parameters:
    config_file (Path): Path to YAML file
    default_values (Dict[str, Any]): Default config values

    Types handled: bool, int, float, Path, Dict. Others kept as strings.

    Examples:
    > load_config_from_yaml(Path('config.yaml'), {'debug': False, 'retries': 3})
    > print(retries)
    """

    import yaml

    if not config_file.exists():
        with open(config_file, 'w') as file:
            yaml.dump(default_values, file)
        print(f'Created default configuration file: {config_file}')
        config = default_values
    else:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

    # Apply casting for all default values
    casted_config = dict_cast_values(config, default_values)

    _set_global_variables(casted_config)


def load_config_from_ini(config_file: Path, default_values: Dict[str, Any], section_name: str = 'DEFAULT') -> None:
    """
    Load config from INI file or create with defaults. Set global variables.

    Parameters:
    config_file (Path): Path to INI file
    default_values (Dict[str, Any]): Default config values
    section_name (str): INI section name, default 'DEFAULT'

    Types handled: bool, int, float, Path. Others kept as strings.

    Examples:
    > load_config_from_ini(Path('config.ini'), {'debug': False, 'retries': 3})
    > print(retries)
    """

    import configparser

    config = configparser.ConfigParser()

    if not config_file.exists():
        # Convert all values to strings for initial config creation
        string_defaults = {k: str(v) for k, v in default_values.items()}
        config[section_name] = string_defaults
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print(f'Created default configuration file: {config_file}')
    else:
        config.read(config_file)

    # Apply casting for all default values
    casted_config = dict_cast_values(dict(config[section_name]), default_values)

    _set_global_variables(casted_config)


def load_config_from_json(config_file: Path, default_values: Dict[str, Any]) -> None:
    """
    Load config from JSON file or create with defaults. Set global variables.

    Parameters:
    config_file (Path): Path to JSON file
    default_values (Dict[str, Any]): Default config values

    Types handled: bool, int, float, Path, Dict. Others kept as strings.

    Examples:
    > load_config_from_json(Path('config.json'), {'debug': False, 'retries': 3})
    > print(retries)
    """

    import json

    if not config_file.exists():
        with open(config_file, 'w') as file:
            json.dump(default_values, file, indent=4)
        print(f"Created default configuration file: {config_file}")
        config = default_values
    else:
        with open(config_file, 'r') as file:
            config = json.load(file)

    # Apply casting for all default values
    casted_config = dict_cast_values(config, default_values)

    _set_global_variables(casted_config)


# Text utils ################################################################

def load_from_yaml(yaml_file: Union[Path, str], encoding: str = 'utf-8') -> Dict:
    import yaml

    with open(Path(yaml_file), 'r', encoding=encoding) as f:
        store = yaml.safe_load(f)
    return store

def save_to_yaml(yaml_file: Union[Path, str], data: Dict, encoding: str = 'utf-8', check_file_content: bool = True) -> None:
    import yaml

    data = yaml.dump(data, default_flow_style=False, allow_unicode=True)
    if (check_file_content == False or
        (check_file_content and get_file_content(yaml_file, encoding=encoding) != data)):
        
        with open(yaml_file, 'w', encoding=encoding) as f:
            f.write(data)

# Utils ################################################################

def contains_path_glob_pattern(input_string):
    # Detect a regular expression pattern to match Path.glob or Path.rglob patterns
    glob_pattern = r'[*?[]'
    match = re.search(glob_pattern, input_string)
    return bool(match)
