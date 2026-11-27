"""Deprecated import aliases for the shared Rust equation generator.

Use ``from sbmlsim_core import OdeSystem``. The former ``system`` and ``formats``
import paths remain aliases of ``sbmlsim_core.ode``; mathematical analysis,
printers and templates have one implementation in the shared core.
"""

import sys
import warnings

from sbmlsim_core import ode as _ode
from sbmlsim_core.ode import (
    FORMATS,
    Format,
    OdeSystem,
    render,
    render_template,
    write,
)

warnings.warn(
    "sbmlutils.converters.ode is deprecated; import from sbmlsim_core instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["FORMATS", "Format", "OdeSystem", "render", "render_template", "write"]

sys.modules[__name__ + ".system"] = _ode
sys.modules[__name__ + ".formats"] = _ode
system = _ode
formats = _ode
