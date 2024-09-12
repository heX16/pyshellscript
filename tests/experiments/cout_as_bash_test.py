import subprocess

class ShellCommand:
    def __init__(self, command):
        self.command = command
        self.process = None
        self.output = None

    def run(self, input_data=None):
        # Выполняем команду с возможностью передачи входных данных через PIPE
        if input_data is not None:
            self.process = subprocess.Popen(self.command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            self.output, _ = self.process.communicate(input=input_data)
        else:
            self.process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, text=True)
            self.output, _ = self.process.communicate()

        return self

    def __rshift__(self, other):
        # Убедимся, что команда выполнена, если не было выполнено до этого
        if self.output is None:
            self.run()

        # Передаем вывод следующей команде
        if isinstance(other, ShellCommand):
            return other.run(input_data=self.output)
        elif isinstance(other, SaveToFile):
            other.write_to_file(self.output)
            return other

class SaveToFile:
    def __init__(self, filename):
        self.filename = filename

    def write_to_file(self, data):
        with open(self.filename, 'w') as file:
            file.write(data)

    def __rshift__(self, other):
        # Для возможности продолжать цепочку после сохранения файла
        return other


# Пример использования
sh = ShellCommand
save_to_file = SaveToFile

sh('ping 127.0.0.1') >> sh('find "Reply"') >> save_to_file('log.txt')
#sh('ping 127.0.0.1') >> save_to_file('log.txt')
