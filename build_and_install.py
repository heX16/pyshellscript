import subprocess
import toml
import re
from pathlib import Path

# Open and read the file
file_path = Path('pyshellscript/pyshellscript.py')
lines = file_path.read_text().splitlines()

try:
    # Find the index of the target line
    index = lines.index('def pyshellscript_version():')
    # Print the line immediately following the target line
    version = lines[index + 1]

    # Regular expression to extract the version number
    match = re.search(r"return\s+'([\d.]+)'", version)
    if match:
        version = match.group(1)
        print('Version:', version)
    else:
        exit(1)
        print('No version found')

except ValueError:
    print('The target line was not found in the file.')
except IndexError:
    print('The target line is at the end of the file, no following line.')

exit(0)

# Path to the pyproject.toml file
pyproject_path = Path('pyproject.toml')

# Read the pyproject.toml file
with pyproject_path.open('r') as file:
    pyproject_data = toml.load(file)

# Extract the version from pyproject.toml
version = pyproject_data['project']['version']
dist_dir = Path('dist')
wheel_file = dist_dir / f'pyshellscript-{version}-py3-none-any.whl'

# Build the project
subprocess.run(['python', '-m', 'build'])

# Check if the wheel file exists
if wheel_file.exists():
    print(f'Installing version: {wheel_file}')
    # Install the wheel file
    subprocess.run(['pip', 'install', str(wheel_file), '--force-reinstall'])
else:
    print(f'Wheel file {wheel_file} not found in {dist_dir}')
