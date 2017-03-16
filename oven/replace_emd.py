from __future__ import print_function
import libsbml


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

            # --------------------------------------
            ref_doc = ref_model.getSBMLDocument()
            print(ref_model)
            for k in range(ref_doc.getNumPlugins()):
                plugin = doc.getPlugin(k)
                print(k, plugin)

                uri = plugin.getURI()
                prefix = plugin.getPrefix()
                doc.enablePackage(uri, prefix, True)

            print("\n")
            # --------------------------------------

            # add model definition for model
            md = libsbml.ModelDefinition(ref_model)
            comp_doc.addModelDefinition(md)

        # remove the emds afterwards (do not remove while iterating over the list)
        for emd_id in emd_ids:
            # remove the emd from the model
            comp_doc.removeExternalModelDefinition(emd_id)

    doc.checkInternalConsistency()
    doc.printErrors()

    return doc


if __name__ == "__main__":
    from os.path import join as pjoin

    directory = './emd_files/'
    top_file = pjoin(directory, 'diauxic_top.xml')

    # replace the ExternalModelDefinitions with ModelDefinitions
    doc_top = libsbml.readSBMLFromFile(top_file)
    flattenExternalModelDefinitions(doc_top)

