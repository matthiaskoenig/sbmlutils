"""
Script to create the tiny model SBML.
The memote report can be created via

    memote report snapshot --filename "report.html" path/to/model.xml
"""

import os
from sbmlutils.modelcreator.creator import Factory


def create(tmp=False):
    """ Create demo model.

    :return:
    """
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    print('-'*80)
    print(models_dir)
    print('-' * 80)

    factory = Factory(modules=['sbmlutils.examples.models.tiny_model.model'],
                      target_dir=os.path.join(models_dir, 'results'),
                      annotations=os.path.join(models_dir, 'annotations.xlsx'))
    factory.create(tmp)


if __name__ == "__main__":
    create()
