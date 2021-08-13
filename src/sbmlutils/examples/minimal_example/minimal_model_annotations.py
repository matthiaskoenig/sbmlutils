"""Annotate an existing model."""
from pathlib import Path

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.metadata.annotator import annotate_sbml


if __name__ == "__main__":
    base_path = Path(__file__).parent

    doc = annotate_sbml(
        source=base_path / "minimal_model.xml",
        annotations_path=base_path / "minimal_model_annotations.xlsx",
        filepath=base_path / "minimal_model_annotations.xml",
    )

    visualize_sbml(
        sbml_path=base_path / "minimal_model_annotations.xml", delete_session=True
    )
