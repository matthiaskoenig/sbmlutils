# Groups (groups)

Use the SBML [groups package](https://sbml.org/documents/specifications/level-3/version-1/groups/) to describe relationships among existing model elements. The three group kinds are `collection` for elements gathered for a shared purpose, `classification` for members of the same class, and `partonomy` for parts of a whole. These relationships leave the model's mathematics unchanged, so the package is declared with `required="false"`.

Use libSBML to add groups to a model written by the sbmlutils factory. The factory and `sbml_to_model` parser omit group content. Keep the document in libSBML and use [`read_sbml` and `write_sbml`](../io.md) to preserve it. Run the examples on this page in order.

## Create the model and enable groups

The model has a two-step pathway in the cytosol, ATP pools in two compartments, and a rule that reports their combined amount. The rule has a `metaId` so a group can reference it later.

```python
from pathlib import Path

import libsbml

from sbmlutils.factory import (
    AssignmentRule,
    Compartment,
    Model,
    ModelUnits,
    Parameter,
    Reaction,
    Species,
    Units,
    create_model,
)
from sbmlutils.io import read_sbml, write_sbml
from sbmlutils.validation import validate_doc

model = Model(
    sid="cell_pathways",
    model_units=ModelUnits(
        time=Units.second, extent=Units.mole, substance=Units.mole, volume=Units.litre
    ),
    compartments=[
        Compartment("cytosol", value=1.0, unit=Units.litre),
        Compartment("mitochondrion", value=0.1, unit=Units.litre),
    ],
    species=[
        Species(
            sid,
            compartment=compartment,
            initialAmount=amount,
            hasOnlySubstanceUnits=True,
        )
        for sid, compartment, amount in [
            ("A", "cytosol", 1.0),
            ("B", "cytosol", 0.0),
            ("C", "cytosol", 0.0),
            ("ATP_c", "cytosol", 0.002),
            ("ATP_m", "mitochondrion", 0.001),
        ]
    ],
    reactions=[
        Reaction("step1", equation="A -> B"),
        Reaction("step2", equation="B -> C"),
    ],
    parameters=[Parameter("total_atp", unit=Units.mole, constant=False)],
    rules=[
        AssignmentRule(
            "total_atp", "ATP_c + ATP_m", unit=Units.mole, metaId="meta_total_atp_rule"
        ),
    ],
)
result = create_model(model, Path("cell_pathways.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
assert not validate_doc(doc).errors

namespace = libsbml.GroupsExtension.getXmlnsL3V1V1()
doc.enablePackage(namespace, "groups", True)
doc.setPackageRequired("groups", False)
groups = doc.getModel().getPlugin("groups")


def add_group(group_id: str, kind: int, *member_ids: str) -> libsbml.Group:
    """Add a group whose members refer to existing SBML IDs."""
    group = groups.createGroup()
    group.setId(group_id)
    group.setKind(kind)
    for member_id in member_ids:
        group.createMember().setIdRef(member_id)
    return group
```

## Collect pathway reactions

A `collection` gathers elements for a purpose without assigning them a common type or a part-of relation. The `idRef` of each member here identifies an existing reaction by its SBML ID.

```python
pathway = add_group(
    "conversion_pathway", libsbml.GROUP_KIND_COLLECTION, "step1", "step2"
)
```

## Classify ATP pools

A `classification` expresses an is-a relationship. Both species are pools of ATP, although each has its own amount and compartment.

```python
atp_pools = add_group("atp_pools", libsbml.GROUP_KIND_CLASSIFICATION, "ATP_c", "ATP_m")
```

## Describe parts of a cell

A `partonomy` expresses a part-of relationship. Here the cytosol and mitochondrion are both parts of the cell represented by the group. The group leaves compartment sizes and species locations as set in the core model.

```python
cell_parts = add_group(
    "cell_parts", libsbml.GROUP_KIND_PARTONOMY, "cytosol", "mitochondrion"
)
```

## Refer to a rule by `metaIdRef`

Each member uses exactly one reference. Use `idRef` for an element with a model ID and `metaIdRef` for an element identified by its `metaid`. An SBML Level 3 Version 1 assignment rule has no `id`. In this collection, `idRef="total_atp"` identifies the parameter, and `metaIdRef="meta_total_atp_rule"` identifies the rule that calculates it.

```python
atp_report = add_group("atp_report", libsbml.GROUP_KIND_COLLECTION, "total_atp")
atp_report.createMember().setMetaIdRef("meta_total_atp_rule")
```

## Nest groups and save

A group can include another group as a member by referencing its ID. For example, `review` contains the pathway group and ATP report group themselves. To include the individual members of a group directly, give its `ListOfMembers` an ID and reference that ID instead. Here `reviewed_reactions` includes `step1` and `step2` through `pathway_members`. Keep references acyclic in either case.

```python
add_group("review", libsbml.GROUP_KIND_COLLECTION, "conversion_pathway", "atp_report")
pathway.getListOfMembers().setId("pathway_members")
add_group("reviewed_reactions", libsbml.GROUP_KIND_COLLECTION, "pathway_members")

path = Path("cell_pathways_groups.xml")
assert not validate_doc(doc).errors
write_sbml(doc, path)

reloaded = read_sbml(path)
assert not validate_doc(reloaded).errors
assert not reloaded.getPackageRequired("groups")
saved_groups = reloaded.getModel().getPlugin("groups")
assert saved_groups.getNumGroups() == 6
assert saved_groups.getGroup("atp_pools").getKind() == libsbml.GROUP_KIND_CLASSIFICATION
assert saved_groups.getGroup("cell_parts").getKind() == libsbml.GROUP_KIND_PARTONOMY

report = saved_groups.getGroup("atp_report")
assert report.getMember(0).getIdRef() == "total_atp"
assert report.getMember(1).getMetaIdRef() == "meta_total_atp_rule"
assert reloaded.getElementByMetaId("meta_total_atp_rule").getVariable() == "total_atp"

review = saved_groups.getGroup("review")
assert review.getMember(0).getIdRef() == "conversion_pathway"
reviewed_reactions = saved_groups.getGroup("reviewed_reactions")
assert reviewed_reactions.getMember(0).getIdRef() == "pathway_members"
listed = saved_groups.getGroup("conversion_pathway").getListOfMembers()
assert listed.getId() == "pathway_members"
assert [listed.get(i).getIdRef() for i in range(listed.size())] == ["step1", "step2"]
```
