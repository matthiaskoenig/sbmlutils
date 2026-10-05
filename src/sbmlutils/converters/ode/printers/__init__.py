"""Printers of SBML math, one per dialect, on the engine of `base.MathPrinter`."""

from sbmlutils.converters.ode.printers.base import (
    MathPrinter,
    Precedence,
    Printed,
    SymbolMap,
    Term,
    UnsupportedMathError,
)
from sbmlutils.converters.ode.printers.document import DocumentPrinter
from sbmlutils.converters.ode.printers.julia import JuliaPrinter
from sbmlutils.converters.ode.printers.latex import LatexPrinter
from sbmlutils.converters.ode.printers.python import PythonPrinter
from sbmlutils.converters.ode.printers.r import RPrinter
from sbmlutils.converters.ode.printers.typst import TypstPrinter

PRINTERS: dict[str, type[MathPrinter]] = {
    PythonPrinter.name: PythonPrinter,
    JuliaPrinter.name: JuliaPrinter,
    RPrinter.name: RPrinter,
    LatexPrinter.name: LatexPrinter,
    TypstPrinter.name: TypstPrinter,
}
"""The printer of each dialect, by its name."""

__all__ = [
    "PRINTERS",
    "DocumentPrinter",
    "JuliaPrinter",
    "LatexPrinter",
    "MathPrinter",
    "Precedence",
    "Printed",
    "PythonPrinter",
    "RPrinter",
    "SymbolMap",
    "Term",
    "TypstPrinter",
    "UnsupportedMathError",
]
