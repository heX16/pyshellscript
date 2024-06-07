from .pyshellscript import *

# I don't know why, but without this lines the `import *` doesn't work
# (although theoretically it should work)
import pyshellscript
__all__ = dir(pyshellscript)
