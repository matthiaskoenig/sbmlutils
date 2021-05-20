"""Creates dictionary of information for given model.

The model dictionary can be used for rendering the HTML report.
The information can be serialized to JSON for later rendering in web app.
"""

import json
import warnings
from pathlib import Path
import pprint
from typing import Any, Dict, Union, List

import libsbml

from sbmlutils.io import read_sbml
from sbmlutils.metadata import miriam
from src.sbmlutils.report import formating
from src.sbmlutils.report.formating import (
    sbo,
    sbaseref,
    derived_units,
    unitDefinitionToString,
    math
)

# TODO: go over specification and support all attributes
# TODO: unify the names of the attributes and lists in JSON to be in line with specification (camel case)
# TODO: rename the info functions
# TODO: do the model history on SBase
# FIXME: support multiple model definitions in comp


class SBMLModelInfo:
    """Class for collecting model information for report.

    The information can be accessed via the 'info' attribute.
    """

    def __init__(
        self,
        doc: libsbml.SBMLDocument,
        model: libsbml.Model,
        math_render: str = "cmathml",  # FIXME: define constants via Enum
    ):
        """Initialize SBMLModelInfo.

        :param doc:
        :param model:
        :param math_render: type of MathML rendering
        """
        self.doc = doc
        self.model = model
        self.math_render = math_render
        self.info = self.create_info()

    @staticmethod
    def from_sbml(source: Union[Path, str], math_render: str = "cmathml") -> 'SBMLModelInfo':
        """Read model info from SBML."""
        doc: libsbml.SBMLDocument = read_sbml(source)
        # FIXME: support multiple model definitions in comp
        model: libsbml.Model = doc.getModel()
        return SBMLModelInfo(doc=doc, model=model, math_render=math_render)

    def __repr__(self) -> str:
        """Get string representation."""
        return f"SBMLInfo({self.doc}, {self.model})"

    def __str__(self) -> str:
        """Get string."""
        return pprint.pformat(self.info, indent=2)

    def to_json(self) -> str:
        """Serialize to JSON representation."""

        if self.info is None:
            self.info = self.create_info()

        model_json = json.dumps(self.info, indent=2)
        return model_json

    def create_info(self) -> Dict[str, Any]:
        """Create information dictionary for report rendering."""
        values = self._create_assignment_map()
        model_info = {
            "model": self.model_dict(model=self.model),
            # core
            "unitDefinitions": self.unit_definitions_dict(),
            "functionDefinitions": self.info_function_definitions(),
            "compartments": self.info_compartments(values),
            "species": self.info_species(),
            "parameters": self.info_parameters(values),
            "initialAssignments": self.info_initial_assignments(),
            "rules": self.info_rules(),
            "constraints": self.info_constraints(),
            "reactions": self.info_reactions(),
            "events": self.info_events(),

            # comp
            "submodels": self.info_submodels(),
            "ports": self.info_ports(),
            # fbc
            "geneProducts": self.info_gene_products(),
            "objectives": self.info_objectives(),
        }
        d = {

            # sbml model information
            # core
            "doc": self.info_document(doc=self.doc),
            "modeldefs": self.info_model_definitions(),
            "models": model_info,  # FIXME: support multiple models with comp
            # helper information
            "values": values,
        }
        return d

    def _create_assignment_map(self) -> Dict:
        """Create dictionary of symbols:assignment for symbols in model.

        This allows to lookup assignments for a given variable.

        :return: assignment dictionary for model
        """
        values = dict()

        # initial assignments
        initial_assignments = []
        assignment: libsbml.InitialAssignment
        for assignment in self.model.getListOfInitialAssignments():
            info = self.sbase_dict(assignment)
            info["sid"] = assignment.getSymbol() if assignment.isSetSymbol() else None
            info["assignment"] = math(assignment, self.math_render)
            info["units"] = derived_units(assignment)

            initial_assignments.append(info)

        values["assignments"] = initial_assignments if len(initial_assignments) > 0 else None

        # rules
        rules = []
        rule: libsbml.Rule
        for rule in self.model.getListOfRules():
            info = self.sbase_dict(rule)
            info["sid"] = rule.getVariable() if rule.isSetVariable() else None
            info["assignment"] = math(rule, self.math_render)
            info["units"] = derived_units(rule)

            rules.append(info)

        values["rules"] = rules if len(rules) > 0 else None

        return values

    @classmethod
    def sbase_dict(cls, sbase: libsbml.SBase) -> Dict[str, Any]:
        """Info dictionary for SBase.

        :param sbase: SBase instance for which info dictionary is to be created
        :return info dictionary for item
        """

        d = {
            "id": sbase.getId() if sbase.isSetId() else None,
            "name": sbase.getName() if sbase.isSetName() else None,
            "metaId": sbase.getMetaId() if sbase.isSetMetaId() else None,
            "sbo": sbo(sbase),
            "notes": sbase.getNotesString() if sbase.isSetNotes() else None,
            "annotation": cls.annotation_info(sbase),
        }

        # see specification 6.6
        # FIXME: add history to all objects (see supported methods: createdDate, modifiedDates (list), creators (list)
        history: libsbml.ModelHistory = sbase.getModelHistory()
        history

        # info["history"] = formating.modelHistoryToString(model.getModelHistory()) if model.isSetModelHistory() else None

        # comp
        item_comp = sbase.getPlugin("comp")
        if item_comp and type(item_comp) == libsbml.CompSBasePlugin:
            # ReplacedBy
            if item_comp.isSetReplacedBy():
                replaced_by = item_comp.getReplacedBy()
                submodel_ref = replaced_by.getSubmodelRef()
                d["replacedBy"] = {
                    "submodel_ref": submodel_ref,
                    "replaced_by_sbaseref": sbaseref(replaced_by)
                }
            else:
                d["replaced_by"] = None

            # ListOfReplacedElements
            if item_comp.getNumReplacedElements() > 0:
                replaced_elements = []
                for rep_el in item_comp.getListOfReplacedElements():
                    submodel_ref = rep_el.getSubmodelRef()
                    replaced_elements.append({
                        "submodel_ref": submodel_ref,
                        "replaced_element_sbaseref": sbaseref(rep_el)
                    })

                d["replaced_elements"] = replaced_elements
            else:
                d["replaced_elements"] = None


        # distrib
        sbml_distrib: libsbml.DistribSBasePlugin = sbase.getPlugin("distrib")
        if sbml_distrib and isinstance(sbml_distrib, libsbml.DistribSBasePlugin):
            d["uncertainties"] = []
            for uncertainty in sbml_distrib.getListOfUncertainties():
                u_dict = SBMLModelInfo.sbase_dict(uncertainty)

                u_dict["uncert_parameters"] = []
                upar: libsbml.UncertParameter
                for upar in uncertainty.getListOfUncertParameters():
                    param_dict = {
                        "var": upar.getVar() if upar.isSetVar() else None,
                        "value": upar.getValue() if upar.isSetValue() else None,
                        "units": upar.getUnits() if upar.isSetUnits() else None,
                        "type": upar.getTypeAsString() if upar.isSetType() else None,
                        "definition_url": upar.getDefinitionURL() if upar.isSetDefinitionURL() else None,
                        "math": formating.math(upar.getMath()) if upar.isSetMath() else None
                    }

                    u_dict["uncert_parameters"].append(param_dict)

                d["uncertainties"].append(u_dict)

        return d

    @classmethod
    def annotation_info(cls, sbase: libsbml.SBase) -> Dict:
        """Render dictionary representation of annotation for sbase.

        :param sbase: SBase instance
        """
        if not sbase.isSetAnnotation():
            return {}                   #FIXME: shouldn't this be None?

        d = {}
        cvterms = []
        for kcv in range(sbase.getNumCVTerms()):
            info = {}
            cv = sbase.getCVTerm(kcv)
            q_type = cv.getQualifierType()
            if q_type == libsbml.MODEL_QUALIFIER:
                qualifier = miriam.ModelQualifierType[cv.getModelQualifierType()]
            elif q_type == libsbml.BIOLOGICAL_QUALIFIER:
                qualifier = miriam.BiologicalQualifierType[
                    cv.getBiologicalQualifierType()]
            info["qualifier"] = qualifier

            links = []
            for k in range(cv.getNumResources()):
                uri = cv.getResourceURI(k)
                tokens = uri.split("/")
                resource_id = tokens[-1]
                link = {
                    "resource_id": resource_id,
                    "uri": uri
                }
                links.append(link)
            info["links"] = links

            cvterms.append(info)

        d["cvterms"] = cvterms

        return d

    def info_sbaseref(self, sbref: libsbml.SBaseRef) -> Dict[str, Any]:
        """Info dictionary for SBaseRef.

        :param sbref: SBaseRef instance for which information dictionary is created
        :return: information dictionary for SBaseRef
        """
        info = self.sbase_dict(sbref)

        info["port_ref"] = sbref.getPortRef() if sbref.setPortRef() else None
        info["id_ref"] = sbref.getIdRef() if sbref.isSetIdRef() else None
        info["unit_ref"] = sbref.getUnitRef() if sbref.isSetUnitRef() else None
        info["metaid_ref"] = sbref.getMetaIdRef() if sbref.isSetMetaIdRef() else None
        info["referenced_element"] = {
            "element": type(sbref.getReferencedElement()).__name__,
            "element_id": sbref.getReferencedElement().getId()
        }

        return info

    def info_document(self, doc: libsbml.SBMLDocument) -> Dict[str, str]:
        """Info dictionary for SBaseRef.

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
        packages["plugins"] = plugins if len(plugins) > 0 else None

        info["packages"] = packages
        return info

    def model_dict(self, model: libsbml.Model) -> Dict[str, str]:
        """Info dictionary for SBML Model.

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
            field = f"{key[0].upper()}{key[1:]}"
            if getattr(model, f"isSet{field}")():
                d[key] = getattr(model, f"get{field}")()
            else:
                d[key] = None

        return d

    def info_model_definitions(self) -> Dict:
        """Information dictionaries for comp:ModelDefinitions.

        :return: list of info dictionaries for comp:ModelDefinitions
        """
        data = {}
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
            data["model_defs"] = model_defs if len(model_defs) > 0 else None

            external_model_defs = []
            emd: libsbml.ExternalModelDefinition
            for emd in doc_comp.getListOfExternalModelDefinitions():
                info = self.sbase_dict(emd)
                info["type"] = {
                    "class": type(emd).__name__,
                    "source_code": emd.getSource()
                }
                external_model_defs.append(info)
            data["external_model_defs"] = external_model_defs if len(model_defs) > 0 else None
        else:
            data = None

        return data

    def info_submodels(self) -> Dict:
        """Information dictionaries for comp:Submodels.

        :return: list of info dictionaries for comp:Submodels
        """
        data = {}
        model_comp = self.model.getPlugin("comp")
        if model_comp:
            submodels = []
            submodel: libsbml.Submodel
            for submodel in model_comp.getListOfSubmodels():
                info = self.sbase_dict(submodel)
                info["model_ref"] = submodel.getModelRef() if submodel.isSetModelRef() else None

                deletions = []
                for deletion in submodel.getListOfDeletions():
                    deletions.append(sbaseref(deletion))
                info["deletions"] = deletions if len(deletions) > 0 else None

                info["time_conversion"] = submodel.getTimeConversionFactor() if submodel.isSetTimeConversionFactor() else None
                info["extent_conversion"] = submodel.getExtentConversionFactor() if submodel.isSetExtentConversionFactor() else None

                submodels.append(info)
            data["submodels"] = submodels if len(submodels) > 0 else None
        else:
            data = None
        return data

    def info_ports(self) -> Dict:
        """Information dictionaries for comp:Ports.

        :return: list of info dictionaries for comp:Ports
        """
        data = {}
        model_comp = self.model.getPlugin("comp")
        if model_comp:
            ports = []
            port: libsbml.Port
            for port in model_comp.getListOfPorts():
                info = self.info_sbaseref(port)
                ports.append(info)

            data["ports"] = ports if len(ports) > 0 else None
        else:
            data = None

        return data

    def info_function_definitions(self) -> List:
        """Information dictionaries for FunctionDefinitions.

        :return: list of info dictionaries for FunctionDefinitions
        """
        func_defs = []
        fd: libsbml.FunctionDefinition
        for fd in self.model.getListOfFunctionDefinitions():
            info = self.sbase_dict(fd)
            info["math"] = math(fd, self.math_render)

            func_defs.append(info)

        return func_defs if len(func_defs) > 0 else None

    def unit_definitions_dict(self) -> List:
        """Information dictionaries for UnitDefinitions.

        :return: list of info dictionaries for UnitDefinitions
        """
        unit_defs = []
        ud: libsbml.UnitDefinition
        for ud in self.model.getListOfUnitDefinitions():
            info = self.sbase_dict(ud)
            info["math"] = formating.formula_to_mathml(ud)
            info["unit_terms"] = formating.units_dict(ud)
            unit_defs.append(info)

        return unit_defs if len(unit_defs) > 0 else None

    def info_compartments(self, assignment_map: Dict[str, str]) -> List:
        """Information dictionaries for Compartments.

        :param assignment_map: map of assignments for symbols
        :return: list of info dictionaries for Compartments
        """

        # FIXME: cleanup assignment map
        compartments = []
        c: libsbml.Compartment
        for c in self.model.getListOfCompartments():
            info = self.sbase_dict(c)
            info["spatialDimensions"] = c.getSpatialDimensions() if c.isSetSpatialDimensions() else None

            info["size"] = c.size if c.isSetSize() else math(assignment_map.get(c.id, ""), self.math_render)
            info["units"] = derived_units(c)
            info["constant"] = c.getConstant() if c.isSetConstant() else None

            compartments.append(info)

        return compartments

    def info_species(self) -> List:
        """Information dictionaries for Species.

        :return: list of info dictionaries for Species
        """

        species = []
        s: libsbml.Species
        for s in self.model.getListOfSpecies():
            info = self.sbase_dict(s)
            info["compartment"] = s.getCompartment() if s.isSetCompartment() else None
            info["has_only_substance_units"] = s.getHasOnlySubstanceUnits() if s.isSetHasOnlySubstanceUnits() else None
            info["boundary_condition"] = s.getBoundaryCondition() if s.isSetBoundaryCondition() else None
            info["constant"] = s.getConstant() if s.isSetConstant() else None
            info["initial_amount"] = s.getInitialAmount() if s.isSetInitialAmount() else None
            info["initial_concentration"] = s.getInitialConcentration() if s.isSetInitialConcentration() else None
            info["substance_units"] = s.getSubstanceUnits() if s.isSetSubstanceUnits() else None
            info["units"] = derived_units(s)

            if s.isSetConversionFactor():
                cf_sid = s.getConversionFactor()
                cf_p: libsbml.Parameter = self.model.getParameter(cf_sid)
                cf_value = cf_p.getValue()
                cf_units = cf_p.getUnits()

                info["conversion_factor"] = {
                    "sid": cf_sid,
                    "value": cf_value,
                    "units": cf_units
                }
            else:
                info["conversion_factor"] = None

            # fbc
            sfbc = s.getPlugin("fbc")
            info["fbc"] = {
                "formula": sfbc.getChemicalFormula() if sfbc.isSetChemicalFormula() else None,
                "charge": sfbc.getCharge() if sfbc.isSetCharge() and sfbc.getCharge() != 0 else None,
            } if sfbc else None

            species.append(info)

        return species if len(species) > 0 else None


    def info_gene_products(self) -> Dict:
        """Information dictionaries for GeneProducts.

        :return: list of info dictionaries for Reactions
        """
        data = {}

        model_fbc: libsbml.FbcModelPlugin = self.model.getPlugin("fbc")
        if model_fbc:
            gene_products = []
            gp: libsbml.GeneProduct
            for gp in model_fbc.getListOfGeneProducts():
                info = self.sbase_dict(gp)
                info["label"] = gp.getLabel() if gp.isSetLabel() else None
                info["associated_species"] = gp.getAssociatedSpecies() if gp.isSetAssociatedSpecies() else None

                gene_products.append(info)
            data["gene_products"] = gene_products if len(gene_products) > 0 else None
        else:
            data = None

        return data

    def info_parameters(self, assignment_map: Dict[str, str]) -> List:
        """Information dictionaries for Parameters.

        :param assignment_map: map of assignments for symbols
        :return: list of info dictionaries for Reactions
        """

        parameters = []
        p: libsbml.Parameter
        for p in self.model.getListOfParameters():
            info = self.sbase_dict(p)
            if p.isSetValue():
                value = p.getValue()
            else:
                value_formula = assignment_map.get(p.getId(), None)
                if value_formula is None:
                    warnings.warn(
                        f"No value for parameter via Value, InitialAssignment or "
                        f"AssignmentRule: {p.getId()}"
                    )
                value = math(value_formula, self.math_render)
            info["value"] = value
            info["units"] = derived_units(p)
            info["constant"] = p.getConstant() if p.isSetConstant() else None
            parameters.append(info)

        return parameters if len(parameters) > 0 else None


    def info_initial_assignments(self) -> List:
        """Information dictionaries for InitialAssignments.

        :return: list of info dictionaries for InitialAssignments
        """
        data = {}

        assignments = []
        assignment: libsbml.InitialAssignment
        for assignment in self.model.getListOfInitialAssignments():
            info = self.sbase_dict(assignment)
            info["symbol"] = assignment.getSymbol() if assignment.isSetSymbol() else None
            info["assignment"] = math(assignment, self.math_render)
            info["units"] = derived_units(assignment)
            assignments.append(info)

        return assignments if len(assignments) > 0 else None


    def info_rules(self) -> List:
        """Information dictionaries for Rules.

        :return: list of info dictionaries for Rules
        """

        rules = []
        rule: libsbml.Rule
        for rule in self.model.getListOfRules():
            info = self.sbase_dict(rule)
            info["variable"] = formating.rule_variable_to_string(rule)
            info["assignment"] = math(rule, self.math_render)
            info["units"] = derived_units(rule)

            rules.append(info)

        return rules if len(rules) > 0 else None


    def info_constraints(self) -> List:
        """Information dictionaries for Constraints.

        :return: list of info dictionaries for Constraints
        """

        constraints = []
        constraint: libsbml.Constraint
        for constraint in self.model.getListOfConstraints():
            info = self.sbase_dict(constraint)
            info["constraint"] = math(constraint, self.math_render)
            constraints.append(info)

        return constraints if len(constraints) > 0 else None


    def info_reactions(self) -> List:
        """Information dictionaries for ListOfReactions.

        :return: list of info dictionaries for Reactions
        """

        reactions = []
        r: libsbml.Reaction
        for r in self.model.getListOfReactions():
            info = self.sbase_dict(r)
            info["reversible"] = r.getReversible() if r.isSetReversible() else None
            info["equation"] = formating.equation_from_reaction(r)
            info["modifiers"] = [mod.getSpecies() for mod in r.getListOfModifiers()]
            info["kinetic_law"] = {
                "formula": math(r.getKineticLaw(), self.math_render),
                "units": derived_units(r.getKineticLaw())
            } if r.isSetKineticLaw() else None

            # fbc
            rfbc = r.getPlugin("fbc")
            info["fbc"] = {
                "bounds": formating.boundsDictFromReaction(r, self.model),
                "gpa": formating.geneProductAssociationDictFromReaction(r)
            } if rfbc else None

            reactions.append(info)

        return reactions if len(reactions) > 0 else None


    def info_objectives(self) -> List:
        """Information dictionaries for Objectives.

        :return: list of info dictionaries for Objectives
        """

        model_fbc: libsbml.FbcModelPlugin = self.model.getPlugin("fbc")
        if model_fbc:
            objectives = []
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
                info["flux_objectives"] = flux_objectives if len(flux_objectives) > 0 else None

                objectives.append(info)

            return objectives if len(objectives) > 0 else None
        else:
            return None


    def info_events(self) -> List:
        """Information dictionaries for Events.

        :return: list of info dictionaries for Events
        """

        events = []
        event: libsbml.Event
        for event in self.model.getListOfEvents():
            info = self.sbase_dict(event)

            trigger = event.getTrigger()
            info["trigger"] = {
                "math": math(trigger, self.math_render),
                "initial_value": trigger.initial_value,
                "persistent": trigger.persistent
            }

            info["priority"] = event.getPriority() if event.isSetPriority() else None
            info["delay"] = event.getDelay() if event.isSetDelay() else None

            assignments = []
            for eva in event.getListOfEventAssignments():
                assignments.append({
                    "id": eva.getId(),
                    "meth": math(eva, self.math_render)
                })

            info["assignments"] = assignments if len(assignments) > 0 else None

            events.append(info)

        return events if len(events) > 0 else None


if __name__ == "__main__":
    from pathlib import Path

    output_dir = Path(__file__).parent / "test"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    print("-" * 80)
    from src.sbmlutils.test import REPRESSILATOR_SBML
    info = SBMLModelInfo.from_sbml(REPRESSILATOR_SBML)
    json_str = info.to_json()
    print(info)
    print("-" * 80)
    print(str(info))
    print("-" * 80)
    print(json_str)
    print("-" * 80)

    with open(output_dir / "test_json.json", "w") as fout:
        fout.write(json_str)

