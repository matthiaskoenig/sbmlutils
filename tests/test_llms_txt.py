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
    """An API page is its prose with the API of each module, as its filters say."""
    (docs_dir / "api").mkdir()
    (docs_dir / "api" / "ode.md").write_text(
        "# ode\n\nThe guide is elsewhere.\n\n::: sbmlutils.converters.ode\n\n"
        "## The ODE system\n\n::: sbmlutils.converters.ode.system\n"
        '    options:\n      filters: ["!^_", "!^OdeSystem$"]\n',
        encoding="utf-8",
    )
    markdown = page_markdown(Page("API", "ode", "api/ode.md"))
    assert markdown.startswith("# ode\n\nThe guide is elsewhere.\n\n")
    assert "\n## sbmlutils.converters.ode\n" in markdown
    assert "\n## The ODE system\n" in markdown
    assert "\n## sbmlutils.converters.ode.system\n" in markdown
    assert "filters:" not in markdown
    # `OdeSystem` is filtered from the second module, so it is listed once
    assert markdown.count("### class `OdeSystem") == 1
    assert "### class `Quantity" in markdown


def test_snippet_needs_a_space_on_its_line(docs_dir: Path) -> None:
    """A snippet line is the marker, blanks and the path, never across lines."""
    (docs_dir / "page.md").write_text('--8<--\n"missing.md"\n', encoding="utf-8")
    assert page_markdown(Page("Guide", "Page", "page.md")) == '--8<--\n"missing.md"\n'
