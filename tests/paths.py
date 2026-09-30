"""Directories with the characters a path handling may get wrong.

A space is percent-encoded in a file URI, a non-ASCII character cannot be
opened by libsbml on Windows, which passes the path to the narrow (ANSI) file
API. sbmlutils reads and writes such a path with python, see
`sbmlutils.io.files`, but libsbml still opens the file of a comp external
model definition itself, which is what `NON_ASCII_EXTERNAL_ON_WINDOWS` marks.
"""

import sys

import pytest

#: libsbml opens the file of an external model definition itself, with the
#: narrow (ANSI) file API on Windows, which cannot open a non-ASCII path
NON_ASCII_EXTERNAL_ON_WINDOWS = pytest.mark.xfail(
    sys.platform == "win32",
    reason="libsbml cannot open an external model definition in a non-ASCII "
    "directory on Windows",
    strict=True,
)

#: a directory with a space, one with a non-ASCII character, and the latter as
#: a parameter which is expected to fail on Windows where external model
#: definitions are resolved in it
SPACE_DIR = "sp ace"
NON_ASCII_DIR = "ü"
NON_ASCII_DIR_WITH_EXTERNALS = pytest.param(
    NON_ASCII_DIR, marks=NON_ASCII_EXTERNAL_ON_WINDOWS
)
