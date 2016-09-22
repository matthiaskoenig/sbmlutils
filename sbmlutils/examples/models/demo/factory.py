"""
Create model.
"""

from __future__ import print_function, division
import os
from sbmlutils import modelcreator
from sbmlutils.modelcreator.modelcreator import Factory

models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class DemoFactory(Factory):
    """
    Implements model factory.
    """
    modules = ['sbmlutils.examples.models.demo.Cell']
    target_dir = os.path.join(models_dir, 'results')
    annotations = os.path.join(models_dir, 'demo_annotations.xlsx')

    @classmethod
    def create(cls):
        """ Create model. """
        return modelcreator.create_model(modules=cls.modules,
                                         target_dir=cls.target_dir,
                                         annotations=cls.annotations)

if __name__ == "__main__":
    DemoFactory.create()
