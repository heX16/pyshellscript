import unittest
from pathlib import Path
import shutil
import os
import sys
from datetime import datetime, timedelta
import time as time_module

from pyshellscript import *


class TestFileCopyFunctions(unittest.TestCase):
    test_dir = Path('file_op_tests')

    def setUp(self):
        # Create test directory
        self.test_dir.mkdir(exist_ok=True)
        # Paths to source and destination directories
        self.source_dir = self.test_dir / 'source'
        self.destination_dir = self.test_dir / 'destination'
        self.source_dir.mkdir(exist_ok=True)
        self.destination_dir.mkdir(exist_ok=True)
        # Create test files
        (self.source_dir / 'file1.txt').write_text('Contents of file 1.')
        (self.source_dir / 'file2.txt').write_text('Contents of file 2.')
        # Create subdirectory with a file
        self.sub_dir = self.source_dir / 'subdir'
        self.sub_dir.mkdir(exist_ok=True)
        (self.sub_dir / 'file3.txt').write_text('Contents of file 3 in subdirectory.')

    def tearDown(self):
        # Remove test directory after each test
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_copy_file(self):
        # Test copy_file function
        source_file = self.source_dir / 'file1.txt'
        destination_file = self.destination_dir / 'copied_file1.txt'

        copy_file(source_file, destination_file)

        # Check that the file was copied
        self.assertTrue(destination_file.exists())
        self.assertEqual(source_file.read_text(), destination_file.read_text())

    def test_copy_files(self):
        # Test copy_files function
        copy_files(self.source_dir, self.destination_dir)

        # Check that all files are copied
        expected_files = [
            self.destination_dir / 'file1.txt',
            self.destination_dir / 'file2.txt',
            self.destination_dir / 'subdir' / 'file3.txt',
        ]
        for file_path in expected_files:
            self.assertTrue(file_path.exists())

        # Check file contents
        for file_path in expected_files:
            original_file = self.source_dir / file_path.relative_to(self.destination_dir)
            self.assertEqual(file_path.read_text(), original_file.read_text())

    def test_copy_file_with_progress(self):
        # Test copy_file_with_progress function
        source_file = self.source_dir / 'file2.txt'
        destination_file = self.destination_dir / 'copied_file2.txt'

        def progress_callback(data, data_len, copied_size, file_size, user_data, error_code):
            progress = copied_size / file_size * 100
            user_data['progress'] = progress

        user_data = {'progress': 0}

        copy_file_with_progress(
            source_file,
            destination_file,
            callback=progress_callback,
            callback_user_data=user_data,
            callback_print_progress=None  # Disable stdout progress output
        )

        # Check that the file was copied
        self.assertTrue(destination_file.exists())
        self.assertEqual(source_file.read_text(), destination_file.read_text())
        # Check that progress reached 100%
        self.assertEqual(user_data['progress'], 100.0)

    def test_format_bytes(self):
        # Test format_bytes function
        self.assertEqual(format_bytes(0), '0 B')
        self.assertEqual(format_bytes(500), '500 B')
        self.assertEqual(format_bytes(1000), '1 KB')
        self.assertEqual(format_bytes(1500), '2 KB')
        self.assertEqual(format_bytes(1024 * 1024), '1 MB')
        self.assertEqual(format_bytes(1024 * 1024 * 1024), '1 GB')
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 1024), '1 TB')

    def test_cp_function(self):
        # Test cp function
        source_file = self.source_dir / 'file1.txt'
        destination_file = self.destination_dir / 'cp_copied_file1.txt'

        cp(source_file, destination_file)

        # Check that the file was copied
        self.assertTrue(destination_file.exists())
        self.assertEqual(source_file.read_text(), destination_file.read_text())

        # Test copying directory
        new_destination_dir = self.test_dir / 'new_destination'
        cp(self.source_dir, new_destination_dir)

        # Check that all files are copied
        expected_files = [
            new_destination_dir / 'file1.txt',
            new_destination_dir / 'file2.txt',
            new_destination_dir / 'subdir' / 'file3.txt',
        ]
        for file_path in expected_files:
            self.assertTrue(file_path.exists())

    @unittest.skipIf(os.name == 'nt', "Skipping symlink test on Windows")
    def test_copy_symlink(self):
        # Test copying symbolic link
        symlink_target = self.source_dir / 'file1.txt'
        symlink_link = self.source_dir / 'symlink_to_file1.txt'
        symlink_link.symlink_to(symlink_target)

        destination_link = self.destination_dir / 'symlink_to_file1.txt'

        copy_file_with_progress(
            symlink_link,
            destination_link,
            follow_symlinks=False,  # Copy as link
            callback_print_progress=None
        )

        # Check that symlink was copied as link
        self.assertTrue(destination_link.is_symlink())
        self.assertEqual(destination_link.resolve(), symlink_target.resolve())

    def test_copy_file_overwrite(self):
        # Test overwriting existing file
        destination_file = self.destination_dir / 'file1.txt'
        destination_file.write_text('Old content')

        source_file = self.source_dir / 'file1.txt'

        copy_file(source_file, destination_file)

        # Check that file was overwritten
        self.assertEqual(destination_file.read_text(), source_file.read_text())

    def test_copy_nonexistent_file(self):
        # Test copying a nonexistent file raises FileNotFoundError
        source_file = self.source_dir / 'nonexistent.txt'
        destination_file = self.destination_dir / 'nonexistent.txt'

        with self.assertRaises(FileNotFoundError):
            copy_file(source_file, destination_file)

    def test_copy_to_nonexistent_directory(self):
        # Test copying to a nonexistent directory raises FileNotFoundError
        source_file = self.source_dir / 'file1.txt'
        destination_dir = self.destination_dir / 'nonexistent_directory'
        destination_file = destination_dir / 'file1.txt'

        with self.assertRaises(FileNotFoundError):
            copy_file(source_file, destination_file)

    def test_copy_empty_directory(self):
        # Test copying an empty directory
        empty_dir = self.source_dir / 'empty_dir'
        empty_dir.mkdir()
        copy_files(empty_dir, self.destination_dir / 'empty_dir_copy')

        # Check that the empty directory was copied
        copied_empty_dir = self.destination_dir / 'empty_dir_copy'
        self.assertTrue(copied_empty_dir.exists())
        self.assertTrue(copied_empty_dir.is_dir())
        # Check that directory is empty
        self.assertEqual(len(list(copied_empty_dir.iterdir())), 0)

    def test_copy_large_number_of_files(self):
        # Test copying a large number of files
        for i in range(100):
            (self.source_dir / f'file_{i}.txt').write_text(f'Contents of file {i}')

        copy_files(self.source_dir, self.destination_dir)

        for i in range(100):
            copied_file = self.destination_dir / f'file_{i}.txt'
            self.assertTrue(copied_file.exists())
            self.assertEqual(copied_file.read_text(), f'Contents of file {i}')

    def test_copy_large_file(self):
        # Test copying a large file
        large_file = self.source_dir / 'large_file.txt'
        large_file_content = 'A' * (10 * 1024 * 1024)  # 10 MB file
        large_file.write_text(large_file_content)

        destination_file = self.destination_dir / 'large_file.txt'

        copy_file_with_progress(large_file, destination_file, callback_print_progress=None)

        self.assertTrue(destination_file.exists())
        self.assertEqual(destination_file.stat().st_size, large_file.stat().st_size)
        self.assertEqual(destination_file.read_text(), large_file_content)

    @unittest.skipIf(os.name == 'nt', "Skipping permission test on Windows")
    def test_copy_file_no_permission(self):
        # Test copying a file without permission
        source_file = self.source_dir / 'file1.txt'
        destination_file = self.destination_dir / 'file1.txt'

        # Remove write permissions from destination directory
        self.destination_dir.chmod(0o555)

        try:
            with self.assertRaises(PermissionError):
                copy_file(source_file, destination_file)
        finally:
            # Restore permissions
            self.destination_dir.chmod(0o755)

    def test_format_bytes_invalid_input(self):
        # Test format_bytes with invalid input
        with self.assertRaises(TypeError):
            format_bytes('not a number')


class TestFileTimeFunctions(unittest.TestCase):
    test_dir = Path('file_time_tests')

    def setUp(self):
        # Create test directory
        self.test_dir.mkdir(exist_ok=True)
        # Create test file
        self.test_file = self.test_dir / 'test_file.txt'
        self.test_file.write_text('Test file content')

    def tearDown(self):
        # Remove test directory after each test
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_get_file_write_time(self):
        # Test getting file modification time
        write_time = get_file_write_time(self.test_file)

        # Check that the returned value is a datetime object
        self.assertIsInstance(write_time, datetime)

        # Check that the time is recent (within the last minute)
        now = datetime.now()
        self.assertLess(now - write_time, timedelta(minutes=1))

    def test_set_file_write_time(self):
        # Test setting file modification time
        # Set to a time in the past
        new_time = datetime.now() - timedelta(days=10)
        set_file_write_time(self.test_file, new_time)

        # Get the time and check it was set correctly
        current_time = get_file_write_time(self.test_file)

        # Compare with a small tolerance for timestamp conversion
        self.assertLess(abs(current_time.timestamp() - new_time.timestamp()), 2)

    def test_get_file_create_time(self):
        # Test getting file creation time
        create_time = get_file_create_time(self.test_file)

        # Check that the returned value is a datetime object
        self.assertIsInstance(create_time, datetime)

        # Check that the time is recent (within the last minute)
        now = datetime.now()
        self.assertLess(now - create_time, timedelta(minutes=1))

    def test_set_file_create_time_basic_functionality(self):
        # Test basic functionality - setting creation time and verifying it was set
        original_create_time = get_file_create_time(self.test_file)
        new_time = datetime(2020, 5, 15, 10, 30, 0)
        
        # Set new creation time
        set_file_create_time(self.test_file, new_time)
        
        # Get creation time after setting
        updated_create_time = get_file_create_time(self.test_file)
        
        # Verify the creation time was actually changed
        # Allow small tolerance for timestamp conversion (within 2 seconds)
        time_diff = abs(updated_create_time.timestamp() - new_time.timestamp())
        self.assertLess(time_diff, 2, 
                       f"Creation time not set correctly. Expected: {new_time}, Got: {updated_create_time}")

    def test_set_file_create_time_past_date(self):
        # Test setting creation time to a date in the past
        past_time = datetime(2018, 1, 1, 0, 0, 0)
        
        set_file_create_time(self.test_file, past_time)
        
        updated_time = get_file_create_time(self.test_file)
        time_diff = abs(updated_time.timestamp() - past_time.timestamp())
        self.assertLess(time_diff, 2)

    def test_set_file_create_time_future_date(self):
        # Test setting creation time to a date in the future
        future_time = datetime.now() + timedelta(days=30)
        
        set_file_create_time(self.test_file, future_time)
        
        updated_time = get_file_create_time(self.test_file)
        time_diff = abs(updated_time.timestamp() - future_time.timestamp())
        self.assertLess(time_diff, 2)

    def test_set_file_create_time_epoch_time(self):
        # Test setting creation time to Unix epoch
        epoch_time = datetime(1970, 1, 1, 0, 0, 0)
        
        set_file_create_time(self.test_file, epoch_time)
        
        updated_time = get_file_create_time(self.test_file)
        time_diff = abs(updated_time.timestamp() - epoch_time.timestamp())
        self.assertLess(time_diff, 2)

    def test_set_file_create_time_microseconds_precision(self):
        # Test setting creation time with microseconds precision
        precise_time = datetime(2022, 6, 15, 14, 30, 45, 123456)
        
        set_file_create_time(self.test_file, precise_time)
        
        updated_time = get_file_create_time(self.test_file)
        # For microseconds precision, allow slightly larger tolerance
        time_diff = abs(updated_time.timestamp() - precise_time.timestamp())
        self.assertLess(time_diff, 2)

    def test_set_file_create_time_multiple_changes(self):
        # Test changing creation time multiple times
        time1 = datetime(2020, 1, 1, 12, 0, 0)
        time2 = datetime(2021, 6, 15, 18, 30, 0)
        time3 = datetime(2019, 12, 31, 23, 59, 59)
        
        # First change
        set_file_create_time(self.test_file, time1)
        updated_time1 = get_file_create_time(self.test_file)
        self.assertLess(abs(updated_time1.timestamp() - time1.timestamp()), 2)
        
        # Second change
        set_file_create_time(self.test_file, time2)
        updated_time2 = get_file_create_time(self.test_file)
        self.assertLess(abs(updated_time2.timestamp() - time2.timestamp()), 2)
        
        # Third change
        set_file_create_time(self.test_file, time3)
        updated_time3 = get_file_create_time(self.test_file)
        self.assertLess(abs(updated_time3.timestamp() - time3.timestamp()), 2)

    def test_set_file_create_time_different_file_types(self):
        # Test with different file types
        
        # Text file
        txt_file = self.test_dir / 'test.txt'
        txt_file.write_text('Text content')
        new_time = datetime(2020, 3, 10, 15, 45, 0)
        set_file_create_time(txt_file, new_time)
        updated_time = get_file_create_time(txt_file)
        self.assertLess(abs(updated_time.timestamp() - new_time.timestamp()), 2)
        
        # Binary file
        bin_file = self.test_dir / 'test.bin'
        bin_file.write_bytes(b'\x00\x01\x02\x03\xFF')
        set_file_create_time(bin_file, new_time)
        updated_time = get_file_create_time(bin_file)
        self.assertLess(abs(updated_time.timestamp() - new_time.timestamp()), 2)
        
        # Empty file
        empty_file = self.test_dir / 'empty.txt'
        empty_file.touch()
        set_file_create_time(empty_file, new_time)
        updated_time = get_file_create_time(empty_file)
        self.assertLess(abs(updated_time.timestamp() - new_time.timestamp()), 2)

    def test_set_file_create_time_large_file(self):
        # Test with large file
        large_file = self.test_dir / 'large_file.dat'
        large_content = b'X' * (5 * 1024 * 1024)  # 5 MB file
        large_file.write_bytes(large_content)
        
        new_time = datetime(2019, 8, 20, 11, 15, 30)
        set_file_create_time(large_file, new_time)
        
        updated_time = get_file_create_time(large_file)
        self.assertLess(abs(updated_time.timestamp() - new_time.timestamp()), 2)

    def test_set_file_create_time_path_vs_string(self):
        # Test that function works the same with Path objects and strings
        new_time = datetime(2021, 12, 25, 0, 0, 0)
        
        # Test with Path object
        set_file_create_time(self.test_file, new_time)
        time_from_path = get_file_create_time(self.test_file)
        
        # Reset file
        self.test_file.touch()
        
        # Test with string path
        set_file_create_time(str(self.test_file), new_time)
        time_from_string = get_file_create_time(self.test_file)
        
        # Both should result in the same time
        self.assertLess(abs(time_from_path.timestamp() - time_from_string.timestamp()), 1)

    def test_set_file_create_time_preserve_other_times(self):
        # Test that setting creation time doesn't affect modification time
        original_mod_time = get_file_write_time(self.test_file)
        new_create_time = datetime(2018, 6, 1, 10, 0, 0)
        
        set_file_create_time(self.test_file, new_create_time)
        
        # Check creation time was set
        updated_create_time = get_file_create_time(self.test_file)
        self.assertLess(abs(updated_create_time.timestamp() - new_create_time.timestamp()), 2)
        
        # Check modification time wasn't significantly changed
        current_mod_time = get_file_write_time(self.test_file)
        # Allow some tolerance as the operation might slightly touch mod time
        self.assertLess(abs(current_mod_time.timestamp() - original_mod_time.timestamp()), 60)

    def test_set_file_create_time_nonexistent_file(self):
        # Test behavior with nonexistent file - should handle gracefully
        nonexistent_file = self.test_dir / 'does_not_exist.txt'
        new_time = datetime(2020, 1, 1, 0, 0, 0)
        
        # Function should handle this gracefully (print message, return)
        # Should not raise an exception
        set_file_create_time(nonexistent_file, new_time)
        
        # File should still not exist
        self.assertFalse(nonexistent_file.exists())

    def test_set_file_create_time_directory_error(self):
        # Test that function correctly rejects directories
        test_dir = self.test_dir / 'test_subdir'
        test_dir.mkdir()
        new_time = datetime(2020, 1, 1, 0, 0, 0)
        
        # Function should handle this gracefully (print message, return)
        set_file_create_time(test_dir, new_time)

    def test_file_time_nonexistent_file(self):
        # Test behavior with nonexistent file
        nonexistent_file = self.test_dir / 'nonexistent.txt'

        # get_file_write_time should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            get_file_write_time(nonexistent_file)

        # get_file_create_time should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            get_file_create_time(nonexistent_file)

    def test_set_write_time_nonexistent_file(self):
        # Test setting write time on nonexistent file
        nonexistent_file = self.test_dir / 'nonexistent.txt'
        new_time = datetime.now() - timedelta(days=10)

        # Function should print error message but not raise exception
        set_file_write_time(nonexistent_file, new_time)
        # Verify file still doesn't exist
        self.assertFalse(nonexistent_file.exists())

    @unittest.skipIf(os.name != 'nt', "This test is Windows-specific")
    def test_windows_specific_create_time(self):
        # Test Windows-specific behavior for creation time
        # Create a new file
        win_test_file = self.test_dir / 'win_test_file.txt'
        win_test_file.write_text('Windows test file')

        # Get initial creation time
        initial_create_time = get_file_create_time(win_test_file)

        # Wait a moment and modify the file
        time_module.sleep(1)
        win_test_file.write_text('Modified content')

        # Get creation time after modification
        modified_create_time = get_file_create_time(win_test_file)

        # On Windows, creation time should not change when file is modified
        self.assertEqual(initial_create_time, modified_create_time)


if __name__ == '__main__':
    unittest.main()
