"""Utility functions."""

import hashlib
from typing import Any

import libsbml


class FrozenClass:
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
    # FIXME: issues with assignment rules in pancreas model
    # print(f"create_hashcode for sbase: '{sbase}'")
    # print(sbase.getId())

    if sbase and hasattr(sbase, "getId") and sbase.isSetId():
        hash_key = sbase.getId()
    else:
        # hash the xml_node
        xml_node: libsbml.XMLNode = sbase.toXMLNode()
        xml_str = xml_node.toString().encode("utf-8")
        # print(f"xml_str -> {xml_node} -> {xml_str}" )
        hash_key = hashlib.md5(xml_str).hexdigest()
    # print(f"-> {hash_key}")
    return hash_key
