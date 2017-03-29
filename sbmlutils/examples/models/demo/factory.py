"""
Create model.
"""

from __future__ import print_function, absolute_import

import os

from sbmlutils.modelcreator.creator import Factory

from .Cell import mid, version


def create(tmp=False):
    """ Create demo model.

    :return:
    """
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    print('-'*80)
    print(models_dir)
    print('-' * 80)

    factory = Factory(modules=['sbmlutils.examples.models.demo.Cell'],
                      target_dir=os.path.join(models_dir, 'results'),
                      annotations=os.path.join(models_dir, 'demo_annotations.xlsx'))
    factory.create(tmp)

    # without annotations
    factory_no_annotations = Factory(
        modules=['sbmlutils.examples.models.demo.Cell'],
        target_dir=os.path.join(models_dir, 'results'),
        mid="{}_{}_{}".format(mid, version, "no_annotations"))
    factory_no_annotations.create(tmp)


if __name__ == "__main__":
    create()
