"""Example model with notes."""
from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *


_m = Model(
    sid="notes",
    name="model with notes showcase",
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
    ```
    # H1
    ## H2
    ### H3
    #### H4
    ##### H5
    ###### H6
    ```

    # H1
    ## H2
    ### H3
    #### H4
    ##### H5
    ###### H6

    ---
    ### Emphasis
    ```
    Emphasis, aka italics, with *asterisks* or _underscores_.

    Strong emphasis, aka bold, with **asterisks** or __underscores__.

    Combined emphasis with **asterisks and _underscores_**.
    ```
    Emphasis, aka italics, with *asterisks* or _underscores_.

    Strong emphasis, aka bold, with **asterisks** or __underscores__.

    Combined emphasis with **asterisks and _underscores_**.

    ---
    ### Lists
    (In this example, leading and trailing spaces are shown with with dots: ⋅)
    ```
    1. First ordered list item
    2. Another item
    ⋅⋅* Unordered sub-list.
    1. Actual numbers don't matter, just that it's a number
    ⋅⋅1. Ordered sub-list
    4. And another item.

    ⋅⋅⋅You can have properly indented paragraphs within list items. Notice the blank line above, and the leading spaces (at least one, but we'll use three here to also align the raw Markdown).

    ⋅⋅⋅To have a line break without a paragraph, you will need to use two trailing spaces.⋅⋅
    ⋅⋅⋅Note that this line is separate, but within the same paragraph.⋅⋅
    ⋅⋅⋅(This is contrary to the typical GFM line break behaviour, where trailing spaces are not required.)

    * Unordered list can use asterisks
    - Or minuses
    + Or pluses
    ```
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
    ```
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
    ```
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
    ### Images
    ```
    Here's our logo (hover to see the title text):

    Inline-style:
    ![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

    Reference-style:
    ![alt text][logo]

    [logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"
    ```
    Here's our logo (hover to see the title text):

    Inline-style:
    ![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

    Reference-style:
    ![alt text][logo]

    [logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"

    ---
    ### Code
    Code blocks are part of the Markdown spec, but syntax highlighting isn't. However,
    many renderers -- like Github's and Markdown Here -- support syntax highlighting.
    Which languages are supported and how those language names should be written will vary from renderer
    to renderer. Markdown Here supports highlighting for dozens of languages
    (and not-really-languages, like diffs and HTTP headers); to see the complete list,
    and how to write the language names, see the [highlight.js](http://softwaremaniacs.org/media/soft/highlight/test.html) demo page.

    ```
    Inline `code` has `back-ticks around` it.
    ```
    Inline `code` has `back-ticks around` it.

    Blocks of code are either fenced by lines with three back-ticks ```, or are indented with four spaces.
    I recommend only using the fenced code blocks -- they're easier and only they support syntax highlighting.

    ```
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
    ```

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
    ---
    ### Blockquotes
    ```
    > Blockquotes are very handy in email to emulate reply text.
    > This line is part of the same quote.

    Quote break.

    > This is a very long line that will still be quoted properly when it wraps. Oh boy let's keep writing to make sure this is long enough to actually wrap for everyone. Oh, you can *put* **Markdown** into a blockquote.
    ```
    > Blockquotes are very handy in email to emulate reply text.
    > This line is part of the same quote.

    Quote break.

    > This is a very long line that will still be quoted properly when it wraps. Oh boy let's keep writing to make sure this is long enough to actually wrap for everyone. Oh, you can *put* **Markdown** into a blockquote.

    ---
    ### Inline HTML
    You can also use raw HTML in your Markdown, and it'll mostly work pretty well.
    ```
    <dl>
      <dt>Definition list</dt>
      <dd>Is something people use sometimes.</dd>

      <dt>Markdown in HTML</dt>
      <dd>Does *not* work **very** well. Use HTML <em>tags</em>.</dd>
    </dl>
    ```
    <dl>
      <dt>Definition list</dt>
      <dd>Is something people use sometimes.</dd>

      <dt>Markdown in HTML</dt>
      <dd>Does *not* work **very** well. Use HTML <em>tags</em>.</dd>
    </dl>

    """
    + templates.terms_of_use,
    creators=templates.creators,
)


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=_m,
        output_dir=EXAMPLES_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    results = create()
