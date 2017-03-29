from __future__ import print_function
import libsbml
import warnings


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
    # FIXME: handle /multiple levels of hierarchies recursively (ExternalModelDefinitions of submodels)

    model = doc.getModel()
    if model is None:
        return doc

    comp_doc = doc.getPlugin("comp")
    emd_list = comp_doc.getListOfExternalModelDefinitions()

    # no ExternalModelDefinitions
    if (emd_list is None) or (len(emd_list) == 0):
        return doc

    # ExternalModelDefinitions set as ModelDefinitions
    emd_ids = []
    mds = []
    for emd in emd_list:
        emd_ids.append(emd.getId())

        # get the model definition from the model
        ref_model = emd.getReferencedModel()

        # store model definition
        md = libsbml.ModelDefinition(ref_model)
        mds.append(md)

    packages = []
    for emd in emd_list:
        # get the model definition from the model
        ref_model = emd.getReferencedModel()
        ref_doc = ref_model.getSBMLDocument()
        # print('\n', ref_model)
        for k in range(ref_doc.getNumPlugins()):

            plugin = ref_doc.getPlugin(k)
            uri = plugin.getURI()
            prefix = plugin.getPrefix()
            name = plugin.getPackageName()
            required = None
            if ref_doc.isSetPackageRequired(name):
                required = ref_doc.getPackageRequired(name)

            packages.append({
                'model': ref_model,
                'uri': uri,
                'prefix': prefix,
                'name': name,
                'required': required
            })

    # remove emds from model (do not remove while iterating over the list)
    for emd_id in emd_ids:
        comp_doc.removeExternalModelDefinition(emd_id)

    # activate all the packages
    from pprint import pprint
    pprint(packages)
    for pdict in packages:
        doc.enablePackage(pdict['uri'], pdict['prefix'], True)
        doc.setPackageRequired(pdict['name'], pdict['required'])

    # now add the model definitions
    for md in mds:
        comp_doc.addModelDefinition(md)

    sbml_str = libsbml.writeSBMLToString(doc)
    doc = libsbml.readSBMLFromString(sbml_str)

    # replacement finished, now go through all ModelDefinitions
    # and add things the packages require
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
                # for some ModelDefinitions we don't get the fbc Plugin ???
                fbc_model = md_model.getPlugin(name)

                print('\tModel:', md_model)
                print('\tFBCModelPlugin:', fbc_model, type(fbc_model))

                # setting because it is required (if unlucky additional info required)
                # but we can't set it because we can't access the FBCModelPlugins of the ModelDefinitions
                if fbc_model is not None:
                    if not fbc_model.isSetStrict():
                        fbc_model.setStrict(False)
                else:
                    print("WARNING: This should never happen. All ModelDefinitions should have a FBCModelPlugin")

    doc.checkInternalConsistency()
    doc.printErrors()

    return doc


if __name__ == "__main__":
    import libsbml
    from os.path import join as pjoin

    directory = './emd_files/'
    top_file = pjoin(directory, 'diauxic_top.xml')

    # replace the ExternalModelDefinitions with ModelDefinitions
    doc_top = libsbml.readSBMLFromFile(top_file)
    doc_no_emd = flattenExternalModelDefinitions(doc_top)

    # write to file
    libsbml.writeSBMLToFile(doc_no_emd, pjoin(directory, 'test_emd_flat.xml'))
    print(libsbml.__version__)


