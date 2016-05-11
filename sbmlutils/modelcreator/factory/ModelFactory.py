"""
Base class for all ModelFactories.

"""
import django
django.setup()
import simapp.db.api as db_api


class ModelFactory(object):

    def core_model(self, Nc, Nf=1, sim_id='core'):
        """ Creates the core model.
         At least every submodel should implement a core model.
        """
        raise NotImplemented

    @staticmethod
    def store_model_in_db(tissue_model, sbml_path=None):
        """ Stores the model in the django database. """
        sbml_path = tissue_model.write_sbml(sbml_path)
        model = db_api.create_model(sbml_path, model_format=db_api.CompModelFormat.SBML)
        return model

