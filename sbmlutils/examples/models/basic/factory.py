from __future__ import print_function, division
import os
from sbmlutils import modelcreator
from sbmlutils.modelcreator.modelcreator import Factory

models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class BasicFactory(Factory):
    """
    Implements model factory.
    """
    modules = ['sbmlutils.examples.models.basic.Cell']
    target_dir = os.path.join(models_dir, 'results')

    @classmethod
    def create(cls):
        """ Create model. """
        return modelcreator.create_model(modules=cls.modules,
                                         target_dir=cls.target_dir)

if __name__ == "__main__":
    BasicFactory.create()
