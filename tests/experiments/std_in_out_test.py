from typing import List
from enum import Enum


class StrProcState(Enum):
    has_output_default = 0
    can_input_default = 100
    can_input_parsing_in_process = 101

    def has_output(self):
        return self.value < StrProcState.can_input_default.value

    def can_input(self):
        return self.value >= StrProcState.can_input_default.value


class StrProcBase:

    def __init__(self):
        super().__init__()
        self.buffer_str = None

    def input(self, s: str):
        self.buffer_str = s

    def eof(self):
        pass

    def output(self) -> str:
        s = self.buffer_str
        self.buffer_str = None
        return s

    def state(self) -> StrProcState:
        return StrProcState.can_input_default if self.buffer_str is None else StrProcState.has_output_default

    def __bool__(self):
        return self.state().has_output()

    def __iter__(self):
        while self:
            yield self.output()


class StrProcLinesUpper(StrProcBase):
    def input(self, s: str):
        super().input(s.upper())


class StrProcLinesPrint(StrProcBase):
    def input(self, s: str):
        print(f'print: "{s}"')
        super().input(s)


class StrProcRemoveControlChars(StrProcBase):
    _delete_chars = None
    _trans_table = None

    def __init__(self):
        super().__init__()
        if StrProcRemoveControlChars._delete_chars is None:
            StrProcRemoveControlChars._delete_chars = ''.join([chr(i) for i in range(32) if i not in (9, 10, 13)])
        if StrProcRemoveControlChars._trans_table is None:
            StrProcRemoveControlChars._trans_table = str.maketrans('', '', StrProcRemoveControlChars._delete_chars)

    def input(self, s: str):
        super().input(s.translate(self._trans_table))


class StrProcReplaceTabs(StrProcBase):
    def __init__(self, spaces_per_tab=4):
        super().__init__()
        self.spaces_per_tab = spaces_per_tab

    def input(self, s: str):
        super().input(s.replace('\t', ' ' * self.spaces_per_tab))


class StrBufferBase(StrProcBase):
    def __init__(self):
        super().__init__()
        self.buffer: List[str] = []

    def input(self, s: str) -> (str | None):
        self.buffer.append(s)
        return None

    def eof(self):
        pass

    def output(self) -> str:
        return self.buffer.pop(0)

    def state(self) -> StrProcState:
        return StrProcState.can_input_default if len(self.buffer) == 0 else StrProcState.has_output_default

    def __bool__(self):
        return len(self.buffer) > 0


class StrProcPipeProcess(StrProcBase):
    def __init__(self, pipe_processes: List[StrProcBase]):
        super().__init__()
        self.pipe_processes = pipe_processes
        self.buffer = StrBufferBase()
        self.pipe_processes.append(self.buffer)

    def str_pipe_process(self):
        # `-1` - skip last Proc, its a buffer
        pos = len(self.pipe_processes) - 1

        while pos > 0:
            pos -= 1
            if pos < 0:
                break

            if self.pipe_processes[pos].state().has_output():
                # get text from the current processor
                out = self.pipe_processes[pos].output()
                # send text to the next processor
                self.pipe_processes[pos + 1].input(out)
                # reset cycle
                pos = len(self.pipe_processes) - 1
                continue

    def input(self, s: str):
        self.pipe_processes[0].input(s)
        self.str_pipe_process()

    def __bool__(self):
        return bool(self.buffer)

    def __iter__(self):
        return iter(self.buffer)


# tests

assert StrProcState.can_input_default.can_input()
assert StrProcState.can_input_parsing_in_process.can_input()
assert not (StrProcState.can_input_parsing_in_process.has_output())
assert StrProcState.has_output_default.has_output()
assert not (StrProcState.has_output_default == StrProcState.can_input_default)

# Example usage:


# ####

process2_pipe_obj = StrProcPipeProcess(
    [StrProcRemoveControlChars(), StrProcReplaceTabs(8), StrProcLinesUpper(), StrProcLinesPrint(),
     StrBufferBase(), StrBufferBase(), StrBufferBase(), StrBufferBase()]
)

input_data = [
    'Hello, world! ver 2',
    'Hello, world 1!\x01\x02\x03',
    'Hello, world 2!\n\r_test_\x01\x02\t\x00\x03_test_!',
]


while len(input_data) > 0:
    process2_pipe_obj.input(input_data.pop(0))
    for s_tmp in process2_pipe_obj:
        print('output():', s_tmp)
