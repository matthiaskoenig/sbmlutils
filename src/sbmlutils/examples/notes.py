"""Example model with notes."""

from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.miriam import *
from sbmlutils.metadata.sbo import *
from sbmlutils.report.sbmlreport import create_online_report
from sbmlutils.units import *


_m = Model(
    sid="notes_example",
    notes="""
    # Model with notes
    ## Description
    All model objects and the model itself can be documented via `notes`.
    Notes can either be HTML or Markdown or a combination of both. The notes on
    this model demonstrate the possible features.

    ## Markdown cheatsheet
    adapted from <https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet>

    ---
    ### Headings
        # H1
        ## H2
        ### H3
        #### H4
        ##### H5
        ###### H6

    # H1
    ## H2
    ### H3
    #### H4
    ##### H5
    ###### H6

    ---
    ### Emphasis

        Emphasis, aka italics, with *asterisks* or _underscores_.

        Strong emphasis, aka bold, with **asterisks** or __underscores__.

        Combined emphasis with **asterisks and _underscores_**.

    Emphasis, aka italics, with *asterisks* or _underscores_.

    Strong emphasis, aka bold, with **asterisks** or __underscores__.

    Combined emphasis with **asterisks and _underscores_**.

    ---
    ### Lists
    1. First ordered list item
    2. Another item
      * Unordered sub-list.
    1. Actual numbers don't matter, just that it's a number
      1. Ordered sub-list
    4. And another item.

       You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

       To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
       Note that this line is separate, but within the same paragraph.⋅⋅
       (This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

    * Unordered list can use asterisks
    - Or minuses
    + Or pluses

    ---
    ### Links
    There are two ways to create links.

    [I'm an inline-style link](https://www.google.com)

    [I'm an inline-style link with title](https://www.google.com "Google's Homepage")

    [I'm a reference-style link][Arbitrary case-insensitive reference text]

    [I'm a relative reference to a repository file](../blob/master/LICENSE)

    [You can use numbers for reference-style link definitions][1]

    Or leave it empty and use the [link text itself].

    URLs and URLs in angle brackets will automatically get turned into links.
    http://www.example.com or <http://www.example.com> and sometimes
    example.com (but not on Github, for example).

    Some text to show that the reference links can follow later.

    [arbitrary case-insensitive reference text]: https://www.mozilla.org
    [1]: http://slashdot.org
    [link text itself]: http://www.reddit.com

    ---
    ### Code
    ```javascript
    var s = "JavaScript syntax highlighting";
    alert(s);
    ```

    ```python
    s = "Python syntax highlighting"
    print s
    ```

    ```
    No language indicated, so no syntax highlighting.
    But let's throw in a <b>tag</b>.
    ```

    """ + templates.terms_of_use,
    creators=templates.creators,
)


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=_m,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    results = create()
    create_online_report(sbml_path=results.sbml_path, server="http://localhost:3456")
