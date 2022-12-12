"""Test bed for FBC version 3.

For latest SBML fbc v3 specification see
https://github.com/bgoli/sbml-fbc-spec/blob/main/sf_svn/spec/main.pdf
"""
from logging import getLogger
from pathlib import Path

import libsbml


# from sbmlutils.console import console
logger = getLogger(__name__)


def check(value: int, message: str) -> bool:
    """Check the libsbml return value and prints message if something happened.

    If 'value' is None, prints an error message constructed using
      'message' and then exits with status code 1. If 'value' is an integer,
      it assumes it is a libSBML return status code. If the code value is
      LIBSBML_OPERATION_SUCCESS, returns without further action; if it is not,
      prints an error message constructed using 'message' along with text from
      libSBML explaining the meaning of the code, and exits with status code 1.
    """
    valid = True
    if value is None:
        logger.error(f"Error: LibSBML returned a null value trying to <{message}>.")
        valid = False
    elif isinstance(value, int):
        if value != libsbml.LIBSBML_OPERATION_SUCCESS:
            logger.error(f"Error encountered trying to '{message}'.")
            logger.error(
                f"LibSBML returned error code {str(value)}: "
                f"{libsbml.OperationReturnValue_toString(value).strip()}"
            )
            valid = False

    return valid


# create document with new fbc version 3 namespace
sbmlns: libsbml.SBMLNamespaces = libsbml.SBMLNamespaces(3, 1)
sbmlns.addPkgNamespace("fbc", 3)

doc: libsbml.SBMLDocument = libsbml.SBMLDocument(sbmlns)
doc_fbc: libsbml.FbcSBMLDocumentPlugin = doc.getPlugin("fbc")
doc_fbc.setRequired(False)

model: libsbml.Model = doc.createModel()
model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
model_fbc.setStrict(True)

# Support for key value pairs exists
c: libsbml.Compartment = model.createCompartment()
c.setId("c1")
c.setSize(1.0)
c.setConstant(True)

s1: libsbml.Species = model.createSpecies()
s1.setId("s1")
s1.setCompartment("c1")
s1.setInitialConcentration(1.0)
s1.setConstant(False)
s1.setHasOnlySubstanceUnits(False)
s1.setBoundaryCondition(False)

# KeyValuePair on Species
s1_fbc: libsbml.FbcSpeciesPlugin = s1.getPlugin("fbc")
kvp_list: libsbml.ListOfKeyValuePairs = s1_fbc.getListOfKeyValuePairs()
kvp_list.setXmlns("http://sbml.org/fbc/keyvaluepair")
kvp: libsbml.KeyValuePair = kvp_list.createKeyValuePair()
check(kvp.setKey("testdata"), "Set Key on KeyValuePair")
check(kvp.setValue("1.0"), "Set Value on KeyValuePair")


s2: libsbml.Species = model.createSpecies()
s2.setId("s2")
s2.setCompartment("c1")
s2.setInitialConcentration(1.0)
s2.setConstant(False)
s2.setHasOnlySubstanceUnits(False)
s2.setBoundaryCondition(False)

# p1: libsbml.Parameter = model.createParameter()
# p1.setId("lb")
# p1.setValue(-100)
# p1.setConstant(True)
# # KeyValue Pair on parameter
# p1_fbc: libsbml.FbcSpeciesPlugin = p1.getPlugin("fbc")
# kvp_list: libsbml.ListOfKeyValuePairs = p1_fbc.getListOfKeyValuePairs()
# # kvp_list.setXmlns("http://sbml.org/fbc/keyvaluepair")
# kvp: libsbml.KeyValuePair = kvp_list.createKeyValuePair()
# check(kvp.setKey("pdata"), "Set Key on KeyValuePair")
# check(kvp.setValue("10.0"), "Set Value on KeyValuePair")
#
# p2: libsbml.Parameter = model.createParameter()
# p2.setId("ub")
# p2.setValue(100)
# p2.setConstant(True)

# Support exists for user constraints
reaction: libsbml.Reaction = model.createReaction()
reaction.setId("r1")
reaction.setReversible(True)
reaction.setFast(False)
fbc_reaction: libsbml.FbcReactionPlugin = reaction.getPlugin("fbc")
fbc_reaction.setUpperFluxBound("ub")
fbc_reaction.setLowerFluxBound("lb")

reactant: libsbml.SpeciesReference = reaction.createReactant()
reactant.setSpecies("s1")
reactant.setConstant(True)
reactant.setStoichiometry(1.0)

product: libsbml.SpeciesReference = reaction.createProduct()
product.setSpecies("s2")
product.setConstant(True)
product.setStoichiometry(1.0)


constraint: libsbml.UserDefinedConstraint = model_fbc.createUserDefinedConstraint()
constraint.setId("constraint1")
constraint.setLowerBound("lb")
constraint.setUpperBound("ub")

component: libsbml.UserDefinedConstraintComponent = (
    constraint.createUserDefinedConstraintComponent()
)
component.setCoefficient(10.0)
component.setVariable("r1")
component.setVariableType(libsbml.FBC_FBCVARIABLETYPE_LINEAR)

sbml_str: str = libsbml.writeSBMLToString(doc)
print("-" * 80)
# console.log(sbml_str)
print(sbml_str)
print("-" * 80)


# checking that SBML string can be read again
doc2 = libsbml.readSBMLFromString(sbml_str)
if doc2.getNumErrors() > 0:
    if doc2.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
        err_message = "Unreadable SBML file"
    elif doc2.getError(0).getErrorId() == libsbml.XMLFileOperationError:
        err_message = "Problems reading SBML file: XMLFileOperationError"
    else:
        err_message = "SBMLDocumentErrors encountered while reading the SBML file."

    # log_sbml_errors_for_doc(doc)
    logger.error(f"`read_sbml` error `{err_message}`")
    for k in range(doc2.getNumErrors()):
        error: libsbml.SBMLError = doc2.getError(k)
        print(f"Error {k}")
        print(error.getMessage())


# from sbmlutils.io import validate_sbml
# from sbmlutils.validation import ValidationOptions
#
#
# validate_sbml(
#     source=sbml_str, validation_options=ValidationOptions(units_consistency=False)
# )
# sbml_path = Path("fbc_version3.xml")
# with open("fbc_version3.xml", "w") as f_sbml:
#     f_sbml.write(sbml_str)
#
# validate_sbml(
#     source=sbml_path, validation_options=ValidationOptions(units_consistency=False)
# )
