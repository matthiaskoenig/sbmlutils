import os
from sbmlutils.modelcreator.creator import Factory


def create(tmp=False):
    """ Create demo model.

    :return:
    """
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    factory = Factory(modules=['sbmlutils.examples.models.fbc.fbc_ex1'],
                      target_dir=os.path.join(models_dir, 'results'))
    factory.create(tmp)

    factory = Factory(modules=['sbmlutils.examples.models.fbc.fbc_ex2'],
                      target_dir=os.path.join(models_dir, 'results'))
    factory.create(tmp)


if __name__ == "__main__":
    create()
