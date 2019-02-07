"""
Create model.
"""
import os
import libsbml
from sbmlutils.modelcreator.creator import Factory
from sbmlutils.examples.models.tiny_model import model

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

    tiny_sbml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'results',
                         '{}_{}.xml'.format(model.mid, model.version))

    doc = libsbml.readSBMLFromFile(tiny_sbml)
    model = doc.getModel()  # type: libsbml.Model
    model.



if __name__ == "__main__":
    create()
