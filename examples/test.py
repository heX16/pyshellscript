from pyshellscript import *
# import pyshellscript


#print(dir(pyshellscript))
#print(globals())
#print(now)
#print(find)
#print(pyshellscript.find)
#print(run_command)

for f in find('./', '*.*', recursively=True):
    if str(get_filename(f)).startswith('te'):
        print('file:', f)
        #pyshellscript.rename..

# pipe example

find_line = '$find me$' # <- test line

# classic pipe `cat test.py | find line`

result = run_command('cat test.py', capture_output=True, raise_exception=True, background=True)
grep_process = run_command(f'find "{find_line}"', stdin=result.stdout, capture_output=True,
                           background=True, raise_exception=False)
print('Result:', grep_process.stdout.read())

# string "pipe" `cat test.py` > out_str > `find line`

result = run_command('cat test.py', capture_output=True, raise_exception=True)
out_str = result.stdout.read()
print('out_str:')
print('```\n'+out_str[0:100],'\n```')
result = run_command(f'find "{find_line}"', capture_output=True, stdin_text=out_str, raise_exception=True)
out_str = result.stdout.read()
print('Result:', out_str)

exit()


# proc test
'''
print(proc_present('python'))
print(proc_list_to_pid_list(get_proc_list()))
print(proc_list_to_names_list(get_proc_list()))
'''

# copy
'''
name = Path('disk_h.7z.001')
src = Path('D:\\heXor\\Backup\\disk_h_24_03\\')
dst = Path('F:\\')
while True:
    if (dst / name).exists():
        num = name.suffix
        num = num[1:]
        num = int(num)
        num += 1
        name = change_filename_ext_in_path(name, f'{num:003}')
        continue
    else:
        print(f'Copy: {src / name}')
        break

copy_file_with_progress(src / name, dst / name)
print('copy ended')
'''
