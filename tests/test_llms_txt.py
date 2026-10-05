"""Test the markdown which `scripts/llms_txt.py` writes for agents."""

from pathlib import Path

import pytest

from scripts import llms_txt
from scripts.llms_txt import Page, page_markdown


@pytest.fixture
def docs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A documentation directory in place of `docs`."""
    monkeypatch.setattr(llms_txt, "DOCS_DIR", tmp_path)
    return tmp_path


def test_snippets_are_included(docs_dir: Path) -> None:
    """A snippet line is the file it names, with the indentation of the line."""
    (docs_dir / "files").mkdir()
    (docs_dir / "files" / "model.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
    (docs_dir / "page.md").write_text(
        '# Page\n\n??? example\n\n    ```python\n    --8<-- "files/model.py"\n    ```\n',
        encoding="utf-8",
    )
    markdown = page_markdown(Page("Guide", "Page", "page.md"))
    assert markdown == (
        "# Page\n\n??? example\n\n    ```python\n    x = 1\n    y = 2\n    ```\n"
    )


def test_missing_snippet_fails(docs_dir: Path) -> None:
    """A snippet of a file which does not exist fails, as it fails the build."""
    (docs_dir / "page.md").write_text('--8<-- "missing.md"\n', encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        page_markdown(Page("Guide", "Page", "page.md"))


def test_every_module_of_an_api_page(docs_dir: Path) -> None:
    """An API page of several modules is the API of each of them."""
    (docs_dir / "api").mkdir()
    (docs_dir / "api" / "ode.md").write_text(
        "# ode\n\n::: sbmlutils.converters.ode\n\n## The ODE system\n\n"
        "::: sbmlutils.converters.ode.system\n    options:\n      filters: []\n",
        encoding="utf-8",
    )
    markdown = page_markdown(Page("API", "ode", "api/ode.md"))
    assert markdown.startswith("# sbmlutils.converters.ode\n")
    assert "\n# sbmlutils.converters.ode.system\n" in markdown
