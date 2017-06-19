"""
Rename restricted sids in models.
"""
from __future__ import absolute_import, print_function, division
from six import iteritems
import libsbml
from sbmlutils import sbmlio
from sbmlutils.utils import timeit
from sbmlutils import validation

@timeit
def rename_restriced_sids(in_path, out_path,
                          restricted={"x": "x_", "y": "y_", "z": "z_", "t": "t_"}):
    """ Rename restriced sids from given dictionary.
    The new sids must not exist in the model!

    :param in_path: sbml in file
    :param out_path: sbml out file
    :param restricted: dictionary of replacements
    :return:
    """
    print('-' * 80)
    print('Renaming restricted ids')
    print('-' * 80)


    print('reading SBML')
    # doc = sbmlio.read_sbml(in_path)
    doc = libsbml.readSBMLFromFile(in_path)
    model = doc.getModel()

    for old_id, new_id in iteritems(restricted):
        element_x = model.getElementBySId(old_id)
        if element_x is not None:
            print("Renaming: ", old_id, '->', new_id)
            element_x.setId(new_id)

            elements = model.getListOfAllElements()
            N = len(elements)
            for k, element in enumerate(elements):
                if k % int(round(N/20)) == 0:
                    print("{:1.2f}".format(1.0*k/N))

                # element.renameSIdRefs(oldid="old_id", newid="new_id")
                element.renameSIdRefs(old_id, new_id)

    print('writing SBML')
    # libsbml.writeSBMLToFile(doc, out_path)
    sbmlio.write_sbml(doc, out_path, validate=validation.VALIDATION_NO_UNITS)


sbml_id = "MODEL1603150001"
in_path = "./{}.xml".format(sbml_id)
out_path = "./{}_fixed.xml".format(sbml_id)

rename_restriced_sids(in_path=in_path, out_path=out_path)



