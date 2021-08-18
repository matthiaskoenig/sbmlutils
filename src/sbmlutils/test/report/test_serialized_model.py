"""Test serialization of SBML Models"""
from pathlib import Path

import logging
import json
import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import GZ_SBML

logger = logging.getLogger(__name__)

@pytest.mark.parametrize("sbml_path", [GZ_SBML])
def test_serialization_gz(sbml_path: Path, tmp_path: Path) -> None:
    """Test report generation for compressed models."""
    serialized_model_info = sbmlreport.create_report(sbml_path=sbml_path, output_dir=tmp_path)

    filename = "test.json"
    with open(filename, "w") as json_file:
        json.dump(serialized_model_info, json_file)
