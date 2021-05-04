"""Creates dictionary of information for given model.

The model dictionary can be used for rendering the HTML report.
The information can be serialized to JSON for later rendering in web app.
"""


import warnings
from typing import Any, Dict, List

import libsbml

from sbmlutils.report import formating
from sbmlutils.report.formating import (
    annotation_to_list,
    boolean,
    cvterm,
    derived_units,
    empty_html,
    id_html,
    math,
    metaid,
    notes,
    sbaseref,
    sbo,
)


class SBMLModelInfo:
    """Class for collecting model information for report.

    The information can be accessed via the 'info' attribute.
    """

    def __init__(
        self,
        doc: libsbml.SBMLDocument,
        model: libsbml.Model,
        math_render: str = "cmathml",
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

    def create_info(self) -> Dict[str, Any]:
        """Create information dictionary for report rendering."""
        values = self._create_assignment_map()
        d = {
            "values": values,
            # core
            "doc": self.info_document(doc=self.doc),
            "model": self.info_model(model=self.model),
            "units": self.info_unit_definitions(),
            "functions": self.info_function_definitions(),
            "compartments": self.info_compartments(values),
            "species": self.info_species(),
            "parameters": self.info_parameters(values),
            "assignments": self.info_initial_assignments(),
            "rules": self.info_rules(),
            "reactions": self.info_reactions(),
            "constraints": self.info_constraints(),
            "events": self.info_events(),
            # comp
            "modeldefs": self.info_model_definitions(),
            "submodels": self.info_submodels(),
            "ports": self.info_ports(),
            # fbc
            "geneproducts": self.info_gene_products(),
            "objectives": self.info_objectives(),
        }
        return d

    def _create_assignment_map(self) -> Dict[str, str]:
        """Create dictionary of symbols:assignment for symbols in model.

        This allows to lookup assignments for a given variable.

        :return: assignment dictionary for model
        """
        values = dict()

        # initial assignments
        assignment: libsbml.InitialAssignment
        for assignment in self.model.getListOfInitialAssignments():
            sid = assignment.getSymbol()
            values[sid] = assignment
        # rules
        rule: libsbml.Rule
        for rule in self.model.getListOfRules():
            sid = rule.getVariable()
            values[sid] = rule

        return values

    @staticmethod
    def info_sbase(sbase: libsbml.SBase) -> Dict[str, Any]:
        """Info dictionary for SBase.

        :param sbase: SBase instance for which info dictionary is to be created
        :return info dictionary for item
        """
        info = {
            "object": sbase,
            "id": sbase.getId(),
            "metaId": metaid(sbase),
            "sbo": sbo(sbase),
            "cvterm": cvterm(sbase),
            "notes": notes(sbase),
            "annotation": annotation_to_list(sbase),
        }

        if sbase.isSetName():
            name = sbase.name
        else:
            name = empty_html()
        info["name"] = name
        info["id_html"] = id_html(sbase)

        # comp
        item_comp = sbase.getPlugin("comp")
        if item_comp and type(item_comp) == libsbml.CompSBasePlugin:
            # ReplacedBy
            if item_comp.isSetReplacedBy():
                replaced_by = item_comp.getReplacedBy()
                submodel_ref = replaced_by.getSubmodelRef()
                info["replaced_by"] = {
                    "submodel_ref": submodel_ref,
                    "replaced_by_sbaseref": sbaseref(replaced_by)
                }

            # ListOfReplacedElements
            if item_comp.getNumReplacedElements() > 0:
                replaced_elements = []
                for rep_el in item_comp.getListOfReplacedElements():
                    submodel_ref = rep_el.getSubmodelRef()
                    replaced_elements.append({
                        "submodel_ref": submodel_ref,
                        "replaced_element_sbaseref": sbaseref(rep_el)
                    })

                info["replaced_elements"] = replaced_elements

        # distrib
        sbml_distrib: libsbml.DistribSBasePlugin = sbase.getPlugin("distrib")
        if sbml_distrib and isinstance(sbml_distrib, libsbml.DistribSBasePlugin):
            info["uncertainties"] = []

            for uncertainty in sbml_distrib.getListOfUncertainties():
                u_dict = SBMLModelInfo.info_sbase(uncertainty)

                u_dict["uncert_parameters"] = []

                upar: libsbml.UncertParameter
                for upar in uncertainty.getListOfUncertParameters():
                    param_dict = {}
                    if upar.isSetVar():
                        param_dict["var"] = upar.getVar()
                    if upar.isSetValue():
                        param_dict["value"] = upar.getValue()
                    if upar.isSetUnits():
                        param_dict["units"] = upar.getUnits()
                    if upar.isSetType():
                        param_dict["type"] = upar.getTypeAsString()
                    if upar.isSetDefinitionURL():
                        param_dict["definition_url"] = upar.getDefinitionURL()
                    if upar.isSetMath():
                        param_dict["math"] = formating.math(upar.getMath())

                    u_dict["uncert_parameters"].append(param_dict)

                info["uncertainties"].append(u_dict)

        return info

    def info_sbaseref(self, sbref: libsbml.SBaseRef) -> Dict[str, Any]:
        """Info dictionary for SBaseRef.

        :param sbref: SBaseRef instance for which information dictionary is created
        :return: information dictionary for SBaseRef
        """
        info = self.info_sbase(sbref)
        port_ref = ""
        if sbref.isSetPortRef():
            port_ref = sbref.getPortRef()
        info["port_ref"] = port_ref
        id_ref = ""
        if sbref.isSetIdRef():
            id_ref = sbref.getIdRef()
        info["id_ref"] = id_ref
        unit_ref = ""
        if sbref.isSetUnitRef():
            unit_ref = sbref.getUnitRef()
        info["unit_ref"] = unit_ref
        metaid_ref = ""
        if sbref.isSetMetaIdRef():
            metaid_ref = sbref.getMetaIdRef()
        info["metaid_ref"] = metaid_ref
        element = sbref.getReferencedElement()
        info["referenced_element"] = {
            "element": type(element).__name__,
            "element_id": element.getId()
        }

    def info_document(self, doc: libsbml.SBMLDocument) -> Dict[str, str]:
        """Info dictionary for SBaseRef.

        :param doc: SBMLDocument
        :return: information dictionary for SBMLDocument
        """
        info = self.info_sbase(doc)
        packages = {}
        packages["document"] = {
            "level": doc.getLevel(),
            "version": doc.getVersion()
        }
        packages["plugins"] = []
        for k in range(doc.getNumPlugins()):
            plugin = doc.getPlugin(k)
            prefix = plugin.getPrefix()
            version = plugin.getPackageVersion()
            packages["plugins"].append({
                "prefix": prefix,
                "version": version
            })
        info["packages"] = packages
        return info

    def info_model(self, model: libsbml.Model) -> Dict[str, str]:
        """Info dictionary for SBML Model.

        :param model: Model
        :return: information dictionary for Model
        """
        info = self.info_sbase(model)
        # FIXME: add history to all objects
        info["history"] = formating.modelHistoryToString(model.getModelHistory())

        return info

    def info_model_definitions(self) -> List[Dict[str, Any]]:
        """Information dictionaries for comp:ModelDefinitions.

        :return: list of info dictionaries for comp:ModelDefinitions
        """
        data = []
        doc_comp: libsbml.CompSBMLDocumentPlugin = self.doc.getPlugin("comp")
        if doc_comp:
            md: libsbml.ModelDefinition
            for md in doc_comp.getListOfModelDefinitions():
                info = self.info_sbase(md)
                info["type"] = {
                    "class": type(md).__name__
                }
                data.append(info)
            emd: libsbml.ExternalModelDefinition
            for emd in doc_comp.getListOfExternalModelDefinitions():
                info = self.info_sbase(emd)
                info["type"] = {
                    "class": type(emd).__name__,
                    "source_code": emd.getSource
                }
                data.append(info)
        return data

    def info_submodels(self) -> List[Dict[str, Any]]:
        """Information dictionaries for comp:Submodels.

        :return: list of info dictionaries for comp:Submodels
        """
        data = []
        model_comp = self.model.getPlugin("comp")
        if model_comp:
            submodel: libsbml.Submodel
            for submodel in model_comp.getListOfSubmodels():
                info = self.info_sbase(submodel)
                info["model_ref"] = submodel.getModelRef()

                deletions = []
                for deletion in submodel.getListOfDeletions():
                    deletions.append(sbaseref(deletion))

                info["deletions"] = deletions

                time_conversion = ""
                if submodel.isSetTimeConversionFactor():
                    time_conversion = submodel.getTimeConversionFactor()
                info["time_conversion"] = time_conversion

                extent_conversion = ""
                if submodel.isSetExtentConversionFactor():
                    extent_conversion = submodel.getExtentConversionFactor()
                info["extent_conversion"] = extent_conversion
                data.append(info)
        return data

    def info_ports(self) -> List[Dict[str, Any]]:
        """Information dictionaries for comp:Ports.

        :return: list of info dictionaries for comp:Ports
        """
        data = []
        model_comp = self.model.getPlugin("comp")
        if model_comp:
            port: libsbml.Port
            for port in model_comp.getListOfPorts():
                info = self.info_sbaseref(port)
                data.append(info)
        return data

    def info_function_definitions(self) -> List[Dict[str, Any]]:
        """Information dictionaries for FunctionDefinitions.

        :return: list of info dictionaries for FunctionDefinitions
        """
        data = []
        fd: libsbml.FunctionDefinition
        for fd in self.model.getListOfFunctionDefinitions():
            info = self.info_sbase(fd)
            info["math"] = math(fd, self.math_render)
            data.append(info)
        return data

    def info_unit_definitions(self) -> List[Dict[str, Any]]:
        """Information dictionaries for UnitDefinitions.

        :return: list of info dictionaries for UnitDefinitions
        """
        data = []
        ud: libsbml.UnitDefinition
        for ud in self.model.getListOfUnitDefinitions():
            info = self.info_sbase(ud)
            info["units"] = {
                "math": formating.formula_to_mathml(
                    formating.unitDefinitionToString(ud)
                ),
                "unit_definition": formating.unit_definitions_dict(ud)
            }
            data.append(info)
        return data

    def info_compartments(self, assignment_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """Information dictionaries for Compartments.

        :param assignment_map: map of assignments for symbols
        :return: list of info dictionaries for Compartments
        """
        data = []
        c: libsbml.Compartment
        for c in self.model.getListOfCompartments():
            info = self.info_sbase(c)
            info["units"] = c.units
            if c.isSetSpatialDimensions():
                spatial_dimensions = c.spatial_dimensions
            else:
                spatial_dimensions = empty_html()
            info["spatial_dimensions"] = spatial_dimensions
            info["constant"] = boolean(c.constant)
            info["derived_units"] = derived_units(c)
            if c.isSetSize():
                size = c.size
            else:
                size = math(assignment_map.get(c.id, ""), self.math_render)
            info["size"] = size
            data.append(info)
        return data

    def info_species(self) -> List[Dict[str, Any]]:
        """Information dictionaries for Species.

        :return: list of info dictionaries for Species
        """
        data = []
        s: libsbml.Species
        for s in self.model.getListOfSpecies():
            info = self.info_sbase(s)
            info["compartment"] = s.compartment
            info["has_only_substance_units"] = boolean(s.has_only_substance_units)
            info["boundary_condition"] = boolean(s.boundary_condition)
            info["constant"] = boolean(s.constant)
            if s.isSetInitialAmount():
                initial_amount = s.initial_amount
            else:
                initial_amount = empty_html()
            info["initial_amount"] = initial_amount
            if s.isSetInitialConcentration():
                initial_concentration = s.initial_concentration
            else:
                initial_concentration = empty_html()
            info["initial_concentration"] = initial_concentration
            info["units"] = s.getUnits()
            info["substance_units"] = s.substance_units
            info["derived_units"] = derived_units(s)

            if s.isSetConversionFactor():
                cf_sid = s.getConversionFactor()
                cf_p: libsbml.Parameter = self.model.getParameter(cf_sid)
                cf_value = cf_p.getValue()
                cf_units = cf_p.getUnits()

                info["conversion_factor"] = {
                    "cf_sid": cf_sid,
                    "cf_value": cf_value,
                    "cf_units": cf_units
                }
            else:
                info["conversion_factor"] = ""

            # fbc
            sfbc = s.getPlugin("fbc")
            if sfbc:
                if sfbc.isSetChemicalFormula():
                    info["fbc_formula"] = sfbc.getChemicalFormula()
                if sfbc.isSetCharge():
                    c = sfbc.getCharge()
                    if c != 0:
                        info["fbc_charge"] = sfbc.getCharge()
                if ("fbc_formula" in info) or ("fbc_charge" in info):
                    info["fbc"] = {
                        "fbc_formula": info.get('fbc_formula', ''),
                        "fbc_charge": info.get('fbc_charge', '')
                    }
            data.append(info)
        return data

    def info_gene_products(self) -> List[Dict[str, Any]]:
        """Information dictionaries for GeneProducts.

        :return: list of info dictionaries for Reactions
        """
        data = []
        model_fbc: libsbml.FbcModelPlugin = self.model.getPlugin("fbc")
        if model_fbc:
            gp: libsbml.GeneProduct
            for gp in model_fbc.getListOfGeneProducts():
                info = self.info_sbase(gp)
                info["label"] = gp.label
                associated_species = empty_html()
                if gp.isSetAssociatedSpecies():
                    associated_species = gp.associated_species
                info["associated_species"] = associated_species
                data.append(info)
        return data

    def info_parameters(self, assignment_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """Information dictionaries for Parameters.

        :param assignment_map: map of assignments for symbols
        :return: list of info dictionaries for Reactions
        """
        data = []
        p: libsbml.Parameter
        for p in self.model.getListOfParameters():
            info = self.info_sbase(p)
            info["units"] = p.units
            if p.isSetValue():
                value = p.value
            else:
                value_formula = assignment_map.get(p.id, None)
                if value_formula is None:
                    warnings.warn(
                        f"No value for parameter via Value, InitialAssignment or "
                        f"AssignmentRule: {p.id}"
                    )
                value = math(value_formula, self.math_render)
            info["value"] = value
            info["derived_units"] = derived_units(p)
            info["constant"] = boolean(p.constant)
            data.append(info)
        return data

    def info_initial_assignments(self) -> List[Dict[str, Any]]:
        """Information dictionaries for InitialAssignments.

        :return: list of info dictionaries for InitialAssignments
        """
        data = []
        assignment: libsbml.InitialAssignment
        for assignment in self.model.getListOfInitialAssignments():
            info = self.info_sbase(assignment)
            info["symbol"] = assignment.symbol
            info["assignment"] = math(assignment, self.math_render)
            info["derived_units"] = derived_units(assignment)
            data.append(info)
        return data

    def info_rules(self) -> List[Dict[str, Any]]:
        """Information dictionaries for Rules.

        :return: list of info dictionaries for Rules
        """
        data = []
        for rule in self.model.getListOfRules():
            info = self.info_sbase(rule)
            info["variable"] = formating.ruleVariableToString(rule)
            info["assignment"] = math(rule, self.math_render)
            info["derived_units"] = derived_units(rule)

            data.append(info)
        return data

    def info_constraints(self) -> List[Dict[str, Any]]:
        """Information dictionaries for Constraints.

        :return: list of info dictionaries for Constraints
        """
        data = []
        constraint: libsbml.Constraint
        for constraint in self.model.getListOfConstraints():
            info = self.info_sbase(constraint)
            info["constraint"] = math(constraint, self.math_render)
            data.append(info)

        return data

    def info_reactions(self) -> List[Dict[str, Any]]:
        """Information dictionaries for ListOfReactions.

        :return: list of info dictionaries for Reactions
        """
        data = []
        r: libsbml.Reaction
        for r in self.model.getListOfReactions():
            info = self.info_sbase(r)
            info["reversible"] = r.reversible
            info["equation"] = formating.equationStringFromReaction(r)

            modifiers = [mod.getSpecies() for mod in r.getListOfModifiers()]
            info["modifiers"] = modifiers

            klaw = r.getKineticLaw()
            info["formula"] = math(klaw, self.math_render)
            info["derived_units"] = derived_units(klaw)

            # fbc
            info["fbc_bounds"] = formating.boundsStringFromReaction(r, self.model)
            info["fbc_gpa"] = formating.geneProductAssociationStringFromReaction(r)
            data.append(info)

        return data

    def info_objectives(self) -> List[Dict[str, Any]]:
        """Information dictionaries for Objectives.

        :return: list of info dictionaries for Objectives
        """
        data = []
        model_fbc: libsbml.FbcModelPlugin = self.model.getPlugin("fbc")
        if model_fbc:
            objective: libsbml.Objective
            for objective in model_fbc.getListOfObjectives():
                info = self.info_sbase(objective)
                info["type"] = objective.getType()

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
                        "reaction": f_obj.getReaction()
                    }
                    flux_objectives.append(part)
                info["flux_objectives"] = flux_objectives
                data.append(info)
        return data

    def info_events(self) -> List[Dict[str, Any]]:
        """Information dictionaries for Events.

        :return: list of info dictionaries for Events
        """
        data = []
        event: libsbml.Event
        for event in self.model.getListOfEvents():
            info = self.info_sbase(event)

            trigger = event.getTrigger()
            info["trigger"] = {
                "math": math(trigger, self.math_render),
                "initial_value": trigger.initial_value,
                "persistent": trigger.persistent
            }

            priority = ""
            if event.isSetPriority():
                priority = event.getPriority()
            info["priority"] = priority

            delay = ""
            if event.isSetDelay():
                delay = event.getDelay()
            info["delay"] = delay

            assignments = []
            for eva in event.getListOfEventAssignments():
                assignments.append({
                    "id": eva.getId(),
                    "meth": math(eva, self.math_render)
                })

            info["assignments"] = assignments
            data.append(info)
        return data
