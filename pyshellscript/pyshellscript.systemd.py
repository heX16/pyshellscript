
def systemd_file_type(file_name: Path):
    """
    Extracts the type of a systemd service file based on its suffix (and validates it).

    :param file_name: Path object representing the file.
    :return: String with the file type if valid (e.g., 'service', 'timer'), or False if invalid.
    """
    valid_types = {
        'service', 'timer', 'socket', 'device', 'mount', 'automount',
        'swap', 'target', 'path', 'slice', 'scope'
    }

    suffix = file_name.suffix[1:]  # Extract suffix without the dot

    if suffix in valid_types:
        return suffix
    return False


def systemd_file_supports_enable(file_type: str) -> bool:
    """
    Checks if a systemd unit file type supports the 'enable' command.

    Supported types for 'enable':
    - service: Enables auto-start of services.
    - timer: Enables scheduling of timers.
    - socket: Enables auto-start of sockets.
    - mount: Enables auto-mounting of filesystem points.
    - automount: Enables automatic mounting of filesystem points.
    - swap: Enables auto-start of swap units.
    - target: Enables grouping of other units.
    - path: Enables file or directory monitoring.

    :param file_type: Type of the systemd unit (e.g., 'service', 'timer').
    :return: True if the 'enable' command is supported, otherwise False.
    """
    enable_supported = {
        'service', 'timer', 'socket', 'mount', 'automount',
        'swap', 'target', 'path'
    }
    return file_type in enable_supported


def systemd_file_supports_start(file_type: str) -> bool:
    """
    Checks if a systemd unit file type supports the 'start' command.

    Supported types for 'start':
    - service: Starts services manually.
    - timer: Activates timers.
    - socket: Activates sockets for listening.
    - mount: Mounts filesystem points.
    - swap: Activates swap units.
    - target: Activates groups of units.

    :param file_type: Type of the systemd unit (e.g., 'service', 'timer').
    :return: True if the 'start' command is supported, otherwise False.
    """
    start_supported = {
        'service', 'timer', 'socket', 'mount', 'swap', 'target'
    }
    return file_type in start_supported

def systemd_unit_inactive(mount_unit: str) -> bool:
    ''' Checks if the SystemD mount unit is inactive '''
    p = systemd_get_properties(mount_unit)
    return p['ActiveState'] == 'inactive'

def systemd_get_properties(unit: str) -> dict:
    '''Calls "systemctl show <unit>" and returns a dict of key=value from the output.'''
    info_dict = {}
    ok = systemd_command('show', unit, check_errcode=False)
    if not ok:
        logger.debug('systemctl show %s failed or returned non-zero code.', unit)
        return info_dict

    for line in run_command_stdout.splitlines():
        if '=' in line:
            key, val = line.split('=', 1)
            info_dict[key] = val
    return info_dict

