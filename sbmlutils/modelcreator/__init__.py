"""
SBML Model Creator, (c) 2016 Matthias Koenig
"""
TODO: sphynx documentation creation
TODO: automatic finding of unit tests with nose & running
TODO: license, readme, versioning

PROGRAM_NAME = "multiscale-modelcreator"
PROGRAM_VERSION = "0.1.0"

__version__ = PROGRAM_VERSION


"""
Create the SinusoidalUnit models for galactose metabolism.
The different model variants are driven by different events.
"""


from __future__ import print_function, division
import os
from sbmlutils.annotation import annotate_sbml_file
from sbmlutils.modelcreator.factory import CellModel
from sbmlutils.report import sbmlreport
from sbmlutils.validation import validate_sbml
from multiscale.examples.testdata import test_dir

"""
def tissue_model():
     # definition of cell model and tissue model
    Nc = 1
    Nf = 1
    version = 129
    cell_model = CellModel.create_model('multiscale.modelcreator.models.galactose.GalactoseCell')
    tissue_dict = TissueModel.createTissueDict(['multiscale.modelcreator.models.SinusoidalUnit',
                                                'multiscale.modelcreator.models.galactose.GalactoseSinusoid'])

    # ---------------------------------------------------------------------------------
    # [1] core model
    # Model without events. Basic model.
    tissue_model = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=tissue_dict,
                               cell_model=cell_model, sim_id='core', events=None)
    tissue_model.createModel()
    sbml_path = tissue_model.writeSBML()
    db_api.create_model(sbml_path, model_format=db_api.CompModelFormat.SBML)
    del tissue_model

    # ---------------------------------------------------------------------------------
    # [2A] multiple dilution indicator
    #    _
    # __| |__ (short rectangular peak in all periportal species)
    # The multiple dilution indicator peak is applied after the system has
    # reached steady state (<1000s) from initial non galactose conditions.
    events = EventData.rect_dilution_peak()
    tissue_model = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=tissue_dict,
                               cell_model=cell_model, sim_id='dilution', events=events)
    tissue_model.createModel()
    sbml_path = tissue_model.writeSBML()
    db_api.create_model(sbml_path, model_format=db_api.CompModelFormat.SBML)
    del tissue_model, events

    # [2B] multiple dilution indicator (Gauss peak)
    events = EventData.gauss_dilution_peak()
    tissue_model = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=tissue_dict,
                               cell_model=cell_model, sim_id='dilution_gauss', events=events)
    tissue_model.createModel()
    sbml_path = tissue_model.writeSBML()
    db_api.create_model(sbml_path, model_format=db_api.CompModelFormat.SBML)
    del tissue_model, events

    # ---------------------------------------------------------------------------------
    # [3] galactose challenge
    # Continous galactose challenge periportal applied (galactose pp__gal) after
    # system has reached steady state. Simulation continued until new steady state
    # under challenge conditions is reached.
    #    ________
    # __|
    events = EventData.galactose_challenge(tc_start=2000.0)
    tissue_model = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=tissue_dict,
                               cell_model=cell_model, sim_id='galchallenge', events=events)
    tissue_model.createModel()
    sbml_path = tissue_model.writeSBML()
    db_api.create_model(sbml_path, model_format=db_api.CompModelFormat.SBML)
    del tissue_model, events

    # ---------------------------------------------------------------------------------
    # [4] galactose step
    # Step-wise increase in the galactose concentration until new steady state
    # concentrations are reached in the system.
    #        _
    #      _| |
    #    _|   |
    # __|     |___
    events = EventData.galactose_step_increase()
    tissue_model = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=tissue_dict,
                               cell_model=cell_model, sim_id='galstep', events=events)
    sbml_path = tissue_model.writeSBML()
    db_api.create_model(sbml_path, model_format=db_api.CompModelFormat.SBML)
"""


# TODO: allow an force overwrite in the database
# TODO: proper checks of models via model hash


def create_model(directory, model_info=[], f_annotations=None, suffix=None):
    """
    :param directory: where to create the SBML files
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
    f_sbml = os.path.join(directory, fname)
    cell_model.write_sbml(f_sbml)

    # annotate
    if f_annotations is not None:
        # overwrite the normal file
        annotate_sbml_file(f_sbml, f_annotations, f_sbml)

    # create report
    sbmlreport.create_sbml_report(sbml=f_sbml, out_dir=directory)

    # add model to database
    # db_api.create_model(f_model, model_format=db_api.CompModelFormat.SBML)

    return [cell_dict, cell_model]

