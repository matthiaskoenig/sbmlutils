"""Printers of SBML math, one per dialect, on the engine of `base.MathPrinter`."""

from sbmlutils.converters.ode.printers.base import (
    MathPrinter,
    Precedence,
    Printed,
    SymbolMap,
    UnsupportedMathError,
)
from sbmlutils.converters.ode.printers.julia import JuliaPrinter
from sbmlutils.converters.ode.printers.python import PythonPrinter
from sbmlutils.converters.ode.printers.r import RPrinter

PRINTERS: dict[str, type[MathPrinter]] = {
    PythonPrinter.name: PythonPrinter,
    JuliaPrinter.name: JuliaPrinter,
    RPrinter.name: RPrinter,
}
"""The printer of each dialect, by its name."""

__all__ = [
    "PRINTERS",
    "JuliaPrinter",
    "MathPrinter",
    "Precedence",
    "Printed",
    "PythonPrinter",
    "RPrinter",
    "SymbolMap",
    "UnsupportedMathError",
]
