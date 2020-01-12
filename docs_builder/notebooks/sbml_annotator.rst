SBML annotator
==============

``sbmlutils`` provides functionality for annotating SBML models.
Annotation is the process of adding metadata to the model and model
components. These metadata are mostly from biological ontologies or
biological databases.

.. code:: ipython3

    from sbmlutils.report import sbmlreport

Annotate existing model
~~~~~~~~~~~~~~~~~~~~~~~

In the first example annotations from an excel file are added to an
existing model. The following annotations are written to the
`./annotations/demo.xml <./annotations/demo.xml>`__ based on pattern
matching.

Annotations are written for the given ``sbml_type`` for all SBML
identifiers which match the given pattern.

.. code:: ipython3

    from sbmlutils.annotation.annotator import ModelAnnotator
    df = ModelAnnotator.read_annotations_df("./annotations/demo_annotations.xlsx", format="xlsx")
    df




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>pattern</th>
          <th>sbml_type</th>
          <th>annotation_type</th>
          <th>qualifier</th>
          <th>resource</th>
          <th>name</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>NaN</td>
          <td>document</td>
          <td>rdf</td>
          <td>BQM_IS</td>
          <td>sbo/SBO:0000293</td>
          <td>non-spatial continuous framework</td>
        </tr>
        <tr>
          <th>1</th>
          <td>^demo_\d+$</td>
          <td>model</td>
          <td>rdf</td>
          <td>BQM_IS</td>
          <td>go/GO:0008152</td>
          <td>metabolic process</td>
        </tr>
        <tr>
          <th>3</th>
          <td>e</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000290</td>
          <td>physical compartment</td>
        </tr>
        <tr>
          <th>4</th>
          <td>e</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>go/GO:0005615</td>
          <td>extracellular space</td>
        </tr>
        <tr>
          <th>5</th>
          <td>e</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>fma/FMA:70022</td>
          <td>extracellular space</td>
        </tr>
        <tr>
          <th>7</th>
          <td>m</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000290</td>
          <td>physical compartment</td>
        </tr>
        <tr>
          <th>8</th>
          <td>m</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>go/GO:0005886</td>
          <td>plasma membrane</td>
        </tr>
        <tr>
          <th>9</th>
          <td>m</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>fma/FMA:63841</td>
          <td>plasma membrane</td>
        </tr>
        <tr>
          <th>11</th>
          <td>c</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000290</td>
          <td>physical compartment</td>
        </tr>
        <tr>
          <th>12</th>
          <td>c</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>go/GO:0005623</td>
          <td>cell</td>
        </tr>
        <tr>
          <th>13</th>
          <td>c</td>
          <td>compartment</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>fma/FMA:68646</td>
          <td>cell</td>
        </tr>
        <tr>
          <th>15</th>
          <td>^Km_\w+$</td>
          <td>parameter</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000027</td>
          <td>Michaelis constant</td>
        </tr>
        <tr>
          <th>16</th>
          <td>^Keq_\w+$</td>
          <td>parameter</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000281</td>
          <td>equilibrium constant</td>
        </tr>
        <tr>
          <th>17</th>
          <td>^Vmax_\w+$</td>
          <td>parameter</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000186</td>
          <td>maximal velocity</td>
        </tr>
        <tr>
          <th>19</th>
          <td>^\w{1}__A$</td>
          <td>species</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000247</td>
          <td>simple chemical</td>
        </tr>
        <tr>
          <th>20</th>
          <td>^\w{1}__B$</td>
          <td>species</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000247</td>
          <td>simple chemical</td>
        </tr>
        <tr>
          <th>21</th>
          <td>^\w{1}__C$</td>
          <td>species</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000247</td>
          <td>simple chemical</td>
        </tr>
        <tr>
          <th>22</th>
          <td>^\w{1}__\w+$</td>
          <td>species</td>
          <td>formula</td>
          <td>NaN</td>
          <td>C6H12O6</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>23</th>
          <td>^\w{1}__\w+$</td>
          <td>species</td>
          <td>charge</td>
          <td>NaN</td>
          <td>0</td>
          <td>NaN</td>
        </tr>
        <tr>
          <th>24</th>
          <td>^b\w{1}$</td>
          <td>reaction</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000185</td>
          <td>transport reaction</td>
        </tr>
        <tr>
          <th>25</th>
          <td>^v\w{1}$</td>
          <td>reaction</td>
          <td>rdf</td>
          <td>BQB_IS</td>
          <td>sbo/SBO:0000176</td>
          <td>biochemical reaction</td>
        </tr>
      </tbody>
    </table>
    </div>



.. code:: ipython3

    from sbmlutils.annotation.annotator import annotate_sbml_file
    
    # create SBML report without performing units checks
    annotate_sbml_file(f_sbml="./annotations/demo.xml", 
                       f_annotations="./annotations/demo_annotations.xlsx", 
                       f_sbml_annotated="./annotations/demo_annotated.xml")

Annotate during model creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the second example the model is annotated during the model creation
process. Annotations are encoded as simple tuples consisting of MIRIAM
identifiers terms and identifiers.org parts.

The list of tuples can be provided on object generation

::

        Species(sid='e__gal', compartment='ext', initialConcentration=3.0,
                    substanceUnit=UNIT_KIND_MOLE, boundaryCondition=True,
                    name='D-galactose', sboTerm=SBO_SIMPLE_CHEMICAL,
                    annotations=[
                        (BQB.IS, "bigg.metabolite/gal"),  # galactose
                        (BQB.IS, "chebi/CHEBI:28061"),  # alpha-D-galactose
                        (BQB.IS, "vmhmetabolite/gal"),
                    ]
                ),

For the full example see
`model\_with\_annotations.py <./model_with_annotations.py>`__

.. code:: ipython3

    import os
    from sbmlutils.modelcreator.creator import Factory
    factory = Factory(modules=['model_with_annotations'],
                      target_dir='./models')
    [_, _, sbml_path] = factory.create()
    
    # check the annotations on the species
    import libsbml
    doc = libsbml.readSBMLFromFile(sbml_path)  # type: libsbml.SBMLDocument
    model = doc.getModel()  # type: libsbml.Model
    s1 = model.getSpecies('e__gal')  # type: libsbml.Species
    print(s1.toSBML())


.. parsed-literal::

    WARNING:sbmlutils.annotation.annotator:https://en.wikipedia.org/wiki/Cytosol does not conform to http(s)://identifiers.org/collection/id


.. parsed-literal::

    [1m[92m
    --------------------------------------------------------------------------------
    /home/mkoenig/git/sbmlutils/docs_builder/notebooks/models/annotation_example_8.xml
    valid                    : TRUE
    check time (s)           : 0.016
    --------------------------------------------------------------------------------
    [0m[0m
    SBML report created: ./models/annotation_example_8.html
    <species metaid="meta_e__gal" sboTerm="SBO:0000247" id="e__gal" name="D-galactose" compartment="ext" initialConcentration="3" substanceUnits="mole" hasOnlySubstanceUnits="false" boundaryCondition="true" constant="false">
      <annotation>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:vCard="http://www.w3.org/2001/vcard-rdf/3.0#" xmlns:vCard4="http://www.w3.org/2006/vcard/ns#" xmlns:bqbiol="http://biomodels.net/biology-qualifiers/" xmlns:bqmodel="http://biomodels.net/model-qualifiers/">
          <rdf:Description rdf:about="#meta_e__gal">
            <bqbiol:is>
              <rdf:Bag>
                <rdf:li rdf:resource="https://identifiers.org/bigg.metabolite/gal"/>
                <rdf:li rdf:resource="https://identifiers.org/chebi/CHEBI:28061"/>
                <rdf:li rdf:resource="https://identifiers.org/vmhmetabolite/gal"/>
              </rdf:Bag>
            </bqbiol:is>
          </rdf:Description>
        </rdf:RDF>
      </annotation>
    </species>

