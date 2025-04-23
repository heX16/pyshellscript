"""
ANNOUNCEMENT!

IN THE NEXT SEASON! SUPER-DUPER NEW FEATURE!
String processing with pipe redirection!
This will be so COOL that `awk` will turn green with envy!
Get ready for a revolution in the world of text processing!
Coming soon to all python scripts!
"""

from typing import List, Set
from enum import Enum, IntEnum
from abc import ABC, abstractmethod

class StrProcState(Enum):
    has_output_default = 0
    has_output_and_can_input = 1
    can_input_default = 100
    can_input_and_parsing_in_process = 101

    def has_output(self):
        return self.value < StrProcState.can_input_default.value

    def can_input(self):
        return self.value >= StrProcState.can_input_default.value


class StrProcFlags(IntEnum):
    is_transit_1_by_1 = 1
    is_infinity_input = 2
    is_infinity_output = 3
    input_buffer_has_memory_limit = 4
    no_output = 5
    has_sub_proc = 6


class AbstractStrProc(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def input(self, s: str):
        pass

    @abstractmethod
    def eof(self):
        pass

    @abstractmethod
    def output(self) -> str:
        pass

    @abstractmethod
    def state(self) -> StrProcState:
        pass

    @staticmethod
    @abstractmethod
    def class_flags() -> Set[StrProcFlags]:
        pass

    @abstractmethod
    def __bool__(self):
        pass

    @abstractmethod
    def __iter__(self):
        pass


class StrProcTransit(AbstractStrProc):

    def __init__(self):
        super().__init__()
        self.buffer_str: str | None = None

    def input(self, s: str):
        if self.buffer_str is not None:
            raise BrokenPipeError(
                'Cannot accept new input: buffer is already full. Please process the existing data first.')
        self.buffer_str = s

    def eof(self):
        pass

    def output(self) -> str:
        if self.buffer_str is None:
            raise BrokenPipeError(
                'Cannot provide output: buffer is empty. Ensure data is provided before attempting to read.')
        s = self.buffer_str
        self.buffer_str = None
        return s

    def state(self) -> StrProcState:
        return StrProcState.can_input_default if self.buffer_str is None else StrProcState.has_output_default

    @staticmethod
    def class_flags() -> Set[StrProcFlags]:
        return {StrProcFlags.is_transit_1_by_1}

    def __bool__(self):
        return self.state().has_output()

    def __iter__(self):
        while self:
            yield self.output()


class StrProcUpper(StrProcTransit):
    def input(self, s: str):
        super().input(s.upper())


class StrProcPrint(StrProcTransit):
    def input(self, s: str):
        print(f'print: "{s}"')
        super().input(s)


class StrProcPrintFinal(StrProcTransit):
    def input(self, s: str):
        print(f'print: "{s}"')

    @staticmethod
    def class_flags() -> Set[StrProcFlags]:
        return {StrProcFlags.no_output}


class StrProcNull(StrProcTransit):
    def input(self, s: str):
        pass

    @staticmethod
    def class_flags() -> Set[StrProcFlags]:
        return {StrProcFlags.no_output, StrProcFlags.is_infinity_input}


class StrProcRemoveControlChars(StrProcTransit):
    _trans_table = None

    def __init__(self):
        super().__init__()
        if StrProcRemoveControlChars._trans_table is None:
            delete_chars = ''.join([chr(i) for i in range(32) if i not in (9, 10, 13)])
            StrProcRemoveControlChars._trans_table = str.maketrans('', '', delete_chars)

    def input(self, s: str):
        super().input(s.translate(self._trans_table))


class StrProcReplaceTabs(StrProcTransit):
    def __init__(self, spaces_per_tab=4):
        super().__init__()
        self.spaces_per_tab = spaces_per_tab

    def input(self, s: str):
        super().input(s.replace('\t', ' ' * self.spaces_per_tab))


class StrBuffer(AbstractStrProc):
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

    def __iter__(self):
        while self:
            yield self.output()

    @staticmethod
    def class_flags() -> Set[StrProcFlags]:
        return {StrProcFlags.is_infinity_input, StrProcFlags.input_buffer_has_memory_limit}


class StrProcPipeProcess(AbstractStrProc):
    def __init__(self, pipe_processes: List[StrProcTransit]):
        super().__init__()
        self.pipe_processes = pipe_processes
        if StrProcFlags.is_infinity_input not in self.pipe_processes[-1].class_flags():
            self.pipe_processes.append(StrBuffer())

    def str_pipe_process(self):
        # `-1` - skip last `StrProc`
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

    def output(self) -> str:
        return self.pipe_processes[-1].output()

    def eof(self):
        for p in self.pipe_processes:
            p.eof()
        self.str_pipe_process()

    def __bool__(self):
        return bool(self.pipe_processes[-1])

    def __iter__(self):
        return iter(self.pipe_processes[-1])

    def state(self) -> StrProcState:
        if self.pipe_processes[-1].state().has_output():
            if self.pipe_processes[0].state().can_input():
                return StrProcState.has_output_and_can_input
            else:
                return StrProcState.has_output_default
        elif self.pipe_processes[0].state().can_input():
            return StrProcState.can_input_default
        else:
            raise BrokenPipeError('Pipeline is in an invalid state: unable to accept input')

    @staticmethod
    def class_flags() -> Set[StrProcFlags]:
        return {StrProcFlags.has_sub_proc}


# Example usage:


# ####

process2_pipe_obj = StrProcPipeProcess(
    [StrProcRemoveControlChars(), StrProcReplaceTabs(8), StrProcUpper(), StrProcPrint(),
     StrBuffer(), StrBuffer(), StrBuffer(), StrBuffer(), StrProcPrint()]
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
