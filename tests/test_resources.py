"""Test the packaged resources."""

from sbmlutils.resources import API_EXAMPLES_MODEL, API_EXAMPLES_OMEX


def test_api_examples_exist() -> None:
    """All models served as examples by sbml4humans exist."""
    for path in API_EXAMPLES_OMEX + API_EXAMPLES_MODEL:
        assert path.is_file(), path


def test_api_examples_unique() -> None:
    """A model is served as example once."""
    paths = API_EXAMPLES_OMEX + API_EXAMPLES_MODEL
    assert len(set(paths)) == len(paths)
