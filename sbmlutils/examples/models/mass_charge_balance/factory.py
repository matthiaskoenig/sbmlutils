import os
from sbmlutils.modelcreator.creator import Factory


def create(tmp=False):
    """ Create model.
    :return:
    """
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    print('-' * 80)
    print(models_dir)
    print('-' * 80)

    factory = Factory(modules=['sbmlutils.examples.models.mass_charge_balance.model'],
                      target_dir=os.path.join(models_dir, 'results'))
    factory.create(tmp)


if __name__ == "__main__":
    create()
