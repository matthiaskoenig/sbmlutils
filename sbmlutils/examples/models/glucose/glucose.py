"""
Create model.
"""

from __future__ import print_function, division
import os
import sbmlutils.factory.Factory as Factory
models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class GlucoseFactory(Factory):
    """
    Implements the factory for the glucose model.
    """

    def __init__(self):
        """
        Create glucose factory with default settings.
        """
        super(GlucoseFactory, self).__init__(
            modules=['sbmlutils.examples.models.glucose.Cell'],
            target_dir = os.path.join(models_dir, 'results'),
            annotations = os.path.join(models_dir, 'glucose_annotations.xlsx')
        )

if __name__ == "__main__":
    GlucoseFactory().create()
