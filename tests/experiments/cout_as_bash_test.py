import subprocess

class ShellCommand:
    """
    A class that represents a shell command. It allows chaining of commands
    using pipes and captures the output for further processing.

    Attributes:
        command (str): The shell command to be executed.
        process (subprocess.Popen): The process object representing the running command.
        output (str): The output of the command after execution.
    """

    def __init__(self, command):
        """
        Initializes the ShellCommand instance with the specified command.

        Args:
            command (str): The shell command to execute.
        """
        self.command = command
        self.process = None

    def run(self, input_process=None):
        """
        Executes the command. If input_process is provided, its output is passed
        as stdin to the command.

        Args:
            input_process (subprocess.Popen, optional): The process whose output
            is piped to this command's input.

        Returns:
            ShellCommand: Returns self to allow method chaining.
        """
        # Execute the command with stdin set to the output of the input process if provided
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            stdin=input_process.stdout if input_process else None,
            stdout=subprocess.PIPE,
            text=True
        )
        return self

    def __rshift__(self, other):
        """
        Overloads the '>>' operator to allow piping of one command's output
        into another command or saving it to a file.

        Args:
            other (ShellCommand or SaveToFile): The next command to run or
            the object to save the output to.

        Returns:
            ShellCommand or SaveToFile: The resulting object after piping.
        """
        # Pipe output directly to the next command
        if isinstance(other, ShellCommand):
            return other.run(input_process=self.process)
        elif isinstance(other, SaveToFile):
            if self.process is None:
                self.run()
            self.process.wait()  # Wait for the process to finish
            output, _ = self.process.communicate()  # Capture the output
            other.write_to_file(output)
            return other


class SaveToFile:
    """
    A class that represents a file-saving operation. It allows the output of
    commands to be saved to a specified file.

    Attributes:
        filename (str): The name of the file to which the output will be saved.
    """

    def __init__(self, filename):
        """
        Initializes the SaveToFile instance with the specified filename.

        Args:
            filename (str): The name of the file to save the output to.
        """
        self.filename = filename

    def write_to_file(self, data):
        """
        Writes the given data to the file.

        Args:
            data (str): The data to write to the file.
        """
        with open(self.filename, 'w') as file:
            file.write(data)

    def __rshift__(self, other):
        """
        Overloads the '>>' operator to allow chaining after saving to a file.

        Args:
            other (any): The next operation or object to process after saving.

        Returns:
            any: The resulting object after chaining.
        """
        return other


# Example usage
sh = ShellCommand
save_to_file = SaveToFile

# Test command:
sh('ping 127.0.0.1') >> sh('find "Reply"') >> save_to_file('log.txt')
#sh('ping 127.0.0.1') >> save_to_file('log.txt')
