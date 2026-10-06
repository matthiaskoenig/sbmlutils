"""The python code blocks of the guide `docs/interpolation.md` run."""

import re
from pathlib import Path

import pytest

GUIDE = Path(__file__).parent.parent.parent / "docs" / "interpolation.md"


def test_guide_code_blocks_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The blocks run in order, in one namespace, in a temporary directory."""
    pytest.importorskip("roadrunner")
    blocks = re.findall(r"```python\n(.*?)```", GUIDE.read_text(), flags=re.DOTALL)
    assert len(blocks) >= 6
    monkeypatch.chdir(tmp_path)
    namespace: dict[str, object] = {}
    for block in blocks:
        exec(compile(block, str(GUIDE), "exec"), namespace)  # noqa: S102
