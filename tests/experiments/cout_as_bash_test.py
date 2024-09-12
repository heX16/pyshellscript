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
        self.output = None

    def run(self, input_data=None):
        """
        Executes the command. If input_data is provided, it is passed to the
        command via stdin.

        Args:
            input_data (str, optional): The input data to pass to the command.

        Returns:
            ShellCommand: Returns self to allow method chaining.
        """
        # Execute the command with input data passed via PIPE if provided
        if input_data is not None:
            self.process = subprocess.Popen(self.command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            self.output, _ = self.process.communicate(input=input_data)
        else:
            self.process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, text=True)
            self.output, _ = self.process.communicate()

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
        # Ensure the command has been executed if not already
        if self.output is None:
            self.run()

        # If the next object is a ShellCommand, pipe the output to it
        if isinstance(other, ShellCommand):
            return other.run(input_data=self.output)
        # If the next object is SaveToFile, write the output to the file
        elif isinstance(other, SaveToFile):
            other.write_to_file(self.output)
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
