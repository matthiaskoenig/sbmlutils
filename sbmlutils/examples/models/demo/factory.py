"""
Create model.
"""
import os
from sbmlutils.modelcreator.creator import Factory
from sbmlutils.examples.models.demo import model


def create(tmp=False):
    """ Create demo model.

    :return:
    """
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    print('-'*80)
    print(models_dir)
    print('-' * 80)

    factory = Factory(modules=['sbmlutils.examples.models.demo.model'],
                      target_dir=os.path.join(models_dir, 'results'),
                      annotations=os.path.join(models_dir, 'demo_annotations.xlsx'))
    factory.create(tmp)

    # without annotations
    factory_no_annotations = Factory(
        modules=['sbmlutils.examples.models.demo.model'],
        target_dir=os.path.join(models_dir, 'results'),
        mid="{}_{}_{}".format(model.mid, model.version, "no_annotations"))
    factory_no_annotations.create(tmp)


if __name__ == "__main__":
    create()
