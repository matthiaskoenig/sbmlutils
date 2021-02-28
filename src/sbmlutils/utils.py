"""Utility functions."""
import functools
import hashlib
import time
import warnings
from typing import Any, Callable

import libsbml
from depinfo import print_dependencies  # type: ignore


def show_versions() -> None:
    """Print dependency information."""
    print_dependencies("sbmlutils")


class bcolors:
    """Colors for console formating."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BGWHITE = "\033[47m"
    BGBLACK = "\033[49m"
    WHITE = "\033[37m"
    BLACK = "\033[30m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def create_metaid(sbase: libsbml.SBase) -> str:
    """Create a globally unique meta id.

    Meta ids are required to store annotations on elements.
    """
    return f"meta_{create_hash_id(sbase)}"


def create_hash_id(sbase: libsbml.SBase) -> str:
    """Create hash code."""
    if sbase and hasattr(sbase, "getId") and sbase.isSetId():
        hash_key = sbase.getId()
    else:
        # hash the xml_node
        xml_node = sbase.toXMLNode()  # type: libsbml.XMLNode
        xml_str = xml_node.toString().encode("utf-8")
        hash_key = hashlib.md5(xml_str).hexdigest()
    return hash_key  # type: ignore


def timeit(f: Callable) -> Callable:
    """Decorate function with timing information.

    :param f: function to time
    :return:
    """

    def timed(*args: Any, **kwargs: Any) -> Any:

        ts = time.time()
        result = f(*args, **kwargs)
        te = time.time()

        print(
            "func:%r args:[%r, %r] took: %2.4f sec"
            % (f.__name__, args, kwargs, te - ts)
        )
        return result

    return timed


def deprecated(f: Callable) -> Callable:
    """Decorate function as deprecated.

    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """

    @functools.wraps(f)
    def new_func(*args: Any, **kwargs: Any) -> Any:
        warnings.warn_explicit(
            "Call to deprecated function {}.".format(f.__name__),
            category=DeprecationWarning,
            filename=f.func_code.co_filename,  # type: ignore
            lineno=f.func_code.co_firstlineno + 1,  # type: ignore
        )
        return f(*args, **kwargs)

    return new_func
