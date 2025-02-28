from pyshellscript import *

def print_process_list_example(process_list, print_format="{:<8} {:<30} {:<10} {}"):
    """
    Example:
    """
    print(print_format.format('PID', 'USER', 'TIME', 'COMMAND'))

    for p in process_list:
        print(print_format.format(
            str(p['pid']),
            str(p['username']),
            round(p['cpu_times'].user + p['cpu_times'].system, 2),
            '-' if p['cmdline'] is None else ' '.join(p['cmdline'])
        ))

print_process_list_example(proc_list_to_dict(get_proc_list()))
