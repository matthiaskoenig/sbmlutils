"""Generate the agent facing files of the documentation site.

Static site generators render the documentation for browsers; agents and large
language models are better served by markdown. This script writes the files of
the [llms.txt convention](https://llmstxt.org/) into the built site:

- `llms.txt`, an index of the documentation with one annotated link per page,
- `llms-full.txt`, the complete documentation as a single markdown file,
- a markdown copy of every page next to its html, so that the links resolve.

The pages of the API reference only contain a mkdocstrings directive
(`::: sbmlutils.factory`), their markdown is generated from the docstrings of the
module with `inspect`, i.e., the same source the html is rendered from.

Run it after `zensical build`:

```bash
uv run zensical build --clean
uv run python scripts/llms_txt.py
```
"""

import importlib
import inspect
import re
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple

REPO_DIR: Path = Path(__file__).parent.parent
DOCS_DIR: Path = REPO_DIR / "docs"
SITE_DIR: Path = REPO_DIR / "site"
CONFIG_PATH: Path = REPO_DIR / "zensical.toml"

DIRECTIVE = re.compile(r"^:::\s+(?P<module>[\w.]+)\s*$", re.MULTILINE)


class Page(NamedTuple):
    """A page of the documentation.

    Attributes:
        section: title of the nav section the page belongs to.
        title: title of the page in the nav.
        path: path of the markdown source relative to `docs/`.
    """

    section: str
    title: str
    path: str


def read_config() -> dict[str, Any]:
    """Read the zensical configuration.

    Returns:
        The `project` table of `zensical.toml`.
    """
    with CONFIG_PATH.open("rb") as f_config:
        config: dict[str, Any] = tomllib.load(f_config)
    return config["project"]


def parse_nav(nav: list[Any], section: str = "Documentation") -> list[Page]:
    """Flatten the nav of the configuration into a list of pages.

    Args:
        nav: nav entries, i.e., single element dictionaries mapping a title to
            either a path or a list of nav entries.
        section: title of the section the entries belong to.

    Returns:
        The pages in the order of the nav.
    """
    pages: list[Page] = []
    for entry in nav:
        for title, value in entry.items():
            if isinstance(value, list):
                # a subsection keeps the title of its top level section, the
                # sections of `llms.txt` are flat
                sub_section = section if section != "Documentation" else title
                pages.extend(parse_nav(value, section=sub_section))
            else:
                pages.append(Page(section=section, title=title, path=value))
    return pages


def summary(markdown: str) -> str:
    """Extract a one line summary from the markdown of a page.

    The first paragraph which is neither a heading, a badge, an image nor a
    code block is used, reduced to its first sentence.

    Args:
        markdown: content of the page.

    Returns:
        The summary, empty if no paragraph was found.
    """
    for block in markdown.split("\n\n"):
        line = block.strip()
        if not line or line.startswith(("#", "!", "[", "```", "|", ">", ":::")):
            continue
        sentence = line.split(". ")[0].replace("\n", " ").strip()
        return re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", sentence).rstrip(":.") + "."
    return ""


def signature(obj: Any) -> str:
    """Render the signature of a class or function.

    Args:
        obj: class or function to render.

    Returns:
        The signature, the bare name if it cannot be determined.
    """
    try:
        return f"{obj.__name__}{inspect.signature(obj)}"
    except (TypeError, ValueError):
        return str(obj.__name__)


def members(obj: ModuleType | type, module: str) -> list[tuple[str, Any]]:
    """Collect the public members which are defined in the given module.

    Args:
        obj: module or class to inspect.
        module: name of the module the members must be defined in.

    Returns:
        The members as `(name, member)` in definition order.
    """
    items: list[tuple[str, Any]] = []
    for name, member in inspect.getmembers(obj):
        if name.startswith("_") or getattr(member, "__module__", None) != module:
            continue
        if inspect.isclass(member) or inspect.isfunction(member):
            items.append((name, member))
    return items


def api_markdown(module_name: str) -> str:
    """Render the API of a module as markdown.

    Args:
        module_name: name of the module, e.g., `sbmlutils.factory`.

    Returns:
        The module docstring followed by the public classes and functions with
        their signatures and docstrings.
    """
    module = importlib.import_module(module_name)
    lines: list[str] = [f"# {module_name}", ""]
    if module.__doc__:
        lines += [inspect.cleandoc(module.__doc__), ""]

    for name, member in members(module, module_name):
        kind = "class" if inspect.isclass(member) else "function"
        lines += [f"## {kind} `{signature(member)}`", ""]
        if member.__doc__:
            lines += [inspect.cleandoc(member.__doc__), ""]
        if not inspect.isclass(member):
            continue
        for _method_name, method in members(member, module_name):
            lines += [f"### `{name}.{signature(method)}`", ""]
            if method.__doc__:
                lines += [inspect.cleandoc(method.__doc__), ""]
    return "\n".join(lines).rstrip() + "\n"


def page_markdown(page: Page) -> str:
    """Return the markdown of a page.

    Args:
        page: page of the documentation.

    Returns:
        The source markdown, or the generated API markdown for the pages of the
        API reference.
    """
    markdown = (DOCS_DIR / page.path).read_text()
    match = DIRECTIVE.search(markdown) if page.path.startswith("api/") else None
    return api_markdown(match.group("module")) if match else markdown


def sections(pages: dict[Page, str]) -> dict[str, list[Page]]:
    """Group the pages by their section, in the order of the nav.

    Args:
        pages: markdown of every page of the documentation.

    Returns:
        The pages of every section, keyed by the section title.
    """
    grouped: dict[str, list[Page]] = {}
    for page in pages:
        grouped.setdefault(page.section, []).append(page)
    return grouped


def write_llms_txt(pages: dict[Page, str], config: dict[str, Any]) -> None:
    """Write the `llms.txt` index of the documentation.

    Args:
        pages: markdown of every page of the documentation.
        config: `project` table of the zensical configuration.
    """
    site_url: str = config["site_url"].rstrip("/")
    lines: list[str] = [
        f"# {config['site_name']}",
        "",
        f"> {config['site_description']}",
        "",
        "The links below point to the markdown source of the documentation. "
        f"[llms-full.txt]({site_url}/llms-full.txt) contains all of it in a "
        "single file.",
    ]

    for section, section_pages in sections(pages).items():
        lines += ["", f"## {section}", ""]
        for page in section_pages:
            url = f"{site_url}/{page.path}"
            summary_text = summary(pages[page])
            lines.append(f"- [{page.title}]({url}): {summary_text}".rstrip())

    lines += [
        "",
        "## Optional",
        "",
        f"- [Repository]({config['repo_url']}): source code, issues and releases.",
        f"- [Sitemap]({site_url}/sitemap.xml): all pages of the rendered site.",
        f"- [objects.inv]({site_url}/objects.inv): the API objects of the "
        "reference as a sphinx inventory.",
        "",
    ]
    (SITE_DIR / "llms.txt").write_text("\n".join(lines))


def write_llms_full_txt(pages: dict[Page, str], config: dict[str, Any]) -> None:
    """Write the complete documentation as a single markdown file.

    Args:
        pages: markdown of every page of the documentation.
        config: `project` table of the zensical configuration.
    """
    site_url: str = config["site_url"].rstrip("/")
    lines: list[str] = [
        f"# {config['site_name']}",
        "",
        f"> {config['site_description']}",
        "",
        f"The complete documentation from {site_url}, one section per page.",
        "",
    ]
    for page, markdown in pages.items():
        lines += [
            "---",
            "",
            f"<!-- {site_url}/{page.path} -->",
            "",
            markdown.strip(),
            "",
        ]
    (SITE_DIR / "llms-full.txt").write_text("\n".join(lines))


def write_markdown(pages: dict[Page, str]) -> None:
    """Write the markdown of every page next to its rendered html.

    Args:
        pages: markdown of every page of the documentation.
    """
    for page, markdown in pages.items():
        path = SITE_DIR / page.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown)


def main() -> None:
    """Generate the agent facing files of the built site."""
    if not SITE_DIR.exists():
        raise SystemExit(f"'{SITE_DIR}' does not exist, run `zensical build` first.")

    config = read_config()
    pages = {page: page_markdown(page) for page in parse_nav(config["nav"])}

    write_markdown(pages)
    write_llms_txt(pages, config)
    write_llms_full_txt(pages, config)
    print(f"llms.txt, llms-full.txt and {len(pages)} markdown pages in '{SITE_DIR}'")


if __name__ == "__main__":
    main()
