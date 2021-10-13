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


class FrozenClass(object):
    """FrozenClass.

    After freezing no additional attributes can be added.
    """

    __isfrozen: bool = False

    def __setattr__(self, key: str, value: Any) -> None:
        """Attribute setter."""
        if self.__isfrozen and not hasattr(self, key):
            raise AttributeError(
                f"{self} is a frozen class, no new attributes. But "
                f"trying to set `{key} = {value}`."
            )
        object.__setattr__(self, key, value)

    def _freeze(self) -> None:
        self.__isfrozen = True


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
        xml_node: libsbml.XMLNode = sbase.toXMLNode()
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
            f"Call to deprecated function {f.__name__}.",
            category=DeprecationWarning,
            filename=f.func_code.co_filename,  # type: ignore
            lineno=f.func_code.co_firstlineno + 1,  # type: ignore
        )
        return f(*args, **kwargs)

    return new_func
