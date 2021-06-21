"""Creates dictionary of information for given model.

The model dictionary can be used for rendering the HTML report.
The information can be serialized to JSON for later rendering in web app.
"""

import json
from pathlib import Path
import pprint
from typing import Any, Dict, Union, List, Optional

import libsbml
import numpy as np

from sbmlutils.io import read_sbml
from sbmlutils.metadata import miriam
from src.sbmlutils.report import units
from src.sbmlutils.report.mathml import astnode_to_latex

# FIXME: support multiple model definitions in comp


def _get_sbase_attribute(sbase: libsbml.Sbase, key: str) -> Optional[Any]:
    """Get SBase attribute."""
    key = f"{key[0].upper()}{key[1:]}"
    if getattr(sbase, f"isSet{key}")():
        return getattr(sbase, f"get{key}")()
    else:
        return None


class SBMLDocumentInfo:
    """Class for collecting information in JSON on an SBMLDocument to create reports.

    A single document can contain multiple models or be a hierarchical
    model (comp package).
    """

    def __init__(
        self,
        doc: libsbml.SBMLDocument,
    ):
        """Initialize SBMLDocumentInfo."""
        self.doc: libsbml.SBMLDocument = doc
        self.info = self.create_info()

    @staticmethod
    def from_sbml(source: Union[Path, str]) -> 'SBMLDocumentInfo':
        """Read model info from SBML."""
        doc: libsbml.SBMLDocument = read_sbml(source)
        return SBMLDocumentInfo(doc=doc)

    def __repr__(self) -> str:
        """Get string representation."""
        return f"SBMLInfo({self.doc})"

    def __str__(self) -> str:
        """Get string."""
        return pprint.pformat(self.info, indent=2)

    def to_json(self) -> str:
        """Serialize to JSON representation."""
        return json.dumps(self.info, indent=2)

    def create_info(self) -> Dict[str, Any]:
        """Create information dictionary for report rendering."""

        # FIXME: support multiple models with comp
        d = {
            "doc": self.document(doc=self.doc),
        }
        if self.doc.isSetModel():
            d["model"] = self.model_dict(self.doc.getModel())
        else:
            d["model"] = None

        d["modelDefinitions"] = self.model_definitions()

        return d

    def model_dict(self, model: libsbml.Model):
        """Creates information for a given model."""
        assignments = self._create_assignment_map()
        rules = self.rules()
        d = {
            # sbml model information
            "model": self.model(model=model),

            # core
            "functionDefinitions": self.function_definitions(model=model),
            "unitDefinitions": self.unit_definitions(model=model),
            "compartments": self.compartments(model=model),
            "species": self.species(model=model),
            "parameters": self.parameters(),
            "initialAssignments": self.initial_assignments(),
            "assignmentRules": rules["assignmentRules"],
            "rateRules": rules["rateRules"],
            "algebraicRules": rules["algebraicRules"],
            "constraints": self.constraints_dict(),
            "reactions": self.reactions(),
            "events": self.events(),

            # comp
            "submodels": self.submodels(),
            "ports": self.ports(),

            # fbc
            "geneProducts": self.gene_products(),
            "objectives": self.objectives(),
        }
        return d

    @staticmethod
    def _sbaseref(sref: libsbml.SBaseRef) -> Optional[Dict]:
        """Format the SBaseRef instance.

        :param sref: SBaseRef instance
        :return: Dictionary containging formatted SBaseRef instance's data
        """

        if sref.isSetPortRef():
            return {
                "type": "port_ref",
                "value": sref.getPortRef()
            }
        elif sref.isSetIdRef():
            return {
                "type": "id_ref",
                "value": sref.getIdRef()
            }
        elif sref.isSetUnitRef():
            return {
                "type": "unit_ref",
                "value": sref.getUnitRef()
            }
        elif sref.isSetMetaIdRef():
            return {
                "type": "meta_ID_ref",
                "value": sref.getMetaIdRef()
            }
        return None

    def _create_assignment_map(self, model: libsbml.Model) -> Dict:
        """Create dictionary of symbols:assignment for symbols in model.

        This allows to lookup assignments for a given variable.

        :return: assignment dictionary for model
        """
        assignments = dict()

        # initial assignments
        initial_assignments = {}
        assignment: libsbml.InitialAssignment
        for assignment in model.getListOfInitialAssignments():
            d = self.sbase_dict(assignment)
            pk_symbol = assignment.getSymbol() if assignment.isSetSymbol() else None
            if pk_symbol:
                d["assignment"] = astnode_to_latex(assignment.getMath()) if assignment.isSetMath() else None
                d["derivedUnits"] = self.ud_to_latex(assignment.getDerivedUnitDefinition())
                initial_assignments[pk_symbol] = d

        assignments["initialAssignments"] = initial_assignments

        # rules
        rules = {}
        rule: libsbml.Rule
        for rule in model.getListOfRules():
            d = self.sbase_dict(rule)

            pk_symbol = rule.getVariable() if rule.isSetVariable() else None
            if pk_symbol:
                d["assignment"] = rule.getMath() if assignment.isSetMath() else None
                d["units"] = rule.getDerivedUnitDefinition()
                rules[pk_symbol] = d

        assignments["rules"] = rules

        return assignments

    @staticmethod
    def _sbml_type(sbase: libsbml.SBase) -> str:
        class_name = str(sbase.__class__)[16:-2]
        return class_name

    def _set_pk(self, sbase: libsbml.Sbase) -> str:
        """Calculate primary key."""
        if not sbase.pk:
            pk: str
            if sbase.isSetId():
                pk = sbase.getId()
            elif sbase.isSetMetaId():
                pk = sbase.getMetaId()
            else:
                xml = sbase.toSBML()
                pk = SBMLDocumentInfo._uuid(xml)
            sbase.pk = pk
        return sbase.pk

    @staticmethod
    def _uuid(xml: str) -> str:
        """Generate unique identifier.

        Sha256 digest of the identifier (mostly the xml string).

        :param identifier: Unique property of the base which is used to generate the
                            SHA256 digest. Mostly the xml is passed.
        """
        return

    @classmethod
    def sbase_dict(cls, sbase: libsbml.SBase) -> Dict[str, Any]:
        """Info dictionary for SBase.

        :param sbase: SBase instance for which info dictionary is to be created
        :return info dictionary for item
        """
        pk = cls._set_pk(sbase)
        d = {
            "pk": pk,
            "sbmlType": cls._sbml_type(sbase),
            "id": sbase.getId() if sbase.isSetId() else None,
            "metaId": sbase.getMetaId() if sbase.isSetMetaId() else None,
            "name": sbase.getName() if sbase.isSetName() else None,
            "sbo": sbase.getSBOTermID() if sbase.isSetSBOTerm() else None,
            "cvterms": cls.cvterms(sbase),
            "history": cls.model_history(sbase),
            "notes": sbase.getNotesString() if sbase.isSetNotes() else None,
        }

        if sbase.getTypeCode() in {libsbml.SBML_DOCUMENT, libsbml.SBML_MODEL}:
            d['xml'] = None
        else:
            d['xml'] = sbase.toSBML()

        # comp
        item_comp = sbase.getPlugin("comp")
        if item_comp and type(item_comp) == libsbml.CompSBasePlugin:
            # ReplacedBy
            if item_comp.isSetReplacedBy():
                replaced_by = item_comp.getReplacedBy()
                submodel_ref = replaced_by.getSubmodelRef()
                d["replacedBy"] = {
                    "submodelRef": submodel_ref,
                    "replacedBySbaseref": cls._sbaseref(replaced_by)
                }
            else:
                d["replacedBy"] = None

            # ListOfReplacedElements
            if item_comp.getNumReplacedElements() > 0:
                replaced_elements = []
                for rep_el in item_comp.getListOfReplacedElements():
                    submodel_ref = rep_el.getSubmodelRef()
                    replaced_elements.append({
                        "submodelRef": submodel_ref,
                        "replacedElementSbaseref": cls._sbaseref(rep_el)
                    })

                d["replacedElements"] = replaced_elements
            else:
                d["replacedElements"] = None


        # distrib
        sbml_distrib: libsbml.DistribSBasePlugin = sbase.getPlugin("distrib")
        if sbml_distrib and isinstance(sbml_distrib, libsbml.DistribSBasePlugin):
            d["uncertainties"] = []
            for uncertainty in sbml_distrib.getListOfUncertainties():
                u_dict = SBMLDocumentInfo.sbase_dict(uncertainty)

                u_dict["uncert_parameters"] = []
                upar: libsbml.UncertParameter
                for upar in uncertainty.getListOfUncertParameters():
                    param_dict = {
                        "var": upar.getVar() if upar.isSetVar() else None,
                        "value": upar.getValue() if upar.isSetValue() else None,
                        "units": upar.getUnits() if upar.isSetUnits() else None,
                        "type": upar.getTypeAsString() if upar.isSetType() else None,
                        "definition_url": upar.getDefinitionURL() if upar.isSetDefinitionURL() else None,
                        "math": cls._math(upar.getMath(), sbase.getModel()) if upar.isSetMath() else None
                    }

                    u_dict["uncert_parameters"].append(param_dict)

                d["uncertainties"].append(u_dict)

        return d

    def sbaseref_dict(self, sbref: libsbml.SBaseRef) -> Dict[str, Any]:
        """Info dictionary for SBaseRef.

        :param sbref: SBaseRef instance for which information dictionary is created
        :return: information dictionary for SBaseRef
        """
        info = self.sbase_dict(sbref)

        info["portRef"] = sbref.getPortRef() if sbref.isSetPortRef() else None
        info["idRef"] = sbref.getIdRef() if sbref.isSetIdRef() else None
        info["unitRef"] = sbref.getUnitRef() if sbref.isSetUnitRef() else None
        info["metaIdRef"] = sbref.getMetaIdRef() if sbref.isSetMetaIdRef() else None
        info["referencedElement"] = {
            "element": type(sbref.getReferencedElement()).__name__,
            "elementId": sbref.getReferencedElement().getId()
        }

        return info

    @classmethod
    def cvterms(cls, sbase: libsbml.SBase) -> Optional[List]:
        """Parse CVTerms information.

        :param sbase: SBase instance
        """
        if not sbase.isSetAnnotation():
            return None

        cvterms = []
        for kcv in range(sbase.getNumCVTerms()):
            cv: libsbml.CVTerm = sbase.getCVTerm(kcv)
            # qualifier
            q_type = cv.getQualifierType()
            if q_type == libsbml.MODEL_QUALIFIER:
                qualifier = miriam.ModelQualifierType[
                    cv.getModelQualifierType()
                ]
            elif q_type == libsbml.BIOLOGICAL_QUALIFIER:
                qualifier = miriam.BiologicalQualifierType[
                    cv.getBiologicalQualifierType()
                ]

            resources = [
                cv.getResourceURI(k) for k in range(cv.getNumResources())
            ]
            cvterms.append({
                "qualifier": qualifier,
                "resources": resources,
            })

        return cvterms

    @classmethod
    def model_history(cls, sbase: libsbml.SBase) -> Optional[Dict]:
        """Render HTML representation of the model history.

        :param mhistory: SBML ModelHistory instance
        :return HTML representation of the model history
        """

        if sbase.isSetModelHistory():
            history: libsbml.ModelHistory = sbase.getModelHistory()
        else:
            return None

        creators = []
        for kc in range(history.getNumCreators()):
            c: libsbml.ModelCreator = history.getCreator(kc)
            creators.append({
                "givenName":  c.getGivenName() if c.isSetGivenName() else None,
                "familyName": c.getFamilyName() if c.isSetFamilyName() else None,
                "organization": c.getOrganization() if c.isSetOrganization() else None,
                "email": c.getEmail() if c.isSetEmail() else None
            })

        created_date = history.getCreatedDate().getDateAsString() if history.isSetCreatedDate() else None
        modified_dates = []
        for km in range(history.getNumModifiedDates()):
            modified_dates.append(history.getModifiedDate(km).getDateAsString())
        return {
            "creators": creators,
            "createdDate": created_date,
            "modifiedDates": modified_dates
        }

    def document(self, doc: libsbml.SBMLDocument) -> Dict[str, str]:
        """Info for SBMLDocument.

        :param doc: SBMLDocument
        :return: information dictionary for SBMLDocument
        """
        info = self.sbase_dict(doc)

        packages = {}
        packages["document"] = {
            "level": doc.getLevel(),
            "version": doc.getVersion()
        }

        plugins = []
        for k in range(doc.getNumPlugins()):
            plugin = doc.getPlugin(k)
            prefix = plugin.getPrefix()
            version = plugin.getPackageVersion()
            plugins.append({
                "prefix": prefix,
                "version": version
            })
        packages["plugins"] = plugins

        info["packages"] = packages
        return info

    def model(self, model: libsbml.Model) -> Dict[str, str]:
        """Info for SBML Model.

        :param model: Model
        :return: information dictionary for Model
        """
        d = self.sbase_dict(model)
        for key in [
            "substanceUnits",
            "timeUnits",
            "volumeUnits",
            "areaUnits",
            "lengthUnits",
            "extentUnits",
            "conversionFactor",
        ]:
            d[key] = _get_sbase_attribute(model, key)

        return d

    def function_definitions(self, model: libsbml.Model) -> List:
        """Information dictionaries for FunctionDefinitions.

        :return: list of info dictionaries for FunctionDefinitions
        """
        func_defs = []
        fd: libsbml.FunctionDefinition
        for fd in model.getListOfFunctionDefinitions():
            info = self.sbase_dict(fd)

            # FIXME: update math: inject lambda
            info["math"] = mathml.cmathml_to_latex(fd.getMath(), model)

            func_defs.append(info)

        return func_defs

    def unit_definitions(self, model: libsbml.Model) -> List:
        """Information for UnitDefinitions.

        :return: list of info dictionaries for UnitDefinitions
        """
        unit_defs = []
        ud: libsbml.UnitDefinition
        for ud in model.getListOfUnitDefinitions():
            info = self.sbase_dict(ud)
            info["units"] = self.ud_to_latex(ud)

            unit_defs.append(info)

        return unit_defs

    @staticmethod
    def ud_to_latex(ud: libsbml.UnitDefinition, model: libsbml.Model) -> Optional[str]:
        """Convert unit definition to latex."""
        if ud is None:
            return None
        ud_str: str = units.unitDefinitionToString(ud)
        astnode = libsbml.parseL3FormulaWithModel(ud_str, model=model)
        mathml_str = libsbml.writeMathMLToString(astnode)
        return mathml.cmathml_to_latex(mathml_str, model=model)

    def compartments(self, model: libsbml.Model) -> List:
        """Information for Compartments.

        :return: list of info dictionaries for Compartments
        """
        compartments = []
        c: libsbml.Compartment
        for c in model.getListOfCompartments():
            d = self.sbase_dict(c)
            for key in [
                "spatialDimensions",
                "size",
                "constant"
            ]:
                d[key] = _get_sbase_attribute(c, key)

            d["units"] = mathml.cmathml_to_latex(_get_sbase_attribute(c, "units"))
            d["derivedUnits"] = mathml.cmathml_to_latex(c.getDerivedUnitDefinition())
            # FIXME: get assignment information into report (see assignment_map); FIXME: larger issue of links

            compartments.append(d)

        return compartments

    def species(self, model: libsbml.Model) -> List:
        """Information for Species.

        :return: list of info dictionaries for Species
        """

        species = []
        s: libsbml.Species
        for s in model.getListOfSpecies():
            d = self.sbase_dict(s)

            for key in [
                "compartment",
                "initialAmount",
                "initialConcentration",
                "substanceUnits",
                "hasOnlySubstanceUnits",
                "boundaryCondition",
                "constant",
            ]:
                d[key] = _get_sbase_attribute(s, key)

            # FIXME: units & derivedUnits missing

            if s.isSetConversionFactor():
                cf_sid = s.getConversionFactor()
                cf_p: libsbml.Parameter = self.model.getParameter(cf_sid)
                cf_value = cf_p.getValue()
                cf_units = cf_p.getUnits()

                d["conversionFactor"] = {
                    "sid": cf_sid,
                    "value": cf_value,
                    "units": cf_units
                }
            else:
                d["conversionFactor"] = {}

            # fbc
            sfbc = s.getPlugin("fbc")
            d["fbc"] = {
                "formula": sfbc.getChemicalFormula() if sfbc.isSetChemicalFormula() else None,
                "charge": sfbc.getCharge() if (sfbc.isSetCharge() and sfbc.getCharge() != 0) else None,
            } if sfbc else None

            species.append(d)

        return species

    def parameters(self, model: libsbml.Model) -> List:
        """Information for SBML Parameters.

        :return: list of info dictionaries for Reactions
        """

        parameters = []
        p: libsbml.Parameter
        for p in model.getListOfParameters():
            info = self.sbase_dict(p)

            if p.isSetValue():
                value = p.getValue()
                if np.isnan(value):
                    value = None

            else:
                value = None
                # FIXME: get assignment information in report
                # value_formula = assignment_map.get(p.getId(), None)
                # if value_formula is None:
                #     warnings.warn(
                #         f"No value for parameter via Value, InitialAssignment or "
                #         f"AssignmentRule: {p.getId()}"
                #     )
                #     value = None
                # else:
                #     value = math(value_formula, self.math_render)

            info["value"] = value
            info["units"] = self.ud_to_latex(p.getUnits() if p.isSetUnits() else None)
            info["derivedUnits"] = self.ud_to_latex(p.getDerivedUnitDefinition())
            info["constant"] = p.getConstant() if p.isSetConstant() else None
            parameters.append(info)

        return parameters

    def initial_assignments(self) -> List:
        """Information for InitialAssignments.

        :return: list of info dictionaries for InitialAssignments
        """

        assignments = []
        assignment: libsbml.InitialAssignment
        for assignment in self.model.getListOfInitialAssignments():
            info = self.sbase_dict(assignment)
            info["symbol"] = assignment.getSymbol() if assignment.isSetSymbol() else None
            info["math"] = mathml.cmathml_to_latex(assignment.getMath(), self.model, self.math_render)
            info["derivedUnits"] = self.ud_to_latex(assignment.getDerivedUnitDefinition())
            assignments.append(info)

        return assignments

    def rules(self, model: libsbml.Model) -> Dict:
        """Information for Rules.

        :return: list of info dictionaries for Rules
        """

        rules = {
            "assignmentRules": [],
            "rateRules": [],
            "algebraicRules": [],
        }
        rule: libsbml.Rule
        for rule in model.getListOfRules():
            info = self.sbase_dict(rule)
            info["variable"] = self._rule_variable_to_string(rule)
            info["math"] = rule.getMath()  # FIXME
            info["derivedUnits"] = self.ud_to_latex(rule.getDerivedUnitDefinition(), model=model)

            type = info["sbmlType"]
            key = f"{type[0].lower()}{type[1:]}s"

            rules[key].append(info)

        return rules

    @staticmethod
    def _rule_variable_to_string(rule: libsbml.Rule) -> str:
        """Format variable for rule.

        :param rule: SBML rule instance
        :return formatted string representation of the rule
        """
        if isinstance(rule, libsbml.AlgebraicRule):
            return "0"
        elif isinstance(rule, libsbml.AssignmentRule):
            return rule.variable  # type: ignore
        elif isinstance(rule, libsbml.RateRule):
            return f"d {rule.variable}/dt"
        else:
            raise TypeError(rule)


    def constraints_dict(self, model: libsbml.Model) -> List:
        """Information for Constraints.

        :return: list of info dictionaries for Constraints
        """

        constraints = []
        constraint: libsbml.Constraint
        for constraint in model.getListOfConstraints():
            info = self.sbase_dict(constraint)
            info["math"] = self._math(constraint.getMath(), self.model, self.math_render)


            info["message"] = constraint.getMessage() if constraint.isSetMessage() else None
            constraints.append(info)

        return constraints

    def reactions(self, model: libsbml.Model) -> List:
        """Information dictionaries for ListOfReactions.

        :return: list of info dictionaries for Reactions

        -- take a look at local parameter once
        -- also made additions for products and reactions
        """

        reactions = []
        r: libsbml.Reaction
        for r in model.getListOfReactions():
            d = self.sbase_dict(r)
            d["reversible"] = r.getReversible() if r.isSetReversible() else None
            d["compartment"] = r.getCompartment() if r.isSetCompartment() else None
            d["listOfReactants"] = [
                self._species_reference(reac) for reac in r.getListOfReactants()
            ]
            d["listOfProducts"] = [
                self._species_reference(prod) for prod in r.getListOfProducts()
            ]
            d["listOfModifiers"] = [mod.getSpecies() for mod in r.getListOfModifiers()]
            d["fast"] = r.getFast() if r.isSetFast() else None
            d["equation"] = self._equation_from_reaction(r)

            klaw: libsbml.KineticLaw = r.getKineticLaw() if r.isSetKineticLaw() else None
            if klaw:
                d["math"]: (klaw.getMath() if klaw.isSetMath() else None)
                    "derivedUnits": self.ud_to_latex(klaw.getDerivedUnitDefinition())
                }

                local_parameters = []
                for i in range(len(klaw.getListOfLocalParameters())):
                    lp: libsbml.LocalParameter = klaw.getLocalParameter(i)
                    lpar_info = {
                        "id": lp.getId() if lp.isSetId() else None,
                        "value": lp.getValue() if lp.isSetValue() else None,
                        "units": self.ud_to_latex(lp.getUnits() if lp.isSetUnits() else None),
                        "derivedUnits": self.ud_to_latex(lp.getDerivedUnitDefinition()),
                    }
                    local_parameters.append(lpar_info)
                d["kineticLaw"]["localParameters"] = local_parameters
            else:
                d["kineticLaw"] = None

            # fbc
            rfbc = r.getPlugin("fbc")
            d["fbc"] = {
                "bounds": self._bounds_dict_from_reaction(r, model),
                "gpa": self._gene_product_association_dict_from_reaction(r)
            } if rfbc else None

            reactions.append(d)

        return reactions

    @staticmethod
    def _species_reference(species: libsbml.SpeciesReference):
        return {
            "species": species.getSpecies() if species.isSetSpecies() else None,
            "stoichiometry": species.getStoichiometry() if species.isSetStoichiometry() else 1.0,
            "constant": species.getConstant() if species.isSetConstant() else None
        }

    @staticmethod
    def _bounds_dict_from_reaction(reaction: libsbml.Reaction, model: libsbml.Model) -> Dict:
        """Render string of bounds from the reaction.

        :param reaction: SBML reaction instance
        :param model: SBML model instance
        :return: String of bounds extracted from the reaction
        """
        bounds = {}
        rfbc = reaction.getPlugin("fbc")
        if rfbc is not None:
            # get values for bounds
            lb_id, ub_id = None, None
            lb_value, ub_value = None, None
            if rfbc.isSetLowerFluxBound():
                lb_id = rfbc.getLowerFluxBound()
                lb_p = model.getParameter(lb_id)
                if lb_p.isSetValue():
                    lb_value = lb_p.getValue()
            if rfbc.isSetUpperFluxBound():
                ub_id = rfbc.getUpperFluxBound()
                ub_p = model.getParameter(ub_id)
                if ub_p.isSetValue():
                    ub_value = ub_p.getValue()

            bounds["lb_value"] = lb_value
            bounds["ub_value"] = ub_value
        else:
            bounds = None

        return bounds

    @staticmethod
    def _gene_product_association_dict_from_reaction(reaction: libsbml.Reaction) -> Dict:
        """Render string representation of the GeneProductAssociation for given reaction.

        :param reaction: SBML reaction instance
        :return: string representation of GeneProductAssociation
        """

        rfbc = reaction.getPlugin("fbc")
        info = rfbc.getGeneProductAssociation().getAssociation().toInfix() if (
            rfbc and rfbc.isSetGeneProductAssociation()
        ) else None

        return info

    # Utility method for equations
    @staticmethod
    def _equation_from_reaction(
        reaction: libsbml.Reaction,
        sep_reversible: str = "&#8646;",
        sep_irreversible: str = "&#10142;",
        modifiers: bool = False,
    ) -> str:
        """Create equation for reaction.

        :param reaction: SBML reaction instance for which equation is to be generated
        :param sep_reversible: escape sequence for reversible equation (<=>) separator
        :param sep_irreversible: escape sequence for irreversible equation (=>) separator
        :param modifiers: boolean flag to use modifiers
        :return equation string generated for the reaction
        """

        left = SBMLDocumentInfo._half_equation(reaction.getListOfReactants())
        right = SBMLDocumentInfo._half_equation(reaction.getListOfProducts())
        if reaction.getReversible():
            # '<=>'
            sep = sep_reversible
        else:
            # '=>'
            sep = sep_irreversible
        if modifiers:
            mods = SBMLDocumentInfo._modifier_equation(reaction.getListOfModifiers())
            if mods is None:
                return " ".join([left, sep, right])
            else:
                return " ".join([left, sep, right, mods])
        return " ".join([left, sep, right])

    @staticmethod
    def _modifier_equation(modifierList: libsbml.ListOfSpeciesReferences) -> str:
        """Render string representation for list of modifiers.

        :param modifierList: list of modifiers
        :return: string representation for list of modifiers
        """
        if len(modifierList) == 0:
            return ""
        mids = [m.getSpecies() for m in modifierList]
        return "[" + ", ".join(mids) + "]"  # type: ignore

    @staticmethod
    def _half_equation(speciesList: libsbml.ListOfSpecies) -> str:
        """Create equation string of the half reaction of the species in the species list.

        :param speciesList: list of species in the half reaction
        :return: half equation string
        """
        items = []
        for sr in speciesList:
            stoichiometry = sr.getStoichiometry()
            species = sr.getSpecies()
            if abs(stoichiometry - 1.0) < 1e-8:
                sd = f"{species}"
            elif abs(stoichiometry + 1.0) < 1e-8:
                sd = f"-{species}"
            elif stoichiometry >= 0:
                sd = f"{stoichiometry} {species}"
            elif stoichiometry < 0:
                sd = f"-{stoichiometry} {species}"
            items.append(sd)
        return " + ".join(items)

    def events(self) -> List:
        """Information dictionaries for Events.

        :return: list of info dictionaries for Events
        """

        events = []
        event: libsbml.Event
        for event in self.model.getListOfEvents():
            info = self.sbase_dict(event)

            info["useValuesFromTriggerTime"] = event.getUseValuesFromTriggerTime() if event.isSetUseValuesFromTriggerTime() else None

            trigger: libsbml.Trigger = event.getTrigger()
            if trigger:
                info["trigger"] = {
                    "math": self._math(trigger.getMath(), self.model, self.math_render),
                    "initialValue": trigger.initial_value,
                    "persistent": trigger.persistent
                }
            else:
                info["trigger"] = None

            info["priority"] = self._math(event.getPriority(), self.model, self.math_render) if event.isSetPriority() else None
            info["delay"] = self._math(event.getDelay(), self.model, self.math_render) if event.isSetDelay() else None

            assignments = []
            eva: libsbml.EventAssignment
            for eva in event.getListOfEventAssignments():
                assignments.append({
                    "variable": eva.getVariable() if eva.isSetVariable() else None,
                    "math": self._math(eva.getMath(), self.model, self.math_render)
                })
            info["listOfEventAssignments"] = assignments

            events.append(info)

        return events

    # ---------------------------------------------------------------------------------
    # comp
    # ---------------------------------------------------------------------------------
    def model_definitions(self) -> Dict:
        """Information for comp:ModelDefinitions.

        :return: list of info dictionaries for comp:ModelDefinitions
        """
        d = {}
        doc_comp: libsbml.CompSBMLDocumentPlugin = self.doc.getPlugin("comp")
        if doc_comp:
            model_defs = []
            md: libsbml.ModelDefinition
            for md in doc_comp.getListOfModelDefinitions():
                info = self.sbase_dict(md)
                info["type"] = {
                    "class": type(md).__name__
                }
                model_defs.append(info)
            # FIXME: parse the model definitions
            d["modelDefs"] = model_defs

            external_model_defs = []
            emd: libsbml.ExternalModelDefinition
            for emd in doc_comp.getListOfExternalModelDefinitions():
                info = self.sbase_dict(emd)
                info["type"] = {
                    "class": type(emd).__name__,
                    "source_code": emd.getSource()
                }
                external_model_defs.append(info)
            d["externalModelDefs"] = external_model_defs
        else:
            d = None

        return d

    def submodels(self, model: libsbml.Model) -> Optional[Dict]:
        """Information dictionaries for comp:Submodels.

        :return: list of info dictionaries for comp:Submodels
        """
        d = []
        model_comp = model.getPlugin("comp")
        if model_comp:
            submodels = []
            submodel: libsbml.Submodel
            for submodel in model_comp.getListOfSubmodels():
                info = self.sbase_dict(submodel)
                info["modelRef"] = submodel.getModelRef() if submodel.isSetModelRef() else None

                deletions = []
                for deletion in submodel.getListOfDeletions():
                    deletions.append(self._sbaseref(deletion))
                info["deletions"] = deletions

                info["timeConversion"] = submodel.getTimeConversionFactor() if submodel.isSetTimeConversionFactor() else None
                info["extentConversion"] = submodel.getExtentConversionFactor() if submodel.isSetExtentConversionFactor() else None

                submodels.append(info)
            d = submodels

        return d

    def ports(self, model: libsbml.Model) -> List:
        """Information for comp:Ports.

        :return: list of info dictionaries for comp:Ports
        """

        model_comp = model.getPlugin("comp")
        ports = []
        if model_comp:
            port: libsbml.Port
            for port in model_comp.getListOfPorts():
                info = self.sbaseref_dict(port)
                ports.append(info)

        return ports

    # ---------------------------------------------------------------------------------
    # fbc
    # ---------------------------------------------------------------------------------
    def gene_products(self) -> Optional[Dict]:
        """Information dictionaries for GeneProducts.

        :return: list of info dictionaries for Reactions

        -- revisit
        """
        data = []

        model_fbc: libsbml.FbcModelPlugin = self.model.getPlugin("fbc")
        if model_fbc:
            gene_products = []
            gp: libsbml.GeneProduct
            for gp in model_fbc.getListOfGeneProducts():
                info = self.sbase_dict(gp)
                info["label"] = gp.getLabel() if gp.isSetLabel() else None
                info["associatedSpecies"] = gp.getAssociatedSpecies() if gp.isSetAssociatedSpecies() else None

                gene_products.append(info)

            data = gene_products
        else:
            data = []

        return data

    def objectives(self) -> List:
        """Information dictionaries for Objectives.

        :return: list of info dictionaries for Objectives
        """

        objectives = []
        model_fbc: libsbml.FbcModelPlugin = self.model.getPlugin("fbc")
        if model_fbc:
            objective: libsbml.Objective
            for objective in model_fbc.getListOfObjectives():
                info = self.sbase_dict(objective)
                info["type"] = objective.getType() if objective.isSetType() else None

                flux_objectives = []
                f_obj: libsbml.FluxObjective
                for f_obj in objective.getListOfFluxObjectives():
                    coefficient = f_obj.getCoefficient()
                    if coefficient < 0.0:
                        sign = "-"
                    else:
                        sign = "+"
                    part = {
                        "sign": sign,
                        "coefficient": abs(coefficient),
                        "reaction": f_obj.getReaction() if f_obj.isSetReaction() else None
                    }
                    flux_objectives.append(part)
                info["fluxObjectives"] = flux_objectives

                objectives.append(info)

        return objectives


if __name__ == "__main__":
    from pathlib import Path

    output_dir = Path(__file__).parent / "test"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    print("-" * 80)
    from src.sbmlutils.test import ICG_BODY, REPRESSILATOR_SBML, RECON3D_SBML, ICG_LIVER, ICG_BODY_FLAT
    info = SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML, "latex")
    json_str = info.to_json()
    print(info)
    print("-" * 80)
    print(json_str)
    print("-" * 80)

    with open(output_dir / "test.json", "w") as fout:
        fout.write(json_str)
