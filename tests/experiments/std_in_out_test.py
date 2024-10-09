from typing import List


class StrProcBase:
    def input(self, s: str) -> (str | None):
        raise NotImplementedError("Subclasses should implement this method")

    def eof():
        pass

    def output() -> str:
        raise NotImplementedError("Subclasses should implement this method")

    def has_output() -> bool:
        return False


class StrProcBase_wip_not_sure:
    def __init__(self, ):
        super().__init__()
        self.s = None

    def input(self, s: str):
        self.s = s

    def eof():
        pass

    def output() -> str:
        s = self.s
        self.s = None
        return s

    def has_output() -> bool:
        return s is not None


class StrProcLinesUpper(StrProcBase):
    def input(self, s: str) -> str:
        return s.upper()


class StrProcLinesPrint(StrProcBase):
    def input(self, s: str) -> None:
        print(s)


class StrProcRemoveControlChars(StrProcBase):
    _delete_chars = None
    _trans_table = None

    def __init__(self, ):
        super().__init__()
        if StrProcRemoveControlChars._delete_chars is None:
            StrProcRemoveControlChars._delete_chars = ''.join([chr(i) for i in range(32) if i not in (9, 10, 13)])
        if StrProcRemoveControlChars._trans_table is None:
            StrProcRemoveControlChars._trans_table = str.maketrans('', '', StrProcRemoveControlChars._delete_chars)

    def input(self, s: str) -> str:
        return s.translate(self._trans_table)


class StrProcReplaceTabs(StrProcBase):
    def __init__(self, spaces_per_tab=4):
        super().__init__()
        self.spaces_per_tab = spaces_per_tab

    def input(self, s: str) -> str:
        return s.replace('\t', ' ' * self.spaces_per_tab)


class StrBufferBase:
    def __init__(self):
        super().__init__()
        self.buffer: List[str] = []

    def input(self, s: str) -> (str | None):
        self.buffer.append(s)
        return None

    def eof():
        pass

    def output() -> str:
        return self.buffer.pop(0)

    def has_output() -> bool:
        return len(self.buffer) > 0


class StrProcPipeProcess(StrProcBase):
    def __init__(self, pipe_processes):
        self.pipe_processes = pipe_processes

    def input(self, s: str) -> str:
        for proc in self.pipe_processes:
            s = proc.input(s)
        return s


class StrProcPipeProcess_wip_not_sure(StrBufferBase):
    def __init__(self, pipe_processes: List[StrProcBase]):
        self.pipe_processes = pipe_processes

    def str_pipe_process(s: str, start_num = 0):
        # TODO: WiP. it's a complicated buffering issue. well, not complicated, but it's 2:00 in the morning...
        #       I will put off this code until tomorrow

        for i in range(start_num, len(self.pipe_processes)):
            proc = self.pipe_processes[i]
            # try get and push some data
            while proc.has_output():
                s_tmp = proc.output()
                super().input(str_pipe_process(s_tmp, i+1))

            # send str to input
            s_result = proc.input(s)
            if s_result is None:
                continue
            s = s_result

        return s

    def input(self, s: str) -> str:
        self.str_pipe_process(s)
        return None



# Example usage:
process1_pipe_obj = StrProcPipeProcess([StrProcRemoveControlChars(), StrProcReplaceTabs(8), StrProcLinesUpper(), StrProcLinesPrint()])

process1_pipe_obj.input('Hello, world 1!\x01\x02\x03')
process1_pipe_obj.input('Hello, world 2!\n\r_test_\x01\x02\t\x00\x03_test_!')
