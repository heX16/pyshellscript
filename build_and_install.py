import subprocess
import re
from pathlib import Path

# Path to the target Python file
file_path = Path('pyshellscript/pyshellscript.py')

# Read all lines from the file
lines = file_path.read_text().splitlines()

try:
    # Find the index of the target function definition
    index = lines.index('def pyshellscript_version():')
    # Get the line immediately following the target line
    version_line = lines[index + 1]

    # Regular expression to extract the version number
    match = re.search(r"return\s+'([\d.]+)'", version_line)
    if match:
        version = match.group(1)
        print('Version "pyshellscript":', version)
    else:
        print('No version found')
        exit(1)

except ValueError:
    print('The target line was not found in the file.')
    exit(1)
except IndexError:
    print('The target line is at the end of the file, no following line.')
    exit(1)

# Path to the pyproject.toml file
pyproject_path = Path('pyproject.toml')

# Read the pyproject.toml file
pyproject_text = pyproject_path.read_text()

# Regular expression to find the version line in pyproject.toml
version_pattern = re.compile(r'version\s*=\s*"([\d.]+)"')

# Find the current version in pyproject.toml
current_version_match = version_pattern.search(pyproject_text)
if current_version_match:
    current_version = current_version_match.group(1)
    if version != current_version:
        # Replace the current version with the new version
        updated_pyproject_text = version_pattern.sub(f'version = "{version}"', pyproject_text)
        # Write the updated content back to pyproject.toml
        pyproject_path.write_text(updated_pyproject_text)
        print(f'Updated pyproject.toml to version: {version}')
    else:
        print(f'No update needed. Current version is already: {current_version}')
else:
    print('Version line not found in pyproject.toml')
    exit(1)

# Extract the updated version from pyproject.toml
project_version = version
dist_dir = Path('dist')
wheel_file = dist_dir / f'pyshellscript-{project_version}-py3-none-any.whl'

# Build the project
subprocess.run(['python', '-m', 'build'])

# Check if the wheel file exists
if wheel_file.exists():
    print(f'Installing version: {wheel_file}')
    # Install the wheel file
    subprocess.run(['pip', 'install', str(wheel_file), '--force-reinstall'])
else:
    print(f'Wheel file {wheel_file} not found in {dist_dir}')
