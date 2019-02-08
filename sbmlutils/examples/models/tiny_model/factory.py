"""
Create model.
"""
import os
import libsbml
from sbmlutils.modelcreator.creator import Factory



# TODO: add event
# TODO: add a constraint

# TODO: add a group
# TODO: add a layout


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
    # factory = Factory(modules=['sbmlutils.examples.models.tiny_model.model2'],
    #                  target_dir=os.path.join(models_dir, 'results'))
    factory.create(tmp)



if __name__ == "__main__":
    create()
