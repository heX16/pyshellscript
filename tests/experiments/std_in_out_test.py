from typing import List
from enum import Enum


class StrProcState(Enum):
    has_output_default = 0
    can_input_default = 1
    can_input_parsing_in_process = 2
    _group_values = 100
    has_output = 101
    can_input = 102

    @staticmethod
    def get_has_output_set():
        return {StrProcState.has_output_default.value}

    @staticmethod
    def get_can_input_set():
        return {StrProcState.can_input_default.value, StrProcState.can_input_parsing_in_process.value}

    @staticmethod
    def is_partial_in_group(group, partial):
        if group == StrProcState.has_output.value:
            if partial in StrProcState.get_has_output_set():
                return True
        if group == StrProcState.can_input.value:
            if partial in StrProcState.get_can_input_set():
                return True
        return False

    def __eq__(self, other):
        if isinstance(other, StrProcState):
            if self.value >= self._group_values.value:
                group = self.value
                partial = other.value
            elif other.value >= self._group_values.value:
                group = other.value
                partial = self.value
            else:
                return super().__eq__(other)

            if partial >= self._group_values.value:
                return False

            return StrProcState.is_partial_in_group(group, partial)
        else:
            return super().__eq__(other)


class StrProcBase:

    def __init__(self):
        super().__init__()
        self.s = None

    def input(self, s: str):
        self.s = s

    def eof(self):
        pass

    def output(self) -> str:
        s = self.s
        self.s = None
        return s

    def state(self) -> StrProcState:
        return StrProcState.can_input_default if self.s is None else StrProcState.has_output_default


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

            if self.pipe_processes[pos].state() == StrProcState.has_output:
                out = self.pipe_processes[pos].output()
                self.pipe_processes[pos + 1].input(out)
                pos = len(self.pipe_processes) - 1
                continue

    def input(self, s: str):
        self.pipe_processes[0].input(s)
        self.str_pipe_process()


# tests

assert StrProcState.can_input_default == StrProcState.can_input
assert StrProcState.can_input_parsing_in_process == StrProcState.can_input
assert not (StrProcState.can_input_parsing_in_process == StrProcState.has_output)
assert StrProcState.has_output_default == StrProcState.has_output
assert not (StrProcState.has_output_default == StrProcState.can_input_default)

# Example usage:


# ####

process2_pipe_obj = StrProcPipeProcess(
    [StrProcRemoveControlChars(), StrProcReplaceTabs(8), StrProcLinesUpper(), StrProcLinesPrint(),
     StrBufferBase(), StrBufferBase(), StrBufferBase(), StrBufferBase()]
)

process2_pipe_obj.input('Hello, world! ver 2')
process2_pipe_obj.input('Hello, world 1!\x01\x02\x03')
process2_pipe_obj.input('Hello, world 2!\n\r_test_\x01\x02\t\x00\x03_test_!')

while process2_pipe_obj.buffer.state() == StrProcState.has_output:
    print(process2_pipe_obj.buffer.output())
