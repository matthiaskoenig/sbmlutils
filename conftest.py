"""Test session configuration.

Two things are set up for the whole test session:

- **matplotlib never opens a window.** The `Agg` backend is selected before
  pyplot is imported anywhere, so a figure created by an example or by a test
  is rendered into a buffer instead of into a window. Without it a test which
  plots blocks on a machine with a display and fails on one without.
- **the examples are importable.** They are not part of the package, they live
  in `examples/` at the root of the repository, see `examples/README.md`.
  pytest puts the directory of this file on `sys.path`, so that
  `tests/examples/test_examples.py` can import the model definition of every
  example and check that it creates a valid model.
"""

from typing import Any

import matplotlib
import pytest

matplotlib.use("Agg", force=True)


@pytest.fixture(autouse=True)
def cytoscape_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, tuple, dict]]:
    """Keep the test session away from a running Cytoscape.

    A Cytoscape open on the machine listens on localhost:1234 and the examples
    call `visualize_sbml(..., delete_session=True)`, which would close the
    session of the user without saving. `py4cytoscape` is therefore replaced
    in `sbmlutils.cytoscape`, the lowest level every example goes through, by
    a recorder, so the call path of the examples is still exercised.

    Returns:
        The recorded calls as (dotted name, args, kwargs).
    """
    calls: list[tuple[str, tuple, dict]] = []

    class _Recorder:
        def __init__(self, name: str = "") -> None:
            self._name = name

        def __getattr__(self, attr: str) -> "_Recorder":
            if attr.startswith("__"):
                raise AttributeError(attr)
            return _Recorder(f"{self._name}.{attr}" if self._name else attr)

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            calls.append((self._name, args, kwargs))
            if self._name == "networks.import_network_from_file":
                return {"networks": [1, 1], "views": [1]}
            return None

    from sbmlutils import cytoscape

    monkeypatch.setattr(cytoscape, "p4c", _Recorder())
    return calls
