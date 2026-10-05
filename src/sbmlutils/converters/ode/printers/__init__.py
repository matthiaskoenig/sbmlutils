"""Printers of SBML math, one per dialect, on the engine of `base.MathPrinter`."""

from sbmlutils.converters.ode.printers.base import (
    MathPrinter,
    Precedence,
    Printed,
    SymbolMap,
    UnsupportedMathError,
)
from sbmlutils.converters.ode.printers.python import PythonPrinter

PRINTERS: dict[str, type[MathPrinter]] = {
    PythonPrinter.name: PythonPrinter,
}
"""The printer of each dialect, by its name."""

__all__ = [
    "PRINTERS",
    "MathPrinter",
    "Precedence",
    "Printed",
    "PythonPrinter",
    "SymbolMap",
    "UnsupportedMathError",
]
