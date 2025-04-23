"""
ANNOUNCEMENT!

IN THE NEXT SEASON! SUPER-DUPER NEW FEATURE!
Input-output redirection through the ">>" symbol!
This will be so COOL that `bash` will turn red with envy!
Get ready for a revolution in the world of console commands!
Coming soon to all python scripts!
"""

import subprocess

class ShellCommand:

    def __init__(self, command):
        self.command = command
        self.process = None
        print(f'INIT: {self.command}')


    def run(self, input_process=None):
        # Execute the command with stdin set to the output of the input process if provided
        print(f'RUN: {self.command}')
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            stdin=input_process.stdout if input_process else None,
            stdout=subprocess.PIPE,
            text=True
        )
        return self


    def pipe_the_process(self, second_process):
        if self.process is None:
            self.run()

        if isinstance(second_process, ShellCommand):
            print(f'self - {self.command}, second_process - {second_process.command}')
            second_process.run(self.process)
        elif isinstance(second_process, SaveToFile):
            print(f'self - {self.command}, second_process - SaveToFile')
            second_process.stdout_write_to_file(self)
        else:
            print('ERROR')

        return second_process


    def __rshift__(self, other):
        # Pipe output directly to the next command
        return self.pipe_the_process(other)

    def __or__(self, other):
        # Pipe output directly to the next command
        return self.pipe_the_process(other)


class SaveToFile:

    def __init__(self, filename):
        self.filename = filename

    def stdout_write_to_file(self, process):
        stdout, stderr = process.process.communicate()  # Capture the output
        code = process.process.wait()  # Wait for the process to finish
        # print(code)
        with open(self.filename, 'w') as file:
            file.write(stdout)

    def __rshift__(self, other):
        print(f'self (rshift) - SaveToFile:{self.filename}, other - ...')
        return other

    def __or__(self, other):
        print(f'self (or) - SaveToFile:{self.filename}, other - ...')
        return other

sh = ShellCommand
save_to_file = SaveToFile

# Example usage

# Test command:
sh('ping 127.0.0.1') >> sh('find "Reply"') >> save_to_file('log.txt')

# Note:
# a_cmd = sh('ping 127.0.0.1')
# b_cmd = sh('find "Reply"')
# b_cmd = a_cmd.rshift( b_cmd )
# c_cmd = save_to_file()
# c_cmd = b_cmd.rshift( c_cmd )

#sh('ping 127.0.0.1') >> save_to_file('log.txt')



"""
-----------------------------------------

create_process('some.exe').run()

p = create_process('some.exe')
p.run()

pipe('some1.exe') >> pipe('some2.exe') >> pipe('some3.exe')

p1 = create_process('some1.exe')
p2 = create_process('some2.exe')
p3 = create_process('some3.exe')
p1 >> p2 >> p3

proc_run_bg('some1.exe')


"""