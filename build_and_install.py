import subprocess
import toml
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
        print('Version:', version)
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
with pyproject_path.open('r') as file:
    pyproject_data = toml.load(file)

# Extract the current version from pyproject.toml
current_version = pyproject_data['project']['version']

# Compare versions and update if different
if version != current_version:
    # Update the version in pyproject.toml
    pyproject_data['project']['version'] = version

    # Write the updated data back to pyproject.toml
    with pyproject_path.open('w') as file:
        toml.dump(pyproject_data, file)
    print(f'Updated pyproject.toml to version: {version}')
else:
    print(f'No update needed. Current version is already: {current_version}')

# Extract the updated version from pyproject.toml
project_version = pyproject_data['project']['version']
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
