"""
Helper functions for creating SBML models.
"""

from __future__ import print_function, division
import os
from sbmlutils.annotation import annotate_sbml_file
from sbmlutils.report import sbmlreport

from factory.model_cell import CellModel


def create_model(target_dir, model_info=[], f_annotations=None, suffix=None):
    """ Create SBML model from given information.

    :param target_dir: where to create the SBML files
    :param model_info: model_info strings of python modules
    :param f_annotations: csv annotation file
    :return:
    """
    print("***", model_info, "***")

    cell_dict = CellModel.createCellDict(model_info)
    cell_model = CellModel(cell_dict=cell_dict)
    cell_model.create_sbml()

    mid = cell_model.model.getId()
    if suffix is not None:
        fname = '{}{}.xml'.format(mid, suffix)
    else:
        fname = '{}.xml'.format(mid)
    f_sbml = os.path.join(target_dir, fname)
    cell_model.write_sbml(f_sbml)

    # annotate
    if f_annotations is not None:
        # overwrite the normal file
        annotate_sbml_file(f_sbml, f_annotations, f_sbml)

    # create report
    sbmlreport.create_sbml_report(sbml=f_sbml, out_dir=target_dir)

    return [cell_dict, cell_model]

