SBML annotation
===============

Annotation of model components with meta-information is an important
step during model building. Annotation is the process of adding metadata
to the model and model components. These metadata are mostly from
biological ontologies or biological databases.

``sbmlutils`` provides functionality for annotating SBML models which
can be used during model creation or later on to add annotations to SBML
models. Annotations have the form of RDF triples consisting of the model
component to annotate (subject), the relationship between model
component and annotation term (predicate), and a term which describes
the meaning of the component (object), which often comes from an
ontology of defined terms.

The predicates come from a clearly defined set of predicates, the MIRIAM
qualifiers (https://co.mbine.org/standards/qualifiers). Ideally the
objects, i.e. annotations, are defined in an ontology which is
registered at https://identifiers.org (see
https://registry.identifiers.org/registry for available resources).

For more information of the importance of model annotations and best
practises we refer to

   Neal, M.L., König, M., Nickerson, D., Mısırlı, G., Kalbasi, R.,
   Dräger, A., Atalag, K., Chelliah, V., Cooling, M.T., Cook, D.L. and
   Crook, S., 2019. Harmonizing semantic annotations for computational
   models in biology. Briefings in bioinformatics, 20(2), pp.540-550.
   `10.1093/bib/bby087 <https://doi.org/10.1093/bib/bby087>`__

..

   Le Novère, N., Finney, A., Hucka, M., Bhalla, U.S., Campagne, F.,
   Collado-Vides, J., Crampin, E.J., Halstead, M., Klipp, E., Mendes, P.
   and Nielsen, P., 2005. Minimum information requested in the
   annotation of biochemical models (MIRIAM). Nature biotechnology,
   23(12), pp.1509-1515. https://www.nature.com/articles/nbt1156

Annotations in ``sbmlutils`` consist of associating
``(predictate, object)`` tuples to model components. For instance to
describe that a ``species`` in the model is a certain entry from CHEBI,
we associate ``(BQB.IS, "chebi/CHEBI:28061")`` with the species. In
addition the special subset of annotations to the Systems Biology
Ontology (SBO) can be directly set on all model components via the
``sboTerm`` attribute.

.. code:: ipython3

    %load_ext autoreload
    %autoreload 2

Annotate during model creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the example the model is annotated during the model creation process.
Annotations are encoded as simple tuples consisting of MIRIAM
identifiers terms and identifiers.org parts. The list of tuples is
provided on object creation. In the example we annotate a ``species``

.. code:: ipython3

    from sbmlutils.units import *
    from sbmlutils.factory import *
    from sbmlutils.metadata import *
    from sbmlutils.modelcreator.creator import CoreModel
    from sbmlutils.validation import validate_doc
    
    model_dict = {
        'mid': 'example_annotation',
        'compartments': [
            Compartment(sid="C", value=1.0, sboTerm=SBO_PHYSICAL_COMPARTMENT)
        ],
        'species': [
            Species(sid='gal', compartment='C', initialConcentration=3.0,
                    name='D-galactose', sboTerm=SBO_SIMPLE_CHEMICAL,
                    annotations=[
                        (BQB.IS, "bigg.metabolite/gal"),  # galactose
                        (BQB.IS, "chebi/CHEBI:28061"),  # alpha-D-galactose
                        (BQB.IS, "vmhmetabolite/gal"),
                    ]
            )
        ]
    }
    
    # create model and print SBML
    core_model = CoreModel.from_dict(model_dict=model_dict)
    print(core_model.get_sbml())
    
    # validate model
    validate_doc(core_model.doc, units_consistency=False);


::


    ---------------------------------------------------------------------------

    ModuleNotFoundError                       Traceback (most recent call last)

    <ipython-input-1-1dda9dce9ed9> in <module>
          2 from sbmlutils.factory import *
          3 from sbmlutils.metadata import *
    ----> 4 from sbmlutils.modelcreator.creator import CoreModel
          5 from sbmlutils.validation import validate_doc
          6 


    ModuleNotFoundError: No module named 'sbmlutils.modelcreator'


For a more complete example see
`model_with_annotations.py <./model_with_annotations.py>`__ which
creates annotations of the form

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

.. code:: ipython3

    from notebook import BASE_DIR
    from sbmlutils.modelcreator.creator import Factory
    from sbmlutils.io import read_sbml
    
    factory = Factory(modules=['model_with_annotations'],
                      output_dir=BASE_DIR / 'models')
    [_, _, sbml_path] = factory.create()
    
    # check the annotations on the species
    import libsbml
    doc = read_sbml(sbml_path)  # type: libsbml.SBMLDocument
    model = doc.getModel()  # type: libsbml.Model
    s1 = model.getSpecies('e__gal')  # type: libsbml.Species
    print(s1.toSBML())


::


    ---------------------------------------------------------------------------

    ModuleNotFoundError                       Traceback (most recent call last)

    <ipython-input-1-9501dacbb6c7> in <module>
          1 from notebook import BASE_DIR
    ----> 2 from sbmlutils.modelcreator.creator import Factory
          3 from sbmlutils.io import read_sbml
          4 
          5 factory = Factory(modules=['model_with_annotations'],


    ModuleNotFoundError: No module named 'sbmlutils.modelcreator'


Annotate existing model
~~~~~~~~~~~~~~~~~~~~~~~

An alternative approach is to annotate existing models from external
annotation files. For instance we can define the annotations in an
external file which we then add to the model based on identifier
matching. The following annotations are written to the
`./annotations/demo.xml <./annotations/demo.xml>`__ based on pattern
matching.

Annotations are written for the given ``sbml_type`` for all SBML
identifiers which match the given pattern.

.. code:: ipython3

    from sbmlutils.metadata.annotator import ModelAnnotator
    df = ModelAnnotator.read_annotations_df(BASE_DIR / 'annotations' / 'demo_annotations.xlsx', file_format="xlsx")
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

    from sbmlutils.metadata.annotator import annotate_sbml
    
    # create SBML report without performing units checks
    doc = annotate_sbml(
        source=BASE_DIR / 'annotations' / 'demo.xml', 
        annotations_path=BASE_DIR / 'annotations' / 'demo_annotations.xlsx', 
        filepath=BASE_DIR / 'annotations' / 'demo_annotated.xml'
    )
    print(doc.getModel())


.. parsed-literal::

    <Model Koenig_demo_14 "Koenig_demo_14">


