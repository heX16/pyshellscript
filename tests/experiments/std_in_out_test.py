class StdInOutBase:
    def __init__(self, next_input=None):
        self.next_input = next_input

    def input(self, s: str):
        if self.next_input is None:
            self.output(s)
        else:
            self.next_input.input(s)

    def output(self, s: str):
        raise NotImplementedError("Subclasses should implement this method")


class StdInOutLinesUpper(StdInOutBase):
    def input(self, s: str):
        super().input(s.upper())


class StdInOutLinesPrint(StdInOutBase):
    def output(self, s: str):
        print(s)


class StdInOutRemoveControlChars(StdInOutBase):
    _delete_chars = None
    _trans_table = None

    def __init__(self, next_input=None):
        super().__init__(next_input)
        if StdInOutRemoveControlChars._delete_chars is None:
            StdInOutRemoveControlChars._delete_chars = ''.join([chr(i) for i in range(32) if i not in (9, 10, 13)])
        if StdInOutRemoveControlChars._trans_table is None:
            StdInOutRemoveControlChars._trans_table = str.maketrans('', '', StdInOutRemoveControlChars._delete_chars)

    def input(self, s: str):
        filtered_str = s.translate(self._trans_table)
        super().input(filtered_str)


class StdInOutReplaceTabs(StdInOutBase):
    def __init__(self, next_input=None, spaces_per_tab=4):
        super().__init__(next_input)
        self.spaces_per_tab = spaces_per_tab

    def input(self, s: str):
        replaced_str = s.replace('\t', ' ' * self.spaces_per_tab)
        super().input(replaced_str)



# Example usage:
#process1 = StdInOutRemoveControlChars(StdInOutLinesUpper(StdInOutLinesPrint()))
process1 = StdInOutRemoveControlChars(StdInOutReplaceTabs(StdInOutLinesUpper(StdInOutLinesPrint())))

process1.input('Hello, world!\x01\x02\x03')
process1.input('Hello, world!\n\r_test_\x01\x02\t\t\x00\x03_test_!')
