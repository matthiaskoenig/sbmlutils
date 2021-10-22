"""Creates dictionary of information for given model.

The model dictionary can be used for rendering the HTML report.
The information can be serialized to JSON for later rendering in web app.
"""
import hashlib
import json
import pprint
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import libsbml
import numpy as np

from sbmlutils.io import read_sbml
from sbmlutils.metadata.miriam import BiologicalQualifierType, ModelQualifierType
from sbmlutils.report.mathml import astnode_to_latex, symbol_to_latex
from sbmlutils.report.units import udef_to_string


def _get_sbase_attribute(sbase: libsbml.SBase, key: str) -> Optional[Any]:
    """Get SBase attribute."""
    key = f"{key[0].upper()}{key[1:]}"
    if getattr(sbase, f"isSet{key}")():
        return getattr(sbase, f"get{key}")()
    else:
        return None


def clean_empty(d: Union[Dict, List, str]) -> Union[Dict, List, str]:
    """Remove empty fields from JSON.

    Reducing to core information.
    """
    if isinstance(d, dict):
        return {k: v for k, v in ((k, clean_empty(v)) for k, v in d.items()) if v}
    if isinstance(d, list):
        return [v for v in map(clean_empty, d) if v]
    return d


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
    def from_sbml(source: Union[Path, str]) -> "SBMLDocumentInfo":
        """Read model info from SBML."""
        doc: libsbml.SBMLDocument = read_sbml(source)
        return SBMLDocumentInfo(doc=doc)

    def __repr__(self) -> str:
        """Get string representation."""
        return f"SBMLInfo({self.doc})"

    def __str__(self) -> str:
        """Get string."""
        return pprint.pformat(self.info, indent=2)

    def to_json(self, strip: bool = True, indent: int = 2) -> str:
        """Serialize to JSON representation."""
        d = self.info
        if strip:
            d = clean_empty(d)  # type: ignore
        return json.dumps(d, indent=indent)

    def create_info(self) -> Dict[str, Any]:
        """Create information dictionary for report rendering."""

        model: Optional[Dict[str, Any]]
        if self.doc.isSetModel():
            model = self.model_dict(self.doc.getModel())
        else:
            model = None

        d = {
            "doc": self.document(doc=self.doc),
            "model": model,
            **self.model_definitions(),
        }

        return d

    def model_dict(
        self, model: Union[libsbml.Model, libsbml.ModelDefinition]
    ) -> Dict[str, Any]:
        """Create information for a given model."""
        assignments = self._create_assignment_map(model=model)
        ports = self._create_port_map(model=model)

        self.maps = {
            "assignments": assignments,
            "ports": ports,
        }

        rules = self.rules(model=model)
        d = {
            # sbml model information
            **self.model(model=model),
            # core
            "functionDefinitions": self.function_definitions(model=model),
            "unitDefinitions": self.unit_definitions(model=model),
            "compartments": self.compartments(model=model, assignments=assignments),
            "species": self.species(model=model, assignments=assignments),
            "parameters": self.parameters(model=model, assignments=assignments),
            "initialAssignments": self.initial_assignments(model=model),
            "assignmentRules": rules["assignmentRules"],
            "rateRules": rules["rateRules"],
            "algebraicRules": rules["algebraicRules"],
            "constraints": self.constraints(model=model),
            "reactions": self.reactions(model=model),
            "events": self.events(model=model),
            # comp
            "submodels": self.submodels(model=model),
            "ports": self.ports(model=model),
            # fbc
            "geneProducts": self.gene_products(model=model),
            "objectives": self.objectives(model=model),
        }
        # add crosslinks
        self.add_compartment_links(d["compartments"], d["species"], d["reactions"])
        self.add_species_links(d["species"], d["reactions"])

        return d

    def add_compartment_links(
        self,
        compartments: List[Dict[str, Any]],
        species: List[Dict[str, Any]],
        reactions: List[Dict[str, Any]],
    ) -> None:
        """Add species and reaction links to compartment."""
        c_map = {c["id"]: c for c in compartments}
        for c in compartments:
            c["species"] = []
            c["reactions"] = []
        for s in species:
            cid = s["compartment"]
            if cid:
                c_map[cid]["species"].append(s["pk"])
        for r in reactions:
            cid = r["compartment"]
            if cid:
                c_map[cid]["reactions"].append(r["pk"])

    def add_species_links(
        self, species: List[Dict[str, Any]], reactions: List[Dict[str, Any]]
    ) -> None:
        """Add reaction links to species."""
        s_map = {s["id"]: s for s in species}
        for s in species:
            s["reactant"] = []
            s["product"] = []
            s["modifier"] = []

        for r in reactions:
            for item in r["listOfReactants"]:
                sid = item["species"]
                if sid:
                    s_map[sid]["reactant"].append(r["pk"])
            for item in r["listOfProducts"]:
                sid = item["species"]
                if sid:
                    s_map[sid]["product"].append(r["pk"])
            for sid in r["listOfModifiers"]:
                if sid:
                    s_map[sid]["modifier"].append(r["pk"])

    @staticmethod
    def _sbaseref(sbaseref: libsbml.SBaseRef) -> Optional[Dict]:
        """Format the SBaseRef instance.

        Used to figure out the type of the SBaseRef.

        :param sbaseref: SBaseRef instance
        :return: Dictionary containing formatted SBaseRef instance's data
        """

        if sbaseref.isSetPortRef():
            return {"type": "port_ref", "value": sbaseref.getPortRef()}
        elif sbaseref.isSetIdRef():
            return {"type": "id_ref", "value": sbaseref.getIdRef()}
        elif sbaseref.isSetUnitRef():
            return {"type": "unit_ref", "value": sbaseref.getUnitRef()}
        elif sbaseref.isSetMetaIdRef():
            return {"type": "metaId_ref", "value": sbaseref.getMetaIdRef()}
        return None

    def _create_port_map(self, model: libsbml.Model) -> Dict:
        """Create dictionary of symbols:port for symbols in model.

        This allows to lookup port for a given Sbase.

        :return: port dictionary for model
        """
        ports: Dict[str, Dict] = {}
        port: libsbml.Port
        comp_model: libsbml.CompModelPlugin = model.getPlugin("comp")
        if comp_model:
            for port in comp_model.getListOfPorts():
                port_info = self.sbaseref_dict(port)
                if port.isSetIdRef():
                    ports[port.getIdRef()] = port_info
                elif port.isSetUnitRef():
                    udef: libsbml.UnitDefinition = model.getUnitDefinition(
                        port.getUnitRef()
                    )
                    # Be careful, this is a different namespace.
                    # I.e. for UnitDefinitions you have to check ports in a different namespace
                    ports[f"units:{udef.getId()}"] = port_info
                elif port.isSetMetaIdRef():
                    metaid = port.getMetaIdRef()
                    sbase: libsbml.SBase = model.getElementByMetaId(metaid)
                    if not sbase:
                        sbase = model.getElementFromPluginsByMetaId(metaid)

                    if sbase.isSetId():
                        ports[sbase.getId()] = port_info

        return ports

    def _create_assignment_map(self, model: libsbml.Model) -> Dict:
        """Create dictionary of symbols:assignment for symbols in model.

        This allows to lookup assignments for a given variable.

        :return: assignment dictionary for model
        """
        assignments: Dict[str, Dict] = {}

        initial_assignment: libsbml.InitialAssignment
        for initial_assignment in model.getListOfInitialAssignments():
            pk_symbol = (
                initial_assignment.getSymbol()
                if initial_assignment.isSetSymbol()
                else None
            )
            if pk_symbol:
                assignments[pk_symbol] = {
                    "pk": self._get_pk(initial_assignment),
                    "id": pk_symbol,
                    "sbmlType": self._sbml_type(initial_assignment),
                }
                math_str = (
                    symbol_to_latex(pk_symbol) + "(0) = "
                    f"{astnode_to_latex(initial_assignment.getMath())}"
                )
                assignments[pk_symbol]["math"] = math_str

        rule: libsbml.Rule
        for rule in model.getListOfRules():
            pk_symbol = rule.getVariable() if rule.isSetVariable() else None
            if pk_symbol:
                assignments[pk_symbol] = {
                    "pk": self._get_pk(rule),
                    "id": pk_symbol,
                    "sbmlType": self._sbml_type(rule),
                }

                math_str = ""
                if assignments[pk_symbol]["sbmlType"] == "AssignmentRule":
                    math_str = (
                        symbol_to_latex(pk_symbol) + " = "
                        f"{astnode_to_latex(rule.getMath()) if rule.isSetMath() else None}"
                    )
                elif assignments[pk_symbol]["sbmlType"] == "RateRule":
                    derivative = "\\frac{d" + symbol_to_latex(pk_symbol) + "}{{dt}}"
                    math_str = f"{derivative} = {astnode_to_latex(rule.getMath()) if rule.isSetMath() else None}"

                assignments[pk_symbol]["math"] = math_str

        return assignments

    @staticmethod
    def _sbml_type(sbase: libsbml.SBase) -> str:
        class_name = str(sbase.__class__)[16:-2]
        return class_name

    @staticmethod
    def _get_pk(sbase: libsbml.SBase) -> str:
        """Calculate primary key."""

        if not hasattr(sbase, "pk"):
            pk: str = f"{SBMLDocumentInfo._sbml_type(sbase)}:"
            if sbase.isSetId():
                pk += sbase.getId()
            elif sbase.isSetMetaId():
                pk += sbase.getMetaId()
            else:
                xml = sbase.toSBML()
                pk += SBMLDocumentInfo._uuid(xml)
            sbase.pk = pk

        return pk

    @staticmethod
    def _uuid(xml: str) -> str:
        """Generate unique identifier.

        SHA1 digest of the identifier (mostly the xml string).
        """
        return str(hashlib.sha1(xml.encode("utf-8")).hexdigest())

    @classmethod
    def sbase_dict(cls, sbase: libsbml.SBase) -> Dict[str, Any]:
        """Info dictionary for SBase.

        :param sbase: SBase instance for which info dictionary is to be created
        :return info dictionary for item
        """
        pk = cls._get_pk(sbase)
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

        # TODO: add the ports information

        if sbase.getTypeCode() in {libsbml.SBML_DOCUMENT, libsbml.SBML_MODEL}:
            d["xml"] = None
        else:
            d["xml"] = sbase.toSBML()

        # comp
        item_comp = sbase.getPlugin("comp")
        if item_comp and type(item_comp) == libsbml.CompSBasePlugin:
            # ReplacedBy
            if item_comp.isSetReplacedBy():
                replaced_by = item_comp.getReplacedBy()
                submodel_ref = replaced_by.getSubmodelRef()
                d["replacedBy"] = {
                    "submodelRef": submodel_ref,
                    "replacedBySbaseref": cls._sbaseref(replaced_by),
                }
            else:
                d["replacedBy"] = None

            # ListOfReplacedElements
            if item_comp.getNumReplacedElements() > 0:
                replaced_elements = []
                for rep_el in item_comp.getListOfReplacedElements():
                    submodel_ref = rep_el.getSubmodelRef()
                    replaced_elements.append(
                        {
                            "submodelRef": submodel_ref,
                            "replacedElementSbaseref": cls._sbaseref(rep_el),
                        }
                    )

                d["replacedElements"] = replaced_elements
            else:
                d["replacedElements"] = None

        # distrib
        sbml_distrib: libsbml.DistribSBasePlugin = sbase.getPlugin("distrib")
        if sbml_distrib and isinstance(sbml_distrib, libsbml.DistribSBasePlugin):
            d["uncertainties"] = []
            for uncertainty in sbml_distrib.getListOfUncertainties():
                u_dict = SBMLDocumentInfo.sbase_dict(uncertainty)

                u_dict["uncertaintyParameters"] = []
                upar: libsbml.UncertParameter
                for upar in uncertainty.getListOfUncertParameters():
                    param_dict = {
                        "var": upar.getVar() if upar.isSetVar() else None,
                        "value": upar.getValue() if upar.isSetValue() else None,
                        "units": upar.getUnits() if upar.isSetUnits() else None,
                        "type": upar.getTypeAsString() if upar.isSetType() else None,
                        "definitionURL": upar.getDefinitionURL()
                        if upar.isSetDefinitionURL()
                        else None,
                        "math": astnode_to_latex(upar.getMath())
                        if upar.isSetMath()
                        else None,
                    }

                    u_dict["uncertaintyParameters"].append(param_dict)

                d["uncertainties"].append(u_dict)

        return d

    def sbaseref_dict(self, sbaseref: libsbml.SBaseRef) -> Dict[str, Any]:
        """Info dictionary for SBaseRef.

        :param sbaseref: SBaseRef instance for which information dictionary is created
        :return: information dictionary for SBaseRef
        """
        d = self.sbase_dict(sbaseref)

        d["portRef"] = sbaseref.getPortRef() if sbaseref.isSetPortRef() else None
        d["idRef"] = sbaseref.getIdRef() if sbaseref.isSetIdRef() else None
        d["unitRef"] = sbaseref.getUnitRef() if sbaseref.isSetUnitRef() else None
        d["metaIdRef"] = sbaseref.getMetaIdRef() if sbaseref.isSetMetaIdRef() else None
        d["referencedElement"] = {
            "element": type(sbaseref.getReferencedElement()).__name__,
            "elementId": sbaseref.getReferencedElement().getId(),
        }

        return d

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
                qualifier = ModelQualifierType[cv.getModelQualifierType()]
            elif q_type == libsbml.BIOLOGICAL_QUALIFIER:
                qualifier = BiologicalQualifierType[cv.getBiologicalQualifierType()]
            else:
                raise ValueError(f"Unsupported qualifier type: '{q_type}'")

            resources = [cv.getResourceURI(k) for k in range(cv.getNumResources())]
            cvterms.append(
                {
                    "qualifier": qualifier,
                    "resources": resources,
                }
            )

        # add SBO term as CVTerm
        if sbase.isSetSBOTerm():
            sbo = sbase.getSBOTermID()
            sbo_in_cvs: bool = False
            for cv in cvterms:
                for resource in cv["resources"]:
                    if sbo in resource:
                        sbo_in_cvs = True
                        break
            if not sbo_in_cvs:
                cvterms = [
                    {
                        "qualifier": "BQB_IS",
                        "resources": [f"https://identifiers.org/{sbo}"],
                    }
                ] + cvterms

        return cvterms

    @classmethod
    def model_history(cls, sbase: libsbml.SBase) -> Optional[Dict]:
        """Parse model history information.

        :return
        """

        if sbase.isSetModelHistory():
            history: libsbml.ModelHistory = sbase.getModelHistory()
        else:
            return None

        creators = []
        for kc in range(history.getNumCreators()):
            c: libsbml.ModelCreator = history.getCreator(kc)
            creators.append(
                {
                    "givenName": c.getGivenName() if c.isSetGivenName() else None,
                    "familyName": c.getFamilyName() if c.isSetFamilyName() else None,
                    "organization": c.getOrganization()
                    if c.isSetOrganization()
                    else None,
                    "email": c.getEmail() if c.isSetEmail() else None,
                }
            )

        created_date = (
            history.getCreatedDate().getDateAsString()
            if history.isSetCreatedDate()
            else None
        )
        modified_dates = []
        for km in range(history.getNumModifiedDates()):
            modified_dates.append(history.getModifiedDate(km).getDateAsString())
        return {
            "creators": creators,
            "createdDate": created_date,
            "modifiedDates": modified_dates,
        }

    def document(self, doc: libsbml.SBMLDocument) -> Dict[str, str]:
        """Info for SBMLDocument.

        :param doc: SBMLDocument
        :return: information dictionary for SBMLDocument
        """
        d = self.sbase_dict(doc)

        packages: Dict[str, Any] = {}
        packages["document"] = {"level": doc.getLevel(), "version": doc.getVersion()}

        plugins: List[Dict[str, Any]] = []
        for k in range(doc.getNumPlugins()):
            plugin: libsbml.SBMLDocumentPlugin = doc.getPlugin(k)
            prefix: str = plugin.getPrefix()
            version: int = plugin.getPackageVersion()
            plugins.append({"prefix": prefix, "version": version})

        packages["plugins"] = plugins

        d["packages"] = packages
        return d

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
        ]:
            d[f"{key}_unit"] = _get_sbase_attribute(model, key)
            d[key] = udef_to_string(d[f"{key}_unit"], model)

        # FIXME: handle analoque to species
        if model.isSetConversionFactor():
            cf_sid = model.getConversionFactor()
            cf_p: libsbml.Parameter = model.getParameter(cf_sid)
            cf_value = cf_p.getValue()
            cf_units = cf_p.getUnits()

            d["conversionFactor"] = {
                "sid": cf_sid,
                "value": cf_value,
                "units": cf_units,
            }
        else:
            d["conversionFactor"] = {}

        return d

    def function_definitions(self, model: libsbml.Model) -> List:
        """Information dictionaries for FunctionDefinitions.

        :return: list of info dictionaries for FunctionDefinitions
        """
        func_defs = []
        fd: libsbml.FunctionDefinition
        for fd in model.getListOfFunctionDefinitions():
            d = self.sbase_dict(fd)
            d["math"] = astnode_to_latex(fd.getMath()) if fd.isSetMath() else None

            func_defs.append(d)

        return func_defs

    def unit_definitions(self, model: libsbml.Model) -> List:
        """Information for UnitDefinitions.

        :return: list of info dictionaries for UnitDefinitions
        """
        unit_defs = []
        ud: libsbml.UnitDefinition
        for ud in model.getListOfUnitDefinitions():
            d = self.sbase_dict(ud)
            d["units"] = udef_to_string(ud)

            key = "units:" + ud.pk.split(":")[-1]
            if key in self.maps["assignments"]:
                d["assignment"] = self.maps["assignments"][key]
            if key in self.maps["ports"]:
                d["port"] = self.maps["ports"][key]

            unit_defs.append(d)

        return unit_defs

    def compartments(
        self, model: libsbml.Model, assignments: Dict[str, Dict[str, str]]
    ) -> List[Dict]:
        """Information for Compartments.

        :return: list of info dictionaries for Compartments
        """

        compartments = []
        c: libsbml.Compartment
        for c in model.getListOfCompartments():
            d = self.sbase_dict(c)
            for key in ["spatialDimensions", "size", "constant"]:
                d[key] = _get_sbase_attribute(c, key)
            if d["size"] is not None and np.isnan(d["size"]):
                # NaN not JSON serializable
                d["size"] = "NaN"

            d["units_sid"] = c.getUnits() if c.isSetUnits() else None
            d["units"] = udef_to_string(d["units_sid"], model)
            d["derivedUnits"] = udef_to_string(c.getDerivedUnitDefinition())

            key = c.pk.split(":")[-1]
            if key in self.maps["assignments"]:
                d["assignment"] = self.maps["assignments"][key]
            if key in self.maps["ports"]:
                d["port"] = self.maps["ports"][key]

            compartments.append(d)

        return compartments

    def species(
        self, model: libsbml.Model, assignments: Dict[str, Dict[str, str]]
    ) -> List[Dict]:
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

            for key in ["initialAmount", "initialConcentration"]:
                if d[key] is not None and np.isnan(d[key]):
                    # NaN not JSON serializable
                    d[key] = "NaN"

            d["units_sid"] = s.getUnits() if s.isSetUnits() else None
            d["units"] = udef_to_string(d["units_sid"], model)
            d["derivedUnits"] = udef_to_string(s.getDerivedUnitDefinition())

            # lookup in maps (PKs are in the form <SBMLType>:<id/metaID/name/etc).
            key = s.pk.split(":")[-1]
            if key in self.maps["assignments"]:
                d["assignment"] = self.maps["assignments"][key]
            if key in self.maps["ports"]:
                d["port"] = self.maps["ports"][key]

            if s.isSetConversionFactor():
                cf_sid = s.getConversionFactor()
                cf_p: libsbml.Parameter = model.getParameter(cf_sid)
                cf_value = cf_p.getValue()
                cf_units = cf_p.getUnits()

                d["conversionFactor"] = {
                    "sid": cf_sid,
                    "value": cf_value,
                    "units": cf_units,
                }
            else:
                d["conversionFactor"] = {}

            # fbc
            sfbc = s.getPlugin("fbc")
            d["fbc"] = (
                {
                    "formula": sfbc.getChemicalFormula()
                    if sfbc.isSetChemicalFormula()
                    else None,
                    "charge": sfbc.getCharge()
                    if (sfbc.isSetCharge() and sfbc.getCharge() != 0)
                    else None,
                }
                if sfbc
                else None
            )

            species.append(d)

        return species

    def parameters(
        self, model: libsbml.Model, assignments: Dict[str, Dict[str, str]]
    ) -> List[Dict]:
        """Information for SBML Parameters.

        :return: list of info dictionaries for Reactions
        """

        parameters = []
        p: libsbml.Parameter
        for p in model.getListOfParameters():
            d = self.sbase_dict(p)

            if p.isSetValue():
                value = p.getValue()
                if np.isnan(value):
                    value = None
            else:
                value = None

            d["value"] = value
            for key in ["value"]:
                if d[key] is not None and np.isnan(d[key]):
                    # NaN not JSON serializable
                    d[key] = "NaN"
            d["constant"] = p.getConstant() if p.isSetConstant() else None
            d["units_sid"] = p.getUnits() if p.isSetUnits() else None
            d["units"] = udef_to_string(d["units_sid"], model)
            d["derivedUnits"] = udef_to_string(p.getDerivedUnitDefinition())

            key = p.pk.split(":")[-1]
            if key in self.maps["assignments"]:
                d["assignment"] = self.maps["assignments"][key]
            if key in self.maps["ports"]:
                d["port"] = self.maps["ports"][key]

            parameters.append(d)

        return parameters

    def initial_assignments(self, model: libsbml.Model) -> List:
        """Information for InitialAssignments.

        :return: list of info dictionaries for InitialAssignments
        """

        assignments = []
        assignment: libsbml.InitialAssignment
        for assignment in model.getListOfInitialAssignments():
            d = self.sbase_dict(assignment)
            d["symbol"] = assignment.getSymbol() if assignment.isSetSymbol() else None
            d["math"] = astnode_to_latex(assignment.getMath())
            d["derivedUnits"] = udef_to_string(assignment.getDerivedUnitDefinition())
            assignments.append(d)

        return assignments

    def rules(self, model: libsbml.Model) -> Dict:
        """Information for Rules.

        :return: list of info dictionaries for Rules
        """

        rules: Dict[str, List] = {
            "assignmentRules": [],
            "rateRules": [],
            "algebraicRules": [],
        }
        rule: libsbml.Rule
        for rule in model.getListOfRules():
            d = self.sbase_dict(rule)
            d["variable"] = self._rule_variable_to_string(rule)
            d["math"] = astnode_to_latex(rule.getMath()) if rule.isSetMath() else None
            d["derivedUnits"] = udef_to_string(rule.getDerivedUnitDefinition())

            type = d["sbmlType"]
            key = f"{type[0].lower()}{type[1:]}s"

            rules[key].append(d)

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

    def constraints(self, model: libsbml.Model) -> List[Dict[str, Any]]:
        """Information for Constraints.

        :return: list of info dictionaries for Constraints
        """

        constraints = []
        constraint: libsbml.Constraint
        for constraint in model.getListOfConstraints():
            d = self.sbase_dict(constraint)
            d["math"] = (
                astnode_to_latex(constraint.getMath())
                if constraint.isSetMath()
                else None
            )
            d["message"] = (
                constraint.getMessage() if constraint.isSetMessage() else None
            )
            constraints.append(d)

        return constraints

    def reactions(self, model: libsbml.Model) -> List[Dict[str, Any]]:
        """Information dictionaries for ListOfReactions.

        :return: list of info dictionaries for Reactions

        -- take a look at local parameter once
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

            klaw: libsbml.KineticLaw = (
                r.getKineticLaw() if r.isSetKineticLaw() else None
            )
            if klaw:
                d_law: Dict[str, Any] = {}
                d_law["math"] = (
                    astnode_to_latex(klaw.getMath()) if klaw.isSetMath() else None
                )
                d_law["derivedUnits"] = udef_to_string(klaw.getDerivedUnitDefinition())

                d_law["localParameters"] = []
                for i in range(len(klaw.getListOfLocalParameters())):
                    lp: libsbml.LocalParameter = klaw.getLocalParameter(i)
                    lpar_info = {
                        "id": lp.getId() if lp.isSetId() else None,
                        "value": lp.getValue() if lp.isSetValue() else None,
                        "units_sid": lp.getUnits() if lp.isSetUnits() else None,
                        "derivedUnits": udef_to_string(lp.getDerivedUnitDefinition()),
                    }
                    lpar_info["units"] = udef_to_string(lpar_info["units_sid"], model)
                    d_law["localParameters"].append(lpar_info)
                d["kineticLaw"] = d_law
            else:
                d["kineticLaw"] = None

            # fbc
            rfbc = r.getPlugin("fbc")
            d["fbc"] = (
                {
                    "bounds": self._bounds_dict_from_reaction(r, model),
                    "gpa": self._gene_product_association_from_reaction(r),
                }
                if rfbc
                else None
            )

            key = r.pk.split(":")[-1]
            if key in self.maps["assignments"]:
                d["assignment"] = self.maps["assignments"][key]
            if key in self.maps["ports"]:
                d["port"] = self.maps["ports"][key]

            reactions.append(d)

        return reactions

    @staticmethod
    def _species_reference(species: libsbml.SpeciesReference) -> Dict[str, Any]:
        """Resolve species reference."""
        return {
            "species": species.getSpecies() if species.isSetSpecies() else None,
            "stoichiometry": species.getStoichiometry()
            if species.isSetStoichiometry()
            else 1.0,
            "constant": species.getConstant() if species.isSetConstant() else None,
        }

    @staticmethod
    def _bounds_dict_from_reaction(
        reaction: libsbml.Reaction, model: libsbml.Model
    ) -> Optional[Dict]:
        """Render string of bounds from the reaction.

        :param reaction: SBML reaction instance
        :param model: SBML model instance
        :return: String of bounds extracted from the reaction
        """
        bounds: Optional[Dict]
        rfbc = reaction.getPlugin("fbc")
        if rfbc is not None:
            # get values for bounds
            lb_id: Optional[str] = None
            ub_id: Optional[str] = None
            lb_value: Optional[float] = None
            ub_value: Optional[float] = None
            if rfbc.isSetLowerFluxBound():
                lb_id = rfbc.getLowerFluxBound()
                lb_p: libsbml.Parameter = model.getParameter(lb_id)
                if lb_p.isSetValue():
                    lb_value = lb_p.getValue()
            if rfbc.isSetUpperFluxBound():
                ub_id = rfbc.getUpperFluxBound()
                ub_p: libsbml.Parameter = model.getParameter(ub_id)
                if ub_p.isSetValue():
                    ub_value = ub_p.getValue()

            bounds = {
                "lowerFluxBound": {
                    "id": lb_id,
                    "value": lb_value,
                },
                "upperFluxBound": {
                    "id": ub_id,
                    "value": ub_value,
                },
            }

        else:
            bounds = None

        return bounds

    @staticmethod
    def _gene_product_association_from_reaction(
        reaction: libsbml.Reaction,
    ) -> Optional[str]:
        """Render string representation of the GeneProductAssociation for given reaction.

        :param reaction: SBML reaction instance
        :return: string representation of GeneProductAssociation
        """

        rfbc = reaction.getPlugin("fbc")
        gpa = (
            str(rfbc.getGeneProductAssociation().getAssociation().toInfix())
            if (rfbc and rfbc.isSetGeneProductAssociation())
            else None
        )

        return gpa

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
            else:
                raise ValueError(f"Half equation could not be generated: '{sr}'")
            items.append(sd)
        return " + ".join(items)

    def events(self, model: libsbml.Model) -> List[Dict[str, Any]]:
        """Information dictionaries for Events.

        :return: list of info dictionaries for Events
        """

        events = []
        event: libsbml.Event
        for event in model.getListOfEvents():
            d = self.sbase_dict(event)

            d["useValuesFromTriggerTime"] = (
                event.getUseValuesFromTriggerTime()
                if event.isSetUseValuesFromTriggerTime()
                else None
            )

            trigger: libsbml.Trigger = (
                event.getTrigger() if event.isSetTrigger() else None
            )
            if trigger:
                d["trigger"] = {
                    "math": astnode_to_latex(trigger.getMath())
                    if trigger.isSetMath()
                    else None,
                    "initialValue": trigger.initial_value,
                    "persistent": trigger.persistent,
                }
            else:
                d["trigger"] = None

            d["priority"] = (
                astnode_to_latex(event.getPriority()) if event.isSetPriority() else None
            )
            delay: libsbml.Delay = event.getDelay() if event.isSetDelay() else None
            if delay:
                d["delay"] = (
                    astnode_to_latex(delay.getMath()) if delay.isSetMath() else None
                )

            assignments = []
            eva: libsbml.EventAssignment
            for eva in event.getListOfEventAssignments():
                assignments.append(
                    {
                        "variable": eva.getVariable() if eva.isSetVariable() else None,
                        "math": astnode_to_latex(eva.getMath())
                        if eva.isSetMath()
                        else None,
                    }
                )
            d["listOfEventAssignments"] = assignments

            events.append(d)

        return events

    # ---------------------------------------------------------------------------------
    # comp
    # ---------------------------------------------------------------------------------
    def model_definitions(self) -> Dict:
        """Information for comp:ModelDefinitions.

        :return: list of info dictionaries for comp:ModelDefinitions
        """
        mds: List[Dict[str, Any]] = []
        emds: List[Dict[str, Any]] = []

        doc_comp: libsbml.CompSBMLDocumentPlugin = self.doc.getPlugin("comp")
        if doc_comp:

            md: libsbml.ModelDefinition
            for md in doc_comp.getListOfModelDefinitions():
                mds.append(self.model_dict(model=md))

            emd: libsbml.ExternalModelDefinition
            for emd in doc_comp.getListOfExternalModelDefinitions():
                d_emd = self.sbase_dict(emd)
                d_emd["modelRef"] = emd.getModelRef() if emd.isSetModelRef() else None
                d_emd["source"] = emd.getSource() if emd.isSetSource() else None
                emds.append(d_emd)

        d: Dict[str, List] = {
            "modelDefinitions": mds,
            "externalModelDefinitions": emds,
        }

        return d

    def submodels(self, model: libsbml.Model) -> List[Dict[str, Any]]:
        """Information dictionaries for comp:Submodels.

        :return: list of info dictionaries for comp:Submodels
        """
        submodels: List[Dict[str, Any]] = []
        model_comp = model.getPlugin("comp")
        if model_comp:
            submodel: libsbml.Submodel
            for submodel in model_comp.getListOfSubmodels():
                d = self.sbase_dict(submodel)
                d["modelRef"] = (
                    submodel.getModelRef() if submodel.isSetModelRef() else None  #
                )

                deletions = []
                for deletion in submodel.getListOfDeletions():
                    deletions.append(self._sbaseref(deletion))
                d["deletions"] = deletions

                d["timeConversion"] = (
                    submodel.getTimeConversionFactor()
                    if submodel.isSetTimeConversionFactor()
                    else None
                )
                d["extentConversion"] = (
                    submodel.getExtentConversionFactor()
                    if submodel.isSetExtentConversionFactor()
                    else None
                )

                submodels.append(d)

        return submodels

    def ports(self, model: libsbml.Model) -> List:
        """Information for comp:Ports.

        :return: list of info dictionaries for comp:Ports
        """

        model_comp = model.getPlugin("comp")
        ports = []
        if model_comp:
            port: libsbml.Port
            for port in model_comp.getListOfPorts():
                d = self.sbaseref_dict(port)
                ports.append(d)

        return ports

    # ---------------------------------------------------------------------------------
    # fbc
    # ---------------------------------------------------------------------------------
    def gene_products(self, model: libsbml.Model) -> List[Dict[str, Any]]:
        """Information dictionaries for GeneProducts.

        :return: list of info dictionaries for Reactions
        """
        gps = []
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        if model_fbc:

            gp: libsbml.GeneProduct
            for gp in model_fbc.getListOfGeneProducts():
                d = self.sbase_dict(gp)
                d["label"] = gp.getLabel() if gp.isSetLabel() else None
                d["associatedSpecies"] = (
                    gp.getAssociatedSpecies() if gp.isSetAssociatedSpecies() else None
                )
                gps.append(d)

        return gps

    def objectives(self, model: libsbml.Model) -> List[Dict[str, Any]]:
        """Information dictionaries for Objectives.

        :return: list of info dictionaries for Objectives
        """

        objectives = []
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        if model_fbc:
            objective: libsbml.Objective
            for objective in model_fbc.getListOfObjectives():
                d = self.sbase_dict(objective)
                d["type"] = objective.getType() if objective.isSetType() else None

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
                        if f_obj.isSetReaction()
                        else None,
                    }
                    flux_objectives.append(part)
                d["fluxObjectives"] = flux_objectives

                objectives.append(d)

        return objectives


if __name__ == "__main__":
    from pathlib import Path

    output_dir = Path(__file__).parent / "test"
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    print("-" * 80)
    from sbmlutils.test import GLUCOSE_SBML

    for source in [
        # COMP_ICG_BODY,
        # COMP_ICG_BODY_FLAT,
        # COMP_ICG_LIVER,
        # COMP_MODEL_DEFINITIONS_SBML,
        # FBC_RECON3D_SBML,
        # FBC_ECOLI_CORE_SBML,
        # DISTRIB_DISTRIBUTIONS_SBML,
        # DISTRIB_UNCERTAINTIES_SBML,
        GLUCOSE_SBML
        # REPRESSILATOR_SBML,
    ]:
        info = SBMLDocumentInfo.from_sbml(source)
        print("-" * 80)
        json_str = info.to_json()
        print(json_str)
        print("-" * 80)

    with open(output_dir / "test.json", "w") as fout:
        fout.write(json_str)

    doc = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    udef = model.getUnitDefinition("dimensionless")
    print("udef", udef)

    print(libsbml.UnitKind_toString(libsbml.UNIT_KIND_DIMENSIONLESS))
    udef = model.getUnitDefinition("metre")
    print("udef", udef)

    print(libsbml.UnitKind_forName("dimensionless"))
    print(libsbml.UnitKind_forName("abc"))
    print(libsbml.UnitKind_toString(libsbml.UNIT_KIND_INVALID))
    print(libsbml.UnitKind_toString(36))
