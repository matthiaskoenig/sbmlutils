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
    # FIXME: handle /multiple levels of hierarchies. This must be done
    # recursively to handle the ExternalModelDefinitions of submodels

    model = doc.getModel()
    if model is None:
        return doc

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
            print('\n', ref_model)
            for k in range(ref_doc.getNumPlugins()):

                plugin = ref_doc.getPlugin(k)

                # enable the package on the main SBMLDocument
                uri = plugin.getURI()
                prefix = plugin.getPrefix()
                name = plugin.getPackageName()
                doc.enablePackage(uri, prefix, True)
                print(name, plugin)

                # set the respective required tag (check if already required=True,
                # to avoid True -> False by later submodels)
                ref_required = None
                if ref_doc.isSetPackageRequired(name):
                    ref_required = ref_doc.getPackageRequired(name)
                    # print('required: ', name, ref_required)

                # FIXME: overwrite, assuming for not that the required is always identical for the packages
                doc.setPackageRequired(name, ref_required)
                print("set required: {} = {}".format(name, ref_required))

            # add model definition for model
            md = libsbml.ModelDefinition(ref_model)
            comp_doc.addModelDefinition(md)

        # remove the emds afterwards (do not remove while iterating over the list)
        for emd_id in emd_ids:
            # remove the emd from the model
            comp_doc.removeExternalModelDefinition(emd_id)

        # the replacement is done, but now we have to go through all ModelDefinitions
        # and add package requirements in model definition :/
        print("-"*80)
        for k in range(doc.getNumPlugins()):
            plugin = doc.getPlugin(k)
            name = plugin.getPackageName()
            print(name, '\n')
            md_list = comp_doc.getListOfModelDefinitions()
            for md_model in md_list:

                # if a package needs something on
                # a model we have to write it on all ModelDefinitions
                # this will break on a package per package basis ! We know about fbc it needs
                # a strict tag so writing this here
                if name == "fbc":
                    fbc_model = md_model.getPlugin(name)
                    print('\tModel:', md_model)
                    print('\tFBCModelPlugin:', fbc_model, type(fbc_model))

                    # setting because it is required (if unlucky additional info required)
                    # but we can't set it because we can't access the FBCModelPlugins of the ModelDefinitions
                    if fbc_model is not None:
                        if not fbc_model.isSetStrict():
                            fbc_model.setStrict(False)


    doc.checkInternalConsistency()
    doc.printErrors()

    return doc


if __name__ == "__main__":
    from os.path import join as pjoin

    directory = './emd_files/'
    top_file = pjoin(directory, 'diauxic_top.xml')

    # replace the ExternalModelDefinitions with ModelDefinitions
    doc_top = libsbml.readSBMLFromFile(top_file)
    doc_flat = flattenExternalModelDefinitions(doc_top)
    from sbmlutils import sbmlio
    sbmlio.write_sbml(doc_flat, pjoin(directory, 'test_emd_flat.xml'))


