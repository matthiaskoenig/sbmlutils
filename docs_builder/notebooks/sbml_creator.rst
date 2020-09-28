SBML creator
============

``sbmlutils`` provides helpers for the creation of SBML models from
scratch.

Create FBA Model
----------------

This example demonstrates the creation of an SBML FBA model from
scratch.

.. code:: ipython3

    from sbmlutils.io import write_sbml, validate_sbml
    from sbmlutils.modelcreator.creator import CoreModel
    
    from sbmlutils.factory import *
    from sbmlutils.units import *
    from sbmlutils.metadata import *
    from sbmlutils.metadata.sbo import *

Model building
~~~~~~~~~~~~~~

Creation of FBA model using multiple packages (``comp``, ``fbc``).

.. code:: ipython3

    UNIT_TIME = "s"
    UNIT_VOLUME = "m3"
    UNIT_LENGTH = "m"
    UNIT_AREA = "m2"
    UNIT_AMOUNT = "itm"
    UNIT_FLUX = "itm_per_s"
    
    model_dict = {
        'packages': ['fbc'],
        'mid': "example_model",
        'model_units': ModelUnits(
            time=UNIT_TIME,
            extent=UNIT_AMOUNT,
            substance=UNIT_AMOUNT,
            length=UNIT_LENGTH,
            area=UNIT_VOLUME,
            volume=UNIT_AREA,
        ),
        'units': {
            # using predefined units
            UNIT_s, UNIT_kg, UNIT_m, UNIT_m2, UNIT_m3,
            UNIT_mM, UNIT_per_s,
            # defining some additional units
            Unit('itm', [(UNIT_KIND_ITEM, 1.0)]),
            Unit('itm_per_s', [(UNIT_KIND_ITEM, 1.0),
                               (UNIT_KIND_SECOND, -1.0)]),
            Unit('itm_per_m3', [(UNIT_KIND_ITEM, 1.0),
                                (UNIT_KIND_METRE, -3.0)]),
        },
        'compartments': [
            Compartment(
                sid='extern', name='external compartment', value=1.0, unit=UNIT_VOLUME, 
                constant=True, spatialDimensions=3
            ),
            Compartment(
                sid='cell', name='cell', value=1.0, unit=UNIT_VOLUME, 
                constant=True, spatialDimensions=3
            ),
            Compartment(
                sid='membrane', name='membrane', value=1.0, unit=UNIT_AREA, 
                constant=True, spatialDimensions=2
            ),
        ],
        'species': [
            # exchange species
            Species(
                sid='A', name="A", initialAmount=0, substanceUnit=UNIT_AMOUNT, 
                hasOnlySubstanceUnits=True, compartment="extern", 
                sboTerm=SBO_SIMPLE_CHEMICAL
            ),
            Species(
                sid='C', name="C", initialAmount=0, substanceUnit=UNIT_AMOUNT, 
                hasOnlySubstanceUnits=True, compartment="extern", 
                sboTerm=SBO_SIMPLE_CHEMICAL
            ),
    
            # internal species
            Species(
                sid='B1', name="B1", initialAmount=0, substanceUnit=UNIT_AMOUNT, 
                hasOnlySubstanceUnits=True, compartment="cell", 
                sboTerm=SBO_SIMPLE_CHEMICAL
            ),
            Species(
                sid='B2', name="B2", initialAmount=0, substanceUnit=UNIT_AMOUNT, 
                hasOnlySubstanceUnits=True, compartment="cell", 
                sboTerm=SBO_SIMPLE_CHEMICAL
            ),
        ],
        'parameters': [
            Parameter(sid="ub_R1", value=1.0, unit=UNIT_FLUX, 
                      constant=True, sboTerm=SBO_FLUX_BOUND),
            Parameter(sid="zero", value=0.0, unit=UNIT_FLUX, 
                      constant=True, sboTerm=SBO_FLUX_BOUND),
            Parameter(sid="ub_default", value=1000, unit=UNIT_FLUX, 
                      constant=True, sboTerm=SBO_FLUX_BOUND),
        ],
        'reactions': [
            # metabolic reactions
            Reaction(
                sid="R1", name="A import (R1)",
                equation="A <-> B1",
                fast=False, reversible=True,
                compartment='membrane',
                lowerFluxBound="zero", upperFluxBound="ub_R1"
            ),
            Reaction(
                sid="R2", name="B1 <-> B2 (R2)",
                equation="B1 <-> B2",
                fast=False, reversible=True,
                compartment='cell',
                lowerFluxBound="zero", upperFluxBound="ub_default",
            ),
            Reaction(
                sid="R3", name="B2 export (R3)",
                equation="B1 <-> C",
                fast=False, reversible=True,
                compartment='membrane',
                lowerFluxBound="zero", upperFluxBound="ub_default"
            ),
            # exchange reactions
            ExchangeReaction(species_id="A"),
            ExchangeReaction(species_id="B1"),
        ],
        'objectives': [
            Objective(sid="R3_maximize", objectiveType="maximize",
                      fluxObjectives={"R3": 1.0}, active=True)
        ]
    }
    
    # create SBMLDocument
    core_model = CoreModel.from_dict(model_dict)
    doc = core_model.create_sbml()
    
    # write SBML file
    sbml_str = write_sbml(doc=doc, validate=True)


.. parsed-literal::

    [1m[92m
    --------------------------------------------------------------------------------
    <?xml version="1.0" encoding="UTF-8"?>
    <!-- Created by sbmlutils version 0.4.0 on 2020-09-27 23:55 with libSBML version 5.18.1. -->
    <sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version2" level="3" version="1" comp:required="true" fbc:required="false">
      <model metaid="meta_example_model" id="example_model" name="example_model" substanceUnits="itm" timeUnits="s" volumeUnits="m2" areaUnits="m3" lengthUnits="m" extentUnits="itm" fbc:strict="false">
        <listOfUnitDefinitions>
          <unitDefinition id="itm_per_m3">
            <listOfUnits>
              <unit kind="item" exponent="1" scale="0" multiplier="1"/>
              <unit kind="metre" exponent="-3" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="m2">
            <listOfUnits>
              <unit kind="metre" exponent="2" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="m">
            <listOfUnits>
              <unit kind="metre" exponent="1" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="s">
            <listOfUnits>
              <unit kind="second" exponent="1" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="m3">
            <listOfUnits>
              <unit kind="metre" exponent="3" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="itm">
            <listOfUnits>
              <unit kind="item" exponent="1" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="mM">
            <listOfUnits>
              <unit kind="mole" exponent="1" scale="-3" multiplier="1"/>
              <unit kind="litre" exponent="-1" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="kg">
            <listOfUnits>
              <unit kind="kilogram" exponent="1" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="per_s">
            <listOfUnits>
              <unit kind="second" exponent="-1" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
          <unitDefinition id="itm_per_s">
            <listOfUnits>
              <unit kind="item" exponent="1" scale="0" multiplier="1"/>
              <unit kind="second" exponent="-1" scale="0" multiplier="1"/>
            </listOfUnits>
          </unitDefinition>
        </listOfUnitDefinitions>
        <listOfCompartments>
          <compartment id="extern" name="external compartment" spatialDimensions="3" size="1" units="m3" constant="true"/>
          <compartment id="cell" name="cell" spatialDimensions="3" size="1" units="m3" constant="true"/>
          <compartment id="membrane" name="membrane" spatialDimensions="2" size="1" units="m2" constant="true"/>
        </listOfCompartments>
        <listOfSpecies>
          <species sboTerm="SBO:0000247" id="A" name="A" compartment="extern" initialAmount="0" substanceUnits="itm" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
          <species sboTerm="SBO:0000247" id="C" name="C" compartment="extern" initialAmount="0" substanceUnits="itm" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
          <species sboTerm="SBO:0000247" id="B1" name="B1" compartment="cell" initialAmount="0" substanceUnits="itm" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
          <species sboTerm="SBO:0000247" id="B2" name="B2" compartment="cell" initialAmount="0" substanceUnits="itm" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
        </listOfSpecies>
        <listOfParameters>
          <parameter sboTerm="SBO:0000612" id="ub_R1" value="1" units="itm_per_s" constant="true"/>
          <parameter sboTerm="SBO:0000612" id="zero" value="0" units="itm_per_s" constant="true"/>
          <parameter sboTerm="SBO:0000612" id="ub_default" value="1000" units="itm_per_s" constant="true"/>
        </listOfParameters>
        <listOfReactions>
          <reaction id="R1" name="A import (R1)" reversible="true" fast="false" compartment="membrane" fbc:lowerFluxBound="zero" fbc:upperFluxBound="ub_R1">
            <listOfReactants>
              <speciesReference species="A" stoichiometry="1" constant="true"/>
            </listOfReactants>
            <listOfProducts>
              <speciesReference species="B1" stoichiometry="1" constant="true"/>
            </listOfProducts>
          </reaction>
          <reaction id="R2" name="B1 &lt;-&gt; B2 (R2)" reversible="true" fast="false" compartment="cell" fbc:lowerFluxBound="zero" fbc:upperFluxBound="ub_default">
            <listOfReactants>
              <speciesReference species="B1" stoichiometry="1" constant="true"/>
            </listOfReactants>
            <listOfProducts>
              <speciesReference species="B2" stoichiometry="1" constant="true"/>
            </listOfProducts>
          </reaction>
          <reaction id="R3" name="B2 export (R3)" reversible="true" fast="false" compartment="membrane" fbc:lowerFluxBound="zero" fbc:upperFluxBound="ub_default">
            <listOfReactants>
              <speciesReference species="B1" stoichiometry="1" constant="true"/>
            </listOfReactants>
            <listOfProducts>
              <speciesReference species="C" stoichiometry="1" constant="true"/>
            </listOfProducts>
          </reaction>
          <reaction sboTerm="SBO:0000627" id="EX_A" reversible="false" fast="false">
            <listOfReactants>
              <speciesReference species="A" stoichiometry="1" constant="true"/>
            </listOfReactants>
          </reaction>
          <reaction sboTerm="SBO:0000627" id="EX_B1" reversible="false" fast="false">
            <listOfReactants>
              <speciesReference species="B1" stoichiometry="1" constant="true"/>
            </listOfReactants>
          </reaction>
        </listOfReactions>
        <comp:listOfPorts>
          <comp:port metaid="m2_port" sboTerm="SBO:0000599" comp:unitRef="m2" comp:id="m2_port" comp:name="m2_port"/>
          <comp:port metaid="m_port" sboTerm="SBO:0000599" comp:unitRef="m" comp:id="m_port" comp:name="m_port"/>
          <comp:port metaid="s_port" sboTerm="SBO:0000599" comp:unitRef="s" comp:id="s_port" comp:name="s_port"/>
          <comp:port metaid="m3_port" sboTerm="SBO:0000599" comp:unitRef="m3" comp:id="m3_port" comp:name="m3_port"/>
          <comp:port metaid="mM_port" sboTerm="SBO:0000599" comp:unitRef="mM" comp:id="mM_port" comp:name="mM_port"/>
          <comp:port metaid="kg_port" sboTerm="SBO:0000599" comp:unitRef="kg" comp:id="kg_port" comp:name="kg_port"/>
          <comp:port metaid="per_s_port" sboTerm="SBO:0000599" comp:unitRef="per_s" comp:id="per_s_port" comp:name="per_s_port"/>
        </comp:listOfPorts>
        <fbc:listOfObjectives fbc:activeObjective="R3_maximize">
          <fbc:objective fbc:id="R3_maximize" fbc:type="maximize">
            <fbc:listOfFluxObjectives>
              <fbc:fluxObjective fbc:reaction="R3" fbc:coefficient="1"/>
            </fbc:listOfFluxObjectives>
          </fbc:objective>
        </fbc:listOfObjectives>
      </model>
    </sbml>
    
    valid                    : TRUE
    check time (s)           : 0.008
    --------------------------------------------------------------------------------
    [0m[0m


