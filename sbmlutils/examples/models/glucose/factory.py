"""
Create model.
"""

from __future__ import print_function, division
import os
from sbmlutils import modelcreator
from sbmlutils.modelcreator.modelcreator import Factory

models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class GlucoseFactory(Factory):
    """
    Implements the factory for the glucose model.
    """
    modules = ['sbmlutils.examples.models.glucose.Cell']
    target_dir = os.path.join(models_dir, 'results')
    annotations = os.path.join(models_dir, 'glucose_annotations.xlsx')

    @staticmethod
    def create():
        """ Create glucose network. """
        return modelcreator.create_model(modules=GlucoseFactory.modules,
                                         target_dir=GlucoseFactory.target_dir,
                                         annotations=GlucoseFactory.annotations)

if __name__ == "__main__":
    GlucoseFactory.create()
