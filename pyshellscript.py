# coding: utf-8
# about: Library for shell scripting in Python
# ver: 2024-03-24
# author: heX
# url: https://github.com/heX16

from pathlib import Path
import os
import sys
import stat
from datetime import datetime, time, date, timedelta
import subprocess
from subprocess import CompletedProcess, Popen
import shutil
import re
import typing
from typing import Any, Callable, Dict, Set, List, Optional
import platform

try:
    import psutil  # pip install psutil
except ImportError:
    psutil = None


# OS ################################################################


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


# Files ################################################################


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
    set_create_time(destination_path, get_create_time(source_path))
    # log(f'File {source_path} copied to {destination_path}')


def cp(source: Path | str, destination: Path | str):
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
    :paran error_code: Error codes (not working - under development).
    """
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
        set_create_time(destination_path, get_create_time(source_path))


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
    source_path = Path("path/to/source/file.txt")
    destination_directory = Path("path/to/destination/")
    move_file_to_dir(source_path, destination_directory)
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
        directory_path: Path | str,
        search_mask: str,
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
        for file in find('~/', '*', recursively=True):
            print(str(file))

        for file in find('~/', '*', recursively=True):
            if file.stat().st_size > 1024 * 1024:  # File size more 1 mb
                print(str(file))

        files = find('~/', '*', recursively=True)
        if files:
            print('File list:')
            for file in files:
                print(str(file))
        else:
            print('File not found')

    """
    directory_path = Path(directory_path).expanduser()
    if not directory_path.exists():
        raise FileNotFoundError(f"The directory {directory_path} does not exist.")

    if recursively:
        return Path(directory_path).rglob(search_mask)
    else:
        return Path(directory_path).glob(search_mask)


def find_dir(directory_path: Path | str, search_mask: str, recursively: bool = False):
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
        for directory in find_directories('~/', 'subdir*', recursively=True):
            print(str(directory))
    """

    def dir_generator(path, mask, recursive):
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
        raise FileNotFoundError(f"The directory {directory_path} does not exist.")

    return dir_generator(directory_path, search_mask, recursively)


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
        set_current_dir('/path/to/new/directory')  # Changes the current working directory
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
        if check_ext(Path("example.txt"), ['txt', 'md']):
            print(f"Extension is allowed.")
    """
    ext_list = [i.lower() for i in ext_list]
    return (ext_list[0] == '*') or (Path(f).suffix.lower()[1:] in ext_list)


def get_file_size(file_path: Path | str) -> int:
    return file_path.stat().st_size


def get_last_modified_time(file_path: Path | str) -> datetime:
    return datetime.fromtimestamp(Path(file_path).stat().st_mtime)


def set_last_modified_time(file_path: Path | str, new_last_modified: datetime):
    file_path = Path(file_path)

    if not file_path.exists() or not file_path.is_file():
        print(f'The file {file_path} does not exist or is not a file.')
        return

    timestamp = new_last_modified.timestamp()

    # file_path.touch()
    os.utime(file_path, (timestamp, timestamp))


def get_create_time(file_path: Path | str) -> datetime:
    path = Path(file_path)
    # On Windows, `os.path.getctime()` returns the creation date.
    # On Unix-like systems, it returns the last metadata change on a file or directory.
    # For actual file creation date, this might not be accurate on Unix-like systems.
    # TODO: `Path.stat().birthtime`: Creation time(on some Unix systems in the FreeBSD family, including macOS)
    # TODO: This method normally follows symlinks; to stat a symlink add the argument follow_symlinks=False, or use lstat().
    creation_time = os.path.getctime(path)
    return datetime.fromtimestamp(creation_time)


def set_create_time(file_path: Path | str, new_create_date: datetime):
    """
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


# Run ################################################################


# Error code after function call `run_command` or `sh`.
# This variable is used after invoking `run_command` or `sh`.
returncode = None


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

def run_command(command: str,
                capture_output=False,
                input=None,
                stdin=None,
                background=False,
                ensure_unique=False,
                return_returncode=False,
                raise_exception=False) -> subprocess.CompletedProcess | subprocess.Popen | int | bool:
    """
    Executes a command with options to run in the background, capture output, ensure it runs only once, and handle stdin.

    Parameters:
    - command (str): The shell command to execute.
    - background (bool): Whether to run the command in the background. Defaults to False.
    - capture_output (bool): Whether to capture the command's stdout and stderr. Defaults to False.
    - ensure_unique (bool): Ensure the command runs only if it's not already running. Defaults to False.
    - raise_exception (bool): Whether to raise an exception if the command is already running and ensure_unique is True.
    - input (str): String to send to the stdin of the subprocess.
    - stdin (subprocess.PIPE or similar): The stdin stream for the subprocess. This should not be used together with 'input'.

    Returns:
    - Returns a `subprocess.Popen` instance. Useful variables: returncode, stdout, stderr.
    - If return_returncode==True returns error code `int`.
    - If ensure_unique==True and the process already present, returns `False`.

    Raises:
    - RuntimeError: If ensure_unique is True and raise_exception is True and the process is already running.
    - ValueError: If both 'input' and 'stdin' are provided.

    Examples:
        ```
        output = run_command('cat test.txt', capture_output=True)
        if output.stdout:
            grep_output = run_command('grep test_line', capture_output=True, input=output.stdout)
            print(grep_output.stdout)
    """
    # TODO: add argument `ensure_unique_check_param = True`
    # TODO: add argument `wait_time_if_found = -1`
    # TODO: add argument `timeout = -1`
    # TODO: add argument `print_result = False` ?

    global returncode

    if input is not None and stdin is not None:
        raise ValueError("Both 'input' and 'stdin' cannot be provided simultaneously.")
    if background and return_returncode:
        raise ValueError("Both 'background' and 'return_returncode' cannot be provided simultaneously.")
    if background and capture_output:
        raise ValueError("Both 'background' and 'capture_output' cannot be provided simultaneously.")

    if ensure_unique:
        # TODO: [BUG] get_filename(command) - need add the trim of the param part
        proc_name = str(get_filename(command))
        if proc_present(proc_name):
            returncode = None
            if raise_exception:
                raise RuntimeError(f"{proc_name} is already running.")
            else:
                return False

    stdin_setting = None
    if stdin is not None:
        stdin_setting = stdin
    elif input is not None:
        stdin_setting = subprocess.PIPE

    stdout_setting = subprocess.PIPE if capture_output else None

    process = subprocess.Popen(
        command, shell=True,
        stdin=stdin_setting, stdout=stdout_setting, stderr=subprocess.PIPE, text=True, universal_newlines=True)
    if input is not None:
        process.stdin.write(input.encode('utf-8'))
        process.stdin.close()

    if not background:
        process.wait()
        returncode = process.returncode

    if return_returncode:
        return process.returncode
    else:
        return process


def sh(command_string: str, background=False, capture_output=False, ensure_unique=False):
    """
    Executes multiple shell commands provided in a single string, separated by newlines.

    Parameters:
    - command_string (str): A string containing multiple commands separated by newlines.
    - background (bool): Whether to run the commands in the background. Defaults to False.
    - capture_output (bool): Whether to capture the commands' stdout and stderr. Defaults to False.
    - ensure_unique (bool): Ensure each command runs only if it's not already running. Defaults to False.

    Returns:
    - If command is one - result of the `run_command` calls.
    - If command is multiline - list of results of the `run_command` calls.
    """
    # TODO: `stop_on_error=False`
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
        # Get a list of all processes
        process_list = get_proc_list()

        # Convert the process list to a dictionary with specified attributes
        ps = proc_list_to_dict(process_list, ['exe', 'pid'])

        # Create a dictionary mapping executable paths to process IDs
        ps_exec = dict()
        for p in ps:
            ps_exec.update({Path(p['exe']): p['pid']})

        print(ps_exec)
    """
    if psutil is None:
        raise ImportError("The psutil library is required but not installed. Install it using 'pip install psutil'")

    result = []
    if only_system:
        skip_system = False
    for p in psutil.process_iter():
        try:
            sys = False
            u = p.username()
            if skip_core and (u is None):
                continue
            if (u == 'NT AUTHORITY\\SYSTEM' or
                    u == 'NT AUTHORITY\\LOCAL SERVICE' or
                    u == 'NT AUTHORITY\\SYSTEM'):
                sys = True
            if skip_system and sys:
                continue
            cmd = p.cmdline()
            if skip_core and (cmd is None or cmd == ''):
                continue
            if only_system and not sys:
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
    @return: list[dict] -- List of dictionaries with keys as attributes and values as the corresponding process information.
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


def print_process_list_example(process_list, print_format="{:<8} {:<30} {:<10} {}"):
    """
    Example:
    print_process_list(proc_list_to_dict(proc_list(), ['pid', 'username', 'cpu_times', 'cmdline']))
    """
    print(print_format.format('PID', 'USER', 'TIME', 'COMMAND'))

    for p in process_list:
        print(print_format.format(
            str(p['pid']),
            str(p['username']),
            round(p['cpu_times'].user + p['cpu_times'].system, 2),
            '-' if p['cmdline'] is None else ' '.join(p['cmdline'])
        ))


# Strings ################################################################

def str_present(target_str: str, find_substr: str) -> bool:
    return False if target_str.find(find_substr) == -1 else True


def get_filename(path: Path | str) -> Path:
    """ Extract filename (with extension) """
    path = Path(path)
    return Path(path.name)


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


def get_datetime() -> datetime:
    return datetime.now()


def now() -> datetime:
    return datetime.now()


# Utils ################################################################


def contains_path_glob_pattern(input_string):
    # Define a regular expression pattern to match Path.glob or Path.rglob patterns
    glob_pattern = r'[*?[]'
    match = re.search(glob_pattern, input_string)
    return bool(match)
