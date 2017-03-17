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
            print(ref_model)
            for k in range(ref_doc.getNumPlugins()):
                plugin = ref_doc.getPlugin(k)

                # enable the package on the main SBMLDocument
                uri = plugin.getURI()
                prefix = plugin.getPrefix()
                name = plugin.getPackageName()
                doc.enablePackage(uri, prefix, True)

                print(k, plugin)
                print(uri, prefix)

                '''
                # set the respective required tag (check if already required=True,
                # to avoid True -> False by later submodels)
                ref_required = None
                if ref_doc.isSetPackageRequired(name):
                    ref_required = ref_doc.getPackageRequired(name)
                    print('required: ', name, ref_required)

                # there is info about requirement
                if ref_required is not None:
                    if doc.isSetPackageRequired(name):
                        required = doc.getPackageRequired(name)
                        print('doc', name, required)
                        # is not required yet, just set the value
                        if not required:
                            doc.setPackageRequired(name, ref_required)
                            print('set required: ', name, ref_required)
                    else:
                        # nothing set yet, just set the value
                        doc.setPackageRequired(name, ref_required)
                        print('set required: ', name, ref_required)
                '''

                # set required attributes for models, i.e. strict for fbc
                if name == "fbc":
                    print("find fbc strict")
                    fbc_ref_model = ref_model.getPlugin(name)
                    ref_strict = fbc_ref_model.getStrict()
                    fbc_model = model.getPlugin(name)
                    print(model)
                    print(fbc_model)

                    fbc_model.setStrict(False)

                    """
                    if fbc_model.isSetStrict():
                        if not fbc_model.getStrict():
                            # only set if strict=False, to avoid True -> False by later submodels
                            fbc_model.setStrict(ref_strict)
                            print('set strict: ', name, ref_strict)
                    else:
                        fbc_model.setStrict(ref_strict)
                        print('set strict: ', name, ref_strict)
                    """
                else:
                    print("no fbc model", name)


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
    doc_flat = flattenExternalModelDefinitions(doc_top)
    from sbmlutils import sbmlio
    sbmlio.write_sbml(doc_flat, pjoin(directory, 'test_emd_flat.xml'))


