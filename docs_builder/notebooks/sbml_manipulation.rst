SBML manipulation
=================

``sbmlutils`` provides functionality for manipulating existing models.
Examples are the merging of multiple SBML models in a combined model.

Model merging
-------------

Merge multiple models into a combined model using the ``comp`` package.

.. code:: ipython3

    import os
    import libsbml
    from pprint import pprint
    
    from sbmlutils import comp
    from sbmlutils import validation
    from sbmlutils import manipulation
    from sbmlutils.tests.data import data_dir
    
    merge_dir = os.path.join(data_dir, 'manipulation', 'merge')
    
    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = ["BIOMD000000000{}".format(k) for k in range(1, 5)]
    model_paths = dict(zip(model_ids,
                           [os.path.join(merge_dir, "{}.xml".format(mid)) for mid in model_ids])
                       )
    pprint(model_paths)
    
    # create merged model
    output_dir = os.path.join(merge_dir, 'output')
    doc = manipulation.merge_models(model_paths, out_dir=output_dir, validate=False)
    
    # validate
    Nall, Nerr, Nwarn = validation.check_doc(doc, units_consistency=False)
    assert Nerr == 0
    assert Nwarn == 0
    assert Nall == 0
    
    # write the merged model
    print(libsbml.writeSBMLToString(doc))
    libsbml.writeSBMLToFile(doc, os.path.join(output_dir, "merged.xml"))
    
    # flatten the merged model
    doc_flat = comp.flattenSBMLDocument(doc)
    Nall, Nerr, Nwarn = validation.check_doc(doc_flat, units_consistency=False)
    libsbml.writeSBMLToFile(doc_flat, os.path.join(output_dir, "merged_flat.xml"));


.. parsed-literal::

    {'BIOMD0000000001': '/home/mkoenig/git/sbmlutils/sbmlutils/tests/data/manipulation/merge/BIOMD0000000001.xml',
     'BIOMD0000000002': '/home/mkoenig/git/sbmlutils/sbmlutils/tests/data/manipulation/merge/BIOMD0000000002.xml',
     'BIOMD0000000003': '/home/mkoenig/git/sbmlutils/sbmlutils/tests/data/manipulation/merge/BIOMD0000000003.xml',
     'BIOMD0000000004': '/home/mkoenig/git/sbmlutils/sbmlutils/tests/data/manipulation/merge/BIOMD0000000004.xml'}
    [1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    check time (s)           : 0.031
    --------------------------------------------------------------------------------
    [0m[0m
    <?xml version="1.0" encoding="UTF-8"?>
    <sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" level="3" version="1" comp:required="true">
      <model id="merged">
        <comp:listOfSubmodels>
          <comp:submodel comp:id="BIOMD0000000001" comp:modelRef="BIOMD0000000001"/>
          <comp:submodel comp:id="BIOMD0000000002" comp:modelRef="BIOMD0000000002"/>
          <comp:submodel comp:id="BIOMD0000000003" comp:modelRef="BIOMD0000000003"/>
          <comp:submodel comp:id="BIOMD0000000004" comp:modelRef="BIOMD0000000004"/>
        </comp:listOfSubmodels>
      </model>
      <comp:listOfExternalModelDefinitions>
        <comp:externalModelDefinition comp:id="BIOMD0000000001" comp:name="BIOMD0000000001" comp:source="/home/mkoenig/git/sbmlutils/sbmlutils/tests/data/manipulation/merge/output/BIOMD0000000001_L3.xml" comp:modelRef="BIOMD0000000001"/>
        <comp:externalModelDefinition comp:id="BIOMD0000000002" comp:name="BIOMD0000000002" comp:source="/home/mkoenig/git/sbmlutils/sbmlutils/tests/data/manipulation/merge/output/BIOMD0000000002_L3.xml" comp:modelRef="BIOMD0000000002"/>
        <comp:externalModelDefinition comp:id="BIOMD0000000003" comp:name="BIOMD0000000003" comp:source="/home/mkoenig/git/sbmlutils/sbmlutils/tests/data/manipulation/merge/output/BIOMD0000000003_L3.xml" comp:modelRef="BIOMD0000000003"/>
        <comp:externalModelDefinition comp:id="BIOMD0000000004" comp:name="BIOMD0000000004" comp:source="/home/mkoenig/git/sbmlutils/sbmlutils/tests/data/manipulation/merge/output/BIOMD0000000004_L3.xml" comp:modelRef="BIOMD0000000004"/>
      </comp:listOfExternalModelDefinitions>
    </sbml>
    
    [1m[92m
    --------------------------------------------------------------------------------
    <SBMLDocument>
    valid                    : TRUE
    check time (s)           : 0.026
    --------------------------------------------------------------------------------
    [0m[0m


