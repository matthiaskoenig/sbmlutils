"""Dependencies of the math of a model and the order they impose.

An assignment can only be evaluated after the assignments of the ids its math names,
so the assignments of a model are evaluated in a topological order of their
dependencies. A cycle has no such order, the model is not well defined.
"""

import heapq
from collections.abc import Sequence
from graphlib import CycleError, TopologicalSorter

import libsbml

from sbmlutils.converters.ode.astutil import walk

__all__ = ["names", "order"]


def names(ast: libsbml.ASTNode | None) -> set[str]:
    """The ids a math refers to.

    These are the names (`<ci>`), not the calls of function definitions, the time,
    avogadro or the other csymbols.

    Args:
        ast: the math, `None` for an element without math

    Returns:
        the ids
    """
    found: set[str] = set()
    if ast is not None:
        for node in walk(ast):
            if node.getType() == libsbml.AST_NAME:
                found.add(node.getName())
    return found


def order(items: Sequence[tuple[str, libsbml.ASTNode | None]]) -> list[str]:
    """Order assignments so that each one comes after the ids it depends on.

    An item depends on the items whose ids its math names; a name which is not the
    id of an item (a constant, a state) is no dependency. Ties are resolved by the
    order of the input: the next item is always the first one in the input whose
    dependencies are all ordered.

    Args:
        items: the id and the math of each assignment, in the order of the document

    Returns:
        the ids in the order of evaluation

    Raises:
        ValueError: if the assignments depend on each other in a cycle, naming the
            ids of the cycle in the order of the input
    """
    index = {sid: k for k, (sid, _) in enumerate(items)}
    sorter: TopologicalSorter[str] = TopologicalSorter()
    for sid, ast in items:
        sorter.add(sid, *(name for name in names(ast) if name in index))
    try:
        sorter.prepare()
    except CycleError as error:
        cycle = sorted(set(error.args[1]), key=index.__getitem__)
        raise ValueError(
            f"The assignments of {cycle} depend on each other in a cycle."
        ) from error

    ordered: list[str] = []
    ready: list[int] = []
    while sorter.is_active():
        for sid in sorter.get_ready():
            heapq.heappush(ready, index[sid])
        sid = items[heapq.heappop(ready)][0]
        ordered.append(sid)
        sorter.done(sid)
    return ordered
