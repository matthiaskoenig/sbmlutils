"""
Model factory for the BasicClearance example model.
"""

from __future__ import print_function

from ModelFactory import ModelFactory
from multiscale.examples.models import TissueModel
from multiscale.modelcreator.events.eventdata import EventData

from oven import CellModel


class BasicClearanceFactory(ModelFactory):
    # define which models to use
    cell_model = CellModel.create_model('clearance.BasicClearanceCell')
    tissue_dict = TissueModel.createTissueDict(['SinusoidalUnit', 'clearance.BasicClearanceSinusoid'])

    @classmethod
    def core_model(cls, Nc, Nf, version, sim_id='core'):
        """ Creates the core model. """
        tissue_model = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=cls.tissue_dict,
                                   cell_model=cls.cell_model, sim_id=sim_id, events=None)
        # TODO: this should be done in the constructor of the model
        tissue_model.createModel()
        return tissue_model

    @classmethod
    def dilution_indicator_model(cls, Nc, Nf, version, sim_id='dilution'):
        """ Creates multiple indicator dilution data for the model.
            ___|---|__ (in all periportal species)
        The multiple dilution indicator peak comes when the system is
        in steady state after the applied initial condition changes:
        """

        # TODO overwrite all parameters necessary for events here
        # i.e. additional information has to be overwritten here
        # keep the core model clean
        events = EventData.rect_dilution_peak()

        tissue_model = TissueModel(Nc=Nc, Nf=Nf, version=version, tissue_dict=cls.tissue_dict,
                                   cell_model=cls.cell_model, sim_id='dilution', events=events)
        tissue_model.createModel()
        return tissue_model


if __name__ == "__main__":
    Nc = 20  # number of cells
    Nf = 1  # compartments per cell
    version = 5  # model version

    # [1] core model
    core_model = BasicClearanceFactory.core_model(Nc, Nf, version)
    BasicClearanceFactory.store_model_in_db(core_model)

    # [2] multiple dilution indicator
    dilution_model = BasicClearanceFactory.dilution_indicator_model(Nc, Nf, version)
    BasicClearanceFactory.store_model_in_db(dilution_model)
