import unittest
from pathlib import Path
import shutil
import os
import sys

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

if __name__ == '__main__':
    unittest.main()
