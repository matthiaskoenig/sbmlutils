import os
from sbmlutils.modelcreator.creator import Factory
models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))


def create_distrib(tmp=False):
    """ Create demo model.

    :return:
    """
    factory = Factory(modules=['sbmlutils.examples.models.distrib.distrib_ex1'],
                      target_dir=os.path.join(models_dir, 'results'))
    factory.create(tmp)


def create_uncertainty(tmp=False):
    """ Create demo model.

    :return:
    """
    factory = Factory(modules=['sbmlutils.examples.models.distrib.uncertainty_ex1'],
                      target_dir=os.path.join(models_dir, 'results'))
    factory.create(tmp)


if __name__ == "__main__":
    create_distrib()
    create_uncertainty()
