"""Annotate an existing model."""

from pathlib import Path

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.metadata.annotator import annotate_sbml


if __name__ == "__main__":

    doc = annotate_sbml(
        source=Path.cwd() / "minimal_model.xml",
        filepath=Path.cwd() / "minimal_model_annotations.xml",
        annotations_path=Path(__file__).parent / "minimal_model_annotations.xlsx",
    )

    visualize_sbml(
        sbml_path=Path.cwd() / "minimal_model_annotations.xml", delete_session=True
    )
