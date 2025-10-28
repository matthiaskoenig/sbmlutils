"""Module for visualization in Cytoscape.

Supports loading of networks, annotations and storing of images.
"""

import os
import tempfile
from dataclasses import dataclass
from enum import Enum

import pandas as pd

os.environ["PY4CYTOSCAPE_DETAIL_LOGGER_DIR"] = str(tempfile.gettempdir())

from pathlib import Path  # noqa: E402
from typing import Any, Union, Optional, Iterable  # noqa: E402

import py4cytoscape as p4c  # type: ignore  # noqa: E402
from requests.exceptions import RequestException  # noqa: E402

from sbmlutils import log  # noqa: E402
from sbmlutils.console import console  # noqa: E402
from sbmlutils.parser import antimony_to_sbml  # noqa: E402


logger = log.get_logger(__name__)


def visualize_antimony(source: Union[Path, str], delete_session: bool = False) -> Any:
    """Visualize antimony in cytoscape."""
    sbml_str = antimony_to_sbml(source=source)
    tmp_file = tempfile.NamedTemporaryFile()
    with open(tmp_file.name, "w", encoding="utf-8") as f_tmp:
        f_tmp.write(sbml_str)

    visualize_sbml(Path(f_tmp.name), delete_session=delete_session)


def visualize_sbml(sbml_path: Path, delete_session: bool = False) -> Optional[int]:
    """Visualize SBML networks in cytoscape.

    Returns dictionary with "networks" and "views".
    """
    try:
        console.print(p4c.cytoscape_version_info())

        if delete_session:
            p4c.session.close_session(save_before_closing=False)

        networks_views = p4c.networks.import_network_from_file(str(sbml_path))
        # console.print(f"{networks_views}")
        network: Optional[int] = networks_views["networks"][1]
        p4c.set_current_view(network=network)  # set the base network
        return network

    except RequestException:
        logger.warning(
            "Could not connect to a running Cytoscape instance. "
            "Start Cytoscape before running the python script."
        )
        return None


def read_layout_xml(sbml_path: Path, xml_path: Path) -> pd.DataFrame:
    """Read own xml layout information form cytoscape."""
    # read positions
    df: pd.DataFrame = pd.read_xml(xml_path, xpath="//boundingBox")
    df = df[["id", "xpos", "ypos"]]
    df.rename(columns={"xpos": "x", "ypos": "y"}, inplace=True)
    df.set_index("id", inplace=True)
    return df


def apply_layout(layout: pd.DataFrame, network: Optional[int] = None) -> None:
    """Apply layout information from Cytoscape to SBML networks."""

    # get SUIDs, sbml_id from node table;
    df_nodes = p4c.get_table_columns(table="node", columns=["sbml id"], network=network)
    sid2suid = {row["sbml id"]: suid for suid, row in df_nodes.iterrows()}

    # FIXME: necessary to check that all sids exist
    suids = [sid2suid[sid] for sid in layout.index.values]
    x_values = layout["x"].values.tolist()
    y_values = layout["y"].values.tolist()
    # z_values = layout["z"].values.tolist()

    # set positions
    # see: https://github.com/cytoscape/py4cytoscape/issues/144
    p4c.set_node_position_bypass(
        suids, new_x_locations=x_values, new_y_locations=y_values, network=network
    )
    # p4c.set_node_property_bypass(suids, new_values=x_values, visual_property='NODE_X_LOCATION', network=network)
    # p4c.set_node_property_bypass(suids, new_values=y_values, visual_property='NODE_Y_LOCATION', network=network)
    # positions = p4c.get_node_position()
    # console.print(f"{positions}")

    # fit content
    p4c.fit_content()

    # remove bypass
    # p4c.clear_node_property_bypass(suids, visual_property='NODE_X_LOCATION', network=network)
    # p4c.clear_node_property_bypass(suids, visual_property='NODE_Y_LOCATION', network=network)
    # positions = p4c.get_node_position()
    # console.print(f"{positions}")


class AnnotationShapeType(str, Enum):
    RECTANGLE = "RECTANGLE"
    ROUND_RECTANGLE = "ROUND_RECTANGLE"


@dataclass
class AnnotationShape:
    type: AnnotationShapeType
    x_pos: int
    y_pos: int
    height: int
    width: int
    fill_color: str = "#000000"
    opacity: int = 100
    border_thickness: int = 1
    border_color: str = "#FFFFFF"
    border_opacity: int = 100
    canvas: str = "background"
    z_order: int = 0


@dataclass
class AnnotationText:
    text: str
    x_pos: int
    y_pos: int
    font_size: int = 12  # Numeric value; default is 12
    font_family: str = "Arial"  # Font family; default is Arial
    font_style: str = "bold"  # Font style; default is none
    color: str = "#000000" ""  # hexadecimal color; default is #000000 (black)
    angle: float = 0  # Angle of text orientation; default is 0.0 (horizontal)
    canvas: str = "background"


@dataclass
class AnnotationBoundedText:
    type: AnnotationShapeType
    text: str
    x_pos: int
    y_pos: int
    height: int
    width: int
    fill_color: str = "#000000"
    opacity: int = 100
    border_thickness: int = 1
    border_color: str = "#FFFFFF"
    border_opacity: int = 100
    font_size: int = 12  # Numeric value; default is 12
    font_family: str = "Arial"  # Font family; default is Arial
    font_style: str = "bold"  # Font style; default is none
    color: str = "#000000" ""  # hexadecimal color; default is #000000 (black)
    angle: float = 0  # Angle of text orientation; default is 0.0 (horizontal)
    canvas: str = "background"


def add_annotations(annotations: Iterable, network: Optional[int] = None) -> None:
    """Add annotations to the network."""

    for a in annotations:
        if isinstance(a, AnnotationShape):
            p4c.add_annotation_shape(
                network=network,
                type=a.type,
                x_pos=a.x_pos,
                y_pos=a.y_pos,
                height=a.height,
                width=a.width,
                fill_color=a.fill_color,
                opacity=a.opacity,
                border_thickness=a.border_thickness,
                border_color=a.border_color,
                border_opacity=a.border_opacity,
                canvas=a.canvas,
                z_order=a.z_order,
            )

        if isinstance(a, AnnotationText):
            p4c.add_annotation_text(
                text=a.text,
                x_pos=a.x_pos,
                y_pos=a.y_pos,
                font_size=a.font_size,
                font_family=a.font_family,
                font_style=a.font_style,
                color=a.color,
                angle=a.angle,
                canvas=a.canvas,
            )
        if isinstance(a, AnnotationBoundedText):
            p4c.add_annotation_bounded_text(
                type=a.type,
                text=a.text,
                x_pos=a.x_pos,
                y_pos=a.y_pos,
                height=a.height,
                width=a.width,
                fill_color=a.fill_color,
                opacity=a.opacity,
                border_thickness=a.border_thickness,
                border_color=a.border_color,
                border_opacity=a.border_opacity,
                font_size=a.font_size,
                font_family=a.font_family,
                font_style=a.font_style,
                color=a.color,
                angle=a.angle,
                canvas=a.canvas,
            )


def export_image(
    image_path: Path,
    format: str = "PNG",
    fit_content: bool = False,
    hide_labels: bool = False,
) -> None:
    """Helper for exporting cytoscape images.

    format (str): Type of image to export, e.g., PNG (default), JPEG, PDF, SVG, PS (PostScript).
    """
    if fit_content:
        p4c.fit_content()

    p4c.export_image(
        filename=str(image_path),
        type=format,
        zoom=400.0,
        overwrite_file=True,
        all_graphics_details=True,
        hide_labels=hide_labels,
    )


if __name__ == "__main__":
    pass
    # # visual style
    # p4c.set_visual_style('Marquee')
    #
    # # fit the content
    # p4c.fit_content()

    # p4c.load_table_data

    # annotations!

    # network_views.export_image
