
class StdInOutBase:
    def input(self, s: str) -> str:
        if self.next_input is None:
            self.output(s)
        else:
            self.next_input.input(s)


class StdInOutLinesUpper(StdInOutBase):
    def input(self, s: str) -> str:
        return s.upper()


class StdInOutLinesPrint(StdInOutBase):
    def input(self, s: str) -> None:
        print(s)


class StdInOutRemoveControlChars(StdInOutBase):
    _delete_chars = None
    _trans_table = None

    def __init__(self, ):
        super().__init__()
        if StdInOutRemoveControlChars._delete_chars is None:
            StdInOutRemoveControlChars._delete_chars = ''.join([chr(i) for i in range(32) if i not in (9, 10, 13)])
        if StdInOutRemoveControlChars._trans_table is None:
            StdInOutRemoveControlChars._trans_table = str.maketrans('', '', StdInOutRemoveControlChars._delete_chars)

    def input(self, s: str) -> str:
        return s.translate(self._trans_table)


class StdInOutReplaceTabs(StdInOutBase):
    def __init__(self, spaces_per_tab=4):
        super().__init__()
        self.spaces_per_tab = spaces_per_tab

    def input(self, s: str) -> str:
        return s.replace('\t', ' ' * self.spaces_per_tab)


class StdInOutPipeProcess(StdInOutBase):
    def __init__(self, pipe_processes):
        self.pipe_processes = pipe_processes

    def input(self, s: str) -> str:
        for proc in self.pipe_processes:
            s = proc.input(s)
        return s

def str_pipe_process(pipe_procs, s: str):
    for proc in pipe_procs:
        s = proc.input(s)


# Example usage:
process1_pipe_obj = StdInOutPipeProcess([StdInOutRemoveControlChars(), StdInOutReplaceTabs(8), StdInOutLinesUpper(), StdInOutLinesPrint()])

process1_pipe_obj.input('Hello, world!\x01\x02\x03')
process1_pipe_obj.input('Hello, world!\n\r_test_\x01\x02\t\x00\x03_test_!')
