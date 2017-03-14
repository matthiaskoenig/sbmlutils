import time
import libsbml

def check_doc(doc, name=None):
    """
        Checks the given SBML document and prints errors of the given severity.

        Individual checks can be changed via the categories
            doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, False)
            doc.setConsistencyChecks(libsbml.LIBSBML_CAT_MODELING_PRACTICE, False)

        :param sbml: SBML file or str
        :type sbml: file | str
        :return: number of errors
        """
    if name is None:
        name = str(doc)

    current = time.clock()
    doc.checkConsistency()
    Nerrors = doc.getNumErrors()

    print('-' * 80)
    print(name)
    print("read time (ms): " + str(time.clock() - current))
    print("validation error(s): " + str(Nerrors))
    print('-' * 80)

    doc.printErrors()
    return Nerrors


def flattenExternalModelDefinitions(doc):
    """ Converts all ExternalModelDefinitions to ModelDefinitions.

    I.e. the definition of models in external files are read
    and directly included in the top model. The resulting
    comp model consists than only of a single file.

    The model refs in the submodel do not change in the process,
    so no need to update the submodels.

    :param doc: SBMLDocument
    :return: SBMLDocument with ExternalModelDefinitions replaced
    """
    # FIXME: handle multiple levels of hierarchies. This must be done
    # recursively to handle the ExternalModelDefinitions of submodels

    comp_doc = doc.getPlugin("comp")
    emd_list = comp_doc.getListOfExternalModelDefinitions()
    if (emd_list is None) or (len(emd_list) == 0):
        # no ExternalModelDefinitions
        return doc
    else:
        emd_ids = []
        for emd in emd_list:
            emd_ids.append(emd.getId())

            # get the model definition from the model
            ref_model = emd.getReferencedModel()

            # add model definition for model
            md = libsbml.ModelDefinition(ref_model)
            comp_doc.addModelDefinition(md)

        # remove the emds afterwards (do not remove while iterating over the list)
        for emd_id in emd_ids:
            # remove the emd from the model
            comp_doc.removeExternalModelDefinition(emd_id)

    return doc

if __name__ == "__main__":

    from os.path import join as pjoin
    directory = './emd_files/'

    top_file = pjoin(directory, 'diauxic_top.xml')
    top_noemd_file = pjoin(directory, 'diauxic_top_noemd.xml')

    # file is valid with emds
    doc_top = libsbml.readSBMLFromFile(top_file)
    check_doc(doc_top, name="doc_top")

    # replace the ExternalModelDefinitions with ModelDefinitions
    doc_top_noemd = flattenExternalModelDefinitions(doc_top)
    # still valid
    check_doc(doc_top_noemd, name="doc_top_noemd")

    # write the file & read the file, not valid
    # probably package information not written
    libsbml.writeSBMLToFile(doc_top_noemd, top_noemd_file)
    doc_top_noemd_read = libsbml.readSBMLFromFile(top_noemd_file)
    check_doc(doc_top_noemd_read, name="doc_top_noemd_read")

