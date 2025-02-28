import os
import time
from pathlib import Path

# Constants for the test
TEST_DIR = Path('%temp%/test_50k_files_del_me')
NUM_FILES = 50000
NUM_DIRS = 10

def setup_test_directory():
    """Setup the test directory with the required number of files and directories."""
    TEST_DIR.mkdir(exist_ok=True)

    # Create files
    files_created = len(list(TEST_DIR.glob('*'))) - len(list(TEST_DIR.glob('*/')))
    for i in range(files_created, NUM_FILES):
        file_path = TEST_DIR / f'file_{i}.txt'
        file_path.touch(exist_ok=True)

    # Create directories
    dirs_created = len(list(TEST_DIR.glob('*/')))
    for i in range(dirs_created, NUM_DIRS):
        dir_path = TEST_DIR / f'dir_{i}'
        dir_path.mkdir(exist_ok=True)

def warm_up_cache():
    """Enumerate all files and directories multiple times to warm up the cache."""
    for _ in range(5):  # Repeat 5 times for thorough caching
        list(TEST_DIR.iterdir())

def test_path_glob():
    """Test Path.glob method and measure its duration."""
    start_time = time.perf_counter()
    directories = list(TEST_DIR.glob('*/'))
    duration = time.perf_counter() - start_time
    return len(directories), duration * 1000  # Convert to milliseconds

def test_os_scandir():
    """Test os.scandir method and measure its duration."""
    start_time = time.perf_counter()
    directories = [entry for entry in os.scandir(TEST_DIR) if entry.is_dir()]
    duration = time.perf_counter() - start_time
    return len(directories), duration * 1000  # Convert to milliseconds

# Setup test environment
setup_test_directory()
warm_up_cache()

# Run both tests
glob_count, glob_duration = test_path_glob()
scandir_count, scandir_duration = test_os_scandir()

print('glob:', glob_count, glob_duration, 'scandir:', scandir_count, scandir_duration)

