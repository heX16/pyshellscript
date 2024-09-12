import subprocess

class ShellCommand:
    def __init__(self, command):
        self.command = command
        self.output = None

    def run(self):
        # Execute the command and save the output
        result = subprocess.run(self.command, shell=True, capture_output=True, text=True)
        self.output = result.stdout
        return self

    def __rshift__(self, other):
        # Ensure the command has already been executed and the output is not empty
        if self.output is None:
            self.run()

        # Redirect the output to the next command
        if isinstance(other, ShellCommand):
            other.input_from(self.output)
            return other.run()
        elif isinstance(other, SaveToFile):
            other.write_to_file(self.output)
            return other

    def input_from(self, input_text):
        # Get data from the previous command
        if input_text is not None:
            self.command = f'echo "{input_text.strip()}" | {self.command}'
        return self


class SaveToFile:
    def __init__(self, filename):
        self.filename = filename

    def write_to_file(self, data):
        with open(self.filename, 'w') as file:
            file.write(data)

    def __rshift__(self, other):
        # For the ability to continue the chain after saving the file (e.g., to other objects)
        return other


# Example of usage
sh = ShellCommand
save_to_file = SaveToFile

#sh('ping test.com') >> sh('find "Reply"') >> save_to_file('log.txt')
sh('ping test.com') >> save_to_file('log.txt')
