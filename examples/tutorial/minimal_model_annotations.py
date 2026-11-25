"""Annotate an existing model."""

from pathlib import Path

from sbmlutils.metadata.annotator import annotate_sbml

if __name__ == "__main__":
    from sbmlutils import log

    log.enable_rich_logging()

    doc = annotate_sbml(
        source=Path.cwd() / "minimal_model.xml",
        filepath=Path.cwd() / "minimal_model_annotations.xml",
        annotations_path=Path(__file__).parent / "minimal_model_annotations.xlsx",
    )
